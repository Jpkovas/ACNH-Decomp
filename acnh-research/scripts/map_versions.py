"""Generate correspondence hypotheses; never transfer function names automatically."""
from __future__ import annotations
import argparse,collections,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def read_json(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def functions(version):
    file=ROOT/'private/outputs'/version/'ghidra/functions.jsonl'
    if not file.exists():return []
    result=[]
    with file.open(encoding='utf-8') as source:
        for line in source:
            function=json.loads(line)
            if 'scalar_constants' not in function or 'string_references' not in function:raise ValueError('Export current Ghidra inventory with constants and string anchors before mapping')
            if not function.get('mnemonics'):continue
            result.append({'address':function['address'],'fingerprint':signature(function),'instructions':len(function['mnemonics']),
                           'context':(len(function.get('callers',[])),len(function.get('callees',[]))),
                           'callers':function.get('callers',[]),'callees':function.get('callees',[]),
                           'constants':frozenset(function.get('scalar_constants',[])),'strings':frozenset(function.get('string_references',[]))})
    by_address={f['address']:f['fingerprint'] for f in result}
    for f in result:
        f['caller_shapes']=frozenset(by_address[x] for x in f.pop('callers') if x in by_address)
        f['callee_shapes']=frozenset(by_address[x] for x in f.pop('callees') if x in by_address)
    return result
def signature(function):
    words=function.get('mnemonics',[])
    shape=sorted(len(b['edges']) for b in function.get('cfg',[]))
    content={'mnemonics':words,'block_degrees':shape}
    return hashlib.sha256(json.dumps(content,sort_keys=True).encode()).hexdigest()
def catalog_delta(version1,version2,format_,key):
    left=read_json(ROOT/'private/outputs'/version1/format_/'catalog.json')[key]
    right=read_json(ROOT/'private/outputs'/version2/format_/'catalog.json')[key]
    field='name' if format_=='bcsv' else 'file'
    a={v[field]:v for v in left};b={v[field]:v for v in right};common=sorted(a.keys()&b.keys())
    return {'added':sorted(b.keys()-a.keys()),'removed':sorted(a.keys()-b.keys()),
            'changed':[k for k in common if a[k]['sha256']!=b[k]['sha256']],
            'unchanged':[k for k in common if a[k]['sha256']==b[k]['sha256']]}

def main():
    p=argparse.ArgumentParser();p.add_argument('--reference',default='1.0.0');p.add_argument('--target',default='3.0.3');a=p.parse_args()
    ref=functions(a.reference);target=functions(a.target);index=collections.defaultdict(list)
    for f in target:
        index[f['fingerprint']].append(f)
    candidates=[]
    for f in ref:
        count=f['instructions']
        matches=index.get(f['fingerprint'],[])
        if not matches:continue
        detailed=[]
        for match in matches[:5]:
            context_equal=f['context']==match['context']
            constants_equal=bool(f['constants']) and f['constants']==match['constants']
            shared_strings=len(f['strings']&match['strings'])
            neighboring_shapes=bool(f['callee_shapes']) and f['callee_shapes']==match['callee_shapes']
            caller_shapes=bool(f['caller_shapes']) and f['caller_shapes']==match['caller_shapes']
            score=0.25+min(0.2,count/100)+(0.05 if context_equal else 0)+(0.1 if len(matches)==1 else 0)+(0.1 if constants_equal else 0)+(0.15 if shared_strings else 0)+(0.05 if neighboring_shapes else 0)+(0.05 if caller_shapes else 0)
            reasons=['identical mnemonic sequence','identical CFG block-degree multiset']
            if context_equal:reasons.append('equal caller/callee counts')
            if constants_equal:reasons.append('equal nonempty scalar-constant sets')
            if shared_strings:reasons.append('shared direct string-reference anchors')
            if neighboring_shapes:reasons.append('equal nonempty callee fingerprint sets')
            if caller_shapes:reasons.append('equal nonempty caller fingerprint sets')
            detailed.append({'address':match['address'],'score':round(score,3),'reasons':reasons,
                             'constant_values_compared':True,'scalar_constant_sets_equal':constants_equal,'string_xrefs_compared':True,'shared_direct_string_anchors':shared_strings,'reviewed':False})
        candidates.append({'reference_address':f['address'],'reference_version':a.reference,'target_version':a.target,'status':'uncertain',
                           'candidates':detailed,'total_candidates':len(matches),'notes':'Mnemonic and CFG evidence alone do not establish equivalence; no symbol transfer'})
    classes_ref=read_json(ROOT/'private/outputs'/a.reference/'nxo/classes.json');classes_target=read_json(ROOT/'private/outputs'/a.target/'nxo/classes.json')
    classes_by_name={c['mangled_name']:c for c in classes_target};class_map=[]
    for c in classes_ref:
        match=classes_by_name.get(c['mangled_name'])
        class_map.append({'reference_address':c['address'],'target_address':match['address'] if match else None,'mangled_name':c['mangled_name'],
                          'status':'mapped' if match and match['rtti_kind']==c['rtti_kind'] else 'uncertain',
                          'evidence':'same Itanium RTTI type name and ABI type-info kind; object layout and behavior not transferred'})
    data={fmt:catalog_delta(a.reference,a.target,fmt,key) for fmt,key in [('bcsv','tables'),('eventflow','flows')]}
    private=ROOT/'private/outputs/version-map';private.mkdir(parents=True,exist_ok=True)
    manual=read_json(ROOT/'metadata/manual-version-review.json')
    if manual['reference']!=a.reference or manual['target']!=a.target:raise ValueError('Manual review belongs to other versions')
    (private/'candidates.json').write_text(json.dumps({'functions':candidates,'classes':class_map,'data':data,'manual_review':manual},indent=2)+'\n',encoding='utf-8')
    summary={'reference':a.reference,'target':a.target,'function_candidates':len(candidates),'function_mappings_reviewed':len(manual['functions']),'full_function_equivalences_under_recorded_contracts':sum(f['status']=='mapped' for f in manual['functions']),
             'terminal_regions_behavior_mapped':len(manual['regions']),'function_names_transferred_automatically':0,'target_annotations_after_independent_review':3,
             'rtti_type_identities_mapped':sum(c['status']=='mapped' for c in class_map),
             'data':{fmt:{k:len(v) for k,v in delta.items()} for fmt,delta in data.items()},
             'allowed_review_states':['mapped','uncertain','absent','split','merged','behavior_changed'],
             'candidate_report':'private/outputs/version-map/candidates.json'}
    (ROOT/'metadata/version-map.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    lines=['# Diferenças verificadas entre versões','',f'Referência: {a.reference}. Alvo: {a.target}.','',
           'As identidades de tipos RTTI são associadas pelo nome codificado e espécie de type_info. Isso não transfere layouts nem equivalência comportamental.',
           'Correspondências de funções são candidatos para revisão; não há transferência automática de nomes. O filtro usa mnemônicos/CFG e o score adiciona constantes, strings diretas e fingerprints de callers/callees. Relocations, indireções e mudanças de inlining podem alterar esses indícios.','',
           '| Formato | Novos | Removidos | Hash alterado | Hash igual |','|---|---:|---:|---:|---:|']
    for fmt,delta in summary['data'].items():lines.append(f"| {fmt} | {delta['added']} | {delta['removed']} | {delta['changed']} | {delta['unchanged']} |")
    lines+=['','O fluxo-piloto AI_NPC_Doc_Airport tem 3 nós alcançáveis em 1.0.0 e 11 em 3.0.3. Ambos passaram no round-trip estrutural. A implementação C++ do fluxo cobre somente o contrato 1.0.0.',
            '',f"Candidatos de funções: {len(candidates)}. Três vínculos receberam revisão técnica individual; dois têm escopo parcial. Identidades RTTI associadas: {summary['rtti_type_identities_mapped']}.",
            '', 'EventFlagInt: a factory do alvo incorpora o construtor separado da base. A região terminal passou em 3.806 casos por versão. A equivalência do backend completo permanece incerta. As duas anotações do alvo foram aplicadas após conferir seus endereços/labels/relocations independentemente.',
            '', 'Murmur3 C-string: função completa associada pelo contrato de entrada/saída após conferir assembly e repetir o diferencial nos dois originais. Código gerado e original diferem. A descoberta no alvo foi independente; o endereço de referência não foi reutilizado.',
            '', 'Evidência versionada: [manual-version-review.json](../metadata/manual-version-review.json). Nenhum nome foi migrado automaticamente.']
    (ROOT/'docs/version_delta.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');print(json.dumps(summary))
if __name__=='__main__':main()
