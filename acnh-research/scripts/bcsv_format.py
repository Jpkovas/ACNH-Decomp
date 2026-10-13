"""Bounds-checked structural parser. Hashed field types remain unknown."""
import struct

def parse_bcsv(blob:bytes)->dict:
    if len(blob)<12:raise ValueError('Truncated BCSV header')
    rows,stride,count,version,enums=struct.unpack_from('<IIHBB',blob)
    if version not in (0,1):raise ValueError('Unsupported BCSV version')
    header=12 if version==0 else 28
    if version==1 and (len(blob)<28 or blob[12:16]!=b'VSCB'):raise ValueError('Invalid VSCB header')
    data_at=header+count*8
    if data_at>len(blob) or rows*stride>len(blob)-data_at:raise ValueError('Truncated BCSV data')
    fields=[struct.unpack_from('<II',blob,header+i*8) for i in range(count)]
    if len({key for key,_ in fields})!=count:raise ValueError('Duplicate field hash')
    offsets=[offset for _,offset in fields]
    if any(offset>=stride for offset in offsets) or any(a>=b for a,b in zip(offsets,offsets[1:])):raise ValueError('Invalid field offsets')
    layout=[{'key':f'{key:08x}','offset':offset,'size':(fields[i+1][1] if i+1<count else stride)-offset,'type':'unknown_bytes'} for i,(key,offset) in enumerate(fields)]
    return {'rows':rows,'stride':stride,'version':version,'enum_flag':enums,'data_offset':data_at,'fields':layout}

def field_bytes(blob:bytes,table:dict,row:int,key:int)->bytes:
    if row<0 or row>=table['rows']:raise IndexError('BCSV row out of bounds')
    field=next((f for f in table['fields'] if int(f['key'],16)==key),None)
    if field is None:raise KeyError('BCSV field not present')
    start=table['data_offset']+row*table['stride']+field['offset']
    return blob[start:start+field['size']]
