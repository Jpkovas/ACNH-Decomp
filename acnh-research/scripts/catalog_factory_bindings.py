"""Recover a same-build sorted query-factory table from an independently proved anchor."""
from __future__ import annotations
import argparse,hashlib,json,struct,sys
from pathlib import Path
import capstone,mmh3
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from nxo_metadata import Image
from validate_identifier_hash import emulate

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--version-id',choices=('1.0.0','3.0.3'),default='1.0.0');args=parser.parse_args()
    version=args.version_id;image=Image(version);text=image.segments[0][1]
    if hashlib.sha256(text).hexdigest()!=image.manifest['segments'][0]['sha256']:raise ValueError('Text provenance differs')
    anchor=0x305bfb0 if version=='1.0.0' else 0x487fe70
    expected_factory=0x456bb0 if version=='1.0.0' else 0x1049734
    md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_LITTLE_ENDIAN);md.detail=True
    def entry(at):
        try:key=struct.unpack('<Q',image.read(at,8))[0]
        except ValueError:return None
        factory=image.relative.get(at+8)
        return (key,factory) if key<=0xffffffff and factory is not None and 0<factory<len(text) else None
    if entry(anchor)!=(0x1bb353cb,expected_factory):raise ValueError('Query-factory anchor differs')
    start=anchor;end=anchor+16
    while entry(start-16) and entry(start-16)[0]<entry(start)[0]:start-=16
    while entry(end) and entry(end-16)[0]<entry(end)[0]:end+=16
    catalog=json.loads((ROOT/'private/outputs'/version/'eventflow/actions-queries.json').read_text())
    bindings=json.loads((ROOT/'private/outputs'/version/'resources/BindInfo.json').read_text())
    names={'EventFlowQuery'+x['name'] for x in catalog if x['kind']=='Query'}
    aliases={b['Key']:b['Value'] for b in bindings['QueryBindData']}
    names.update(aliases);names.update(aliases.values())
    hashes={};collisions=[]
    original_hash=text[0x1bf0:0x1d1c] if version=='1.0.0' else text[0x5bd550:0x5bd654]
    for name in sorted(names):
        key=mmh3.hash(name.encode(),0,signed=False)
        if emulate(original_hash,name.encode(),0)!=key:raise ValueError('Original hash differs for binding name')
        if key in hashes:collisions.append([hashes[key],name])
        hashes[key]=name
    rows=[];linked=0
    for at in range(start,end,16):
        key,factory=entry(at);calls=[]
        for instruction in md.disasm(image.read(factory,min(512,len(text)-factory)),factory):
            if instruction.mnemonic=='bl':calls.append(instruction.operands[0].imm)
            if instruction.mnemonic=='ret':break
        row={'version_id':version,'key_address':hex(0x7100000000+at),'hash':f'{key:08x}','factory':hex(0x7100000000+factory),
             'binding_name':hashes.get(key),'name_status':'inferred','confidence':'medium','aliases':[k for k,v in aliases.items() if v==hashes.get(key)],
             'direct_calls':[hex(0x7100000000+x) for x in calls],'notes':'Factory-table hash identity; constructor/handler link requires per-entry assembly review'}
        if row['binding_name']:linked+=1
        rows.append(row)
    pilot=next(r for r in rows if r['hash']=='1bb353cb')
    if pilot['binding_name']!='EventFlowQueryEventFlagInt':raise ValueError('Pilot binding identity differs')
    if version=='1.0.0':
        if pilot['direct_calls']!=['0x7101967710','0x7100406280']:raise ValueError('Reference factory calls differ')
        if image.relative[0x32e0158]+0x10!=0x3056660 or image.relative[0x3056660+0x30]!=0x406390:raise ValueError('Reference vtable chain differs')
    else:
        if pilot['direct_calls']!=['0x7103f033a0','0x71002478c0'] or image.relative[0x4871920]!=0xf183d0:raise ValueError('Target factory/vtable chain differs')
        if [image.string(x) for x in (0x3f86b91,0x3f6c7c0,0x3fdf0be)]!=['AccessKey','Border','FlagCheckType']:raise ValueError('Target parameter labels differ')
    pilot.update(confidence='high',constructor='0x7100406280' if version=='1.0.0' else 'inlined in factory',
                 vtable='0x7103056660' if version=='1.0.0' else '0x71048718f0',handler='0x7100406390' if version=='1.0.0' else '0x7100f183d0',handler_slot='0x30',
                 allocation_bytes=0x138,allocation_alignment=8,
                 evidence=['same-version BindInfo alias targets','original ARM64 Murmur3 over binding names','sorted hash/factory table relocation','factory BL to constructor','constructor vptr','vtable handler relocation'])
    out=ROOT/'private/outputs'/version/'factory-bindings';out.mkdir(parents=True,exist_ok=True)
    (out/'queries.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    report={'version_id':version,'table_start':hex(0x7100000000+start),'table_end_exclusive':hex(0x7100000000+end),'entry_stride':16,
            'table_entries':len(rows),'bindings_matched':linked,'binding_names_original_hash_checked':len(names),'collisions_in_tested_names':collisions,
            'pilot':pilot,'limits':['Boundary inferred from monotonic contiguous hash/factory pairs; consumer array count not independently proved',
                                   'Matched names are logical binding identities, not recovered original C++ class declarations',
                                   'Only pilot constructor/vtable/handler chain individually validated; table and hash-function addresses independently reviewed per build']}
    (ROOT/'metadata'/version/'factory-bindings-summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'version_id':version,'entries':len(rows),'bindings_matched':linked,'hash_collisions':len(collisions),'pilot':pilot['binding_name']}))
if __name__=='__main__':main()
