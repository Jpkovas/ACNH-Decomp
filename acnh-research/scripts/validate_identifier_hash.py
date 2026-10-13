from __future__ import annotations
import argparse,ctypes,hashlib,json,random,subprocess
from pathlib import Path
import mmh3,unicorn
from unicorn import arm64_const as reg
ROOT=Path(__file__).resolve().parents[1]

def run(args,log):
    result=subprocess.run([str(a) for a in args],capture_output=True,text=True)
    log.write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError('Command failed: '+log.name)

def emulate(code,data,seed,alignment=0,invalid=False):
    uc=unicorn.Uc(unicorn.UC_ARCH_ARM64,unicorn.UC_MODE_ARM)
    uc.mem_map(0x1000,0x2000);uc.mem_write(0x1000,code)
    uc.mem_map(0x10000,0x2000)
    address=0x10000+alignment
    uc.mem_write(address,data+b'\0');uc.reg_write(reg.UC_ARM64_REG_X0,0 if invalid else address)
    uc.reg_write(reg.UC_ARM64_REG_X1,seed);uc.reg_write(reg.UC_ARM64_REG_X30,0x3000)
    uc.reg_write(reg.UC_ARM64_REG_SP,0x20000)
    saved=[0x12340000+i for i in range(19,30)]
    for i,v in zip(range(19,30),saved):uc.reg_write(getattr(reg,'UC_ARM64_REG_X'+str(i)),v)
    uc.emu_start(0x1000,0x3000,count=1000000)
    if [uc.reg_read(getattr(reg,'UC_ARM64_REG_X'+str(i))) for i in range(19,30)]!=saved or uc.reg_read(reg.UC_ARM64_REG_SP)!=0x20000:
        raise ValueError('Callee-saved register or stack divergence')
    return uc.reg_read(reg.UC_ARM64_REG_W0)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--version-id',choices=('1.0.0','3.0.3'),default='1.0.0');args=parser.parse_args()
    version=args.version_id;start,stop=(0x1bf0,0x1d1c) if version=='1.0.0' else (0x5bd550,0x5bd654)
    out=ROOT/'private/outputs'/version/'identifier-hash';out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((ROOT/'metadata'/version/'nso.json').read_text());text=(ROOT/'private/outputs'/version/'segments/text.bin').read_bytes()
    if hashlib.sha256(text).hexdigest()!=manifest['segments'][0]['sha256']:raise ValueError('Text provenance mismatch')
    original=text[start:stop];(out/'reference.bin').write_bytes(original)
    assembly='.text\n.p2align 2\n.globl acnh_murmur3_cstr\n.type acnh_murmur3_cstr,@function\nacnh_murmur3_cstr:\n.incbin "'+(out/'reference.bin').as_posix()+'"\n.size acnh_murmur3_cstr,.-acnh_murmur3_cstr\n'
    (out/'reference.s').write_text(assembly,encoding='utf-8')
    llvm=next((ROOT/'private/tools/llvm').iterdir())/'bin'
    flags=['--target=aarch64-none-elf','-O2','-ffreestanding','-fno-exceptions','-fno-rtti','-fno-stack-protector']
    run([llvm/'clang.exe','--target=aarch64-none-elf','-c',out/'reference.s','-o',out/'reference.o'],out/'reference-build.log')
    run([llvm/'clang++.exe',*flags,'-I',ROOT/'reconstructed/include','-c',ROOT/'reconstructed/src/identifier_hash.cpp','-o',out/'reconstructed.o'],out/'reconstructed-build.log')
    run([llvm/'llvm-objcopy.exe','--dump-section','.text='+str(out/'reconstructed.bin'),out/'reconstructed.o'],out/'objcopy.log')
    compiled=(out/'reconstructed.bin').read_bytes()
    run([ROOT/'private/tools/downloads/objdiff-cli-windows-x86_64.exe','diff','-1',out/'reference.o','-2',out/'reconstructed.o','-o',out/'objdiff.json','--format','json-pretty','acnh_murmur3_cstr'],out/'objdiff.log')
    dll=ctypes.CDLL(str(ROOT/'build/clang/identifier_hash.dll'));native=dll.acnh_murmur3_cstr
    native.argtypes=[ctypes.c_char_p,ctypes.c_uint32];native.restype=ctypes.c_uint32
    random_=random.Random(0x1BF0)
    cases=[(b'',seed) for seed in (0,1,0xffffffff)]+[(b'A'*n,seed) for n in range(0,20) for seed in (0,1,0xdeadbeef)]+[(bytes(random_.randrange(1,256) for _ in range(random_.randrange(1,256))),random_.getrandbits(32)) for _ in range(256)]
    cases+=[(b'ab\0ignored',0),(b'EventFlowQueryDummy',0),(b'EventFlowQueryCheckErrorType',0)]
    for data,seed in cases:
        expected=mmh3.hash(data.split(b'\0',1)[0],seed,signed=False)
        for alignment in (0,1,3):
            if emulate(original,data,seed,alignment)!=expected or emulate(compiled,data,seed,alignment)!=expected or native(data,seed)!=expected:
                raise ValueError('Identifier hash differential failure')
    invalid_cases=0
    for code in (original,compiled):
        try:emulate(code,b'',0,invalid=True)
        except unicorn.UcError as error:
            if error.errno!=unicorn.UC_ERR_READ_UNMAPPED:raise
            invalid_cases+=1
        else:raise ValueError('Invalid pointer did not fault as observed')
    identifiers=set()
    catalog=json.loads((ROOT/'private/outputs'/version/'eventflow/actions-queries.json').read_text())
    for entry in catalog:identifiers.add('EventFlow'+entry['kind']+entry['name'])
    for name in sorted(identifiers):
        data=name.encode('utf-8');expected=mmh3.hash(data,0,signed=False)
        if emulate(original,data,0)!=expected or emulate(compiled,data,0)!=expected or native(data,0)!=expected:raise ValueError('Observed identifier hash differs')
    diff=json.loads((out/'objdiff.json').read_text())
    matches=[s.get('match_percent') for s in diff['left']['sections'] if s.get('name')=='.text']
    report={'version_id':version,'module':'main','address':hex(0x7100000000+start),'relative_address':hex(start),'original_size':len(original),'compiled_size':len(compiled),
            'name':'acnh_murmur3_cstr','name_status':'inferred','confidence_behavior':'high','confidence_original_name':'unknown',
            'original_sha256':hashlib.sha256(original).hexdigest(),'equivalent_to':'MurmurHash3 x86_32 over NUL-terminated bytes and uint32 seed',
            'synthetic_cases':len(cases),'alignments':3,'observed_identifiers_checked':len(identifiers),'invalid_pointer_faults_verified':invalid_cases,
            'original_arm64_vs_python_vs_native_vs_recompiled_arm64':True,'exact_instruction_bytes':original==compiled,'objdiff_text_match_percent':matches[0] if matches else None,
            'flags':flags,'anchor':'Same-version initializer at 0x71004645e0 calls this function with seed zero and stores its result at region-relative 0x154 near the EventFlowQueryDummy label' if version=='1.0.0' else 'Independent target constant-load search; entry after padding at 0x71005bd550; control flow and avalanche reviewed through ret at 0x71005bd650',
            'precondition':'readable NUL-terminated byte string, length < 2^32; null pointer faults in original and reconstruction',
            'objdiff_report':'private/outputs/'+version+'/identifier-hash/objdiff.json'}
    (ROOT/'metadata'/version/'identifier-hash-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
