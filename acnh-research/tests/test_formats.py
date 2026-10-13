import hashlib,struct,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TMP=ROOT/'private/test-tmp'
TMP.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'scripts'))
from audit_inputs import pfs_entries,extract_pfs
from bcsv_format import parse_bcsv,field_bytes
from inspect_nso import inspect
from validate_save_schemas import validate,TYPE,MEMBERS,NAME,SIZE,OFFSET,LENGTH,ALIGN

class FormatTests(unittest.TestCase):
    def test_smmh_layout_bounds_and_nested_types(self):
        leaf={TYPE:1,SIZE:4,ALIGN:4,MEMBERS:[]}
        field={TYPE:1,NAME:9,SIZE:4,ALIGN:4,OFFSET:4,LENGTH:2}
        container={TYPE:2,SIZE:12,ALIGN:4,MEMBERS:[field]}
        self.assertEqual(validate([leaf,container])['nested_layout_checks'],1)
        invalid={**container,MEMBERS:[{**field,LENGTH:3}]}
        self.assertRaises(ValueError,validate,[leaf,invalid])
        self.assertRaises(ValueError,validate,[leaf,{**container,MEMBERS:[{**field,OFFSET:1}]}])
        self.assertRaises(ValueError,validate,[{**leaf,SIZE:8},container])
        self.assertRaises(ValueError,validate,[leaf,leaf])
    def test_pfs_extract_and_bounds(self):
        with tempfile.TemporaryDirectory(dir=TMP) as directory:
            self.assertTrue(Path(directory).resolve().is_relative_to(TMP.resolve()))
            file=Path(directory)/'test.nsp';name=b'sample.bin\0';payload=b'own synthetic fixture'
            raw=b'PFS0'+struct.pack('<III',1,len(name),0)+struct.pack('<QQII',0,len(payload),0,0)+name+payload
            file.write_bytes(raw);self.assertEqual(pfs_entries(file)[0]['size'],len(payload))
            extract_pfs(file,Path(directory)/'out');self.assertEqual((Path(directory)/'out/sample.bin').read_bytes(),payload)
            (Path(directory)/'out/sample.bin').write_bytes(b'x'*len(payload))
            self.assertRaises(ValueError,extract_pfs,file,Path(directory)/'out')
            file.write_bytes(raw[:-1]);self.assertRaises(ValueError,pfs_entries,file)
    def test_pfs_traversal_rejected(self):
        with tempfile.TemporaryDirectory(dir=TMP) as directory:
            self.assertTrue(Path(directory).resolve().is_relative_to(TMP.resolve()))
            file=Path(directory)/'test.nsp';name=b'../escape\0'
            file.write_bytes(b'PFS0'+struct.pack('<III',1,len(name),0)+struct.pack('<QQII',0,0,0,0)+name)
            self.assertRaises(ValueError,pfs_entries,file)
    def test_bcsv_fields_and_invalid_offsets(self):
        raw=struct.pack('<IIHBB',2,6,2,0,1)+struct.pack('<IIII',7,0,8,4)+struct.pack('<IHIH',0xffffffff,65535,0,0)
        table=parse_bcsv(raw);self.assertEqual(field_bytes(raw,table,0,7),b'\xff'*4)
        self.assertEqual(field_bytes(raw,table,1,8),b'\0\0')
        self.assertRaises(IndexError,field_bytes,raw,table,2,7);self.assertRaises(KeyError,field_bytes,raw,table,0,5)
        for cut in range(len(raw)):self.assertRaises(ValueError,parse_bcsv,raw[:cut])
        bad=bytearray(raw);struct.pack_into('<I',bad,24,0);self.assertRaises(ValueError,parse_bcsv,bytes(bad))
    def test_nso_hash_and_segment_bounds(self):
        with tempfile.TemporaryDirectory(dir=TMP) as directory:
            self.assertTrue(Path(directory).resolve().is_relative_to(TMP.resolve()))
            file=Path(directory)/'main';header=bytearray(256);header[:4]=b'NSO0';struct.pack_into('<I',header,12,56)
            segments=[b'code',b'data',b'vars']
            for i,segment in enumerate(segments):
                struct.pack_into('<III',header,16+i*16,256+i*4,i*4096,4)
                header[160+i*32:192+i*32]=hashlib.sha256(segment).digest()
            file.write_bytes(header+b''.join(segments));self.assertEqual(len(inspect(file)['segments']),3)
            bad=bytearray(file.read_bytes());bad[-1]^=1;file.write_bytes(bad);self.assertRaises(ValueError,inspect,file)

if __name__=='__main__':unittest.main()
