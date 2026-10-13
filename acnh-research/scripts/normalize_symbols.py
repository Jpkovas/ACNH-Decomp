from __future__ import annotations
import argparse,json
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--version-id',required=True);a=p.parse_args()
    root=ROOT/'private/outputs'/a.version_id
    functions=[]
    file=root/'ghidra/functions.jsonl'
    inventory=json.loads((root/'ghidra/inventory-summary.json').read_text(encoding='utf-8'))
    if not file.exists() or inventory['analysis_timeout']:raise ValueError('Complete function inventory required')
    if file.exists():
        with file.open(encoding='utf-8') as source:
            for line in source:
                f=json.loads(line)
                if f['version_id']!=a.version_id:raise ValueError('Inventory version differs')
                functions.append({k:f.get(k) for k in ('version_id','module','address','relative_address','size','name','name_status','confidence','kind','signature','callers','callees','evidence','reviewed')})
    if not functions or len(functions)!=inventory['functions_discovered']:raise ValueError('Inventory is missing or incomplete')
    classes=json.loads((root/'nxo/classes.json').read_text(encoding='utf-8'))
    externals=json.loads((root/'ghidra/externals.json').read_text(encoding='utf-8')) if (root/'ghidra/externals.json').exists() else []
    addresses={f['address'] for f in functions}|{f['address'] for f in externals}
    unresolved=sorted({target for f in functions for target in (f['callers'] or [])+(f['callees'] or []) if target not in addresses})
    out=root/'symbols';out.mkdir(parents=True,exist_ok=True)
    validated=[]
    annotations=ROOT/'metadata'/a.version_id/'reviewed-annotations.json'
    if annotations.exists():
        notes=json.loads(annotations.read_text())
        for symbol in notes['symbols']:
            address=symbol['address'].removeprefix('0x')
            if address not in addresses:raise ValueError('Reviewed symbol is absent from Ghidra function inventory: '+address)
            item=dict(symbol,version_id=a.version_id,module='main',kind='function',reviewer='Codex technical review; independent human review not recorded')
            validated.append(item)
            for f in functions:
                if f['address']==address:
                    f.update(name=symbol['name'],name_status=symbol['name_status'],confidence=symbol['confidence'],reviewed=symbol['reviewed'],evidence=symbol['evidence'],signature_status=symbol['signature_status'])
                    break
    with (out/'functions.jsonl').open('w',encoding='utf-8') as dest:
        for f in functions:dest.write(json.dumps(f)+'\n')
    (out/'symbols.yaml').write_text(yaml.safe_dump({'version_id':a.version_id,'functions_file':'functions.jsonl','function_count':len(functions),'reviewed_symbols':validated,'externals':externals,'classes':classes,'unresolved_graph_addresses':unresolved},allow_unicode=True,sort_keys=False),encoding='utf-8')
    public=ROOT/'metadata'/a.version_id
    (public/'validated_symbols.yaml').write_text(yaml.safe_dump({'version_id':a.version_id,'symbols':validated},allow_unicode=True,sort_keys=False),encoding='utf-8')
    summary={'version_id':a.version_id,'functions':len(functions),'external_functions':len(externals),'rtti_classes':len(classes),'functions_reviewed_in_full':sum(v['reviewed'] is True for v in validated),'partially_reviewed_functions':sum(v['reviewed']=='partial' for v in validated),
             'unresolved_call_graph_addresses':len(unresolved),'raw_inventory':'private/outputs/'+a.version_id+'/symbols/symbols.yaml',
             'unresolved_addresses_are_research_items':True}
    (public/'symbols-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary))
if __name__=='__main__':main()
