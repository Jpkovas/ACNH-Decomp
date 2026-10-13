"""Measure private PCM capture; repair only the RIFF lengths after abrupt process exit."""
from __future__ import annotations
import argparse
import array
import hashlib
import json
import math
import struct
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=Path)
    parser.add_argument('--finalize', action='store_true', help='Use only after the producer has exited')
    args = parser.parse_args()
    raw = args.input.read_bytes()
    if len(raw) < 44 or raw[:4] != b'RIFF' or raw[8:16] != b'WAVEfmt ' or raw[36:40] != b'data':
        raise ValueError('Expected a canonical PCM WAV capture')
    tag, channels, rate, byte_rate, alignment, bits = struct.unpack_from('<HHIIHH', raw, 20)
    if (tag, channels, rate, byte_rate, alignment, bits) != (1, 2, 48000, 192000, 4, 16):
        raise ValueError('Unexpected capture format')
    if (len(raw)-44) % alignment:
        raise ValueError('Incomplete PCM frame')
    advertised_size = struct.unpack_from('<I', raw, 40)[0]
    if args.finalize:
        with args.input.open('r+b') as stream:
            stream.seek(4); stream.write(struct.pack('<I', len(raw)-8))
            stream.seek(40); stream.write(struct.pack('<I', len(raw)-44))
        raw = args.input.read_bytes()
    pcm = array.array('h'); pcm.frombytes(raw[44:])
    metrics = []
    for channel in range(channels):
        values = pcm[channel::channels]
        metrics.append(dict(nonzero_samples=sum(x != 0 for x in values),
                            peak=max(map(abs, values), default=0),
                            rms=math.sqrt(sum(float(x)*x for x in values)/max(1, len(values))),
                            clipped_samples=sum(x in (-32768, 32767) for x in values)))
    report = dict(sample_rate=rate, channels=channels, bits=bits,
                  pcm_frames=len(pcm)//channels, duration_seconds=len(pcm)/channels/rate,
                  channel_metrics=metrics, sha256=hashlib.sha256(raw).hexdigest(),
                  riff_lengths_finalized=args.finalize, previous_advertised_data_bytes=advertised_size,
                  actual_data_bytes=len(raw)-44,
                  limitations='Signal measurements do not establish perceptual accuracy or complete game playability')
    args.input.with_suffix('.audio.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
