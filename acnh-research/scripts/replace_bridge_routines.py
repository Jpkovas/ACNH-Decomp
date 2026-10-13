"""Replace two independently reviewed entry points in private generated C.

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
        records.append(dict(function=name, module_relative=hex(address-0x8005000),
                            generated_file=path.name,
                            evidence='Existing original ARM64 differential validation',
                            interior_entries='interpreter fallback'))
    for record in records:
        record['generated_file_sha256'] = hashlib.sha256((generated/record['generated_file']).read_bytes()).hexdigest()
    target = ROOT/'metadata/windows/1.0.0/reconstructed-replacements.json'
    target.write_text(json.dumps(dict(version_id='1.0.0', replacements=records,
                                     whole_game_decompiled=False), indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(replaced_entries=len(records), entire_game_decompiled=False)))


if __name__ == '__main__':
    main()
