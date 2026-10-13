"""Replace independently reviewed entries in private generated C.

Interior entry points keep interpreter fallback. This is source replacement, not
a blanket claim that generated functions were decompiled. Only ACNH 1.0.0.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def function_end(text: str, brace: int) -> int:
    pattern = re.compile(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[{}]', re.S)
    depth = 0
    for token in pattern.finditer(text, brace):
        if token[0] == '{':
            depth += 1
        elif token[0] == '}':
            depth -= 1
            if not depth:
                return token.end()
    raise ValueError('Unterminated generated function')


def main():
    expected = 'f8d248109ff72999b4600ae3749f8c7397fb960f7ad3ab8dee3018ae9e14e900'
    nso = ROOT/'private/windows/bridge/ACNH_1_0_0_data/exefs/main'
    if hashlib.sha256(nso.read_bytes()).hexdigest() != expected:
        raise ValueError('Refusing unreviewed executable version')
    generated = ROOT/'private/windows/bridge/ACNH_1_0_0_build'
    routines = {
        'F_8006BF0': ('unsigned acnh_murmur3_cstr(const char*, unsigned);',
                      'acnh_murmur3_cstr((const char*)(c->mem+c->x[0]),(unsigned)c->x[1])', 0x8006BF0),
        'F_800FC10': ('unsigned acnh_constant_zero(const void*);',
                      'acnh_constant_zero((const void*)(c->mem+c->x[0]))', 0x800FC10),
    }
    records = []
    for name, (declaration, call, address) in routines.items():
        matches = []
        for path in sorted(generated.glob('code_*.c')):
            text = path.read_text(encoding='utf-8')
            definition = re.search(r'void '+name+r'\(CPU\* RESTRICT c,u64 e\)\s*\{', text)
            if definition:
                matches.append((path, text, definition))
        if len(matches) != 1:
            raise ValueError(f'Expected exactly one definition of {name}, got {len(matches)}')
        path, text, definition = matches[0]
        end = function_end(text, definition.end()-1)
        body = f'''extern {declaration}
void {name}(CPU* RESTRICT c,u64 e) {{
 /* ACNH_RECONSTRUCTED: reviewed 1.0.0 entry; other entries retain fallback. */
 if(e!=0x{address:X}ull) {{ snx_interp_entry(c,e); return; }}
 c->pc=e;
 c->x[0]={call};
 c->pc=c->x[30];
}}'''
        start = definition.start()
        # On a repeat invocation leave the existing declaration in place.
        if 'ACNH_RECONSTRUCTED' in text[start:end]:
            pass
        else:
            path.write_text(text[:start]+body+text[end:], encoding='utf-8', newline='\n')
        records.append(dict(function=name, module='main', module_relative=hex(address-0x8005000),
                            generated_file=path.name,
                            evidence='Existing original ARM64 differential validation',
                            interior_entries='interpreter fallback'))
    sdk = ROOT/'private/windows/bridge/ACNH_1_0_0_data/exefs/sdk'
    if hashlib.sha256(sdk.read_bytes()).hexdigest() != '31ce67e8701584ba812dceeae9b590d7a6ad642bcb5aa74d2fe3ea5c5474250d':
        raise ValueError('Refusing unreviewed SDK version')
    validation = json.loads((ROOT/'metadata/windows/1.0.0/npad-full-key-validation.json').read_text())
    if validation['differential_cases'] < 3130 or not validation['original_arm64_unmodified']:
        raise ValueError('FullKey original differential evidence missing')
    if validation['cpp_source_sha256'] != hashlib.sha256((ROOT/'reconstructed/src/npad_full_key.cpp').read_bytes()).hexdigest():
        raise ValueError('FullKey C++ source changed after original validation')
    matches = []
    for candidate in sorted(generated.glob('code_*.c')):
        candidate_text = candidate.read_text(encoding='utf-8')
        candidate_definition = re.search(r'void F_C50CA00\(CPU\* RESTRICT c,u64 e\)\s*\{', candidate_text)
        if candidate_definition: matches.append((candidate,candidate_text,candidate_definition))
    if len(matches) != 1: raise ValueError('Expected exactly one reviewed SDK definition')
    path,text,definition = matches[0]
    end = function_end(text, definition.end()-1)
    if 'ACNH_RECONSTRUCTED' not in text[definition.start():end] or 'const unsigned*' not in text[max(0,definition.start()-200):definition.start()]:
        body = '''extern unsigned acnh_npad_full_key_states(int*,void*,int,const void*,const unsigned*,const unsigned char*,void*,void*);
void F_C50CA00(CPU* RESTRICT c,u64 e) {
 /* ACNH_RECONSTRUCTED: SDK FullKey reader; initializer remains original. */
 if(e!=0xC50CA00ull) { snx_interp_entry(c,e); return; }
 u64 count=c->x[0],states=c->x[1],capacity=c->x[2],device=c->x[3],lr=c->x[30];
 c->pc=e; c->x[30]=e+0x24;
 CALLDYN(0xC50BFD0ull);
 if(c->pc!=e+0x24) return;
 u32 id=*(u32*)(c->mem+device),index=id<8?id:id==0x10?9:8;
 u64 entry=__atomic_load_n((u64*)(c->mem+0xD427090ull+index*8),__ATOMIC_ACQUIRE);
 c->x[0]=acnh_npad_full_key_states((int*)(c->mem+count),c->mem+states,(int)capacity,
   entry?c->mem+entry:0,(const unsigned*)(c->mem+0xD4270E0ull),c->mem+0xD427160ull,0,0);
 c->x[30]=lr; c->pc=lr;
}'''
        prefix = re.sub(r'extern unsigned acnh_npad_full_key_states\([^;\n]*\);\s*$', '', text[:definition.start()])
        path.write_text(prefix+body+text[end:],encoding='utf-8',newline='\n')
    records.append(dict(function='F_C50CA00',module='sdk',module_relative='0x341a00',
        generated_file=path.name,evidence='npad-full-key-validation.json: original ARM64 comparisons',
        initializer='original SDK entry 0x340fd0',interior_entries='interpreter fallback'))
    for record in records:
        record['generated_file_sha256'] = hashlib.sha256((generated/record['generated_file']).read_bytes()).hexdigest()
    target = ROOT/'metadata/windows/1.0.0/reconstructed-replacements.json'
    target.write_text(json.dumps(dict(version_id='1.0.0', replacements=records,
                                     whole_game_decompiled=False), indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(replaced_entries=len(records), entire_game_decompiled=False)))


if __name__ == '__main__':
    main()
