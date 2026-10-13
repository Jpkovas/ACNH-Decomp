"""Exercise reconstructed routines through the actual translated DLL dispatch ABI."""
from __future__ import annotations
import ctypes as ct
import argparse
import hashlib
import json
import random
import struct
from pathlib import Path
import mmh3

ROOT = Path(__file__).resolve().parents[1]


class Vector(ct.Union):
    _fields_ = [('bytes', ct.c_uint8*16), ('words', ct.c_uint64*2)]


class CPU(ct.Structure):
    _fields_ = [('x', ct.c_uint64*32), ('pc', ct.c_uint64),
                ('n', ct.c_uint32), ('z', ct.c_uint32), ('cf', ct.c_uint32), ('vf', ct.c_uint32),
                ('v', Vector*32), ('fpcr', ct.c_uint32), ('fpsr', ct.c_uint32),
                ('tpidr', ct.c_uint64), ('tpidrro', ct.c_uint64),
                ('excl_addr', ct.c_uint64), ('excl_val', ct.c_uint64), ('excl_val2', ct.c_uint64),
                ('excl_size', ct.c_uint32), ('excl_on', ct.c_uint32),
                ('mem', ct.c_void_p), ('disp', ct.c_void_p), ('code_lo', ct.c_uint64),
                ('code_hi', ct.c_uint64), ('rt', ct.c_void_p), ('thread', ct.c_void_p)]


class Module(ct.Structure):
    _fields_ = [('abi', ct.c_uint32), ('nmods', ct.c_uint32), ('mods', ct.c_void_p),
                ('nentries', ct.c_uint32), ('entry_addr', ct.POINTER(ct.c_uint64)),
                ('entry_fn', ct.POINTER(ct.c_void_p)), ('interp', ct.c_void_p),
                ('code_lo', ct.c_uint64), ('code_hi', ct.c_uint64), ('title', ct.c_void_p),
                ('title_id', ct.c_uint64), ('main_stack', ct.c_uint32),
                ('main_prio', ct.c_uint32), ('main_core', ct.c_uint32)]


def find_entry(module: Module, address: int):
    low, high = 0, module.nentries
    while low < high:
        mid = (low+high)//2
        if module.entry_addr[mid] < address:
            low = mid+1
        else:
            high = mid
    if low == module.nentries or module.entry_addr[low] != address:
        raise ValueError(f'Missing dispatch entry {address:#x}')
    return ct.CFUNCTYPE(None, ct.POINTER(CPU), ct.c_uint64)(module.entry_fn[low])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--module', type=Path, default=ROOT/'private/windows/bridge/ACNH_1_0_0_code.dll')
    args = parser.parse_args()
    if ct.sizeof(CPU) != 896 or CPU.mem.offset != 848 or Module.entry_addr.offset != 24:
        raise ValueError('Unexpected host ABI layout')
    path = args.module
    dll = ct.CDLL(str(path))
    dll.snx_module.restype = ct.POINTER(Module)
    module = dll.snx_module().contents
    if module.abi != 3 or module.nmods != 4:
        raise ValueError('Unexpected translated module ABI')
    murmur = find_entry(module, 0x8006bf0)
    zero = find_entry(module, 0x800fc10)
    rng = random.Random(0xac10)
    corpus = [b'', b'EventFlagInt', b'A'*4095, bytes(range(1, 256))]
    corpus += [bytes(rng.randrange(1, 256) for _ in range(length)) for length in range(1, 65)]
    checks = 0
    for payload in corpus:
        for alignment in range(4):
            for seed in (0, 1, 0xdeadbeef, 0xffffffff):
                memory = ct.create_string_buffer(len(payload)+256)
                pointer = 128+alignment
                ct.memmove(ct.addressof(memory)+pointer, payload+b'\0', len(payload)+1)
                cpu = CPU()
                cpu.mem = ct.addressof(memory)
                cpu.x[0], cpu.x[1], cpu.x[30] = pointer, seed, 0x1234567890
                for i in range(19, 30):
                    cpu.x[i] = rng.getrandbits(64)
                cpu.x[31] = 0x12340000
                preserved = list(cpu.x[19:30])+[cpu.x[31]]
                before = memory.raw
                murmur(ct.byref(cpu), 0x8006bf0)
                if cpu.x[0] != mmh3.hash(payload, seed, signed=False) or cpu.pc != cpu.x[30]:
                    raise AssertionError('Hash result or return PC mismatch')
                if list(cpu.x[19:30])+[cpu.x[31]] != preserved or memory.raw != before:
                    raise AssertionError('Callee saved state or input mutated')
                checks += 1
    zero_checks = 0
    for value in (0, 1, 0xffffffff, 0xffffffffffffffff):
        cpu = CPU()
        cpu.x[0], cpu.x[30] = value, 0x1234567890
        zero(ct.byref(cpu), 0x800fc10)
        if cpu.x[0] != 0 or cpu.pc != cpu.x[30]:
            raise AssertionError('Constant zero dispatch mismatch')
        zero_checks += 1
    full_key = find_entry(module, 0xc50ca00)
    # Reserve sparse guest address space for the SDK globals used by its adapter.
    import mmap
    guest_memory = mmap.mmap(-1, 0xe000000)
    guest_base = ct.addressof(ct.c_char.from_buffer(guest_memory))
    init_calls = [0]
    guest_function = ct.CFUNCTYPE(None, ct.POINTER(CPU), ct.c_uint64)
    def isolated_init(pointer, address):
        if address != 0xc50bfd0: raise AssertionError('Unexpected dependency entry')
        init_calls[0] += 1
        pointer.contents.pc = pointer.contents.x[30]
    initialize = guest_function(isolated_init)
    dispatch = (ct.c_void_p*1)(ct.cast(initialize,ct.c_void_p).value)
    full_key_checks = 0
    for tail in range(17):
        for capacity in (0,1,8,17):
            entry = 0x4000
            for age in range(17):
                slot = (tail-age)%17
                payload = struct.pack('<QQ4iII',1000-age,1<<age,age,-age,age*2,-age*2,1,0)
                guest_memory[entry+0x48+slot*48:entry+0x50+slot*48] = struct.pack('<Q',1000-age)
                guest_memory[entry+0x50+slot*48:entry+0x78+slot*48] = payload
            guest_memory[entry+0x38:entry+0x48] = struct.pack('<QQ',tail,17)
            for device in (0,7,0x10,0x20):
                index = device if device < 8 else 9 if device == 0x10 else 8
                guest_memory[0xd427090+index*8:0xd427098+index*8] = struct.pack('<Q',entry)
                guest_memory[0x2000:0x2004] = struct.pack('<I',device)
                guest_memory[0x1000:0x1000+0x500] = b'\xa5'*0x500
                cpu = CPU()
                cpu.mem = guest_base
                cpu.disp = ct.addressof(dispatch)
                cpu.code_lo, cpu.code_hi = 0xc50bfd0,0xc50bfd4
                cpu.x[0],cpu.x[1],cpu.x[2],cpu.x[3],cpu.x[30] = 0x800,0x1000,capacity,0x2000,0x1234567890
                for i in range(19,30):cpu.x[i]=rng.getrandbits(64)
                cpu.x[31]=0x3000
                preserved=list(cpu.x[19:30])+[cpu.x[31]]
                full_key(ct.byref(cpu),0xc50ca00)
                if cpu.x[0] or cpu.pc != cpu.x[30] or list(cpu.x[19:30])+[cpu.x[31]] != preserved:
                    raise AssertionError('FullKey dispatch ABI mismatch')
                if struct.unpack('<i',guest_memory[0x800:0x804])[0] != capacity:
                    raise AssertionError('FullKey dispatch count mismatch')
                for age in range(capacity):
                    data=struct.unpack('<QQ4iII',guest_memory[0x1000+age*40:0x1028+age*40])
                    if data != (1000-age,1<<age,age,-age,age*2,-age*2,1,0):
                        raise AssertionError('FullKey dispatch payload mismatch')
                if guest_memory[0x1000+capacity*40:0x1500] != b'\xa5'*(0x500-capacity*40):
                    raise AssertionError('FullKey dispatch wrote past caller capacity')
                full_key_checks += 1
    if init_calls[0] != full_key_checks:raise AssertionError('FullKey initializer delegation mismatch')
    guest_memory.close()
    flag_entry = find_entry(module, 0x840b85c)
    flag_checks = 0
    pairs = [(value, border) for value in (0, 1, 2, 3, 31, 32, 0x7fffffff, 0x80000000, 0xfffffffe, 0xffffffff)
             for border in (-2147483648, -1, 0, 1, 2, 31, 32, 33, 2147483647)]
    pairs += [(rng.getrandbits(32), ct.c_int32(rng.getrandbits(32)).value) for _ in range(256)]
    for value, border in pairs:
        for mode in list(range(10))+[0xffffffff]:
            memory = ct.create_string_buffer(0x3000)
            object_address, stack = 0x800, 0x1800
            ct.memmove(ct.addressof(memory)+object_address, b'\xa5'*0x200, 0x200)
            struct.pack_into('<i', memory, object_address+0x100, border)
            struct.pack_into('<I', memory, object_address+0x128, mode)
            cpu = CPU(); cpu.mem = ct.addressof(memory)
            cpu.x[0], cpu.x[19] = value | (rng.getrandbits(32) << 32), object_address
            cpu.x[31], cpu.x[29] = stack, stack+0x140
            restored = {register: rng.getrandbits(64) for register in range(19, 25)}
            restored[28], restored[29], restored[30] = rng.getrandbits(64), rng.getrandbits(64), 0x1234567890
            for offset, registers in ((0x100, [28]), (0x110, [24, 23]), (0x120, [22, 21]),
                                      (0x130, [20, 19]), (0x140, [29, 30])):
                for index, register in enumerate(registers): struct.pack_into('<Q', memory, stack+offset+index*8, restored[register])
            before = memory.raw
            limit = border & 0xffffffff
            expected = int((value != limit, value == limit, value <= limit, value < limit,
                            value >= limit, value > limit, value.bit_count() < border)[mode]) if mode < 7 else 0
            flag_entry(ct.byref(cpu), 0x840b85c)
            if cpu.x[0] != expected or cpu.pc != restored[30] or cpu.x[31] != stack+0x150:
                raise AssertionError('EventFlagInt predicate or epilogue mismatch')
            if any(cpu.x[register] != saved for register, saved in restored.items()):
                raise AssertionError('EventFlagInt epilogue did not restore saved registers')
            if memory.raw != before: raise AssertionError('Reconstructed EventFlagInt region wrote guest memory')
            flag_checks += 1
    with path.open('rb') as source:
        checksum = hashlib.file_digest(source, 'sha256').hexdigest()
    report = dict(version_id='1.0.0', passed=True, snx_abi=module.abi,
                  dll_sha256=checksum, dll_size=path.stat().st_size,
                  hash_dispatch_cases=checks, zero_dispatch_cases=zero_checks,
                  full_key_dispatch_cases=full_key_checks,
                  flag_int_partial_region_cases=flag_checks,
                  full_key_initializer='isolated callback; actual initializer remains original SDK',
                  scope='Three reviewed entries and the EventFlagInt terminal region through the actual DLL; query backends, interior fallback and whole gameplay unvalidated')
    target = ROOT/'metadata/windows/1.0.0/replacements-validation.json'
    target.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
