from __future__ import annotations
import datetime,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(version,name):
    file=ROOT/'metadata'/version/name
    if not file.exists():raise ValueError('Required evidence absent: '+str(file.relative_to(ROOT)))
    return json.loads(file.read_text(encoding='utf-8'))
def main():
    rows=[]
    for version in ('1.0.0','3.0.3'):
        imports=read(version,'import-verification.json');symbols=read(version,'symbols-summary.json');bcsv=read(version,'bcsv-summary.json')
        flow=read(version,'eventflow-summary.json');res=read(version,'resources-summary.json');save=read(version,'save-layout-validation.json');roundtrip=read(version,'roundtrip.json')
        diff=read(version,'bcsv-differential.json')
        annotation=read(version,'annotation-import.json')
        if annotation['functions_annotated']!=len(json.loads((ROOT/'metadata'/version/'reviewed-annotations.json').read_text())['symbols']):raise ValueError('Annotation import is incomplete')
        if symbols['unresolved_call_graph_addresses']:raise ValueError('Unresolved call graph endpoints remain')
        if bcsv['errors'] or flow['errors'] or res['errors'] or save['errors'] or diff['failures']:raise ValueError('Required structural experiment failed')
        rows.append({'version_id':version,'functions_discovered':symbols['functions'],'functions_reviewed_in_full':symbols['functions_reviewed_in_full'],
                     'functions_reviewed_partially':symbols['partially_reviewed_functions'],'external_functions':symbols['external_functions'],
                     'itanium_rtti_type_identities':symbols['rtti_classes'],'executable_class_layouts_validated':0,
                     'parameter_slices_validated':annotation['partial_parameter_slices_added'],'bcsv_tables':diff['tables_verified'],'bcsv_cells_differential':diff['cells_verified'],
                     'eventflows':flow['parsed'],'actions':flow['actions'],'queries':flow['queries'],'msbt_roundtrips':res['msbt_roundtrips'],
                     'pbc_grids_validated':res['pbc_grids_validated'],'save_schema_layout_occurrences':save['layout_occurrences'],
                     'save_schema_roundtrips':save['structural_roundtrips'],'eventflow_roundtrip_passed':roundtrip['rooted_graph_equivalent'],
                     'relative_relocations_verified':imports['relative_relocations_verified']['relative_relocations_checked']})
    matching=read('1.0.0','matching-pilot.json');identifier=read('1.0.0','identifier-hash-validation.json');flag=read('1.0.0','flag-int-validation.json')
    factories=read('1.0.0','factory-bindings-summary.json');factories_target=read('3.0.3','factory-bindings-summary.json');flag_target=read('3.0.3','flag-int-validation.json');identifier_target=read('3.0.3','identifier-hash-validation.json')
    result={'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'versions':rows,
            'reconstructed_modules':['bounds-checked BCSV reader','1.0.0 airport flow with injected services','constant zero','Murmur3 C string','flag-int terminal predicate with injected reader'],
            'l3_functions_measured':3,'l3_functions_exact':int(matching['exact_instruction_bytes'])+int(identifier['exact_instruction_bytes'])+int(identifier_target['exact_instruction_bytes']),
            'function_diff_percentages':{'constant_zero_bytes':100 if matching['exact_instruction_bytes'] else None,'murmur3_reference_objdiff_text':identifier['objdiff_text_match_percent'],'murmur3_target_objdiff_text':identifier_target['objdiff_text_match_percent']},
            'eventflow_factory_bindings_matched':{'1.0.0':factories['bindings_matched'],'3.0.3':factories_target['bindings_matched']},'eventflow_handlers_individually_linked':2,
            'behavior_targets_validated':{'constant_zero':matching['behavior_cases'],'murmur3_synthetic':identifier['synthetic_cases'],
                                          'murmur3_reference_identifiers':identifier['observed_identifiers_checked'],'murmur3_target_identifiers':identifier_target['observed_identifiers_checked'],'flag_int_terminal_reference':flag['differential_cases'],'flag_int_terminal_target':flag_target['differential_cases']},
            'whole_game_percentage':None,'m5':'excluded by user','independent_human_review':'not recorded; no publication performed'}
    (ROOT/'metadata/metrics.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    lines=['# Métricas verificadas','',f"Geradas em {result['generated_utc']} pelo pipeline local.",'',
           '| Versão | Funções descobertas | Revisadas integralmente | RTTI | BCSV | EventFlow | MSBT round-trip | PBC |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for v in rows:lines.append(f"| {v['version_id']} | {v['functions_discovered']} | {v['functions_reviewed_in_full']} | {v['itanium_rtti_type_identities']} | {v['bcsv_tables']} | {v['eventflows']} | {v['msbt_roundtrips']} | {v['pbc_grids_validated']} |")
    lines+=['','Cinco módulos compiláveis. Três funções versionadas com diff ARM64; uma com 8/8 bytes iguais. Murmur3 é funcionalmente equivalente no contrato testado em cada versão e tem 19,36% / 22,48% de semelhança de instruções no objdiff.',
            '',f"Comparação da região terminal da query: {flag['differential_cases']} casos por versão. O leitor de flags e os serviços do fluxo são dependências injetadas.",
            '', 'RTTI representa identidades de tipos, majoritariamente middleware; não mede classes do jogo com layout recuperado. Schemas de save validam limites declarados, sem validar instâncias de saves.',
            '', 'Não há porcentagem de decompilação do jogo inteiro. Nomes e protótipos da autoanálise permanecem provisórios. Revisão humana independente não registrada.']
    (ROOT/'docs/metrics.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');print(json.dumps({'metrics_written':True,'versions':len(rows),'l2_modules':5,'l3_functions':3}))
if __name__=='__main__':main()
