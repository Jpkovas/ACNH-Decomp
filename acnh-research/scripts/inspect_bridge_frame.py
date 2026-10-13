"""Convert an unmodified RGB PPM capture to PNG and measure visible content."""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    with args.input.open('rb') as stream:
        if stream.readline().strip() != b'P6':
            raise ValueError('Expected binary RGB PPM')
        width, height = map(int, stream.readline().split())
        if not (0 < width <= 7680 and 0 < height <= 4320):
            raise ValueError('Capture dimensions out of bounds')
        if stream.readline().strip() != b'255':
            raise ValueError('Expected 8-bit channels')
        rgb = stream.read(width*height*3+1)
    if len(rgb) != width*height*3:
        raise ValueError('RGB payload length does not match dimensions')
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack('>I', len(data))+kind+data+struct.pack('>I', zlib.crc32(kind+data))
    raw = b''.join(b'\0'+rgb[y*width*3:(y+1)*width*3] for y in range(height))
    png = b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw))+chunk(b'IEND', b'')
    args.input.with_suffix('.png').write_bytes(png)
    black = sum(rgb[i:i+3] == b'\0\0\0' for i in range(0, len(rgb), 3))
    report = dict(width=width, height=height, rgb_sha256=hashlib.sha256(rgb).hexdigest(),
                  nonblack_pixels=width*height-black, completely_black=black == width*height,
                  note='Nonblack pixels do not by themselves establish correct rendering or gameplay')
    args.input.with_suffix('.frame.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
