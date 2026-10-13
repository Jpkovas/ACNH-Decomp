"""Compare hand-recovered AccessKey parsing and selection against ACNH 1.0.0.

The original parser and token helper execute unchanged in Unicorn. Only imported
memcpy is isolated. SafeString's original no-op/termination functions also run.
The namespace region uses an injected immutable table, isolating its lazy getter.
"""
from __future__ import annotations

import argparse
import ctypes as ct
import hashlib
import json
import os
import random
import struct
import sys
from pathlib import Path

import unicorn as un
from unicorn import arm64_const as reg

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nxo_metadata import Image

BASE = 0x7100000000
PARSER, PARSER_SIZE = 0x216670, 0x52C
TOKEN_HELPER, TOKEN_HELPER_SIZE = 0x6B6C0, 0x2C4
SELECT_START, SELECT_STOP = 0x406564, 0x406624
MEMCPY, TABLE_GETTER = 0x220E430, 0x309FF0
STACK, STOP = 0x400000, 0x403000
OBJECTS, INPUT, KEY, NAMESPACE, TABLE = 0x500000, 0x510000, 0x5A0000, 0x5A1000, 0x5A2000


class Original:
    def __init__(self, image):
        self.image = image
        self.uc = un.Uc(un.UC_ARCH_ARM64, un.UC_MODE_ARM)
        pages = (0x1000, 0x6B000, 0x216000, 0x309000, 0x406000, 0x1990000,
                 0x220E000, 0x29CA000, 0x29B9000, 0x2A3E000, 0x301C000,
                 0x301D000, 0x31A6000, 0x32D0000)
        for page in pages:
            self.uc.mem_map(BASE + page, 0x1000)
            self.uc.mem_write(BASE + page, image.read(page, 0x1000))
            for address, target in image.relative.items():
                if page <= address < page + 0x1000:
                    self.uc.mem_write(BASE + address, struct.pack('<Q', BASE + target))
        self.uc.mem_map(STACK, 0x4000)
        self.uc.mem_map(OBJECTS, 0x1000)
        self.uc.mem_map(INPUT, 0x90000)
        self.uc.mem_map(KEY, 0x4000)
        self.memcpy_calls = 0
        self.table_calls = 0
        for target in (MEMCPY, TABLE_GETTER):
            self.uc.hook_add(un.UC_HOOK_CODE, self.dependency,
                             begin=BASE + target, end=BASE + target)

    def dependency(self, uc, address, size, context):
        if address == BASE + MEMCPY:
            destination = uc.reg_read(reg.UC_ARM64_REG_X0)
            source = uc.reg_read(reg.UC_ARM64_REG_X1)
            length = uc.reg_read(reg.UC_ARM64_REG_X2)
            if length > 0x80000:
                raise ValueError('Unexpected memcpy size')
            if length:
                uc.mem_write(destination, bytes(uc.mem_read(source, length)))
            self.memcpy_calls += 1
            uc.reg_write(reg.UC_ARM64_REG_PC, uc.reg_read(reg.UC_ARM64_REG_LR))
        elif address == BASE + TABLE_GETTER:
            self.table_calls += 1
            uc.reg_write(reg.UC_ARM64_REG_X0, TABLE)
            uc.reg_write(reg.UC_ARM64_REG_PC, uc.reg_read(reg.UC_ARM64_REG_LR))

    def preserved(self):
        rng = random.Random(0x216670)
        values = [rng.getrandbits(64) for _ in range(11)]
        for index, value in enumerate(values, 19):
            self.uc.reg_write(getattr(reg, f'UC_ARM64_REG_X{index}'), value)
        self.uc.reg_write(reg.UC_ARM64_REG_SP, STACK + 0x2000)
        self.uc.reg_write(reg.UC_ARM64_REG_LR, STOP)
        return values

    def check_preserved(self, values):
        actual = [self.uc.reg_read(getattr(reg, f'UC_ARM64_REG_X{i}')) for i in range(19, 30)]
        if actual != values or self.uc.reg_read(reg.UC_ARM64_REG_SP) != STACK + 0x2000:
            raise AssertionError('Parser callee-saved register or stack divergence')

    def split(self, payload, key_before, key_capacity, namespace_before, namespace_capacity,
              input_buffer=False, key_alias_input=False, namespace_alias_key=False):
        uc = self.uc
        input_before = payload + b'\0' + b'\xD3' * 8
        objects = bytearray(b'\xCC' * 0x100)
        struct.pack_into('<QQ', objects, 0, BASE + 0x301C1C0, INPUT)
        if input_buffer:
            struct.pack_into('<QQi', objects, 0, BASE + 0x301D7A0, INPUT, len(payload) + 1)
        key_pointer = INPUT if key_alias_input else KEY + 16
        namespace_pointer = key_pointer if namespace_alias_key else NAMESPACE + 16
        struct.pack_into('<QQi', objects, 0x40, BASE + 0x301D7A0, key_pointer, key_capacity)
        struct.pack_into('<QQi', objects, 0x80, BASE + 0x301D7A0, namespace_pointer, namespace_capacity)
        uc.mem_write(OBJECTS, bytes(objects))
        uc.mem_write(INPUT, input_before)
        uc.mem_write(KEY, key_before)
        uc.mem_write(NAMESPACE, namespace_before)
        values = self.preserved()
        uc.reg_write(reg.UC_ARM64_REG_X0, OBJECTS)
        uc.reg_write(reg.UC_ARM64_REG_X1, OBJECTS + 0x40)
        uc.reg_write(reg.UC_ARM64_REG_X2, OBJECTS + 0x80)
        uc.emu_start(BASE + PARSER, STOP, count=80000000)
        if uc.reg_read(reg.UC_ARM64_REG_PC) != STOP:
            raise ValueError('Original parser did not return')
        self.check_preserved(values)
        self.last_x0 = uc.reg_read(reg.UC_ARM64_REG_X0)
        if bytes(uc.mem_read(OBJECTS, len(objects))) != objects:
            raise AssertionError('Parser unexpectedly modified SafeString headers')
        if bytes(uc.mem_read(INPUT, len(input_before))) != input_before:
            raise AssertionError('Parser unexpectedly modified immutable input')
        return bytes(uc.mem_read(KEY, len(key_before))), bytes(uc.mem_read(NAMESPACE, len(namespace_before)))

    def select(self, text, table):
        uc = self.uc
        uc.mem_write(NAMESPACE, text + b'\0' + b'\0' * 64)
        pointers = []
        for index, item in enumerate(table):
            address = TABLE + 0x100 + index * 0x100
            pointers.append(address)
            uc.mem_write(address, item + b'\0')
        uc.mem_write(TABLE, struct.pack('<13Q', *pointers))
        uc.mem_write(STACK + 0x2000 + 0x10,
                     struct.pack('<QQi', BASE + 0x301D7A0, NAMESPACE, 64))
        uc.reg_write(reg.UC_ARM64_REG_SP, STACK + 0x2000)
        uc.reg_write(reg.UC_ARM64_REG_W23, 0)
        self.table_calls = 0
        uc.emu_start(BASE + SELECT_START, BASE + SELECT_STOP, count=100000)
        if uc.reg_read(reg.UC_ARM64_REG_PC) != BASE + SELECT_STOP:
            raise ValueError('Namespace selector did not reach its boundary')
        result = struct.unpack('<I', uc.mem_read(STACK + 0x2000, 4))[0]
        if bytes(uc.mem_read(NAMESPACE, len(text) + 1)) != text + b'\0':
            raise AssertionError('Namespace selector changed its terminated input')
        return result, self.table_calls


def oracle_copy(before, capacity, field):
    result = bytearray(before)
    count = min(len(field), capacity - 1)
    result[16:16 + count] = field[:count]
    result[16 + count] = 0
    return bytes(result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--report', type=Path,
                        default=ROOT / 'metadata/1.0.0/access-key-validation.json')
    args = parser.parse_args()
    image = Image('1.0.0')
    for segment, (_, data) in zip(image.manifest['segments'], image.segments):
        if hashlib.sha256(data).hexdigest() != segment['sha256']:
            raise ValueError('NSO segment provenance mismatch')
    if image.relative[0x32D0668] + 0x10 != 0x301C1C0 or image.relative[0x301C1D8] != 0x19C0:
        raise ValueError('EventFlagInt input SafeString callback anchor differs')
    if image.read(0x19C0, 4) != b'\xC0\x03\x5F\xD6':
        raise ValueError('Known input callback is not the original ret')
    direct_callers = []
    code = image.segments[0][1]
    for index, (word,) in enumerate(struct.iter_unpack('<I', code[:len(code) // 4 * 4])):
        if word & 0xFC000000 != 0x94000000:
            continue
        displacement = word & 0x3FFFFFF
        if displacement & (1 << 25):
            displacement -= 1 << 26
        if index * 4 + displacement * 4 == PARSER:
            direct_callers.append(index * 4)
    reviewed_callers = (0x309B60, 0x30AD50, 0x30BBA0, 0x30CA20, 0x30CC2C,
                        0x30DDD0, 0x31C770, 0x31CA30, 0x3408EC, 0x4055E0,
                        0x406560, 0x4075F0)
    if direct_callers != list(reviewed_callers):
        raise ValueError('Direct caller set differs from the reviewed assembly')
    directory = os.add_dll_directory(str(ROOT / 'private/tools/llvm-mingw/llvm-mingw-20261006-ucrt-x86_64/bin'))
    library = ct.CDLL(str(args.library.resolve()))
    split = library.acnh_access_key_split
    split.argtypes = [ct.c_char_p, ct.c_void_p, ct.c_int32, ct.c_void_p, ct.c_int32]
    split.restype = None
    select = library.acnh_access_key_namespace
    select.argtypes = [ct.c_char_p, ct.POINTER(ct.c_char_p)]
    select.restype = ct.c_uint32
    original = Original(image)
    rng = random.Random(0x216670)
    cases = [b'', b'plain', b':', b'::', b':::ignored', b'prefix:key',
             b'prefix:', b':key', b'prefix:key:ignored', b' prefix : key ',
             bytes(range(1, 256)), b'A' * 4095, b'A' * 511 + b':' + b'B' * 511]
    cases += [b'A' * size + b':' + b'B' * size for size in (1, 2, 3, 63, 64, 65, 127, 128, 129)]
    cases += [bytes(rng.randrange(1, 256) for _ in range(rng.randrange(256))) for _ in range(256)]
    capacities = [(128, 64), (1, 1), (2, 2), (3, 4), (127, 63)]
    total = 0
    return_categories = {'key_buffer_pointer': 0, 'input_object_pointer': 0,
                         'temporary_delimiter_object_pointer': 0}
    def check_return(payload):
        separator = payload.find(b':')
        if separator < 0:
            category, expected = 'key_buffer_pointer', KEY + 16
        elif separator + 1 == len(payload):
            category, expected = 'input_object_pointer', OBJECTS
        else:
            category, expected = 'temporary_delimiter_object_pointer', STACK + 0x2000 - 0x70
        if original.last_x0 != expected:
            raise AssertionError(f'Original x0 effect differs: {original.last_x0:#x} vs {expected:#x}')
        return_categories[category] += 1
    for payload in cases:
        for key_capacity, namespace_capacity in capacities:
            key_before = bytes(rng.getrandbits(8) for _ in range(192))
            namespace_before = bytes(rng.getrandbits(8) for _ in range(128))
            key = ct.create_string_buffer(key_before, len(key_before))
            namespace = ct.create_string_buffer(namespace_before, len(namespace_before))
            split(payload, ct.addressof(key) + 16, key_capacity,
                  ct.addressof(namespace) + 16, namespace_capacity)
            actual = original.split(payload, key_before, key_capacity, namespace_before, namespace_capacity)
            check_return(payload)
            fields = payload.split(b':')
            expected = (oracle_copy(key_before, key_capacity, fields[0]), namespace_before) if len(fields) == 1 else (
                oracle_copy(key_before, key_capacity, fields[1]),
                oracle_copy(namespace_before, namespace_capacity, fields[0]))
            if actual != expected or (key.raw, namespace.raw) != expected:
                raise AssertionError(f'AccessKey split divergence in case {total}')
            total += 1
    # Exercise a long readable input close to the original SafeString scan bound.
    for payload in (b'L' * 0x7FF00, b'L' * 0x7FF00 + b':tail'):
        key_before, namespace_before = b'\xA5' * 192, b'\x5A' * 128
        key = ct.create_string_buffer(key_before, len(key_before))
        namespace = ct.create_string_buffer(namespace_before, len(namespace_before))
        split(payload, ct.addressof(key) + 16, 128, ct.addressof(namespace) + 16, 64)
        actual = original.split(payload, key_before, 128, namespace_before, 64)
        check_return(payload)
        if actual != (key.raw, namespace.raw):
            raise AssertionError('Long input divergence')
        total += 1
    original_table = [part.strip().encode('ascii') for part in image.string(0x2955BB6).split(',')]
    if len(original_table) != 13:
        raise ValueError('Original namespace table shape differs')
    synthetic_table = [f'synthetic_{index}'.encode('ascii') for index in range(13)]
    selection_cases = 0
    for table in (original_table, synthetic_table):
        native_table = (ct.c_char_p * 13)(*table)
        texts = table + [b'', b'unknown', b' ' + table[0], table[0] + b' ', table[1].lower(), b'\xFF']
        texts += [item[:-1] for item in table] + [item + b'x' for item in table]
        for text in texts:
            expected = table.index(text) if text in table else 0
            actual, calls = original.select(text, table)
            expected_calls = expected + 1 if text in table else 13
            if actual != expected or select(text, native_table) != expected or calls != expected_calls:
                raise AssertionError('Namespace selection divergence')
            selection_cases += 1
    report = {
        'version_id': '1.0.0', 'module': 'main',
        'parser_relative_address': hex(PARSER), 'parser_size': PARSER_SIZE,
        'original_token_helper': {'relative_address': hex(TOKEN_HELPER), 'size': TOKEN_HELPER_SIZE},
        'namespace_region': {'start': hex(SELECT_START), 'stop': hex(SELECT_STOP)},
        'parser_sha256': hashlib.sha256(image.read(PARSER, PARSER_SIZE)).hexdigest(),
        'token_helper_sha256': hashlib.sha256(image.read(TOKEN_HELPER, TOKEN_HELPER_SIZE)).hexdigest(),
        'parser_cases': total, 'namespace_cases': selection_cases,
        'cpp_source_sha256': hashlib.sha256((ROOT/'reconstructed/src/access_key.cpp').read_bytes()).hexdigest(),
        'original_arm64_vs_native_vs_independent_oracle': True,
        'original_argument_layout': {
            'input': {'register': 'x0', 'vptr_offset': 0, 'data_offset': 8},
            'key': {'register': 'x1', 'vptr_offset': 0, 'data_offset': 8, 'signed_capacity_offset': 16},
            'namespace': {'register': 'x2', 'vptr_offset': 0, 'data_offset': 8, 'signed_capacity_offset': 16},
            'event_flag_int_input_member_offset': '0xd0',
            'event_flag_int_input_vptr_relative': '0x301c1c0',
            'event_flag_int_input_callback_relative': '0x19c0',
            'input_callback_slot': '0x18'
        },
        'input_callback_body': {'relative_address': '0x19c0', 'size': 4,
                                'sha256': hashlib.sha256(image.read(0x19C0, 4)).hexdigest()},
        'reviewed_direct_callers': [
            {'call_site': hex(site), 'parser_x0_consumed': False,
             'discarded_by': ('explicit x0 assignment' if site in (0x30CA20, 0x3408EC)
                              else 'zero-initialized index enters no-argument namespace table getter, which overwrites x0')}
            for site in direct_callers],
        'parser_original_calls': {'memcpy_isolated': original.memcpy_calls,
                                  'safe_string_callbacks': 'original 0x19c0 and 0x1990780'},
        'buffer_writes_and_guards_checked': True,
        'parser_register_and_stack_preservation_checked': True,
        'original_x0_exit_effects': {
            'observed_cases': return_categories,
            'no_separator': 'key data pointer',
            'separator_is_last_input_byte': 'input SafeString object pointer',
            'separator_followed_by_non_nul': 'entry SP - 0x70, temporary delimiter SafeString object',
            'native_research_api_return': 'void; these incidental ARM64 register effects need a separate bridge adapter'
        },
        'contract': {'capacities_include_nul': True, 'absent_separator_preserves_namespace': True,
                     'fields_consumed': 2, 'separator': 'colon', 'unmatched_namespace_index': 0,
                     'namespace_table_entries': 13},
        'limitations': [
            'This is a semantic research interface; original C++ SafeString declarations and ABI are not recovered.',
            'Input must be readable and NUL-terminated below 2^19 bytes; output capacities must be positive.',
            'Input and output buffers must be distinct and non-overlapping; arbitrary mutable virtual callbacks are excluded.',
            'The parser and original token helper run unchanged; imported memcpy is isolated.',
            'Namespace selection executes its original region with an injected immutable table; lazy table initialization is excluded.',
            'All 12 direct BL callers were reviewed and discard the incidental x0 return; indirect callers are not proved.',
            'SaveIO backends, dispatch side effects and the full EventFlagInt handler remain unrecovered.',
            'No Windows game DLL integration or gameplay validation is claimed by this isolated test.'
        ],
        'proposed_bridge_fallback_conditions': [
            'Input callback differs from the original no-op main+0x19c0.',
            'Either output capacity is nonpositive.',
            'Input or output byte intervals overlap.',
            'Input has no NUL before 2^19 bytes.'
        ]
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'parser_cases': total, 'namespace_cases': selection_cases, 'passed': True}))
    directory.close()


if __name__ == '__main__':
    main()
