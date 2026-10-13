"""Inspect the private, bounded first-suspect FIFO snapshot without executing it."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

HEADER = struct.Struct("<22I4Q")
MAX_WORDS = 16_384
STAGES = ("enqueue", "before_writeback", "after_writeback", "first_suspect")


def parser_state(values):
    return dict(mode=values[0], subchannel=values[1], method=hex(values[2]),
                batch_words=values[3], consumed_words=values[4])


def scan_headers(words, initial):
    """Decode boundaries only. Calls to engines and GPU memory writes are excluded."""
    remaining = max(0, initial[3] - initial[4])
    offset = min(remaining, len(words))
    headers = 0
    while offset < len(words):
        word = words[offset]
        mode = word >> 29
        headers += 1
        if word and mode in (0, 2, 6, 7):
            return dict(offset=offset, word=hex(word), mode=mode, headers_seen=headers)
        offset += 1
        if mode in (1, 3, 5):
            offset += (word >> 16) & 0x1FFF
    return None


def compare(left, right):
    common = min(len(left), len(right))
    differences = [(i, left[i], right[i]) for i in range(common) if left[i] != right[i]]
    return dict(common_words=common, identical_lengths=len(left) == len(right),
                changed_words=len(differences),
                first_differences=[dict(offset=i, before=hex(a), after=hex(b))
                                   for i, a, b in differences[:16]])


def inspect(raw):
    if len(raw) < 8 + HEADER.size or raw[:8] != b"SNXFFUL1":
        raise ValueError("Unsupported or incomplete FIFO failure snapshot")
    head = HEADER.unpack_from(raw, 8)
    if head[0] != 1 or any(count > MAX_WORDS for count in head[9:13]):
        raise ValueError("Invalid FIFO failure header")
    expected = 8 + HEADER.size + sum(head[9:13]) * 4
    if len(raw) != expected:
        raise ValueError("Truncated FIFO failure arrays or unexpected trailing data")
    entry = head[22]
    if ((entry >> 42) & 0x1FFFFF) != head[3] or head[2] >= head[3]:
        raise ValueError("Failure index or entry size does not match its metadata")
    offset = 8 + HEADER.size
    arrays = []
    stages = {}
    initial = head[16:21]
    for index, name in enumerate(STAGES):
        count = head[9 + index]
        data = raw[offset:offset + count * 4]
        words = struct.unpack(f"<{count}I", data) if count else ()
        arrays.append(words)
        stages[name] = dict(captured_words=count, complete=count == head[3],
                            sha256=hashlib.sha256(data).hexdigest(),
                            first_suspect=scan_headers(words, initial))
        if index < 3:
            stages[name]["unreadable_pages"] = head[13 + index]
            stages[name]["cpu_start"] = hex(head[23 + index])
        offset += count * 4
    return dict(format="SNXFFUL1", channel=head[1], entry=hex(entry),
                gpu_start=hex(entry & 0xFFFFFFFFFC), total_words=head[3],
                observed_suspect=dict(offset=head[2], word=hex(head[21]), mode=head[21] >> 29),
                initial_parser=parser_state(initial), failure_parser=parser_state(head[4:9]),
                stages=stages,
                transitions={f"{STAGES[i]}_to_{STAGES[i + 1]}": compare(arrays[i], arrays[i + 1])
                             for i in range(3)},
                limitations="Guest writes can race each snapshot. Missing suffixes and unreadable pages are "
                            "explicit. Header scanning records boundaries only, not engine side effects.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    private_root = Path(__file__).resolve().parents[1] / "private"
    source = args.input.resolve()
    if not source.is_relative_to(private_root):
        raise ValueError("Game FIFO snapshots and their reports must remain under private/")
    report = inspect(source.read_bytes())
    destination = source.with_suffix(".json")
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(dict(report=str(destination), observed_suspect=report["observed_suspect"],
                          transitions=report["transitions"])))


if __name__ == "__main__":
    main()
