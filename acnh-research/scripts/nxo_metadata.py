"""Read MOD0/ELF metadata and relocation-backed Itanium RTTI per version."""
from __future__ import annotations
import argparse,collections,json,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class Image:
    def __init__(self,version):
        self.version=version
        self.manifest=json.loads((ROOT/'metadata'/version/'nso.json').read_text())
        self.segments=[(s['memory_offset'],(ROOT/'private/outputs'/version/'segments'/(s['name'][1:]+'.bin')).read_bytes()) for s in self.manifest['segments']]
        mod=struct.unpack('<I',self.read(4,4))[0]
        if self.read(mod,4)!=b'MOD0':raise ValueError('MOD0 not found')
        self.dynamic=mod+struct.unpack('<i',self.read(mod+4,4))[0]
        self.tags={}
        for i in range(4096):
            key,value=struct.unpack('<QQ',self.read(self.dynamic+i*16,16))
            if key==0:break
            self.tags[key]=value
        else:raise ValueError('Unterminated dynamic table')
        strings=self.read(self.tags[5],self.tags[10])
        _,count=struct.unpack('<II',self.read(self.tags[4],8));self.symbols=[]
        if count>100000 or self.tags[11]!=24:raise ValueError('Unsupported ELF symbol table')
        for i in range(count):
            name,info,other,section,address,size=struct.unpack('<IBBHQQ',self.read(self.tags[6]+i*24,24))
            end=strings.find(b'\0',name)
            if name>=len(strings) or end<0:raise ValueError('Invalid symbol name')
            self.symbols.append({'name':strings[name:end].decode('utf-8','strict'),'section':section,'value':address,'size':size})
        self.relative={};self.rela=[]
        if 7 in self.tags:
            if self.tags[9]!=24 or self.tags[8]%24:raise ValueError('Invalid RELA dimensions')
            self.rela=list(struct.iter_unpack('<QQq',self.read(self.tags[7],self.tags[8])))
            for address,info,addend in self.rela:
                if info&0xffffffff==1027:self.relative[address]=addend
        if 36 in self.tags:
            if self.tags.get(37)!=8 or self.tags[35]%8:raise ValueError('Invalid RELR dimensions')
            cursor=0
            for (entry,) in struct.iter_unpack('<Q',self.read(self.tags[36],self.tags[35])):
                if entry&1:
                    if cursor==0:raise ValueError('RELR bitmap without base')
                    for bit in range(1,64):
                        if entry&(1<<bit):
                            address=cursor+(bit-1)*8
                            self.relative[address]=struct.unpack('<Q',self.read(address,8))[0]
                    cursor+=63*8
                else:
                    if entry%8:raise ValueError('Unaligned RELR target')
                    self.relative[entry]=struct.unpack('<Q',self.read(entry,8))[0];cursor=entry+8
    def read(self,address,size):
        for start,data in self.segments:
            if start<=address and address+size<=start+len(data):return data[address-start:address-start+size]
        raise ValueError('Address outside initialized segments: '+hex(address))
    def string(self,address):
        for start,data in self.segments:
            if start<=address<start+len(data):
                at=address-start;end=data.find(b'\0',at,min(at+4096,len(data)))
                if end<0:raise ValueError('Unterminated RTTI string')
                return data[at:end].decode('ascii','strict')
        raise ValueError('String outside image')

def main():
    p=argparse.ArgumentParser();p.add_argument('--version-id',required=True);a=p.parse_args();image=Image(a.version_id)
    out=ROOT/'private/outputs'/a.version_id/'nxo';out.mkdir(parents=True,exist_ok=True)
    with (out/'relative-relocations.tsv').open('w',encoding='ascii') as f:
        for address,addend in sorted(image.relative.items()):f.write(f'{address:x}\t{addend:x}\n')
    classes={}
    for address,info,addend in image.rela:
        idx=info>>32
        if idx>=len(image.symbols):raise ValueError('Relocation symbol out of bounds')
        name=image.symbols[idx]['name']
        if info&0xffffffff!=257 or not name.startswith('_ZTVN10__cxxabiv1') or 'type_info' not in name:continue
        if address+8 not in image.relative:continue
        encoded=image.string(image.relative[address+8])
        parents=[]
        if '__si_class_type_info' in name:
            if address+16 in image.relative:parents.append({'typeinfo_address':hex(image.relative[address+16]),'offset':0,'flags':None})
        elif '__vmi_class_type_info' in name:
            flags,count=struct.unpack('<II',image.read(address+16,8))
            if count>1024:raise ValueError('Invalid RTTI parent count')
            for i in range(count):
                at=address+24+i*16
                if at not in image.relative:raise ValueError('RTTI base without relocation')
                offset_flags=struct.unpack('<q',image.read(at+8,8))[0]
                parents.append({'typeinfo_address':hex(image.relative[at]),'offset':offset_flags>>8,'flags':offset_flags&255})
        classes[address]={'version_id':a.version_id,'module':'main','address':hex(0x7100000000+address),'relative_address':hex(address),
                          'kind':'class','mangled_name':encoded,'name_status':'demangled','confidence':'high',
                          'rtti_kind':name,'parents':parents,'evidence':['ELF symbol for ABI type_info vtable','relocation-backed type name and base descriptors'],
                          'object_layout_validated':False,'vtable_candidates':[]}
    llvm=next((ROOT/'private/tools/llvm').iterdir())/'bin/llvm-cxxfilt.exe'
    result=subprocess.run([str(llvm)],input='\n'.join('_ZTS'+c['mangled_name'] for c in classes.values())+'\n',capture_output=True,text=True,check=True)
    names=result.stdout.splitlines()
    if len(names)!=len(classes):raise ValueError('Demangler output count mismatch')
    for item,name in zip(classes.values(),names):item['name']=name.removeprefix('typeinfo name for ')
    for address,addend in image.relative.items():
        if addend not in classes:continue
        start=address+8;methods=[];cursor=start
        while cursor in image.relative and 0<=image.relative[cursor]<image.manifest['segments'][0]['memory_size']:
            methods.append(hex(0x7100000000+image.relative[cursor]));cursor+=8
            if len(methods)>1024:break
        if methods:
            classes[addend]['vtable_candidates'].append({'address':hex(0x7100000000+start),'methods':methods,'confidence':'medium','name_status':'provisional'})
    (out/'classes.json').write_text(json.dumps(list(classes.values()),indent=2)+'\n',encoding='utf-8')
    (out/'dynamic.json').write_text(json.dumps({'version_id':a.version_id,'dynamic_address':hex(image.dynamic),'tags':{str(k):hex(v) for k,v in image.tags.items()},'symbols':image.symbols},indent=2)+'\n',encoding='utf-8')
    summary={'version_id':a.version_id,'elf_symbols':len(image.symbols),'relative_relocations':len(image.relative),
             'itanium_rtti_classes':len(classes),'inheritance_edges':sum(len(c['parents']) for c in classes.values()),
             'vtable_candidates':sum(len(c['vtable_candidates']) for c in classes.values()),'object_layouts_validated':0,
             'relr_present':36 in image.tags,'address_basis':'Ghidra image base 0x7100000000, offsets independently parsed from same NSO'}
    (ROOT/'metadata'/a.version_id/'rtti-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary))
if __name__=='__main__':main()
