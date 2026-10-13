"""Validate the guarded AccessKey recovery through the real Windows module ABI.

An optional --adapter-library checks the standalone guard before the coordinated
game DLL build. That mode verifies rejection, and does not claim fallback-body
execution. The default mode calls F_821B670 in the actual game module, comparing
its supported and safely excluded cases against unmodified original ARM64.
"""
from __future__ import annotations

import argparse
import ctypes as ct
import hashlib
import json
import mmap
import os
import random
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nxo_metadata import Image
from validate_access_key import Original, OBJECTS, INPUT, KEY, NAMESPACE, STACK
from validate_bridge_replacements import CPU, Module, find_entry
from replace_bridge_routines import ACCESS_KEY_ADAPTER_REVISION, access_key_compiled_provenance

MAIN_BASE, ENTRY = 0x8005000, 0x821B670
NOOP, TERMINATE = 0x80069C0, 0x9995780
MEMCPY_TARGET, MEMCPY_GOT = NOOP + 4, MAIN_BASE + 0x32CE7E0
MEMORY_SIZE = 0xE000000


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--module', type=Path,
                        default=ROOT/'private/windows/bridge/ACNH_1_0_0_code.dll')
    parser.add_argument('--adapter-library', type=Path)
    args = parser.parse_args()
    path = (args.adapter_library or args.module).resolve()
    adapter_only = args.adapter_library is not None
    manifest_path = ROOT/'metadata/windows/1.0.0/reconstructed-replacements.json'
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    records = [record for record in manifest.get('guarded_entries', []) if record.get('function') == 'F_821B670']
    if len(records) != 1 or records[0].get('adapter_revision') != ACCESS_KEY_ADAPTER_REVISION:
        raise ValueError('Missing corresponding AccessKey build manifest; run the coordinated build first')
    record = records[0]
    for field, source in (('cpp_source_sha256', ROOT/'reconstructed/src/access_key.cpp'),
                          ('adapter_source_sha256', ROOT/'windows_bridge/access_key_adapter.c'),
                          ('generated_file_sha256', ROOT/'private/windows/bridge/ACNH_1_0_0_build'/record['generated_file'])):
        if record[field] != hashlib.sha256(source.read_bytes()).hexdigest():
            raise ValueError(f'AccessKey manifest does not match current {field}; no validation report written')
    compiled_record = record.get('compiled_provenance', {})
    provenance_path = ROOT/'private/windows/bridge/ACNH_1_0_0_build'/compiled_record.get('generated_file', '')
    if not provenance_path.is_file() or compiled_record.get('generated_file_sha256') != hashlib.sha256(provenance_path.read_bytes()).hexdigest():
        raise ValueError('AccessKey compiled provenance source differs from its build manifest')
    expected_provenance = access_key_compiled_provenance(record)
    return_lrs = [int(value, 16) for value in record['reviewed_return_lrs']]
    if len(return_lrs) != 12 or len(set(return_lrs)) != 12:
        raise ValueError('Expected twelve distinct reviewed caller return addresses')
    library_hash_before = hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()
    dll_directory = os.add_dll_directory(str(ROOT/'private/tools/llvm-mingw/llvm-mingw-20261006-ucrt-x86_64/bin'))
    library = ct.CDLL(str(path))
    try:
        compiled_provenance = getattr(library, compiled_record['export'])
    except AttributeError as error:
        raise ValueError('Loaded AccessKey DLL lacks corresponding compiled provenance; no validation report written') from error
    compiled_provenance.argtypes = []
    compiled_provenance.restype = ct.c_char_p
    if json.loads(compiled_provenance().decode('ascii')) != expected_provenance:
        raise ValueError('Loaded AccessKey DLL provenance differs from source/build manifest; no validation report written')
    guard = library.acnh_bridge_access_key_try
    guard.argtypes = [ct.POINTER(CPU), ct.c_uint64]
    guard.restype = ct.c_int
    if ct.sizeof(CPU) != 896 or CPU.mem.offset != 848:
        raise ValueError('Unexpected runtime CPU ABI')
    entry = None
    module = None
    if not adapter_only:
        library.snx_module.restype = ct.POINTER(Module)
        module = library.snx_module().contents
        if module.abi != 3 or module.nmods != 4:
            raise ValueError('Unexpected ACNH translated module')
        entry = find_entry(module, ENTRY)
    image = Image('1.0.0')
    original = Original(image)
    memory = mmap.mmap(-1, MEMORY_SIZE)
    guest_base = ct.addressof(ct.c_char.from_buffer(memory))
    for offset, data in image.segments:
        memory[MAIN_BASE + offset:MAIN_BASE + offset + len(data)] = data
    for address, target in image.relative.items():
        struct.pack_into('<Q', memory, MAIN_BASE + address, MAIN_BASE + target)
    dependencies = dict(noop=0, terminate=0, memcpy=0)
    callback_errors = []
    guest_function = ct.CFUNCTYPE(None, ct.POINTER(CPU), ct.c_uint64)
    dispatch = None
    callbacks = []
    if not adapter_only:
        noop_entry = find_entry(module, NOOP)
        terminate_entry = find_entry(module, TERMINATE)
        def noop(pointer, address):
            dependencies['noop'] += 1
            noop_entry(pointer, address)
        def terminate(pointer, address):
            dependencies['terminate'] += 1
            terminate_entry(pointer, address)
        def memcpy(pointer, address):
            cpu = pointer.contents
            destination, source, length = cpu.x[0], cpu.x[1], cpu.x[2]
            if destination + length > MEMORY_SIZE or source + length > MEMORY_SIZE:
                callback_errors.append('Out-of-range imported memcpy')
            else:
                ct.memmove(guest_base + destination, guest_base + source, length)
            dependencies['memcpy'] += 1
            cpu.pc = cpu.x[30]
        callbacks = [guest_function(noop), guest_function(memcpy), guest_function(terminate)]
        dispatch = (ct.c_void_p * ((TERMINATE + 4 - NOOP) // 4))()
        for address, callback in zip((NOOP, MEMCPY_TARGET, TERMINATE), callbacks):
            dispatch[(address - NOOP) // 4] = ct.cast(callback, ct.c_void_p).value
        struct.pack_into('<Q', memory, MEMCPY_GOT, MEMCPY_TARGET)
    rng = random.Random(0x821B670)
    payloads = [b'', b'plain', b':', b'::', b':::ignored', b'prefix:key', b'prefix:',
                b':key', b'prefix:key:ignored', b' prefix : key ', bytes(range(1, 256)),
                b'A' * 4095, b'A' * 511 + b':' + b'B' * 511]
    cases = [(payload, key_capacity, namespace_capacity, {}, True)
             for payload in payloads for key_capacity, namespace_capacity in ((128, 64), (1, 1), (2, 2), (3, 4), (127, 63))]
    cases += [(bytes(rng.randrange(1, 256) for _ in range(rng.randrange(256))), 128, 64, {}, True)
              for _ in range(128)]
    cases += [(payload, 128, 64, {'input_buffer': True}, False)
              for payload in (b'plain', b'prefix:key', b'prefix:', b'prefix:key:ignored')]
    cases += [(b'plain', 128, 64, {'key_alias_input': True}, False),
              (b'prefix:key', 128, 64, {'namespace_alias_key': True}, False),
              (b'L' * 0x80000, 128, 64, {}, False),
              (b'L' * 0x80001, 128, 64, {}, False),
              (b'prefix:key', 128, 64, {'unknown_caller': True}, False)]
    counts = dict(fast_path=0, fallback_body=0, guard_rejections=0)
    reviewed_lr_counts = {hex(value): 0 for value in return_lrs}
    for index, (payload, key_capacity, namespace_capacity, options, handled) in enumerate(cases):
        key_before = bytes(rng.getrandbits(8) for _ in range(192))
        namespace_before = bytes(rng.getrandbits(8) for _ in range(128))
        original_options = {key: value for key, value in options.items() if key != 'unknown_caller'}
        expected = original.split(payload, key_before, key_capacity, namespace_before, namespace_capacity, **original_options)
        input_before = payload + b'\0' + b'\xD3' * 8
        objects = bytearray(b'\xCC' * 0x100)
        input_vptr = MAIN_BASE + (0x301D7A0 if options.get('input_buffer') else 0x301C1C0)
        struct.pack_into('<QQ', objects, 0, input_vptr, INPUT)
        if options.get('input_buffer'):
            struct.pack_into('<i', objects, 16, len(payload) + 1)
        key_pointer = INPUT if options.get('key_alias_input') else KEY + 16
        namespace_pointer = key_pointer if options.get('namespace_alias_key') else NAMESPACE + 16
        struct.pack_into('<QQi', objects, 0x40, MAIN_BASE + 0x301D7A0, key_pointer, key_capacity)
        struct.pack_into('<QQi', objects, 0x80, MAIN_BASE + 0x301D7A0, namespace_pointer, namespace_capacity)
        memory[OBJECTS:OBJECTS + len(objects)] = objects
        memory[INPUT:INPUT + len(input_before)] = input_before
        memory[KEY:KEY + len(key_before)] = key_before
        memory[NAMESPACE:NAMESPACE + len(namespace_before)] = namespace_before
        stack = STACK + 0x2000
        memory[stack - 0xF0:stack] = b'\xFA' * 0xF0
        cpu = CPU()
        cpu.mem = guest_base
        if dispatch is not None:
            cpu.disp = ct.addressof(dispatch)
            cpu.code_lo, cpu.code_hi = NOOP, TERMINATE + 4
        return_lr = 0x1234567890 if options.get('unknown_caller') else return_lrs[index % len(return_lrs)]
        cpu.x[0], cpu.x[1], cpu.x[2], cpu.x[30], cpu.x[31] = OBJECTS, OBJECTS + 0x40, OBJECTS + 0x80, return_lr, stack
        for register in range(19, 30):
            cpu.x[register] = rng.getrandbits(64)
        preserved = list(cpu.x[19:32])
        cpu_before = bytes(cpu)
        dependency_before = dict(dependencies)
        if adapter_only:
            accepted = guard(ct.byref(cpu), ENTRY)
            if accepted != int(handled):
                raise AssertionError(f'Guard decision mismatch in case {index}')
            if not accepted:
                if bytes(cpu) != cpu_before:
                    raise AssertionError('Rejected guard changed CPU')
                if (memory[KEY:KEY + len(key_before)], memory[NAMESPACE:NAMESPACE + len(namespace_before)]) != (key_before, namespace_before):
                    raise AssertionError('Rejected guard changed output memory')
                counts['guard_rejections'] += 1
                continue
        else:
            entry(ct.byref(cpu), ENTRY)
        if callback_errors:
            raise AssertionError(callback_errors)
        actual = (memory[KEY:KEY + len(key_before)], memory[NAMESPACE:NAMESPACE + len(namespace_before)])
        if actual != expected or cpu.x[0] != original.last_x0:
            raise AssertionError(f'Output or original x0 divergence in case {index}')
        if cpu.pc != cpu.x[30] or cpu.pc != return_lr or list(cpu.x[19:32]) != preserved:
            raise AssertionError('Parser ABI did not preserve SP/LR/callee-saved state')
        if memory[OBJECTS:OBJECTS + len(objects)] != objects or memory[INPUT:INPUT + len(input_before)] != input_before:
            raise AssertionError('Parser changed its headers or readable input')
        stack_changed = memory[stack - 0xF0:stack] != b'\xFA' * 0xF0
        if handled:
            if stack_changed or dependencies != dependency_before:
                raise AssertionError('Supported case did not use the guarded native path')
            counts['fast_path'] += 1
            reviewed_lr_counts[hex(return_lr)] += 1
        else:
            if not stack_changed or dependencies == dependency_before:
                raise AssertionError('Excluded case did not execute the translated fallback')
            counts['fallback_body'] += 1
    # Invalid capacities and interior addresses are checked as guard decisions.
    # They are not executed through the original body, which may access invalid memory.
    cpu = CPU(); cpu.mem = guest_base
    cpu.x[0], cpu.x[1], cpu.x[2], cpu.x[31] = OBJECTS, OBJECTS + 0x40, OBJECTS + 0x80, STACK + 0x2000
    cpu.x[30] = return_lrs[0]
    struct.pack_into('<QQ', memory, OBJECTS, MAIN_BASE + 0x301C1C0, INPUT)
    struct.pack_into('<QQi', memory, OBJECTS + 0x40, MAIN_BASE + 0x301D7A0, KEY + 16, 128)
    struct.pack_into('<QQi', memory, OBJECTS + 0x80, MAIN_BASE + 0x301D7A0, NAMESPACE + 16, 64)
    for capacity in (0, -1, -2147483648):
        struct.pack_into('<i', memory, OBJECTS + 0x40 + 16, capacity)
        before = bytes(cpu)
        if guard(ct.byref(cpu), ENTRY) or bytes(cpu) != before:
            raise AssertionError('Invalid capacity was accepted or mutated CPU')
        counts['guard_rejections'] += 1
    if guard(ct.byref(cpu), ENTRY + 4):
        raise AssertionError('Interior entry accepted as recovered function entry')
    counts['guard_rejections'] += 1
    if not all(reviewed_lr_counts.values()):
        raise AssertionError('Not all twelve reviewed callers exercised the guarded path')
    library_hash_after = hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()
    if library_hash_before != library_hash_after or manifest_path.read_bytes() != manifest_bytes:
        raise ValueError('Library or build manifest changed during validation; no report written')
    report = dict(version_id='1.0.0', passed=True, runtime_entry=hex(ENTRY),
                  mode='standalone guard only' if adapter_only else 'actual game DLL entry',
                  library_sha256=library_hash_after,
                  corresponding_manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
                  embedded_provenance_verified=expected_provenance,
                  cases=counts, original_arm64_compared=True,
                  cpp_source_sha256=expected_provenance['cpp_source_sha256'],
                  adapter_source_sha256=expected_provenance['adapter_source_sha256'],
                  fast_path_by_reviewed_return_lr=reviewed_lr_counts,
                  unknown_caller_uses_original_fallback=not adapter_only,
                  preserved=['x19..x29', 'SP', 'LR', 'return PC', 'output canaries', 'headers', 'input'],
                  imported_memcpy='isolated native memory copy; original SafeString callbacks executed in full module mode',
                  original_inactive_stack_writes_reproduced=False,
                  incidental_x0_preserved=True,
                  limitations=['Guard checks no page permissions; headers and readable buffers remain caller preconditions',
                               'Callee-saved ABI is checked; original caller-saved/NZCV state and dead stack bytes are excluded',
                               'Guard-only rejection does not prove execution of the original fallback',
                               'Entire parser, EventFlagInt backend and whole-game decompilation are not claimed'])
    target = (ROOT/'private/outputs/1.0.0/access-key/adapter-validation.json' if adapter_only else
              ROOT/'metadata/windows/1.0.0/access-key-bridge-validation.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'passed': True, 'mode': report['mode'], 'cases': counts}))
    memory.close()
    dll_directory.close()


if __name__ == '__main__':
    main()
