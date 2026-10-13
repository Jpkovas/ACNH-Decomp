"""Verify the intended versioned surface; do not read ignored private content."""
from __future__ import annotations
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT.parent
def main():
    base=['git','-c','safe.directory='+WORKSPACE.as_posix(),'-C',str(WORKSPACE)]
    result=subprocess.run([*base,'ls-files','--cached','--others','--exclude-standard','-z'],capture_output=True,check=True)
    paths=sorted(set(x.decode('utf-8') for x in result.stdout.split(b'\0') if x));errors=[];records=[]
    forbidden_suffixes={'.keys','.nsp','.nca','.xci','.tik','.cert','.bfevfl','.bcsv','.msbt','.bfres','.bntx','.pbc','.gpr','.pyc','.bin','.dll','.exe'}
    for relative in paths:
        path=WORKSPACE/relative
        if relative.startswith(('gamedump/','acnh-research/private/','acnh-research/vendor/','acnh-research/build/')) or path.suffix.lower() in forbidden_suffixes:
            errors.append('Unexpected private/binary path: '+relative);continue
        raw=path.read_bytes()
        if re.search(rb'(?im)^\s*(?:header_key|master_key_[0-9a-f]{2}|titlekek_[0-9a-f]{2})\s*=\s*(?:0x)?[0-9a-f]{32,}\s*$',raw):errors.append('Secret assignment in '+relative)
        if len(raw)>2*1024*1024:errors.append('Unexpectedly large versioned artifact: '+relative)
        records.append({'path':relative,'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    ignores=['gamedump/prod.keys','gamedump/sample.nsp','acnh-research/private/probe.bin','acnh-research/vendor/check/LICENSE','acnh-research/build/check.exe']
    ignored=subprocess.run([*base,'check-ignore',*ignores],capture_output=True,text=True,check=True).stdout.splitlines()
    if set(ignored)!=set(ignores):errors.append('Required ignore coverage missing')
    report={'passed':not errors,'files_checked':len(records),'required_ignores_checked':len(ignores),'errors':errors,
            'scope':'intended Git paths and secret-assignment patterns; not a legal determination or whole-disk secret scan'}
    (ROOT/'private/outputs/versioned-files-audit.json').write_text(json.dumps({'summary':report,'files':records},indent=2)+'\n',encoding='utf-8')
    (ROOT/'metadata/versioned-files-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
    if errors:raise SystemExit(1)
if __name__=='__main__':main()
