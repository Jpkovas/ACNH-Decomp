from __future__ import annotations
import datetime,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from nxo_metadata import Image

def main():
    inventory=json.loads((ROOT/'metadata/package_inventory.json').read_text())
    lock=json.loads((ROOT/'inputs.lock.json').read_text())
    now=datetime.datetime.now(datetime.timezone.utc).isoformat();results=[]
    for package,version in [('base','1.0.0'),('update','3.0.3')]:
        nso=json.loads((ROOT/'metadata'/version/'nso.json').read_text());image=Image(version)
        main=ROOT/'private/inputs/extracted'/package/'exefs/main'
        if hashlib.sha256(main.read_bytes()).hexdigest()!=nso['input_sha256']:raise ValueError('NSO provenance mismatch')
        initial=json.loads((ROOT/'private/outputs'/version/'ghidra/import-layout.json').read_text())
        clean=json.loads((ROOT/'private/outputs'/version/'ghidra-reimport/import-layout.json').read_text())
        keys=('language','format','image_base','executable_sha256','memory_blocks')
        if any(initial[k]!=clean[k] for k in keys):raise ValueError('Fresh Ghidra import differs')
        if clean['language']!='AARCH64:LE:64:v8A' or clean['executable_sha256']!=nso['input_sha256']:raise ValueError('Import identity differs')
        mod=struct.unpack('<I',image.read(4,4))[0]
        bss_start=mod+struct.unpack('<i',image.read(mod+8,4))[0]
        bss_end=mod+struct.unpack('<i',image.read(mod+12,4))[0]
        blocks=[b for b in clean['memory_blocks'] if b['initialized']]
        for s in nso['segments']:
            start=s['memory_offset'];end=start+s['memory_size']
            parts=sorted((int(b['relative_address'],16),int(b['relative_address'],16)+b['size']) for b in blocks if start<=int(b['relative_address'],16)<end)
            cursor=start
            for left,right in parts:
                if left!=cursor:raise ValueError('Imported segment gap/overlap')
                cursor=right
            if cursor!=end:raise ValueError('Imported segment size differs')
        bss=next(b for b in clean['memory_blocks'] if b['name']=='.bss')
        if int(bss['relative_address'],16)!=bss_start or bss['size']!=bss_end-bss_start:raise ValueError('MOD0 BSS differs from loader')
        item=next(m for m in inventory if m['package']==package and m['content_type']=='Program')
        artifact=next(v for v in lock['artifacts'] if ('[v0]' in v['filename'] if package=='base' else '[v2228224]' in v['filename']))
        artifact.update(verified_display_version=version,module_id=nso['module_id'],module='main',internal_path=item['nca']+'::ExeFS/main',
                        executable_sha256=nso['input_sha256'],executable_size=nso['file_size'],sdk_version_header=item['sdk'],
                        extraction_tool='borntohonk/hactool 1.5.4' if package=='update' else 'SciresM/hactool 1.4.0',
                        analysis_tool='Ghidra 12.1.4',loader_revision='5d80d195bf284f8ad5f2f9b66c3bdd5c67dd66a6')
        if package=='update':artifact['depends_on_base_package_sha256']=lock['artifacts'][0]['sha256']
        report={'version_id':version,'module':'main','sha256':nso['input_sha256'],'module_id':nso['module_id'],'verified_utc':now,
                'fresh_import_matches_initial':True,'architecture':clean['language'],'image_base':clean['image_base'],
                'initialized_segments_fully_covered':True,'mod0_bss':{'start':hex(bss_start),'end':hex(bss_end),'size':bss_end-bss_start},
                'nso_header_bss_size':nso['bss_size'],'bss_note':'NSO header reservation includes alignment/padding; loader BSS follows the independently checked MOD0 range',
                'relative_relocations_verified':json.loads((ROOT/'metadata'/version/'relocation-verification.json').read_text()),
                'limitations':['3.0.3 loader does not label a separate GOT block; original data ranges and relative relocation values are verified',
                               'Autoanalysis signatures and discovered function boundaries remain provisional']}
        (ROOT/'metadata'/version/'import-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');results.append(report)
    lock['provenance_finalized_utc']=now;lock['scope']='base and update main/RomFS analyzed; DLC packages audited, not separately reconstructed; firmware unused'
    (ROOT/'inputs.lock.json').write_text(json.dumps(lock,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([{'version_id':v['version_id'],'fresh_import_matches_initial':True,'bss':v['mod0_bss']} for v in results]))
if __name__=='__main__':main()
