"""Inspect bounded private FIFO samples without executing or changing guest commands."""
from __future__ import annotations
import argparse
import json
import struct
from pathlib import Path

HEADER=struct.Struct('<8IQQ')
SAMPLE=struct.Struct('<QI128I4x')
SIZE=HEADER.size+3*SAMPLE.size

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('input',type=Path)
    args=parser.parse_args()
    raw=args.input.read_bytes()
    if raw[:8] not in (b'SNXFIFO2',b'SNXFIFO3'):raise ValueError('Unsupported FIFO trace format')
    records=[];enqueue_changes=[];landing_changes=[];odd=[]
    for offset in range(8,len(raw)-SIZE+1,SIZE):
        head=HEADER.unpack_from(raw,offset)
        samples=[SAMPLE.unpack_from(raw,offset+HEADER.size+i*SAMPLE.size) for i in range(3)]
        count=samples[0][1]
        if count>128 or any(s[1]!=count for s in samples):raise ValueError('Invalid bounded sample count')
        words=[s[2:2+count] for s in samples]
        base=dict(record=head[0],channel=head[1],words=head[2],entry=hex(head[8]),cpu=hex(head[9]),
                  address=hex(samples[0][0]),pending=dict(mode=head[3],sub=head[4],method=hex(head[5]),count=head[6],consumed=head[7]))
        if words[0]!=words[1]:enqueue_changes.append(base)
        if words[1]!=words[2]:landing_changes.append(base)
        # Only decode complete samples; interrupted batches and long entries retain unknown suffixes.
        if head[2]==count:
            remaining=max(0,head[6]-head[7]);i=min(remaining,count)
            while i<count:
                word=words[2][i];mode=word>>29;i+=1
                if word and mode in (0,2,6,7):
                    odd.append(dict(**base,word=i-1,value=hex(word),mode=mode))
                    break
                if mode in (1,3,5):i+= (word>>16)&0x1fff
        records.append(base)
    records.sort(key=lambda record:record['record'])
    report=dict(records=len(records),first_record=records[0]['record'] if records else None,
                last_record=records[-1]['record'] if records else None,
                enqueue_execution_prefix_changes=len(enqueue_changes),
                pending_write_landing_prefix_changes=len(landing_changes),
                enqueue_change_examples=enqueue_changes[:12],landing_change_examples=landing_changes[:12],
                suspect_header_examples=odd[:12],complete_records_bytes=8+len(records)*SIZE,
                limitations='Prefixes capped at 128 words; uncommon/legacy header modes are diagnostic suspects, not discarded commands')
    args.input.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(report))

if __name__=='__main__':main()
