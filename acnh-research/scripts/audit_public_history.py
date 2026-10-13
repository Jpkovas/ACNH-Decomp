"""Check every local Git blob for binary/private material before publication."""
from __future__ import annotations
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
GIT = ['git', '-c', 'safe.directory='+WORKSPACE.as_posix(), '-C', str(WORKSPACE)]


def run(*args, input=None):
    return subprocess.run([*GIT, *args], input=input, capture_output=True, check=True).stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, default=ROOT/'metadata/public-history-verification.json')
    args = parser.parse_args()
    destination = args.report.resolve()
    destination.relative_to(ROOT)
    objects = [row.split() for row in run('cat-file', '--batch-all-objects',
               '--batch-check=%(objectname) %(objecttype) %(objectsize)').decode().splitlines()]
    blobs = [row for row in objects if row[1] == 'blob']
    content = run('cat-file', '--batch', input=(''.join(row[0]+'\n' for row in blobs)).encode())
    paths = {}
    for row in run('rev-list', '--objects', '--all', '--reflog').decode().splitlines():
        sha, _, name = row.partition(' ')
        if name:
            paths.setdefault(sha, []).append(name)
    errors = []
    cursor = 0
    private_roots = ('gamedump/', 'acnh-research/private/', 'acnh-research/vendor/', 'acnh-research/build/')
    suffixes = {'.keys', '.nsp', '.nca', '.xci', '.tik', '.cert', '.dll', '.exe', '.bin',
                '.bfevfl', '.bcsv', '.msbt', '.bfres', '.bntx', '.pbc', '.gpr', '.rdc', '.ppm', '.wav'}
    secrets = re.compile(rb'(?im)^\s*(?:header_key|master_key_[0-9a-f]{2}|titlekek_[0-9a-f]{2})\s*=\s*(?:0x)?[0-9a-f]{32,}\s*$')
    for sha, _, expected_size in blobs:
        end = content.index(b'\n', cursor)
        header = content[cursor:end].decode().split()
        size = int(header[2])
        if header[0] != sha or size != int(expected_size):
            raise ValueError('Unexpected Git batch object')
        raw = content[end+1:end+1+size]
        cursor = end+size+2
        reasons = []
        if b'\0' in raw:
            reasons.append('binary NUL bytes')
        if secrets.search(raw):
            reasons.append('secret assignment')
        if size > 2*1024*1024:
            reasons.append('large object needs review')
        for path in paths.get(sha, []):
            if path.startswith(private_roots) or Path(path).suffix.lower() in suffixes:
                reasons.append('private/binary historical path: '+path)
        if reasons:
            errors.append(dict(object=sha, paths=paths.get(sha, []), reasons=reasons))
    report = dict(passed=not errors, git_objects_checked=len(objects), historical_blobs_checked=len(blobs),
        commits_checked=sum(row[1] == 'commit' for row in objects), errors=errors,
        audited_head=run('rev-parse', 'HEAD').decode().strip(),
        scope='All local Git objects including unreachable blobs; path/binary/secret checks plus separate source/license review. No legal conclusion.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps(report))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
