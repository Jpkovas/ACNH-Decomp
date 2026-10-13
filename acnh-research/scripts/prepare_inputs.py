"""Use the user's local keyset; never print or persist tool key output."""
from __future__ import annotations
import argparse
import json
import os
import re
import struct
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def sanitized(text: str) -> str:
    lines=[]
    for line in text.splitlines():
        if re.search(r'titlekey|key area|decrypted key|encrypted key|key \d|master_key|header_key',line,re.I):
            continue
        lines.append(re.sub(r'\b[0-9a-fA-F]{32,}\b','[redacted]',line))
    return '\n'.join(lines)+'\n'

def environment(packages: Path) -> dict:
    keydir=ROOT/'private/key-config/switch'
    keydir.mkdir(parents=True,exist_ok=True)
    values=[]
    for ticket in sorted(packages.glob('**/*.tik')):
        raw=ticket.read_bytes()
        signature=struct.unpack_from('<I',raw)[0]
        base={0x10000:0x240,0x10003:0x240,0x10001:0x140,0x10004:0x140,0x10002:0x80,0x10005:0x80}.get(signature)
        if base is None or len(raw)<base+0x170:
            raise ValueError('Unsupported ticket layout')
        if raw[base+0x141] != 0:
            raise ValueError('Personalized ticket requires a separate authorized extraction workflow')
        values.append(raw[base+0x160:base+0x170].hex()+' = '+raw[base+0x40:base+0x50].hex())
    (keydir/'title.keys').write_text('\n'.join(values)+'\n',encoding='ascii')
    env=os.environ.copy()
    env['XDG_CONFIG_HOME']=str(keydir.parent)
    return env

def run(tool:Path,keys:Path,env:dict,nca:Path,args:list[str],log:Path) -> str:
    command=[str(tool),'-k',str(keys),'--disablekeywarns','--suppresskeys',*args,str(nca)]
    proc=subprocess.run(command,env=env,capture_output=True)
    clean=sanitized(proc.stdout.decode('utf-8','replace')+proc.stderr.decode('utf-8','replace'))
    log.parent.mkdir(parents=True,exist_ok=True)
    log.write_text(clean,encoding='utf-8')
    if proc.returncode or re.search(r'Error:|Invalid NCA|Failed to|Unable to',clean,re.I):
        raise RuntimeError(f'hactool failed; sanitized log: {log.name}; exit {proc.returncode}')
    return clean

def compatible_keyset(source: Path) -> Path:
    selected=[]
    for line in source.read_text(encoding='utf-8-sig').splitlines():
        if '=' not in line:
            continue
        name,value=(x.strip() for x in line.split('=',1))
        name=name.lower()
        if name=='header_key' or re.fullmatch(r'(titlekek|master_key|key_area_key_application|key_area_key_ocean|key_area_key_system)_[0-9a-f]{2}',name):
            if value.startswith(('0x','0X')):
                value=value[2:]
            expected=64 if name=='header_key' else 32
            if len(value)!=expected or not re.fullmatch(r'[0-9a-fA-F]+',value):
                raise ValueError('Invalid supplied key encoding for '+name)
            selected.append(name+' = '+value)
    target=ROOT/'private/key-config/research.keys'
    target.write_text('\n'.join(selected)+'\n',encoding='ascii')
    return target

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--keys',type=Path,required=True)
    parser.add_argument('--extract',action='store_true')
    parser.add_argument('--package',choices=('base','update','both'),default='both')
    parser.add_argument('--tool',type=Path)
    args=parser.parse_args()
    packages=ROOT/'private/inputs/packages'
    tool=args.tool.resolve() if args.tool else ROOT/'private/tools/hactool/hactool.exe'
    env=environment(packages)
    keys=compatible_keyset(args.keys.resolve())
    inventory=[]
    programs={}
    selected=('base','update') if args.package=='both' else (args.package,)
    for label in selected:
        for nca in sorted((packages/label).glob('*.nca')):
            clean=run(tool,keys,env,nca,['-i'],ROOT/f'private/outputs/preparation/{label}-{nca.stem}.log')
            metadata={'package':label,'nca':nca.name}
            for key,pattern in {'content_type':r'^Content Type:\s*(.+)$','title_id':r'^Title ID:\s*(.+)$','sdk':r'^SDK Version:\s*(.+)$','master_key_revision':r'^Master Key Revision:\s*(.+)$'}.items():
                match=re.search(pattern,clean,re.M)
                metadata[key]=match[1].strip() if match else None
            inventory.append(metadata)
            if metadata['content_type']=='Program':
                programs[label]=nca
            print(f'{label}/{nca.name}: {metadata["content_type"]}',flush=True)
    (ROOT/'metadata').mkdir(exist_ok=True)
    inventory_file=ROOT/'metadata/package_inventory.json'
    previous=json.loads(inventory_file.read_text(encoding='utf-8')) if inventory_file.exists() else []
    inventory=[m for m in previous if m['package'] not in selected]+inventory
    inventory_file.write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')
    if not args.extract:
        return
    for label in selected:
        if label not in programs:
            raise ValueError('Missing Program NCA: '+label)
        out=ROOT/'private/inputs/extracted'/label
        out.mkdir(parents=True,exist_ok=True)
        options=['-x','--exefsdir',str(out/'exefs'),'--romfsdir',str(out/'romfs')]
        if label=='update':
            base=programs.get('base') or max((packages/'base').glob('*.nca'),key=lambda p:p.stat().st_size)
            options+=['--basenca',str(base)]
        run(tool,keys,env,programs[label],options,ROOT/f'private/outputs/preparation/extract-{label}.log')
        main=out/'exefs/main'
        if not main.is_file() or main.read_bytes()[:4]!=b'NSO0':
            raise RuntimeError('Extraction did not produce NSO0 main: '+label)
        print(f'Extracted {label}: NSO0 main and RomFS',flush=True)

if __name__=='__main__':
    main()
