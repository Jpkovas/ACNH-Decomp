from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path
import lz4.block

def inspect(path:Path,out:Path|None=None)->dict:
    blob=path.read_bytes()
    if len(blob)<0x100 or blob[:4]!=b'NSO0':
        raise ValueError('Not a complete NSO0 header')
    flags=struct.unpack_from('<I',blob,0xC)[0]
    segments=[];contents=[]
    for i,name in enumerate(('.text','.rodata','.data')):
        file_at,mem_at,size=struct.unpack_from('<III',blob,0x10+i*0x10)
        compressed=bool(flags&(1<<i))
        stored=struct.unpack_from('<I',blob,0x60+i*4)[0] if compressed else size
        if file_at<0x100 or file_at+stored>len(blob) or size>512*1024*1024:
            raise ValueError('Invalid NSO segment bounds')
        raw=blob[file_at:file_at+stored]
        data=lz4.block.decompress(raw,uncompressed_size=size) if compressed else raw
        if len(data)!=size:
            raise ValueError('NSO decompressed length mismatch')
        digest=hashlib.sha256(data).hexdigest()
        hash_enabled=bool(flags&(1<<(3+i)))
        expected=blob[0xA0+i*0x20:0xC0+i*0x20].hex()
        if hash_enabled and digest!=expected:
            raise ValueError('NSO segment hash mismatch')
        segment={'name':name,'file_offset':file_at,'memory_offset':mem_at,'memory_size':size,
                 'stored_size':stored,'compressed':compressed,'sha256':digest,
                 'hash_verified':hash_enabled}
        segments.append(segment)
        contents.append((name,data))
    for a,b in zip(segments,segments[1:]):
        if a['memory_offset']+a['memory_size']>b['memory_offset']:
            raise ValueError('Overlapping NSO memory ranges')
    bss=struct.unpack_from('<I',blob,0x3C)[0]
    if out:
        out.mkdir(parents=True,exist_ok=True)
        for name,data in contents:
            target=out/(name[1:]+'.bin');temporary=target.with_suffix('.partial')
            temporary.write_bytes(data);temporary.replace(target)
    return {'format':'NSO0','version_id':None,'module':'main','input_sha256':hashlib.sha256(blob).hexdigest(),
            'file_size':len(blob),'module_id':blob[0x40:0x60].hex(),'header_flags':flags,
            'segments':segments,'bss_size':bss,'address_basis':'relative to image base; Ghidra base recorded separately'}

def main():
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('--version-id',required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--segments-dir',type=Path)
    a=p.parse_args();result=inspect(a.input,a.segments_dir);result['version_id']=a.version_id
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
