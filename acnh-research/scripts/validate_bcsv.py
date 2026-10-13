"""Differential validation against the independently maintained upstream parser."""
import argparse,json,subprocess,sys,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor/CylindricalEarth'))
import bcsv

def main():
    p=argparse.ArgumentParser();p.add_argument('romfs',type=Path);p.add_argument('--version-id',required=True);p.add_argument('--probe',type=Path,default=ROOT/'build/clang/bcsv_probe.exe');a=p.parse_args()
    checked=0;fields=0;cells=0;failed=[]
    for file in sorted(a.romfs.glob('Bcsv/*.bcsv')):
        try:
            oracle=bcsv.File(bcsv.Row);oracle.load(file.read_bytes())
            result=subprocess.run([str(a.probe.resolve()),str(file.resolve())],capture_output=True,text=True,check=True)
            lines=result.stdout.splitlines();header=list(map(int,lines[0].split()))
            if header[0]!=len(oracle.rows) or header[2]!=len(oracle.fields):raise ValueError('Table shape differs')
            for key,offset,size,crc in (map(int,line.split()) for line in lines[1:]):
                if oracle.fields[key]!=(offset,size):raise ValueError('Field layout differs')
                joined=b''.join(row._data[key] for row in oracle.rows)
                if zlib.crc32(joined)!=crc:raise ValueError('Field values differ')
                fields+=1;cells+=len(oracle.rows)
            checked+=1
        except Exception as e:failed.append({'name':file.name,'error':str(e)})
    report={'version_id':a.version_id,'tables_verified':checked,'fields_verified':fields,'cells_verified':cells,'failures':failed,
            'oracle':'CylindricalEarth bcsv.File(bcsv.Row)','scope':'every field byte slice in every row; semantic field types not inferred'}
    out=ROOT/'metadata'/a.version_id;out.mkdir(parents=True,exist_ok=True)
    (out/'bcsv-differential.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
    if failed:raise SystemExit(1)
if __name__=='__main__':main()
