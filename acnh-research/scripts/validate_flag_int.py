"""Differential-check the actual terminal region, without patching its instructions."""
from __future__ import annotations
import argparse,ctypes,hashlib,json,random,struct,sys
from pathlib import Path
import unicorn
from unicorn import arm64_const as reg
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from nxo_metadata import Image
REGIONS={
 '1.0.0':{'code_page':0x406000,'table_page':0x29f1000,'start':0x40685c,'stop':0x406a2c,'handler':0x406390,'vtable':0x3056660,'vptr_got':0x32e0158},
 '3.0.3':{'code_page':0xf18000,'table_page':0x406a000,'start':0xf188d4,'stop':0xf18a6c,'handler':0xf183d0,'vtable':0x48718f0,'vptr_got':None}
}

def original(image,value,border,mode):
    uc=unicorn.Uc(unicorn.UC_ARCH_ARM64,unicorn.UC_MODE_ARM)
    base=0x7100000000
    region=REGIONS[image.version]
    for at in (region['code_page'],region['table_page']):
        uc.mem_map(base+at,0x1000);uc.mem_write(base+at,image.read(at,0x1000))
    uc.mem_map(0x400000,0x2000);uc.mem_map(0x500000,0x1000)
    obj=bytearray(0x200);struct.pack_into('<I',obj,0x100,border&0xffffffff);struct.pack_into('<I',obj,0x128,mode)
    uc.mem_write(0x500000,bytes(obj));uc.reg_write(reg.UC_ARM64_REG_X19,0x500000)
    uc.reg_write(reg.UC_ARM64_REG_X29,0x401000);uc.reg_write(reg.UC_ARM64_REG_W0,value)
    uc.reg_write(reg.UC_ARM64_REG_SP,0x401000)
    def stop(uc,address,size,userdata):
        if address==base+region['stop']:uc.emu_stop()
    uc.hook_add(unicorn.UC_HOOK_CODE,stop)
    uc.emu_start(base+region['start'],base+region['stop']+4,count=1000)
    if uc.reg_read(reg.UC_ARM64_REG_PC)!=base+region['stop']:raise ValueError('Unexpected terminal control flow')
    if uc.mem_read(0x500000,0x200)!=obj:raise ValueError('Predicate modified query object')
    return uc.reg_read(reg.UC_ARM64_REG_W0)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--version-id',choices=REGIONS,default='1.0.0');args=parser.parse_args()
    image=Image(args.version_id);region=REGIONS[args.version_id]
    for s,(_,data) in zip(image.manifest['segments'],image.segments):
        if hashlib.sha256(data).hexdigest()!=s['sha256']:raise ValueError('NSO segment provenance mismatch')
    dll=ctypes.CDLL(str(ROOT/'build/clang/flag_int.dll'));fn=dll.acnh_flag_int_predicate
    fn.argtypes=[ctypes.c_uint32,ctypes.c_int32,ctypes.c_uint32];fn.restype=ctypes.c_uint32
    rng=random.Random(0x40685c)
    pairs=[(v,b) for v in (0,1,2,3,31,32,0x7fffffff,0x80000000,0xfffffffe,0xffffffff) for b in (-2147483648,-1,0,1,2,31,32,33,2147483647)]
    pairs += [(rng.getrandbits(32),ctypes.c_int32(rng.getrandbits(32)).value) for _ in range(256)]
    modes=range(10);count=0
    for value,border in pairs:
        for mode in list(modes)+[0xffffffff]:
            limit=border&0xffffffff
            expected=int((value!=limit,value==limit,value<=limit,value<limit,value>=limit,value>limit,value.bit_count()<border)[mode]) if mode<7 else 0
            if original(image,value,border,mode)!=expected or fn(value,border,mode)!=expected:raise ValueError('Predicate divergence')
            count+=1
    vtable=region['vtable']
    if region['vptr_got'] and image.relative[region['vptr_got']]+0x10!=vtable:raise ValueError('Constructor vptr anchor changed')
    if image.relative[vtable+0x30]!=region['handler']:raise ValueError('Vtable handler anchor changed')
    if args.version_id=='3.0.3':
        if struct.unpack('<Q',image.read(0x487fe70,8))[0]!=0x1bb353cb or image.relative[0x487fe78]!=0x1049734:raise ValueError('Target factory binding differs')
        if [image.string(x) for x in (0x3f86b91,0x3f6c7c0,0x3fdf0be)]!=['AccessKey','Border','FlagCheckType']:raise ValueError('Target factory parameter labels differ')
    report={'version_id':args.version_id,'module':'main','handler_address':hex(0x7100000000+region['handler']),
            'constructor_address':'0x7100406280' if args.version_id=='1.0.0' else 'inlined in factory 0x7101049734',
            'vtable_address':hex(0x7100000000+vtable),'handler_slot':'0x30','validated_region':hex(0x7100000000+region['start'])+'..'+hex(0x7100000000+region['stop']),
            'terminal_region_sha256':hashlib.sha256(image.read(region['start'],region['stop']-region['start'])).hexdigest(),'differential_cases':count,
            'input_pairs':len(pairs),'check_types':[0,1,2,3,4,5,6,7,8,9,0xffffffff],'object_write_divergences':0,
            'original_arm64_vs_native_vs_independent_oracle':True,'comparison_modes':['not_equal','equal','unsigned_less_equal','unsigned_less','unsigned_greater_equal','unsigned_greater','popcount_less_than_signed_border'],
            'parameters_validated':{'border':{'offset':'0x100','size':4},'check_type':{'offset':'0x128','size':4}},
            'name_status':'inferred','name_confidence':'high for logical binding identity; original C++ class name unknown','behavior_confidence':'high',
            'inferred_binding':'EventFlagInt; same-version constructor labels AccessKey, Border, FlagCheckType and BindInfo maps NpcInt/SystemInt aliases to EventFlagInt',
            'limitations':['Only terminal comparison region validated against original ARM64; full handler includes access-key parsing and multiple SaveIO backends',
                           'C++ query uses an injected value reader; backend effects and original C++ declaration are not proved',
                           'Base Ghidra initially omitted the virtual handler and some indirect-switch blocks; target addresses were independently located through its own relocation/data/assembly chain',
                           'Only the terminal contract is compared between versions; backend behavior is not transferred'],
            'binding_chain_evidence':'metadata/1.0.0/factory-bindings-summary.json' if args.version_id=='1.0.0' else 'metadata/3.0.3/reviewed-annotations.json; table key independently located at 0x710487fe70'}
    (ROOT/'metadata'/args.version_id/'flag-int-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
