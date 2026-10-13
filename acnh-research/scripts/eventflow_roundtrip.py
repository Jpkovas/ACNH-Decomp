from __future__ import annotations
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from eventflow_catalog import parse_bfevfl,graph

def canonical(g):
    nodes={n['id']:n for n in g['nodes']};edges=dict(g['edges']);mapped={};records=[]
    def visit(name):
        if name is None:return None
        if name in mapped:return mapped[name]
        idx=len(records);mapped[name]=idx;records.append(None);node=nodes[name]
        record={k:v for k,v in node.items() if k not in ('id','next','cases','forks','join')}
        if 'next' in node:record['next']=visit(node['next'])
        if 'cases' in node:
            cases=sorted((v,dest) for dest,values in node['cases'].items() for v in values)
            record['cases']=[[v,visit(dest)] for v,dest in cases]
        if 'forks' in node:record['forks']=[visit(n) for n in node['forks']];record['join']=visit(node['join'])
        records[idx]=record;return idx
    roots=[]
    for r in sorted(g['entrypoints'],key=lambda r:r['name']):
        roots.append({**r,'first':visit(edges.get(r['name']))})
    return {'entrypoints':roots,'nodes':records}

def run(args,log):
    result=subprocess.run([sys.executable,str(ROOT/'scripts/invoke_upstream.py'),*args],capture_output=True,text=True)
    log.write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError('Upstream failed: '+log.name)

def main():
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('--version-id',required=True);a=p.parse_args()
    out=ROOT/'private/outputs'/a.version_id/'roundtrip';out.mkdir(parents=True,exist_ok=True)
    csv=ROOT/'private/outputs'/a.version_id/'eventflow/functions.csv'
    run(['decompiler','--functions',str(csv),'--out-dir',str(out),str(a.input.resolve())],out/'decompile.log')
    txt=out/(a.input.stem+'.evfl.txt');source=out/(a.input.stem+'.evfl')
    source.write_bytes(txt.read_bytes())
    result=out/(a.input.stem+'.bfevfl')
    run(['compiler','--functions',str(csv),'-o',str(result),str(source)],out/'compile.log')
    original=a.input.read_bytes();rebuilt=result.read_bytes()
    before=canonical(graph(parse_bfevfl(original)));after=canonical(graph(parse_bfevfl(rebuilt)))
    (out/'canonical-original.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
    (out/'canonical-rebuilt.json').write_text(json.dumps(after,indent=2)+'\n',encoding='utf-8')
    report={'version_id':a.version_id,'flow':a.input.name,'input_sha256':hashlib.sha256(original).hexdigest(),
            'rebuilt_sha256':hashlib.sha256(rebuilt).hexdigest(),'input_size':len(original),'rebuilt_size':len(rebuilt),
            'same_bytes':original==rebuilt,'rooted_graph_equivalent':before==after,
            'reachable_nodes':len(before['nodes']),'entries':len(before['entrypoints']),
            'equivalence_scope':'serialized actions, queries, parameters, branches, entry variables, rooted graph; engine handlers not emulated'}
    public=ROOT/'metadata'/a.version_id;public.mkdir(parents=True,exist_ok=True)
    (public/'roundtrip.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    if before!=after:raise SystemExit('Round-trip graph divergence')
if __name__=='__main__':main()
