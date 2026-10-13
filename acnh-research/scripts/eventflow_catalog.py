"""Version-specific structural extraction using the reviewed ACNH decompiler."""
from __future__ import annotations
import argparse,csv,hashlib,json,sys
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor/acnh-eventflow-decompiler'))
from decompiler.bfevfl import parse_bfevfl
from decompiler.nodes import ActionNode,SwitchNode,SubflowNode,ForkNode,JoinNode
from decompiler.datatype import Argument,ActorMarker,infer_types

def value(v):
    if isinstance(v,Argument):return {'argument':str(v)}
    if isinstance(v,ActorMarker):return {'actor_argument':list(v)}
    if isinstance(v,dict):return {k:value(x) for k,x in sorted(v.items())}
    if isinstance(v,(list,tuple)):return [value(x) for x in v]
    return v

def graph(flow):
    nodes=[]
    for node in flow.nodes:
        row={'id':node.name,'kind':type(node).__name__}
        if hasattr(node,'params'):row['params']=value(node.params)
        if isinstance(node,ActionNode):row.update(actor=list(node.action.actor_name),function=node.action.name,next=node.nxt)
        elif isinstance(node,SwitchNode):row.update(actor=list(node.query.actor_name),function=node.query.name,cases={k:sorted(v) for k,v in sorted(node.cases.items())})
        elif isinstance(node,SubflowNode):row.update(flowchart=node.ns,entrypoint=node.called_root_name,next=node.nxt)
        elif isinstance(node,ForkNode):row.update(forks=node.forks,join=node.join_node.name)
        elif isinstance(node,JoinNode):row.update(next=node.nxt)
        nodes.append(row)
    roots=[{'name':r.name,'variables':[{'name':v.name,'type':str(v.type_),'initial':v.initial_value} for v in r.vardefs]} for r in flow.roots]
    known={n['id'] for n in nodes}|{r['name'] for r in roots}
    if any(a not in known or b not in known for a,b in flow.edges):raise ValueError('Orphan graph edge')
    return {'flowchart':flow.flowchart_name,'entrypoints':roots,'nodes':nodes,'edges':flow.edges}

def main():
    p=argparse.ArgumentParser();p.add_argument('romfs',type=Path);p.add_argument('--version-id',required=True);a=p.parse_args()
    out=ROOT/'private/outputs'/a.version_id/'eventflow';out.mkdir(parents=True,exist_ok=True)
    rows=[];errors=[];functions={};param_conflicts=defaultdict(set)
    for file in sorted(a.romfs.glob('EventFlow/*.bfevfl')):
        try:
            raw=file.read_bytes();flow=parse_bfevfl(raw);g=graph(flow)
            g['version_id']=a.version_id;g['input_sha256']=hashlib.sha256(raw).hexdigest()
            (out/(file.stem+'.graph.json')).write_text(json.dumps(g,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
            rows.append({'file':file.name,'sha256':g['input_sha256'],'nodes':len(flow.nodes),'edges':len(flow.edges),'actors':len(flow.actors),'entrypoints':len(flow.roots)})
            for node in flow.nodes:
                if not isinstance(node,(ActionNode,SwitchNode)):continue
                function=node.action if isinstance(node,ActionNode) else node.query
                kind='Action' if isinstance(node,ActionNode) else 'Query'
                types={k:str(v) for k,v in infer_types(node.params).items()}
                key=(kind,function.name)
                if key not in functions:functions[key]={'params':types,'actors':set(),'cases':set(),'uses':0}
                item=functions[key];item['uses']+=1;item['actors'].add(function.actor_name)
                if item['params']!=types:param_conflicts[key].add(tuple(sorted(types.items())))
                if kind=='Query':
                    for values in node.cases.values():item['cases'].update(values)
        except Exception as error:
            errors.append({'file':file.name,'error':type(error).__name__+': '+str(error)})
    headers=['Type','Name','Parameters','Return','ConversionKey','Conversion','NegatedConversion','ParseType','ParseRule']
    with (out/'functions.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(headers)
        for (kind,name),item in sorted(functions.items()):
            # A case range is observed usage, not proof of the handler return domain.
            ret='int' if kind=='Query' else ''
            params='; '.join(k+': '+('any' if t=='_argument' else t) for k,t in item['params'].items())
            writer.writerow([kind,name,params,ret,'','','','function' if kind=='Query' else '',''])
    catalog=[]
    for (kind,name),item in sorted(functions.items()):
        catalog.append({'version_id':a.version_id,'kind':kind,'name':name,'parameters_observed':item['params'],
                        'actors':[list(v) for v in sorted(item['actors'])],'case_values_observed':sorted(item['cases']),
                        'uses':item['uses'],'confidence':'medium','name_status':'original',
                        'evidence':'same-version EventFlow serialized function name and parameter encodings',
                        'return_domain_verified':False,'parameter_conflicts':bool(param_conflicts[(kind,name)])})
    (out/'actions-queries.json').write_text(json.dumps(catalog,indent=2)+'\n',encoding='utf-8')
    (out/'catalog.json').write_text(json.dumps({'version_id':a.version_id,'flows':rows,'errors':errors},indent=2)+'\n',encoding='utf-8')
    summary={'version_id':a.version_id,'files':len(rows)+len(errors),'parsed':len(rows),'errors':len(errors),
             'actions':sum(k[0]=='Action' for k in functions),'queries':sum(k[0]=='Query' for k in functions),
             'parameter_conflicts':len([x for x in param_conflicts.values() if x]),'functions_csv_scope':'observed signatures; return domains unverified'}
    public=ROOT/'metadata'/a.version_id;public.mkdir(parents=True,exist_ok=True)
    (public/'eventflow-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary))
if __name__=='__main__':main()
