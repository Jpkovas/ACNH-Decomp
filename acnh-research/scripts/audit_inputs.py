"""Audit packages without reading or exporting key and ticket values."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from datetime import datetime, timezone

def sha256(path: Path) -> str:
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()

def pfs_entries(path: Path) -> list[dict]:
    total = path.stat().st_size
    with path.open('rb') as f:
        header = f.read(16)
        if len(header) != 16 or header[:4] != b'PFS0':
            raise ValueError('Not PFS0')
        count, string_size, reserved = struct.unpack_from('<III', header, 4)
        base = 16 + count * 24 + string_size
        if count > 100000 or string_size > 16*1024*1024 or base > total:
            raise ValueError('Invalid PFS0 directory bounds')
        entries = f.read(count * 24)
        strings = f.read(string_size)
        result, ranges, names = [], [], set()
        for i in range(count):
            offset, size, name_at, unused = struct.unpack_from('<QQII', entries, i*24)
            end = strings.find(b'\0', name_at)
            if name_at >= len(strings) or end < 0:
                raise ValueError('Invalid PFS0 filename')
            name = strings[name_at:end].decode('utf-8', 'strict')
            reserved_name=name.split('.',1)[0].upper() in {'CON','PRN','AUX','NUL',*(f'COM{n}' for n in range(1,10)),*(f'LPT{n}' for n in range(1,10))}
            if not name or name.casefold() in names or any(c in name for c in '/\\:*?"<>|') or name.endswith(('.', ' ')) or reserved_name:
                raise ValueError('Unsafe or duplicate PFS0 filename')
            if offset + size > total-base:
                raise ValueError('PFS0 entry exceeds package')
            names.add(name.casefold())
            item = {'name': name, 'offset': base+offset, 'size': size}
            if name.endswith('.nca') and size>=0x204:
                f.seek(base+offset+0x200)
                item['plaintext_header'] = f.read(4) in (b'NCA2', b'NCA3')
            result.append(item)
            if size:
                ranges.append((offset, offset+size))
        ranges.sort()
        if any(a[1] > b[0] for a,b in zip(ranges,ranges[1:])):
            raise ValueError('Overlapping PFS0 entries')
        return result

def extract_pfs(path: Path, destination: Path) -> list[dict]:
    entries = pfs_entries(path)
    destination.mkdir(parents=True, exist_ok=True)
    with path.open('rb') as source:
        for entry in entries:
            target = destination / entry['name']
            if target.exists():
                if target.stat().st_size != entry['size']:
                    raise ValueError(f'Existing entry size differs: {target.name}')
                source.seek(entry['offset']);remaining=entry['size'];expected=hashlib.sha256()
                while remaining:
                    chunk=source.read(min(8*1024*1024,remaining))
                    if not chunk:raise ValueError('Truncated package during existing-entry verification')
                    expected.update(chunk);remaining-=len(chunk)
                if sha256(target)!=expected.hexdigest():raise ValueError('Existing entry content differs: '+target.name)
                continue
            temporary = target.with_suffix(target.suffix+'.partial')
            source.seek(entry['offset'])
            remaining = entry['size']
            with temporary.open('wb') as out:
                while remaining:
                    chunk = source.read(min(8*1024*1024, remaining))
                    if not chunk:
                        raise ValueError('Truncated package')
                    out.write(chunk)
                    remaining -= len(chunk)
            temporary.replace(target)
    return entries

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('input_dir',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--extract',type=Path)
    args=parser.parse_args()
    artifacts=[]
    for path in sorted(args.input_dir.glob('*.nsp')):
        entries=pfs_entries(path)
        version_claim=re.search(r'\[v(\d+)\]',path.name)
        display_claim=re.search(r'Up v([\d.]+)',path.name)
        entry={'filename':path.name,'title':'Animal Crossing: New Horizons',
               'size':path.stat().st_size,'sha256':sha256(path),'format':'PFS0',
               'origin':'user_supplied_origin_unverified',
               'package_version_filename_claim':int(version_claim[1]) if version_claim else None,
               'display_version_filename_claim':display_claim[1] if display_claim else None,
               'verified_display_version':None,'module_id':None,'entries':entries}
        artifacts.append(entry)
        print(f'Audited: {path.name}',flush=True)
        if args.extract:
            label='update' if '2326800' in path.name else ('base' if '2326000' in path.name else 'dlc-'+sha256(path)[:12])
            extract_pfs(path,args.extract/label)
        lock={'schema_version':1,'analysis_utc':datetime.now(timezone.utc).isoformat(),
              'secret_values_included':False,'artifacts':artifacts}
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(lock,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

if __name__=='__main__':
    main()
