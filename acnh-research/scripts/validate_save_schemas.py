"""Validate per-file hashed SMMH layouts; never reuse historical names as facts."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import byml
ROOT=Path(__file__).resolve().parents[1]
TYPE='5c65d8b5';MEMBERS='a2fb4a94';NAME='25efa387';SIZE='b4a58247';OFFSET='a7bb2e42';LENGTH='1e0eae33';LENGTH2='a9f41a61';ALIGN='4a4cb5b4'

def validate(entries):
    if not isinstance(entries,list):raise ValueError('SMMH root must be a list')
    types={};fields=0;overlaps=0;gaps=0;nested_checks=0
    for t in entries:
        type_id=t[TYPE];size=t[SIZE];align=t[ALIGN]
        if type_id in types:raise ValueError('Duplicate type in file')
        if size<0 or align<1 or align&(align-1) or size%align:raise ValueError('Invalid type size/alignment')
        types[type_id]=t
    for t in entries:
        intervals=[];ids=set()
        for f in t[MEMBERS]:
            length=f[LENGTH]*f.get(LENGTH2,1);offset=f[OFFSET];size=f[SIZE];align=f[ALIGN]
            if f[NAME] in ids:raise ValueError('Duplicate field in type')
            ids.add(f[NAME])
            if size<0 or f[LENGTH]<0 or f.get(LENGTH2,1)<0 or offset<0 or offset+size*length>t[SIZE]:raise ValueError('Field outside type bounds')
            if align<1 or align&(align-1) or offset%align or size%align:raise ValueError('Invalid field alignment')
            if f[TYPE] in types:
                if types[f[TYPE]][SIZE]!=size or types[f[TYPE]][ALIGN]!=align:raise ValueError('Nested type size/alignment mismatch')
                nested_checks+=1
            intervals.append((offset,offset+size*length));fields+=1
        end=0
        for start,stop in sorted(intervals):
            if start<end:overlaps+=1
            elif start>end:gaps+=1
            end=max(end,stop)
        if end<t[SIZE]:gaps+=1
    return {'types':len(types),'fields':fields,'nested_layout_checks':nested_checks,'overlapping_ranges':overlaps,'padding_gaps':gaps}

def main():
    p=argparse.ArgumentParser();p.add_argument('romfs',type=Path);p.add_argument('--version-id',required=True);a=p.parse_args()
    out=ROOT/'private/outputs'/a.version_id/'save-layouts';out.mkdir(parents=True,exist_ok=True)
    files=[];errors=[]
    for file in sorted((a.romfs/'System/Smmh').glob('*.byml')):
        try:
            raw=file.read_bytes();original=byml.Byml(raw).parse();stats=validate(original)
            rebuilt=byml.Writer(original,be=False,version=2).get_bytes();reread=byml.Byml(rebuilt).parse()
            if reread!=original:raise ValueError('BYML round-trip structure differs')
            (out/file.name).write_bytes(rebuilt)
            files.append({'file':file.name,'sha256':hashlib.sha256(raw).hexdigest(),**stats,'roundtrip_structure':True})
        except Exception as e:errors.append({'file':file.name,'error':type(e).__name__+': '+str(e)})
    (out/'catalog.json').write_text(json.dumps({'version_id':a.version_id,'files':files,'errors':errors},indent=2)+'\n',encoding='utf-8')
    report={'version_id':a.version_id,'files_checked':len(files),'layout_occurrences':sum(f['types'] for f in files),
            'field_occurrences':sum(f['fields'] for f in files),'nested_layout_checks':sum(f['nested_layout_checks'] for f in files),
            'overlapping_ranges':sum(f['overlapping_ranges'] for f in files),'padding_gaps':sum(f['padding_gaps'] for f in files),
            'structural_roundtrips':len(files),'errors':len(errors),'hash_names':'preserved as numeric identifiers; historical names not promoted',
            'coverage':'all System/Smmh BYML files in this RomFS; schema offsets only, no real save instance or executable consumer validated'}
    (ROOT/'metadata'/a.version_id/'save-layout-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
    if errors:raise SystemExit(1)
if __name__=='__main__':main()
