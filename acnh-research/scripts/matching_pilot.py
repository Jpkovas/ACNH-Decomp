"""Measure one real function. Binary snippets and objdiff bodies stay private."""
from __future__ import annotations
import hashlib,json,random,struct,subprocess
from pathlib import Path
import unicorn
import capstone
from unicorn import arm64_const
ROOT=Path(__file__).resolve().parents[1]

def command(args,log):
    result=subprocess.run([str(v) for v in args],capture_output=True,text=True)
    log.write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError('Command failed: '+log.name)

def execute(code,values):
    uc=unicorn.Uc(unicorn.UC_ARCH_ARM64,unicorn.UC_MODE_ARM)
    uc.mem_map(0x1000,0x1000);uc.mem_write(0x1000,code)
    for i,value in enumerate(values):uc.reg_write(getattr(arm64_const,'UC_ARM64_REG_X'+str(i)),value)
    uc.reg_write(arm64_const.UC_ARM64_REG_X30,0x1000+len(code))
    uc.emu_start(0x1000,0x1000+len(code),count=10)
    return [uc.reg_read(getattr(arm64_const,'UC_ARM64_REG_X'+str(i))) for i in range(30)]

def main():
    out=ROOT/'private/outputs/1.0.0/matching';out.mkdir(parents=True,exist_ok=True)
    text=(ROOT/'private/outputs/1.0.0/segments/text.bin').read_bytes()
    original=text[0xAC10:0xAC18]
    decoder=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM)
    if [(i.mnemonic,i.op_str) for i in decoder.disasm(original,0x710000ac10)]!=[('mov','w0, wzr'),('ret','')]:
        raise ValueError('Pilot function behavior changed; review required')
    # Anchor is the same-version R_AARCH64_RELATIVE relocation in a function-pointer table.
    ro=(ROOT/'private/outputs/1.0.0/segments/rodata.bin').read_bytes()
    md=json.loads((ROOT/'metadata/1.0.0/nso.json').read_text())
    if hashlib.sha256(text).hexdigest()!=md['segments'][0]['sha256']:raise ValueError('Uncompressed text hash differs from the inspected NSO')
    start=0x2212040-md['segments'][1]['memory_offset'];rela=ro[start:start+0x6f63d8]
    if (0x301CA30,1027,0xAC10) not in list(struct.iter_unpack('<QQq',rela)):
        raise ValueError('Pilot function pointer anchor absent')
    (out/'reference.bin').write_bytes(original)
    assembly='.text\n.p2align 2\n.globl acnh_constant_zero\n.type acnh_constant_zero,@function\nacnh_constant_zero:\n.incbin "'+(out/'reference.bin').as_posix()+'"\n.size acnh_constant_zero,.-acnh_constant_zero\n'
    (out/'reference.s').write_text(assembly,encoding='utf-8')
    llvm=next((ROOT/'private/tools/llvm').iterdir())/'bin'
    flags=['--target=aarch64-none-elf','-O2','-ffreestanding','-fno-exceptions','-fno-rtti','-fno-stack-protector']
    command([llvm/'clang.exe','--target=aarch64-none-elf','-c',out/'reference.s','-o',out/'reference.o'],out/'reference-build.log')
    command([llvm/'clang++.exe',*flags,'-I',ROOT/'reconstructed/include','-c',ROOT/'reconstructed/src/constant_zero.cpp','-o',out/'reconstructed.o'],out/'reconstructed-build.log')
    command([llvm/'llvm-objcopy.exe','--dump-section','.text='+str(out/'reconstructed.bin'),out/'reconstructed.o'],out/'objcopy.log')
    command([ROOT/'private/tools/downloads/objdiff-cli-windows-x86_64.exe','diff','-1',out/'reference.o','-2',out/'reconstructed.o','-o',out/'objdiff.json','--format','json-pretty','acnh_constant_zero'],out/'objdiff.log')
    compiled=(out/'reconstructed.bin').read_bytes()
    rnd=random.Random(0xAC10);cases=[[v]*30 for v in (0,1,0xffffffffffffffff)]+[[rnd.getrandbits(64) for _ in range(30)] for _ in range(128)]
    for values in cases:
        before=execute(original,values);after=execute(compiled,values)
        if before!=after or before[0]!=0 or before[1:]!=values[1:]:raise ValueError('ARM64 behavior or register-preservation divergence')
    report={'version_id':'1.0.0','module':'main','address':'0x710000ac10','relative_address':'0xac10','size':len(original),
            'function_label':'acnh_constant_zero','name_status':'inferred','confidence_behavior':'high','confidence_original_signature':'low',
            'anchor':{'kind':'relative relocation in function-pointer table','address':'0x710301ca30','relocation_type':'R_AARCH64_RELATIVE'},
            'original_classification':'unknown constant-return method; EventFlow membership not established',
            'original_sha256':hashlib.sha256(original).hexdigest(),'compiled_sha256':hashlib.sha256(compiled).hexdigest(),
            'exact_instruction_bytes':original==compiled,'bytes_equal':sum(a==b for a,b in zip(original,compiled)),
            'compiler':'Clang 23.1.3','flags':flags,'behavior_cases':len(cases),'arm64_emulator':'Unicorn 2.1.4',
            'objdiff_report':'private/outputs/1.0.0/matching/objdiff.json','original_compiler_identified':False,
            'scope':'one 8-byte function; no whole-game matching percentage'}
    (ROOT/'metadata/1.0.0/matching-pilot.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
