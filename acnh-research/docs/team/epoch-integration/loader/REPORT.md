# Epoch v2 loader gate

Task `/root/epoch_loader_gate`, 2026-10-13. Status: isolated-tested; independent
review required. All three own synthetic module cases passed against the real
candidate runtime. Coverage increment is zero. Gameplay and save/reload were
not tested.

The loader installs the optional mapping epoch table before `mem_init` and
before checking `SnxModule.abi`. Each fixture returns a non-null descriptor with
ABI zero, deliberately different from `SNX_ABI == 3`. Accepted and legacy
fixtures therefore stop at the ABI error before guest-memory/guest-filesystem
initialization, services, renderer or guest startup. The rejected setter stops earlier at the loader
error. No title module, dump, asset, firmware, key or game executable was used.

## Results

| Own fixture | Expected terminal result | Observed result |
| --- | --- | --- |
| Legacy, only `snx_module` export | ABI mismatch after absence of optional setter | Exit 1, expected ABI fatal, 0.031 s, PID 25144 |
| Setter accepts valid v2 | Negotiate, then ABI mismatch | Exit 1, expected ABI fatal, 0.031 s, PID 33728 |
| Setter deliberately refuses valid v2 | Extension refusal, then loader failure | Exit 1, refusal warning and expected loader fatal, 0.031 s, PID 33128 |

These are expected-error terminal exits, not successful game exits. Every
process exited on its own, with no timeout or forced termination. Timeout was
five seconds per fixture. `--headless=1` is parsed by `snx_startup_options`
before `load_code`; `win_fatal_box` returns immediately in that mode. The
harness requires the expected stderr sequence, explicit exit code and observed
process termination. A timeout would fail the gate and be recorded as forced
termination of only the exact own child PID.

Both setter fixtures observed version 2, table size 40, lease size 32, null user,
non-null domain and callable begin/end pointers. `GetModuleHandleExW` confirmed
begin, end and domain addresses belong to the main runtime executable. The
fixture passed a non-null own byte address to the real begin callback and a
lease prefilled with `0xa5`; begin returned zero and left the lease unchanged.
The actual source ordering binds this observation to the pre-`mem_init` call.
The callback also rejects a wrong base after initialization, so its return value
alone would not prove the ready flag's state without that ordering evidence.

The real end callback refused the unacquired lease and a null lease. The
unacquired lease remained byte-for-byte unchanged. This proves a callable end
pointer and safe refusal, not a successful lease acquisition or release.
The accepting setter returned one; the rejecting setter returned zero only
after checking the same received table. PE export logs confirm that legacy has
only `snx_module`, while accepting/rejecting fixtures export both module and
epoch setter. No v1 setter is exported by any fixture.

## Binding and reproduction

Working directory: `D:/ACNH_Decomp/acnh-research`, PowerShell, Windows x64.
Starting project HEAD: `a31cfa8e0521323aed1b82f5eca5c4d86d77e357`.
Vendor HEAD: `ac54f1124ad02381a9c2d98bde6c5a4f44bae6da`. Existing uncommitted
sources were read without reset, checkout, staging or editing. The supplied
runtime was not copied, restored or changed by this worker.

Runtime tested: `build/windows-bridge/vulkan/scarletnx.exe`.
SHA256 before and after all cases:
`6455fa93bf1378e1edec2334d1bfa52d139d4e7545560f224bcbf8b077e820cd`.
The coordinator may later restore that build path to the default binary;
reproduction must select the saved epoch runtime with this exact hash.

```powershell
& 'private/tools/python/python.exe' 'private/team/epoch-loader-gate/gate.py' --prepare
& 'private/tools/python/python.exe' 'private/team/epoch-loader-gate/gate.py' --runtime 'build/windows-bridge/vulkan/scarletnx.exe' --runtime-sha256 6455fa93bf1378e1edec2334d1bfa52d139d4e7545560f224bcbf8b077e820cd --timeout 5
```

`gate.py --prepare` records every compiler/PE-inspection argv, exit status,
source hash, compiler executable hash, DLL hash and log hash in
`private/team/epoch-loader-gate/build.json`. Clang version was 23.1.3, Win64
GNU target, from the existing llvm-mingw 20261006 UCRT toolchain. Each DLL was
compiled with `-std=c11 -O1 -Wall -Wextra -Werror -shared` and the corresponding
`FIXTURE_MODE`. Runtime execution argv, PID, exit code, duration, stderr events
and all stdout/stderr/runtime-log hashes are in `validation.json`.

Build report SHA256:
`0727867b2c0b846d41d9c097137b045db1ac712a5089c31d5da514d201300343`.
Validation report SHA256:
`3007957bc7c968b91e03a5a9c7b4c6d4e31b708a19e6badfd36e2286b513b693`.

| Fixture artifact | SHA256 |
| --- | --- |
| `legacy_code.dll` | `554fac5675b2863c496cff333976289ce8f0bd5f2f85d9c035fcd8c69f1decea` |
| `accept_code.dll` | `acce1f465df51cfc0cdfc8cc02a9ef82e0fa80cc6774313db5adbf146a76f38e` |
| `reject_code.dll` | `16772617347fbebc4b3a11e949921840a6c0b15c48d1b37eb52a186791bca702` |

The complete initial/final source hashes are in both private reports and
`delivery.json`. Of particular relevance, `main.c` was
`70115814f028f94a538df6019132c4517cc2e0da4c796398a43909e43fb4f530`, `mem.c`
was `d5b5e4a736a159a958b3c212fe30ec190b4bbd8fcc44212e26432235b2e68710`, and
the epoch runtime include was
`6e32d164fa902e3f232f0941cde90386bb864fce2896146bace9f5d981152e9d`.
All bound sources were stable through preparation and execution.

## Inventory, provenance and limits

Only `private/team/epoch-loader-gate/` and this report/delivery directory were
written. Private inventory: `fixture.c`, `gate.py`, three DLLs, three compiler
logs, three PE export/import logs, three stdout logs, three stderr logs, three
runtime logs, `build.json`, `validation.json`, `inventory.json`, and copies of
`LICENSE`, `LICENSE.apache`, `NOTICE` under `licenses/`. Public inventory:
this report and `delivery.json`. No shared source or runtime was edited.

The own fixture mirrors the epoch ABI independently, with static Win64 size
checks; it does not contain the provider/cache implementation. It includes the
published ScarletNX `abi/cpu.h` to use the actual module descriptor. Runtime
loader and callbacks execute as built; the fixture module, setter decision,
non-null base and lease bytes are synthetic. There are no original game
callees, modeled guest systems, guest registers/PC, original-body fallbacks or
reconstructed entries in this gate. The three fixtures are loader scenarios,
not distinct original ABI-body cases or new coverage.

Own fixture/scripts are GPL-3.0-or-later. Included open source ABI retains
SwitchRecomp by MZ Labs credit, underlying Apache-2.0 notice and ScarletNX fork
GPL-3.0-or-later terms. License/NOTICE copies are retained privately beside the
fixtures. No game copyright material was copied.

No compilation or runtime case failed; all logs are retained. This gate does
not test a valid game module, the production module's install implementation,
successful initialized-memory leases, epoch mutation/invalidation, concurrency,
cache behavior, Windows input/audio/save, Vulkan initialization or affected
game scenes. The build's relationship to all runtime compilation inputs must
also remain bound by the coordinator's build/CTest evidence; this worker binds
the tested binary and the relevant readable source files, without independently
rebuilding the runtime.

Integration: retain the reports and own fixture artifacts; bind this proof to
the same epoch runtime hash used in module and CTest gates; obtain independent
review; keep real startup, tutorial/gameplay and real save/reload as separate
mandatory tests. Shared ownership conflicts: none. Timing lease was inactive
before the small fixture compilation and before each execution. There is no
default-promotion authorization or success claim from these results.
