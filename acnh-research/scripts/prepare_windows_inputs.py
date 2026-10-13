"""Prepare a private single-file RomFS using the supplied, sanitized keyset."""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_inputs import ROOT, compatible_keyset, environment, run


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(8*1024*1024), b''):
            result.update(chunk)
    return result.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version-id', default='1.0.0', choices=['1.0.0'])
    parser.add_argument('--keys', type=Path, required=True)
    args = parser.parse_args()
    inventory = json.loads((ROOT/'metadata/package_inventory.json').read_text())
    entry = next(item for item in inventory if item['package'] == 'base' and item['content_type'] == 'Program')
    nca = ROOT/'private/inputs/packages/base'/entry['nca']
    target = ROOT/'private/windows/bridge/ACNH_1_0_0_data/romfs.bin'
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix('.bin.partial')
    if not target.exists():
        keys = compatible_keyset(args.keys.resolve())
        env = environment(ROOT/'private/inputs/packages')
        run(ROOT/'private/tools/hactool/hactool.exe', keys, env, nca,
            ['-x', '--romfs', str(partial)], ROOT/'private/windows/romfs-container-extraction.log')
    candidate = target if target.exists() else partial
    size = candidate.stat().st_size
    with candidate.open('rb') as source:
        header = source.read(0x50)
    if len(header) != 0x50:
        raise ValueError('Incomplete RomFS header')
    words = struct.unpack('<10Q', header)
    if words[0] != 0x50 or words[9] > size:
        raise ValueError('Expected a plain RomFS with a 0x50-byte header')
    for offset, length in zip(words[1:9:2], words[2:9:2]):
        if offset > size or length > size-offset:
            raise ValueError('RomFS metadata extent exceeds the file')
    checksum = digest(candidate)
    if candidate == partial:
        partial.replace(target)
    report = dict(version_id=args.version_id, source_nca=entry['nca'],
                  tool='hactool 1.4.0', romfs_size=size, romfs_sha256=checksum,
                  metadata_extents_in_bounds=True,
                  note='Header and extents verified; runtime content reads still require validation')
    output = ROOT/'metadata/windows'/args.version_id/'romfs-container.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
