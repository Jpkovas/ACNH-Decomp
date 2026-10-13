"""Verify every NSO and record version-specific module/import contracts.

Raw symbol lists and decompressed bytes stay in private/. Public results contain
hashes, counts and unresolved interface names only, never generated guest code.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from inspect_nso import inspect

ROOT = Path(__file__).resolve().parents[1]
ORDER = ['rtld', 'main', *('subsdk'+str(i) for i in range(9)), 'sdk']


class Module:
    def __init__(self, path: Path, version: str):
        self.path = path
        self.output = ROOT/'private/windows/modules'/version/path.name
        self.manifest = inspect(path, self.output/'segments')
        self.manifest.update(module=path.name, version_id=version)
        self.segments = [(s['memory_offset'], (self.output/'segments'/(s['name'][1:]+'.bin')).read_bytes())
                         for s in self.manifest['segments']]
        self.tags: dict[int, int] = {}
        self.dynamic_entries: list[tuple[int, int]] = []
        mod = self.u32(4)
        if self.read(mod, 4) != b'MOD0':
            raise ValueError(f'{path.name}: MOD0 signature missing')
        self.mod0 = mod
        self.dynamic = mod + struct.unpack('<i', self.read(mod+4, 4))[0]
        for i in range(4096):
            tag, value = struct.unpack('<QQ', self.read(self.dynamic+i*16, 16))
            if tag == 0:
                break
            self.dynamic_entries.append((tag, value))
            self.tags[tag] = value
        else:
            raise ValueError('Unterminated dynamic table')
        self.symbols: list[dict] = []
        if 6 in self.tags:
            if self.tags.get(11, 24) != 24:
                raise ValueError('Symbol enumeration requires ELF64 entry size')
            if 4 in self.tags:
                bucket_count, count = struct.unpack('<II', self.read(self.tags[4], 8))
                if count > 200000 or bucket_count > 200000:
                    raise ValueError('Implausible SysV hash dimensions')
                self.read(self.tags[4], 8+4*(bucket_count+count))
                self.symbol_count_basis = 'DT_HASH nchain'
            elif 0x6ffffef5 in self.tags:
                gnu = self.tags[0x6ffffef5]
                buckets, symoffset, bloom_size, _ = struct.unpack('<IIII', self.read(gnu, 16))
                if buckets > 200000 or bloom_size > 200000:
                    raise ValueError('Implausible GNU hash dimensions')
                bucket_at = gnu+16+bloom_size*8
                self.read(gnu, 16+bloom_size*8+buckets*4)
                maximum = max(struct.unpack('<'+'I'*buckets, self.read(bucket_at, buckets*4)), default=0)
                count = symoffset
                if maximum:
                    if maximum < symoffset or maximum > 200000:
                        raise ValueError('Invalid GNU hash bucket')
                    chain_at = bucket_at+buckets*4+(maximum-symoffset)*4
                    while maximum < 200000:
                        word = self.u32(chain_at)
                        maximum += 1
                        chain_at += 4
                        if word & 1:
                            count = maximum
                            break
                    else:
                        raise ValueError('Unterminated GNU hash chain')
                self.symbol_count_basis = 'DT_GNU_HASH terminal chain'
            else:
                raise ValueError('No hash table for exact symbol enumeration')
            strings = self.read(self.tags[5], self.tags[10])
            for i in range(count):
                name, info, other, section, value, size = struct.unpack('<IBBHQQ', self.read(self.tags[6]+i*24, 24))
                end = strings.find(b'\0', name)
                if name >= len(strings) or end < 0:
                    raise ValueError('Invalid ELF string offset')
                self.symbols.append(dict(name=strings[name:end].decode('utf-8'), binding=info>>4,
                                         type=info & 15, visibility=other & 3, section=section, value=value, size=size))
            self.needed = [self.cstring(self.tags[5]+value) for tag, value in self.dynamic_entries if tag == 1]
        else:
            self.needed = []
        self.relocations = []
        for pointer_tag, size_tag, kind in [(7, 8, 'rela'), (23, 2, 'plt')]:
            if pointer_tag not in self.tags:
                continue
            length = self.tags[size_tag]
            if length % 24 or (kind == 'rela' and self.tags.get(9) != 24):
                raise ValueError('Invalid RELA table dimensions')
            if kind == 'plt' and self.tags.get(20) != 7:
                raise ValueError('PLT relocations are not RELA')
            for offset, info, addend in struct.iter_unpack('<QQq', self.read(self.tags[pointer_tag], length)):
                symbol = info >> 32
                if symbol >= len(self.symbols):
                    raise ValueError('Relocation symbol index out of bounds')
                self.relocations.append(dict(offset=offset, type=info & 0xffffffff,
                                             symbol_index=symbol, addend=addend, table=kind))
        self.relr_count = 0
        if 36 in self.tags:
            if self.tags.get(37) != 8 or self.tags[35] % 8:
                raise ValueError('Invalid RELR dimensions')
            cursor = None
            for (entry,) in struct.iter_unpack('<Q', self.read(self.tags[36], self.tags[35])):
                if entry & 1:
                    if cursor is None:
                        raise ValueError('RELR bitmap without address')
                    self.relr_count += (entry >> 1).bit_count()
                    cursor += 63*8
                else:
                    if entry % 8:
                        raise ValueError('Unaligned RELR target')
                    self.relr_count += 1
                    cursor = entry+8
        init_size = self.tags.get(27, 0)
        if init_size % 8 or (init_size and 25 not in self.tags):
            raise ValueError('Invalid INIT_ARRAY dimensions')
        if init_size:
            self.read(self.tags[25], init_size)
        self.init_count = init_size//8

    def read(self, address: int, size: int) -> bytes:
        for start, data in self.segments:
            if start <= address and size >= 0 and address+size <= start+len(data):
                return data[address-start:address-start+size]
        raise ValueError(f'{self.path.name}: range outside initialized segments: {address:#x}+{size:#x}')

    def u32(self, address: int) -> int:
        return struct.unpack('<I', self.read(address, 4))[0]

    def cstring(self, address: int) -> str:
        for start, data in self.segments:
            if start <= address < start+len(data):
                at = address-start
                end = data.find(b'\0', at, min(at+16384, len(data)))
                if end < 0:
                    raise ValueError('Unterminated string')
                return data[at:end].decode('utf-8')
        raise ValueError('String outside segments')

    def imports(self):
        return [s for s in self.symbols if s['name'] and s['section'] == 0 and s['binding'] in (1, 2)]

    def exports(self):
        return [s for s in self.symbols if s['name'] and s['section'] != 0
                and s['binding'] in (1, 2) and s['visibility'] in (0, 3)]

    def summary(self):
        return dict(module=self.path.name, input_sha256=self.manifest['input_sha256'],
                    module_id=self.manifest['module_id'], segments=self.manifest['segments'],
                    bss_size=self.manifest['bss_size'], mod0=hex(self.mod0), dynamic=hex(self.dynamic),
                    symbols=len(self.symbols), symbol_count_basis=getattr(self, 'symbol_count_basis', None),
                    imports=len(self.imports()), exports=len(self.exports()),
                    needed=self.needed, relocations_by_type=dict(collections.Counter(str(r['type']) for r in self.relocations)),
                    relr_relocations=self.relr_count, initializer_slots=self.init_count,
                    init_offset=hex(self.tags[12]) if 12 in self.tags else None,
                    addresses_relative_to_module=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version-id', required=True)
    parser.add_argument('--exefs', type=Path, required=True)
    args = parser.parse_args()
    modules = [Module(args.exefs/name, args.version_id) for name in ORDER if (args.exefs/name).is_file()]
    if not any(m.path.name == 'main' for m in modules):
        raise ValueError('ExeFS lacks main')
    definitions = collections.defaultdict(list)
    for module in modules:
        for symbol in module.exports():
            definitions[symbol['name']].append(dict(module=module.path.name, **symbol))
    edges = []
    unresolved = []
    for module in modules:
        for symbol in module.imports():
            candidates = [s for s in definitions[symbol['name']] if s['module'] != module.path.name]
            row = dict(importer=module.path.name, symbol=symbol['name'], weak=symbol['binding'] == 2,
                       providers=[s['module'] for s in candidates])
            edges.append(row)
            if not candidates:
                unresolved.append(row)
        payload = dict(manifest=module.manifest, dynamic_entries=module.dynamic_entries,
                       symbols=module.symbols, relocations=module.relocations)
        (module.output/'metadata.json').write_text(json.dumps(payload, indent=2)+'\n', encoding='utf-8')
    output = ROOT/'private/windows/modules'/args.version_id
    (output/'import-graph.json').write_text(json.dumps(edges, indent=2)+'\n', encoding='utf-8')
    npdm = args.exefs/'main.npdm'
    summary = dict(version_id=args.version_id, module_order=[m.path.name for m in modules],
                   npdm_sha256=hashlib.sha256(npdm.read_bytes()).hexdigest() if npdm.exists() else None,
                   modules=[m.summary() for m in modules], import_edges=len(edges),
                   resolved_import_edges=len(edges)-len(unresolved), unresolved_imports=unresolved,
                   note='Export candidates are static; runtime symbol precedence has not been validated')
    target = ROOT/'metadata/windows'/args.version_id/'exefs-profile.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(version_id=args.version_id, modules=len(modules), imports=len(edges),
                          unresolved=len(unresolved), unresolved_strong=sum(not s['weak'] for s in unresolved),
                          module_summaries=[{k: m.summary()[k] for k in ('module', 'symbols', 'imports', 'exports', 'initializer_slots')} for m in modules])))


if __name__ == '__main__':
    main()
