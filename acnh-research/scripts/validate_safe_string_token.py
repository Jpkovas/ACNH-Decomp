"""Compare the hand-recovered SafeString token helper with original ARM64 execution.

Game instructions and SafeString callbacks run unchanged. Only imported memcpy is
isolated, as in the existing AccessKey harness. Reports with binary hashes stay private.
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

from unicorn import arm64_const as reg

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_access_key import BASE, INPUT, KEY, OBJECTS, STOP, Original, ROOT, TOKEN_HELPER, TOKEN_HELPER_SIZE
from nxo_metadata import Image

DELIMITERS = 0x600000
ITERATOR = OBJECTS + 0x100
EMPTY_RELATIVE = 0x29B9D8F
SCAN_LAST = 0x80000


def bounded_length(text):
    position = text[:SCAN_LAST + 1].find(b"\0")
    return position if position >= 0 else 0


def oracle(source, index, delimiters, capacity, exact_alias):
    if exact_alias:
        return 0, None
    first_length = bounded_length(source)
    if index < 0 or index > first_length:
        return 0, b"\0"
    alphabet = delimiters[:SCAN_LAST + 1].split(b"\0", 1)[0]
    tail = source[index:]
    finish = next(i for i, byte in enumerate(tail) if byte == 0 or byte in alphabet)
    count = min(finish, capacity - 1)
    return count, tail[:count] + b"\0"


class TokenOriginal(Original):
    def __init__(self, image):
        super().__init__(image)
        self.uc.mem_map(DELIMITERS, 0x90000)

    def run(self, source, index, delimiters, output_before, capacity, mode, alias_offset=0):
        uc = self.uc
        objects = bytearray(b"\xCC" * 0x200)
        struct.pack_into("<QQ", objects, 0, BASE + 0x301C1C0, INPUT)
        destination = KEY + 16
        if mode == "source":
            destination = INPUT + index
        elif mode == "empty":
            destination = BASE + EMPTY_RELATIVE
        elif mode == "delimiter":
            destination = DELIMITERS + 16 + alias_offset
        struct.pack_into("<QQi", objects, 0x40, BASE + 0x301D7A0, destination, capacity)
        struct.pack_into("<QiIQQ", objects, 0x100, OBJECTS, index, 0x89ABCDEF,
                         BASE + 0x301C1C0, DELIMITERS + 16)
        uc.mem_write(OBJECTS, bytes(objects))
        uc.mem_write(INPUT, source)
        uc.mem_write(DELIMITERS, b"\xD7" * 16 + delimiters)
        uc.mem_write(KEY, output_before)
        preserved = self.preserved()
        uc.reg_write(reg.UC_ARM64_REG_X0, ITERATOR)
        uc.reg_write(reg.UC_ARM64_REG_X1, OBJECTS + 0x40)
        uc.emu_start(BASE + TOKEN_HELPER, STOP, count=100_000_000)
        if uc.reg_read(reg.UC_ARM64_REG_PC) != STOP:
            raise AssertionError("Token helper did not return")
        self.check_preserved(preserved)
        if bytes(uc.mem_read(OBJECTS, len(objects))) != objects:
            raise AssertionError("Token helper changed object headers or iterator position")
        return (uc.reg_read(reg.UC_ARM64_REG_W0), bytes(uc.mem_read(INPUT, len(source))),
                bytes(uc.mem_read(DELIMITERS + 16, len(delimiters))),
                bytes(uc.mem_read(KEY, len(output_before))),
                bytes(uc.mem_read(BASE + EMPTY_RELATIVE, 1)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--report", type=Path,
                        default=ROOT / "private/outputs/1.0.0/safe-string-token/validation.json")
    args = parser.parse_args()
    if not args.report.resolve().is_relative_to(ROOT / "private"):
        raise ValueError("Original binary hashes and detailed reports must remain private")
    image = Image("1.0.0")
    for segment, (_, data) in zip(image.manifest["segments"], image.segments):
        if hashlib.sha256(data).hexdigest() != segment["sha256"]:
            raise ValueError("NSO segment provenance mismatch")
    if image.relative[0x32D0660] != 0x2A3E3F1 or image.read(0x2A3E3F1, 1) != b"\0":
        raise ValueError("Original terminator anchor differs")
    if image.relative[0x32D07A8] != 0x31A6150 or image.relative[0x31A6158] != EMPTY_RELATIVE:
        raise ValueError("Original empty SafeString anchor differs")
    if image.read(EMPTY_RELATIVE, 1) != b"\0":
        raise ValueError("Original fallback string is not empty")
    directory = os.add_dll_directory(str(ROOT / "private/tools/llvm-mingw/llvm-mingw-20261006-ucrt-x86_64/bin"))
    library = ct.CDLL(str(args.library.resolve()))
    native = library.acnh_safe_string_copy_token
    native.argtypes = [ct.c_void_p, ct.c_int32, ct.c_void_p, ct.c_void_p, ct.c_int32, ct.c_void_p]
    native.restype = ct.c_int32
    original = TokenOriginal(image)
    rng = random.Random(TOKEN_HELPER)
    totals = dict(normal=0, exact_source_alias=0, exact_empty_alias=0, delimiter_alias=0,
                  source_scan_boundary=0, delimiter_scan_boundary=0)

    def check(payload, alphabet, index, capacity, category="normal", mode="separate", alias_offset=0):
        source = payload + b"\0" + b"\xD3" * 128
        delimiter = alphabet + b"\0" + b"\xE5" * 128
        output_before = bytes(rng.getrandbits(8) for _ in range(192))
        source_native = ct.create_string_buffer(source, len(source))
        delimiter_native = ct.create_string_buffer(delimiter, len(delimiter))
        output_native = ct.create_string_buffer(output_before, len(output_before))
        empty_native = ct.create_string_buffer(b"\0\xA7")
        destination = ct.addressof(output_native) + 16
        if mode == "source":
            destination = ct.addressof(source_native) + index
        elif mode == "empty":
            destination = ct.addressof(empty_native)
        elif mode == "delimiter":
            destination = ct.addressof(delimiter_native) + alias_offset
        copied = native(ct.addressof(source_native), index, ct.addressof(delimiter_native),
                        destination, capacity, ct.addressof(empty_native))
        actual = original.run(source, index, delimiter, output_before, capacity, mode, alias_offset)
        expected_count, write = oracle(source, index, delimiter, capacity, mode in ("source", "empty"))
        expected_source = bytearray(source)
        expected_delimiter = bytearray(delimiter)
        expected_output = bytearray(output_before)
        if write is not None:
            target, start = (expected_delimiter, alias_offset) if mode == "delimiter" else (expected_output, 16)
            target[start:start + len(write)] = write
        expected = (expected_count, bytes(expected_source), bytes(expected_delimiter), bytes(expected_output), b"\0")
        native_actual = (copied, source_native.raw, delimiter_native.raw, output_native.raw, empty_native.raw[:1])
        if actual != expected or native_actual != expected:
            raise AssertionError(f"Token divergence: category={category}, case={sum(totals.values())}, "
                                 f"index={index}, capacity={capacity}, mode={mode}, "
                                 f"counts(original/native/oracle)={actual[0]}/{copied}/{expected_count}")
        totals[category] += 1

    samples = [(b"", b":"), (b"plain", b":"), (b"a:b:c", b":"), (b":::abc", b":"),
               (b"a;b:c", b":;"), (b"abcdef", b""), (b"abc", b"abc"),
               (bytes(range(1, 256)), bytes((255, 128, 64))), (b"A" * 257 + b":tail", b":"),
               (b"token end", b" "), (b"a:b", b"a"), (b"a:b", b"b")]
    samples += [(bytes(rng.randrange(1, 256) for _ in range(rng.randrange(96))),
                 bytes(rng.randrange(1, 256) for _ in range(rng.randrange(8)))) for _ in range(64)]
    for payload, alphabet in samples:
        indices = sorted({-0x80000000, -1, 0, len(payload) // 2, len(payload), len(payload) + 1, 0x7FFFFFFF})
        for index in indices:
            for capacity in (1, 2, 4, 17, 64):
                check(payload, alphabet, index, capacity)
            if 0 <= index <= len(payload):
                check(payload, alphabet, index, 17, "exact_source_alias", "source")
            else:
                check(payload, alphabet, index, 17, "exact_empty_alias", "empty")
        for offset in (0, 1, min(3, len(alphabet))):
            check(payload, alphabet, 0, 17, "delimiter_alias", "delimiter", offset)

    # The original's final triple reads offset 0x80000. An absent terminator returns length zero;
    # the token walk at index zero can still reach a later delimiter or NUL.
    for length in (SCAN_LAST - 1, SCAN_LAST, SCAN_LAST + 1):
        payload = b"L" * length
        for index in (0, 1, length):
            check(payload, b":", index, 17, "source_scan_boundary")
        check(payload + b":tail", b":", 0, 17, "source_scan_boundary")
    for delimiter_length in (SCAN_LAST - 1, SCAN_LAST, SCAN_LAST + 1):
        check(b"Bz", b"A" * delimiter_length, 0, 17, "delimiter_scan_boundary")
        check(b"Bz", b"A" * delimiter_length + b"B", 0, 17, "delimiter_scan_boundary")

    report = dict(version_id="1.0.0", module="main", relative_address=hex(TOKEN_HELPER),
                  original_bytes=TOKEN_HELPER_SIZE,
                  original_sha256=hashlib.sha256(image.read(TOKEN_HELPER, TOKEN_HELPER_SIZE)).hexdigest(),
                  cases=sum(totals.values()), categories=totals,
                  original_arm64_vs_native_vs_independent_oracle=True,
                  original_iterator_and_object_headers_preserved=True,
                  original_callee_saved_registers_and_stack_preserved=True,
                  all_buffer_bytes_and_canaries_checked=True,
                  isolated_memcpy_calls=original.memcpy_calls,
                  contract=dict(capacity_includes_nul=True, iterator_is_not_advanced=True,
                                invalid_index_selects_empty_string=True, exact_source_alias_returns_zero=True,
                                scan_last_offset=hex(SCAN_LAST), exhausted_length_scan_returns_zero=True,
                                token_walk_has_no_equivalent_scan_limit=True),
                  limitations=["SafeString callbacks execute the original no-op; arbitrary mutation is excluded.",
                               "Capacities must be positive; original invalid-capacity behavior is not made safe.",
                               "Only exact source alias is covered; partial overlap of memcpy ranges is excluded.",
                               "Original C++ class declarations and a guest ABI adapter are not recovered here.",
                               "No full game DLL integration, deployment or gameplay validation is claimed."])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(dict(cases=report["cases"], categories=totals, passed=True)))
    directory.close()


if __name__ == "__main__":
    main()
