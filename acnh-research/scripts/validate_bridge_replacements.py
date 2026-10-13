"""Exercise reconstructed routines through the actual translated DLL dispatch ABI."""
from __future__ import annotations
import ctypes as ct
import hashlib
import json
import random
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
    if ct.sizeof(CPU) != 896 or CPU.mem.offset != 848 or Module.entry_addr.offset != 24:
        raise ValueError('Unexpected host ABI layout')
    path = ROOT/'private/windows/bridge/ACNH_1_0_0_code.dll'
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
    with path.open('rb') as source:
        checksum = hashlib.file_digest(source, 'sha256').hexdigest()
    report = dict(version_id='1.0.0', passed=True, snx_abi=module.abi,
                  dll_sha256=checksum, dll_size=path.stat().st_size,
                  hash_dispatch_cases=checks, zero_dispatch_cases=zero_checks,
                  scope='Two reviewed entries through the actual DLL; interior fallback and whole gameplay unvalidated')
    target = ROOT/'metadata/windows/1.0.0/replacements-validation.json'
    target.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
