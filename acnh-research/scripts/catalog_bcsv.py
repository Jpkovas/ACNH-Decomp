import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from bcsv_format import parse_bcsv

def main():
    p=argparse.ArgumentParser();p.add_argument('romfs',type=Path);p.add_argument('--version-id',required=True);a=p.parse_args()
    tables=[];errors=[]
    for file in sorted(a.romfs.glob('Bcsv/*.bcsv')):
        try:
            raw=file.read_bytes();tables.append({'name':file.name,'sha256':hashlib.sha256(raw).hexdigest(),**parse_bcsv(raw)})
        except Exception as e:errors.append({'name':file.name,'error':str(e)})
    out=ROOT/'private/outputs'/a.version_id/'bcsv';out.mkdir(parents=True,exist_ok=True)
    (out/'catalog.json').write_text(json.dumps({'version_id':a.version_id,'tables':tables,'errors':errors},indent=2)+'\n',encoding='utf-8')
    summary={'version_id':a.version_id,'tables':len(tables),'errors':len(errors),'rows':sum(t['rows'] for t in tables),
             'fields':sum(len(t['fields']) for t in tables),'field_type_status':'unknown unless individually reviewed'}
    public=ROOT/'metadata'/a.version_id;public.mkdir(parents=True,exist_ok=True)
    (public/'bcsv-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary))
if __name__=='__main__':main()
