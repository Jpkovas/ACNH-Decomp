"""Extract a requested system RomFS from the user's local firmware ZIP.

Keys and decrypted inputs stay private; command output is sanitized by the
existing input preparation helper. No firmware download or key acquisition.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import struct
import sys
import zipfile
from pathlib import Path
from Crypto.Cipher import AES

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_inputs import compatible_keyset, run

def header_sector(raw: bytes, key: bytes, sector: int, endian: str) -> bytes:
    data_cipher = AES.new(key[:16], AES.MODE_ECB)
    tweak_cipher = AES.new(key[16:], AES.MODE_ECB)
    tweak = int.from_bytes(tweak_cipher.encrypt(sector.to_bytes(16, endian)), 'little')
    output = bytearray()
    for at in range(0, len(raw), 16):
        block = (int.from_bytes(raw[at:at+16], 'little') ^ tweak).to_bytes(16, 'little')
        output += (int.from_bytes(data_cipher.decrypt(block), 'little') ^ tweak).to_bytes(16, 'little')
        carry = tweak >> 127
        tweak = ((tweak << 1) & ((1 << 128)-1)) ^ (0x87 if carry else 0)
    return bytes(output)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--keys', type=Path, required=True)
    parser.add_argument('--firmware', type=Path, required=True)
    parser.add_argument('--title-id', required=True)
    args = parser.parse_args()
    title_id = int(args.title_id, 16)
    if not 0x0100000000000800 <= title_id <= 0x01000000000008FF:
        raise ValueError('Only explicitly selected system data archives are supported')
    keys = compatible_keyset(args.keys)
    key = next(bytes.fromhex(line.split('=', 1)[1].strip()) for line in keys.read_text().splitlines()
               if line.split('=', 1)[0].strip() == 'header_key')
    private = ROOT/'private/windows/system-archives'/f'{title_id:016x}'
    private.mkdir(parents=True, exist_ok=True)
    matches = []
    checked = 0
    with zipfile.ZipFile(args.firmware) as archive:
        for item in archive.infolist():
            if not item.filename.lower().endswith('.nca'):
                continue
            with archive.open(item) as stream:
                raw = stream.read(0x400)
            if len(raw) < 0x400:
                raise ValueError('Truncated firmware NCA header')
            header = None
            for endian in ('big', 'little'):
                trial = header_sector(raw[0x200:0x400], key, 1, endian)
                if trial[:4] in (b'NCA2', b'NCA3'):
                    header = trial
                    break
            if header is None:
                raise ValueError('Provided keyset cannot read a firmware NCA header')
            checked += 1
            if struct.unpack_from('<Q', header, 0x10)[0] == title_id and header[5] in (4, 5):
                matches.append(item)
        if len(matches) != 1:
            raise ValueError(f'Expected one requested data NCA; found {len(matches)}')
        item = matches[0]
        nca = private/'archive.nca'
        with archive.open(item) as source, nca.open('wb') as destination:
            while block := source.read(1024*1024):
                destination.write(block)
    target = ROOT/'private/windows/bridge/ACNH_1_0_0_data/system/archives'/f'{title_id:016x}.romfs'
    target.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env['XDG_CONFIG_HOME'] = str(ROOT/'private/key-config')
    run(ROOT/'private/tools/hactoolmodern/hactool.exe', keys, env, nca,
        ['--romfs='+str(target)], private/'extraction.log')
    header = struct.unpack('<10Q', target.read_bytes()[:0x50])
    size = target.stat().st_size
    if header[0] != 0x50 or header[9] > size:
        raise ValueError('Extracted system RomFS header is invalid')
    for at in (1, 3, 5, 7):
        if header[at] + header[at+1] > size:
            raise ValueError('System RomFS metadata extent is invalid')
    report = dict(title_id=f'{title_id:016x}', firmware_zip_sha256=hashlib.file_digest(args.firmware.open('rb'), 'sha256').hexdigest(),
        headers_verified=checked, nca_sha256=hashlib.file_digest(nca.open('rb'), 'sha256').hexdigest(),
        romfs_sha256=hashlib.file_digest(target.open('rb'), 'sha256').hexdigest(), romfs_size=size,
        tool='hactool 1.5.4', proprietary_archive_private=True, whole_game_decompiled=False)
    (ROOT/'metadata/windows/1.0.0'/f'system-archive-{title_id:016x}.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))

if __name__ == '__main__':
    main()
