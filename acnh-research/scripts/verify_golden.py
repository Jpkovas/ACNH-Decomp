"""Assert recorded data results against a manifest tied to each exact executable."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    golden=json.loads((ROOT/'tests/golden_manifest.json').read_text());checks=0
    for version,item in golden['versions'].items():
        nso=json.loads((ROOT/'metadata'/version/'nso.json').read_text())
        if nso['input_sha256']!=item['executable_sha256']:raise ValueError('Golden applies to another executable')
        for segment in nso['segments']:
            raw=ROOT/'private/outputs'/version/'segments'/(segment['name'][1:]+'.bin')
            if hashlib.sha256(raw.read_bytes()).hexdigest()!=segment['sha256']:raise ValueError('Private segment changed')
            checks+=1
        for file,expected in item['reports'].items():
            actual=json.loads((ROOT/'metadata'/version/file).read_text())
            for key,value in expected.items():
                if actual[key]!=value:raise ValueError(f'Golden differs: {version}/{file}:{key}')
                checks+=1
    report={'passed':True,'assertions':checks,'scope':'exact-input regression of recorded reports plus all six current decompressed segment hashes; does not rerun all experiments'}
    (ROOT/'metadata/golden-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
