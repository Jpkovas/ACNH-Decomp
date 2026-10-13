from __future__ import annotations
import argparse,hashlib,io,json,struct,sys
from collections import Counter
from pathlib import Path
import byml,sarc,zstandard
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor/CylindricalEarth'))
import msbt,pbc

def archive(file):
    raw=file.read_bytes()
    if raw[:4]==b'\x28\xb5\x2f\xfd':raw=zstandard.ZstdDecompressor().decompress(raw,max_output_size=512*1024*1024)
    return sarc.SARC(raw)

def main():
    p=argparse.ArgumentParser();p.add_argument('romfs',type=Path);p.add_argument('--version-id',required=True);a=p.parse_args()
    out=ROOT/'private/outputs'/a.version_id/'resources';out.mkdir(parents=True,exist_ok=True)
    messages=[];collisions=[];schemas=[];bindings=[];errors=[]
    for file in sorted((a.romfs/'Message').glob('*USen*.sarc.zs')):
        try:
            arc=archive(file)
            for name in arc.list_files():
                if not name.endswith('.msbt'):continue
                blob=bytes(arc.get_file_data(name));m=msbt.MSBT();m.load(blob)
                rebuilt=m.pack();check=msbt.MSBT();check.load(rebuilt)
                equivalent=all(k in check.data and v.text==check.data[k].text and v.attribute==check.data[k].attribute for k,v in m.data.items()) and len(m.data)==len(check.data)
                messages.append({'archive':file.name,'file':name,'messages':len(m.data),'sha256':hashlib.sha256(blob).hexdigest(),
                                 'labels':list(m.data),'roundtrip_structure':equivalent,'roundtrip_bytes':blob==rebuilt})
                if not equivalent:raise ValueError('MSBT round-trip divergence')
        except Exception as e:errors.append({'file':str(file.relative_to(a.romfs)),'format':'MSBT','error':type(e).__name__+': '+str(e)})
    for file in sorted((a.romfs/'Model').glob('*_pbc*.zs')):
        try:
            arc=archive(file)
            for name in arc.list_files():
                if not name.endswith('.pbc'):continue
                blob=bytes(arc.get_file_data(name))
                if len(blob)<20 or blob[:4]!=b'pbc\0':raise ValueError('Invalid PBC header')
                w,h,x,y=struct.unpack_from('<iiii',blob,4)
                if w<=0 or h<=0 or w*h>16*1024*1024 or 20+w*h*52>len(blob):raise ValueError('Invalid PBC bounds')
                oracle=pbc.PBC(blob)
                grid=bytearray(w*h*4)
                for row in range(h):
                    for col in range(w):
                        index=20+(row*w+col)*52
                        aa,bb,cc,dd=blob[index+48:index+52]
                        at=row*4*w+col*2;grid[at]=aa;grid[at+2*w]=bb;grid[at+2*w+1]=cc;grid[at+1]=dd
                if grid!=oracle.data:raise ValueError('PBC collision-grid divergence')
                collisions.append({'archive':file.name,'file':name,'width':w,'height':h,'offset':[x,y],
                                   'cell_bytes':52,'collision_counts':dict(Counter(grid)),
                                   'collision_grid_validated':True,'height_fields':'12 preceding words per cell remain uninterpreted'})
        except Exception as e:errors.append({'file':str(file.relative_to(a.romfs)),'format':'PBC','error':type(e).__name__+': '+str(e)})
    for file in sorted((a.romfs/'System/Smmh').glob('*.byml')):
        try:
            raw=file.read_bytes();parsed=byml.Byml(raw).parse()
            schemas.append({'file':file.name,'sha256':hashlib.sha256(raw).hexdigest(),'root_kind':type(parsed).__name__,'root_count':len(parsed)})
            (out/(file.stem+'.json')).write_text(json.dumps(parsed,indent=2,default=str)+'\n',encoding='utf-8')
        except Exception as e:errors.append({'file':str(file.relative_to(a.romfs)),'format':'SMMH/BYML','error':type(e).__name__+': '+str(e)})
    for file in sorted((a.romfs/'EventFlow/Info').glob('*.byml')):
        try:
            raw=file.read_bytes();parsed=byml.Byml(raw).parse()
            bindings.append({'file':file.name,'sha256':hashlib.sha256(raw).hexdigest(),'root_count':len(parsed)})
            (out/(file.stem+'.json')).write_text(json.dumps(parsed,indent=2,default=str)+'\n',encoding='utf-8')
        except Exception as e:errors.append({'file':str(file.relative_to(a.romfs)),'format':'EventFlow/BYML','error':type(e).__name__+': '+str(e)})
    report={'version_id':a.version_id,'messages':messages,'pbc':collisions,'save_schemas':schemas,'eventflow_info':bindings,'errors':errors}
    (out/'catalog.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    summary={'version_id':a.version_id,'message_language_sample':'USen','msbt_files':len(messages),'messages_indexed':sum(v['messages'] for v in messages),
             'msbt_roundtrips':sum(v['roundtrip_structure'] for v in messages),'pbc_files':len(collisions),'pbc_grids_validated':len(collisions),
             'save_schema_files':len(schemas),'eventflow_info_files':len(bindings),'errors':len(errors)}
    public=ROOT/'metadata'/a.version_id;public.mkdir(parents=True,exist_ok=True)
    (public/'resources-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary))
if __name__=='__main__':main()
