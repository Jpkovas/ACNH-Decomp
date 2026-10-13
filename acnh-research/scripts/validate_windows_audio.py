"""Exercise the exported native audio renderer with independently constructed PCM/ADPCM signals."""
from __future__ import annotations
import argparse
import ctypes as C
import hashlib
import json
import struct
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REV = 0x38564552
CHECK = C.CFUNCTYPE(C.c_int, C.c_void_p, C.c_uint64, C.c_uint64, C.c_int)
SUBMIT = C.CFUNCTYPE(None, C.c_void_p, C.POINTER(C.c_int16), C.c_int, C.c_uint32, C.c_uint32)
NOTIFY = C.CFUNCTYPE(None, C.c_void_p, C.c_int)


def run_case(library, sample_format, right_gain, muted=False, end_of_stream=True):
    memory_size = 0x100000
    memory = C.create_string_buffer(memory_size)
    config = C.create_string_buffer(struct.pack('<8I4B4I', 48000, 240, 2, 0, 1, 1, 0, 0,
                                               0, 0, 0, 0, 0, 0, 0, REV))
    work_size = (library.acnh_audio_work_size(config) + 4095) & ~4095
    assert 0 < work_size < memory_size, work_size
    # ADPCM with zero prediction coefficients gives exact signed nibble * 16 values.
    pattern = [(i % 16 - 8)*16 for i in range(1792)]
    if sample_format == 2:
        wave = struct.pack('<1792h', *pattern)
    else:
        encoded = bytearray()
        for start in range(0, len(pattern), 14):
            encoded.append(4)  # predictor 0, scale 2^4
            for at in range(start, start+14, 2):
                encoded.append(((pattern[at]//16 & 15) << 4) | (pattern[at+1]//16 & 15))
        wave = bytes(encoded)
    address = 0x20000
    C.memmove(C.addressof(memory)+address, wave, len(wave))
    behavior = struct.pack('<IIQ', REV, 0, 0)
    pools = bytearray(4*0x20)
    for i in range(4): struct.pack_into('<I', pools, i*0x20+16, 3)
    struct.pack_into('<QQI', pools, 0, address, 0x2000, 4)
    resource = bytearray(0x70)
    struct.pack_into('<Iff', resource, 0, 0, 0 if muted else 1, 0 if muted else right_gain)
    resource[0x64] = 1
    voice = bytearray(0x170)
    struct.pack_into('<I', voice, 4, 0x10000000)
    voice[8:12] = bytes([1, 1, 0, sample_format])
    struct.pack_into('<IIIIff', voice, 0xC, 48000, 128, 0, 1, 1, 1)
    struct.pack_into('<I', voice, 0x3C, 1)
    if sample_format == 6: struct.pack_into('<QQ', voice, 0x48, address+0x1000, 32)
    struct.pack_into('<II', voice, 0x58, 0, 0xffffffff)
    struct.pack_into('<QQII', voice, 0x60, address, len(wave), 0, len(pattern))
    voice[0x79] = int(end_of_stream)
    for slot in range(1, 4): voice[0x60+slot*0x38+0x1A] = 1  # unused slots are already acknowledged
    struct.pack_into('<H', voice, 0x15C, 2)  # skip pitch/SRC so the oracle is exact
    mix_header = struct.pack('<II24x', 0xCAFEBABE, 1)
    mix = bytearray(0x930)
    struct.pack_into('<fII', mix, 0, 1, 48000, 2)
    mix[0xC:0xE] = b'\1\1'
    struct.pack_into('<I', mix, 0x18, 0x20000000)
    struct.pack_into('<II', mix, 0x924, 0x7fffffff, 0xffffffff)
    sink = bytearray(0x140)
    sink[:2] = b'\1\1'
    struct.pack_into('<I', sink, 4, 0x30000000)
    sink[0x20:0x2C] = b'MainAudioOut'
    struct.pack_into('<I', sink, 0x120, 2)
    sink[0x124:0x126] = b'\0\1'
    performance = bytes(0x10)
    parts = [behavior, pools, resource, voice, mix_header, mix, sink, performance]
    total = 64 + sum(map(len, parts))
    header = struct.pack('<16I', REV, len(behavior), len(pools), len(voice), len(resource),
                         0, len(mix_header)+len(mix), len(sink), len(performance), 0, 0, 0, 0, 0, 0, total)
    incoming = C.create_string_buffer(header+b''.join(parts))
    outgoing = C.create_string_buffer(1024)
    data = []
    done = threading.Event()
    errors = []
    memory_checks = []
    notifications = []

    @CHECK
    def check(user, va, size, write):
        memory_checks.append((va, size, write))
        return int(va <= memory_size and size <= memory_size-va)

    @SUBMIT
    def submit(user, samples, count, rate, channels):
        if (count, rate, channels) != (480, 48000, 2): errors.append((count, rate, channels))
        data.extend(samples[:count])
        if len(data) >= 480*12: done.set()

    @NOTIFY
    def notify(user, signaled): notifications.append(signaled)

    handle = C.c_void_p()
    result = library.acnh_audio_create(config, memory, memory_size, check, submit, notify, None,
                                       0x40000, work_size, C.byref(handle))
    assert result == 0 and handle.value, hex(result)
    try:
        result = library.acnh_audio_update(handle, incoming, total, outgoing, len(outgoing), None, 0)
        assert result == 0, hex(result)
        assert library.acnh_audio_control(handle, 0, 0) == 0
        assert done.wait(3), f'DSP did not provide buffers: {len(data)}'
        assert library.acnh_audio_control(handle, 1, 0) == 0
        assert not errors, errors
        # A one-frame gain ramp is permitted. The second full block must match exactly.
        expected_left = ([0]*len(pattern) if muted else pattern)[240:480]
        expected_right = [int(x*right_gain) for x in expected_left]
        assert data[480:960:2] == expected_left, (sample_format, data[480:512:2], expected_left[:16])
        assert data[481:960:2] == expected_right, (sample_format, data[481:513:2], expected_right[:16])
        assert all(x == 0 for x in data[len(pattern)*2:]), 'Voice read beyond its end of stream'
        assert memory_checks, 'DSP did not validate guest memory'
        assert 0 in notifications and 1 in notifications
        # Query the real DSP status without submitting the wave buffer again.
        voice[8] = 0
        voice[0x7A] = 1
        parts[3] = voice
        query = C.create_string_buffer(header+b''.join(parts))
        assert library.acnh_audio_update(handle, query, total, outgoing, len(outgoing), None, 0) == 0
        pool_bytes = struct.unpack_from('<I', outgoing.raw, 8)[0]
        played, consumed = struct.unpack_from('<QI', outgoing.raw, 64+pool_bytes)
        assert (played, consumed) == (0 if end_of_stream else len(pattern), 1), (played, consumed)
        return dict(format='PCM16' if sample_format == 2 else 'GC-ADPCM', right_gain=right_gain,
                    muted=muted, end_of_stream=end_of_stream, exact_samples_verified=480, played_samples=played,
                    consumed_wave_buffers=consumed, memory_checks=len(memory_checks), passed=True)
    finally:
        library.acnh_audio_destroy(handle)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--library', type=Path, default=ROOT/'private/windows/audio/ACNH_audio.dll')
    args = parser.parse_args()
    library = C.CDLL(str(args.library.resolve()))
    library.acnh_audio_work_size.argtypes = [C.c_void_p]
    library.acnh_audio_work_size.restype = C.c_uint64
    library.acnh_audio_create.argtypes = [C.c_void_p, C.c_void_p, C.c_uint64, CHECK, SUBMIT, NOTIFY,
                                         C.c_void_p, C.c_uint64, C.c_uint64, C.POINTER(C.c_void_p)]
    library.acnh_audio_create.restype = C.c_int
    library.acnh_audio_update.argtypes = [C.c_void_p, C.c_void_p, C.c_int, C.c_void_p, C.c_int, C.c_void_p, C.c_int]
    library.acnh_audio_update.restype = C.c_int
    library.acnh_audio_control.argtypes = [C.c_void_p, C.c_int, C.c_uint]
    library.acnh_audio_control.restype = C.c_int
    library.acnh_audio_destroy.argtypes = [C.c_void_p]
    cases = [run_case(library, 2, 1, end_of_stream=False), run_case(library, 6, 1),
             run_case(library, 6, .25), run_case(library, 6, .25, True)]
    report = dict(passed=True, cases=cases, library_sha256=hashlib.sha256(args.library.read_bytes()).hexdigest(),
                  scope='Known PCM16 and zero-predictor ADPCM, channel gains, mute, bounds checks, end of stream and DSP statuses',
                  limitations='Not a hardware-reference comparison of all effects, resamplers or splitters')
    path = ROOT/'metadata/windows/1.0.0/native-audio-validation.json'
    path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__': main()
