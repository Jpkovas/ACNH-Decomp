"""Check historical same-version BCSV decoders and link message references locally."""
from __future__ import annotations
import argparse,collections,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(ROOT/'vendor/CylindricalEarth'))
from bcsv_format import parse_bcsv,field_bytes
import bcsv

def main():
    p=argparse.ArgumentParser();p.add_argument('romfs',type=Path);p.add_argument('--version-id',required=True);a=p.parse_args()
    out=ROOT/'private/outputs'/a.version_id/'semantics';out.mkdir(parents=True,exist_ok=True)
    table_rows=[];decoder_errors=[];field_count=0;enum_cells=0;unknown_enums=0
    if a.version_id=='1.0.0':
        import specs_100
        for file in sorted(a.romfs.glob('**/*.bcsv')):
            cls=specs_100.lookup.get(file.name)
            if cls is None:continue
            raw=file.read_bytes();table=parse_bcsv(raw);fields=[]
            context=type('Context',(),{'jp_enums':table['enum_flag']==0})()
            present={int(f['key'],16):f for f in table['fields']}
            for name,field in vars(cls).items():
                if not isinstance(field,bcsv.Field):continue
                entry={'name_from_upstream':name,'hash':f'{field.key:08x}','decoder':type(field).__name__,'name_status':'inferred','confidence':'medium','evidence':'specs_100 plus same-version field presence and decoder validation'}
                if field.key not in present:
                    entry['status']='absent';fields.append(entry);continue
                entry.update(offset=present[field.key]['offset'],byte_width=present[field.key]['size']);bad=0;unknown=0
                for row in range(table['rows']):
                    try:
                        decoded=field.decode(field_bytes(raw,table,row,field.key),context)
                        if isinstance(field,bcsv.Enum):
                            enum_cells+=1
                            if isinstance(decoded,str) and decoded.startswith('_UNK_'):unknown+=1;unknown_enums+=1
                        if isinstance(field,bcsv.String) and decoded.startswith('UTF-8 err '):bad+=1
                    except (ValueError,struct.error,UnicodeError,KeyError):bad+=1
                entry.update(rows_checked=table['rows'],decode_failures=bad,unknown_enum_values=unknown,
                             status='compatible_sample' if bad==0 else 'decoder_conflict')
                if bad:decoder_errors.append({'table':file.name,'field':name,'failures':bad})
                fields.append(entry);field_count+=1
            table_rows.append({'version_id':a.version_id,'table':file.name,'fields':fields})
    resources=json.loads((ROOT/'private/outputs'/a.version_id/'resources/catalog.json').read_text())
    labels=set()
    for m in resources['messages']:
        prefix=m['archive'].removesuffix('.sarc.zs').rsplit('_',1)[0]+'/'+m['file'].removesuffix('.msbt')
        labels.update(prefix+':'+label for label in m['labels'])
    links=[];totals=collections.Counter()
    for file in sorted((ROOT/'private/outputs'/a.version_id/'eventflow').glob('*.graph.json')):
        flow=json.loads(file.read_text(encoding='utf-8'))
        for node in flow['nodes']:
            for param,value in node.get('params',{}).items():
                if param not in ('MessageID','MessageID1','MessageID2','MessageID3'):continue
                if not isinstance(value,str):totals['dynamic']+=1;continue
                if not value:totals['empty']+=1;continue
                status='resolved' if value in labels else 'unresolved'
                totals[status]+=1;links.append({'flow':file.name,'node':node['id'],'parameter':param,'message_key':value,'status':status})
    (out/'bcsv-types.json').write_text(json.dumps({'version_id':a.version_id,'tables':table_rows,'decoder_errors':decoder_errors},indent=2)+'\n',encoding='utf-8')
    (out/'message-xrefs.json').write_text(json.dumps({'version_id':a.version_id,'language':'USen','links':links},indent=2)+'\n',encoding='utf-8')
    report={'version_id':a.version_id,'tables_with_historical_same_version_specs':len(table_rows),'fields_with_decoders_checked':field_count,
            'enum_cells_checked':enum_cells,'unknown_enum_cells':unknown_enums,'decoder_conflict_fields':len(decoder_errors),
            'message_reference_counts':dict(totals),'message_language_sample':'USen','target_schema_policy':'no 1.0.0 decoder or enum transferred to 3.0.3',
            'unresolved_messages':'retained for investigation; dynamic/random selection and archive naming can require further resolution',
            'type_confidence':'decoder compatibility is observed; upstream field names and intended semantic types remain inferred'}
    (ROOT/'metadata'/a.version_id/'semantics-summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
