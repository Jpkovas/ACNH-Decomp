"""Compare recovered SDK FullKey snapshot logic against original ARM64.

The original 504-byte body is executed unchanged. Its one initialization call
is isolated; this test validates snapshot reading, not the initializer itself.
"""
from __future__ import annotations
import ctypes as ct
import argparse
import hashlib
import json
import os
import random
import struct
from pathlib import Path
import unicorn as un
from unicorn import arm64_const as reg

ROOT = Path(__file__).resolve().parents[1]
BASE = 0x7100000000
ENTRY = 0x200000
OUTPUT = 0x300000
COUNT = 0x301000
DEVICE = 0x302000
START, LENGTH, INITIALIZE = 0x341a00, 504, 0x340fd0
GLOBAL = 0x125c028
DLL = ROOT/'build/windows-bridge/npad_full_key.dll'
EXPECTED = '31ce67e8701584ba812dceeae9b590d7a6ad642bcb5aa74d2fe3ea5c5474250d'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--library', type=Path, default=DLL)
    args = parser.parse_args()
    sdk = ROOT/'private/windows/modules/1.0.0/sdk'
    manifest = json.loads((sdk/'metadata.json').read_text())['manifest']
    nso = ROOT/'private/windows/bridge/ACNH_1_0_0_data/exefs/sdk'
    if hashlib.file_digest(nso.open('rb'), 'sha256').hexdigest() != EXPECTED:
        raise ValueError('Unreviewed SDK version')
    raw = (sdk/'segments/text.bin').read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest['segments'][0]['sha256']:
        raise ValueError('SDK text provenance mismatch')
    dll_directory = os.add_dll_directory(str(ROOT/'private/tools/llvm-mingw/llvm-mingw-20261006-ucrt-x86_64/bin'))
    library = ct.CDLL(str(args.library.resolve()))
    function = library.acnh_npad_full_key_states
    function.argtypes = [ct.c_void_p,ct.c_void_p,ct.c_int32,ct.c_void_p,ct.c_void_p,ct.c_void_p,ct.c_void_p,ct.c_void_p]
    function.restype = ct.c_uint32
    uc = un.Uc(un.UC_ARCH_ARM64, un.UC_MODE_ARM)
    uc.mem_map(BASE+0x340000,0x2000)
    uc.mem_write(BASE+0x340000,raw[0x340000:0x342000])
    uc.mem_map(BASE+0x125c000,0x1000)
    uc.mem_map(ENTRY,0x2000)
    uc.mem_map(OUTPUT,0x3000)
    uc.mem_map(0x400000,0x2000)
    stop = 0x401000
    observations = dict(initializations=0, race=None, reads=0, filter_race=False, filter_reads=0)
    def dependency(uc,address,size,context):
        if address == BASE+INITIALIZE:
            observations['initializations'] += 1
            uc.reg_write(reg.UC_ARM64_REG_PC, uc.reg_read(reg.UC_ARM64_REG_LR))
    uc.hook_add(un.UC_HOOK_CODE,dependency)
    def changing_producer(uc,access,address,size,value,context):
        if address == BASE+0x125c0e0 and observations['filter_race']:
            observations['filter_reads'] += 1
            if observations['filter_reads'] == 2:uc.mem_write(address,struct.pack('<I',1))
        if address == observations['race']:
            observations['reads'] += 1
            if observations['reads'] == 2:
                old = struct.unpack('<Q',uc.mem_read(address,8))[0]
                uc.mem_write(address,struct.pack('<Q',(old+1)&((1<<64)-1)))
    uc.hook_add(un.UC_HOOK_MEM_READ,changing_producer)
    rng = random.Random(0x341a00)
    cases = [(tail,count,capacity,mode,enabled) for tail in range(17)
        for count in (0,1,2,8,16,17,-1) for capacity in (-1,0,1,2,8,16,17,32)
        for mode,enabled in ((0,0),(0,1),(1,1))]
    cases += [(rng.randrange(17),rng.randrange(18),rng.randrange(18),rng.randrange(2),rng.randrange(2)) for _ in range(256)]
    total = 0
    race_cases = 0
    filter_race_cases = 0
    def check(tail,count,capacity,mode,enabled,missing=False,race=False,filter_race=False):
        nonlocal total,race_cases
        ring = bytearray(0x400)
        struct.pack_into('<Q',ring,0x38,tail)
        struct.pack_into('<Q',ring,0x40,count&0xffffffff)
        selected = min(max(count,0),capacity)
        latest = rng.getrandbits(64)
        payloads = {}
        for age in range(17):
            slot = (tail-age)%17
            sample = (latest-age)&((1<<64)-1)
            buttons = rng.getrandbits(64)|0xf000
            payload = struct.pack('<QQ4iII',sample,buttons,
                *[rng.randrange(-32768,32768) for _ in range(4)],rng.getrandbits(32),rng.getrandbits(32))
            struct.pack_into('<Q',ring,0x48+slot*0x30,sample)
            ring[0x50+slot*0x30:0x78+slot*0x30] = payload
            payloads[age] = payload
        native_ring = ct.create_string_buffer(bytes(ring))
        native_out = ct.create_string_buffer(b'\xa5'*0x500,0x500)
        native_count = ct.c_int32(0x12345678)
        device_id = rng.choice([0,1,7,0x10,0x20])
        index = device_id if device_id < 8 else 9 if device_id == 0x10 else 8
        uc.mem_write(BASE+GLOBAL+0x68+index*8,struct.pack('<Q',0 if missing else ENTRY))
        uc.mem_write(BASE+0x125c0e0,struct.pack('<I',mode))
        uc.mem_write(BASE+0x125c160,bytes([enabled]))
        uc.mem_write(ENTRY,bytes(ring))
        uc.mem_write(OUTPUT,b'\xa5'*0x500)
        uc.mem_write(COUNT,struct.pack('<I',0x12345678))
        uc.mem_write(DEVICE,struct.pack('<I',device_id))
        for i,value in enumerate((COUNT,OUTPUT,capacity&0xffffffff,DEVICE)):
            uc.reg_write(reg.UC_ARM64_REG_X0+i,value)
        uc.reg_write(reg.UC_ARM64_REG_SP,0x400800)
        uc.reg_write(reg.UC_ARM64_REG_LR,stop)
        saved_registers = [reg.UC_ARM64_REG_X19+i for i in range(10)] + [reg.UC_ARM64_REG_X29]
        saved = [rng.getrandbits(64) for _ in saved_registers]
        for register,value in zip(saved_registers,saved):uc.reg_write(register,value)
        observations['reads'] = 0
        observations['filter_reads'] = 0
        observations['filter_race'] = filter_race
        raced_offset = 0x48+((tail+18-selected)%17)*0x30
        observations['race'] = ENTRY+raced_offset if race else None
        uc.emu_start(BASE+START,stop,count=10000)
        if uc.reg_read(reg.UC_ARM64_REG_PC) != stop:raise ValueError('Original did not return')
        if [uc.reg_read(register) for register in saved_registers] != saved:
            raise ValueError('Original callee saved registers changed')
        hook_type = ct.CFUNCTYPE(None,ct.c_void_p,ct.c_size_t)
        native_reads = [0]
        native_filter_reads = [0]
        native_mode, native_enabled = ct.c_uint32(mode), ct.c_uint8(enabled)
        def native_mutation(context,address):
            if address == ct.addressof(native_mode) and filter_race:
                native_filter_reads[0] += 1
                if native_filter_reads[0] == 2:native_mode.value = 1
            if address == ct.addressof(native_ring)+raced_offset:
                native_reads[0] += 1
                if native_reads[0] == 2:
                    word = ct.c_uint64.from_address(address)
                    word.value += 1
        native_hook = hook_type(native_mutation)
        actual = function(ct.byref(native_count),native_out,capacity,None if missing else native_ring,
            ct.byref(native_mode),ct.byref(native_enabled),ct.cast(native_hook,ct.c_void_p) if race or filter_race else None,None)
        original = uc.reg_read(reg.UC_ARM64_REG_W0)
        original_count = struct.unpack('<i',uc.mem_read(COUNT,4))[0]
        if actual != original or native_count.value != original_count or native_out.raw != uc.mem_read(OUTPUT,0x500):
            raise ValueError(f'Snapshot divergence: {tail,count,capacity,mode,enabled,missing,race}')
        expected = bytearray(b'\xa5'*0x500)
        if not missing:
            for age in range(max(selected,0)):
                payload = bytearray(payloads[age])
                if mode == 0 and enabled and not (filter_race and age >= 1):
                    buttons = struct.unpack_from('<Q',payload,8)[0]
                    if buttons&0x2000:buttons &= ~0x8000
                    if buttons&0x1000:buttons &= ~0x4000
                    struct.pack_into('<Q',payload,8,buttons)
                expected[age*40:(age+1)*40] = payload
        if native_out.raw != expected:raise ValueError('Independent chronological snapshot oracle failed')
        total += 1
        if race:race_cases += 1
    for case in cases:check(*case)
    for tail in range(17):check(tail,8,8,0,1,race=True)
    for tail in range(17):check(tail,8,8,0,1,filter_race=True)
    filter_race_cases = 17
    check(0,1,1,0,1,missing=True)
    report = dict(version_id='1.0.0',module='sdk',symbol='_ZN2nn3hid6detail13GetNpadStatesEPiPNS0_16NpadFullKeyStateEiRKj',
        module_relative=hex(START),original_bytes=LENGTH,original_body_sha256=hashlib.sha256(raw[START:START+LENGTH]).hexdigest(),
        sdk_input_sha256=EXPECTED,differential_cases=total,producer_race_cases=race_cases,filter_config_change_cases=filter_race_cases,
        cpp_source_sha256=hashlib.sha256((ROOT/'reconstructed/src/npad_full_key.cpp').read_bytes()).hexdigest(),
        tested_library_sha256=hashlib.file_digest(args.library.open('rb'),'sha256').hexdigest(),
        initializer_invocations=observations['initializations'],original_arm64_unmodified=True,
        independent_snapshot_oracle=True,all_ring_tail_positions=True,callee_saved_preserved=True,
        missing_entry_result='0x58cca', limitations=['SDK initializer isolated, not reconstructed by this test',
            'Malformed or permanently inconsistent shared-memory producer can retry indefinitely like original',
            'Not proof of whole-game decompilation or playable build'])
    (ROOT/'metadata/windows/1.0.0/npad-full-key-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__ == '__main__':main()
