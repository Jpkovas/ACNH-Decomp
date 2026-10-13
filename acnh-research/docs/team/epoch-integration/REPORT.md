# Mapping epoch v2 integrated candidate

Task: `epoch-integration`, delegated thread
`01a13760-cf3c-7953-b7c6-f1d5a26365a6`, 2026-10-13, Windows x64 / PowerShell.
The existing fourteen entries are preserved. The separate candidate DLL and
runtime pass the fresh module gates, thirteen CTests and three own loader
scenarios. Independent evidence review is in [review/REVIEW.md](review/REVIEW.md).
This delivery adds **zero reconstructed bytes** and does not establish startup
recovery, gameplay/tutorial, real save/reload or completion of decompilation.

## Candidate and preserved defaults

All artifact paths are relative to `D:/ACNH_Decomp/acnh-research`.

| Artifact | SHA256 | Bytes |
| --- | --- | ---: |
| `private/windows/bridge-epoch-candidate/ACNH_1_0_0_code.dll` | `98de63ffcac31d91cdb94d2f147d70741fa320359d195cd7a0ad5bd4e804ff02` | 292592640 |
| `private/windows/runtime-epoch-candidate/scarletnx.exe` | `6455fa93bf1378e1edec2334d1bfa52d139d4e7545560f224bcbf8b077e820cd` | 26260992 |
| `private/windows/bridge-epoch-candidate/ACNH_1_0_0.exe` | same epoch runtime hash | 26260992 |
| Preserved `private/windows/bridge/ACNH_1_0_0_code.dll` | `2797747f4e69977388ff27cf9d04341b2b55a631a9c739f30351b7101a9a730d` | 292586496 |
| Restored `build/windows-bridge/vulkan/scarletnx.exe` | `dfe9256e44081bdeefa30c6b87e18442c0eade390cc919ff1d401be7c96c7f94` | 26258944 |

The runtime build path contained `6455fa93...` throughout CTest and loader
execution. Its exact hash was checked before and after those gates. The default
was restored only after both completed, at `2026-10-13T22:45:53.7685435Z`.
The DLL default was never replaced. The final packaging rerun reported no work
to compile and preserved the tested DLL and manifest hashes. Do not reproduce
this candidate using the restored default runtime implicitly.

`private/team/epoch-integration/default-restoration.json`,
`final-snapshot.json`, `window-release.json` and the gate logs preserve this
sequence. The final snapshot SHA256 is
`a4054090c3f2b57d05e9b7d615b6c68b19b37acb88271fa0567b6ea75374d470`.
The shared build window is released. All workers in this integration front are
quiescent during the coordinator's subsequent real startup timing lease.

## Change and contract

The startup regression investigation measured expensive guest `VirtualQuery`
calls. Reusing positive range descriptors without retaining a mapping lease
across the access would permit a stale mapping/permission race. Epoch v2 makes
descriptor reuse conditional on reacquiring the real runtime mapping lock and
matching epoch, runtime domain, reservation base/span and callback identities.
Descriptors retained between entries are inert. Callbacks, original fallback,
dependency lookup and dispatch run after release; native suffixes reacquire.

All reserve/commit/decommit attempts in `mem.c`, including failed attempts and
rollback, invalidate the global epoch before the host operation under the
existing lock. The protection wrapper uses the same lock and invalidation.
Exhaustion makes epoch zero sticky and disables reuse. Lease ownership is native
thread/address bound; invalid end/scope states terminate instead of handing off.
This is a supported synchronous entry contract, not a general object lifetime
or guest permission guarantee. No new memory-lock-to-Vulkan-lock edge was found.

The optional API is version 2, 40 bytes; lease is 32 bytes. CPU size 896,
memory offset 848 and `SNX_ABI=3` stay unchanged. The loader actually installs
the optional table **before `mem_init`**. Installation copies the table without
acquiring the uninitialized lock, and begin refuses before the atomic ready
flag is published. Frozen candidate comments describing installation after
initialization are imprecise; this report records the implemented ordering.
Old modules have no setter; old runtimes leave v2 modules uncached. V1 loader
negotiation remains present. Static modules skip dynamic negotiation and remain
uncached. No live API replacement is supported.

## Inventory and provenance

Starting project HEAD was `a31cfa8e0521323aed1b82f5eca5c4d86d77e357` and vendor
HEAD `ac54f1124ad02381a9c2d98bde6c5a4f44bae6da`. Existing uncommitted work was
preserved. There was no reset, clean, staging, commit, push or real game launch
by this thread.

Shared source changes are the audited patch in `runtime/kernel/mem.c` and
`runtime/core/main.c`; `windows_bridge/save_io_access_module.c` and
`windows_bridge/CMakeLists.txt`; `scripts/replace_bridge_routines.py`,
`build_windows_bridge.ps1`, `build_windows_game.ps1`,
`validate_bridge_save_io_access.py`, and
`report_decompilation_byte_coverage.py`. The new patch is
`patches/scarletnx-windows-range-epoch.patch`, SHA256
`a313c8223584bbd25b7b463feb3ccc865b1fc4b933fcc160d1c2ce3f7558912f`.
The two runtime postimages were independently reconstructed from the saved
baseline plus that patch in memory, ignoring only CRLF/LF differences.

The four existing frozen `windows_range_epoch_candidate*` sources were inputs,
not edited here. CMake's normal SaveIO context now selects them. The generator
hashes those sources into the existing five-body SaveIO provenance; semantic
body revision remains `save-io-abi-candidate-v1`. The manifest still selects
fourteen complete entries, one partial region and two guarded entries, and its
SHA256 is `8dae1c62417722dffb65ff559edcefca6ac8011bdb2601d477859fc6166bf8c6`.
Player21 sources and unrelated fronts were not integrated or edited.

The runtime builder checks the layered v1/v2 patches. V2's adjacent loader
insertion changes old v1 reverse-patch context; when exact v2 reverse checking
passes, every contiguous additive v1 block must still exist. The checker rejects
v1 removals rather than silently applying this method to a non-additive patch.
The game builder accepts explicit `-RuntimePath` for reproducible packaging of
the saved candidate. Coverage follows the actual private report paths for Npad
and SaveIO, validates they remain inside `private`, and preserves earlier proof
files instead of overwriting them.

Fresh metadata: `metadata/windows/1.0.0/reconstructed-replacements.json`,
`replacements-validation.json`, `event-context-bridge-validation.json`,
`flag-table-bridge-validation.json`, `access-key-bridge-validation.json`,
`npad-initialization-module-validation.json`,
`save-io-access-module-validation.json`, `decompilation-byte-coverage.json`.
The access-key prior report was outside the original saved source baseline;
its fresh hash is recorded without manufacturing a before hash.

Private inventory includes the starting source copies/hashes, preserved default
runtime, gate runner, collector, source/toolchain/generated hashes, twelve gate
records and logs, failed invocation record/log, CTest definition JSON, restoration
record, immutable report copies and release record below
`private/team/epoch-integration/`. Review and loader workers write only their own
private directories and `docs/team/epoch-integration/{review,loader}/`.
Complete paths and SHA256 are in `delivery.json` and `final-snapshot.json`.

The inherited SwitchRecomp/MZ Labs Apache-2.0 notices and ScarletNX
GPL-3.0-or-later fork terms remain intact. Candidate source follows the project
license. Dumps, assets, original instructions, generated/lifted code and all
executables/fixture outputs remain private. Public delivery contains aggregate
counts, paths and hashes only. Elysium stays excluded; 3.0.3 analysis is untouched.

## Fresh gates and their actual scope

| Gate | Passed corpus | Interpretation |
| --- | --- | --- |
| Core entries | hash 1088, zero 4, FullKey 272 | Actual DLL entry dispatch; FullKey initializer remains a declared callback |
| Event context | 11571 | Four actual leaf entries compared with unmodified original ARM64 |
| Flag index | 3930 primary; 3933 actual dispatch | One complete entry; extra fallback/interior checks do not add bodies |
| Flag default | 6319 primary; 6322 actual dispatch | Existing guarded entry, excluded from complete-body coverage |
| AccessKey | 193 native, 9 original fallbacks, 4 guard decisions | Existing guarded entry; real original SafeString callbacks, native memcpy model |
| Npad initialization | 401: 218 complete, 56 escapes, 37 rejected, 90 interiors | Actual module; six original dependencies remain models; pending-callee subset is not added twice |
| SaveIO, no API | 150 native + 15 sentinels + 5 interior sentinels + 6 defined original fallbacks | Separate uncached provider process |
| SaveIO, epoch API2 | Same 176 selection/body cases | Same case corpus repeated with real mem.c fixture lock/epoch; not 176 new cases |
| Runtime CTest | 13/13 | Runtime/tools/filesystem/headless Vulkan own fixtures; no title scene |
| Real loader, own modules | 3/3 | Legacy/accept/reject; deliberate ABI/loader error exits before guest execution |

SaveIO checks all GPR/NZCV/PC, full mapped fixtures/frames/canaries, dependency
callback order, extra CPU state, guards, prefix effects and no entry replay.
The 22 escapes and five post-effect handoffs are subsets of the 150 native
cases. The actual production module refused unknown v1, short API, missing
domain and reinstallation. With API2, 272 callback boundaries observed the real
lock released. Seven late protection mutations and seven restorations used the
real locked epoch wrapper and advanced its epoch. The fixture DLL is
`12ee06ad733ff0c451bb496df53e267b0c80384e760ba330129daad55596482a`;
its build report and compiled `mem_epoch_test.c` copy are bound by SHA256.

SaveIO helper RET/RET0 paths execute unmodified original callback instructions.
Caller imports and one helper mutation variant are explicit models. Populated
dispatch entries are fixture callbacks, not recovered dependency bodies.
Rejection/interior sentinels prove selection and absence of effects; six defined
fallback fixtures separately execute original bodies. They do not reconstruct
the original service backend or establish guest data synchronization.

The earlier frozen isolated concurrency report (83 real SRW/host mapping
transactions, ABA/protection/wrap/fail-stop cases) is historical supporting
evidence. Its validator hash predates this thread's API2 adaptation. It is not
relabeled as a new execution of the current validator. Fresh actual-module
reports use validator SHA256
`fd3d10a6e38b4260562181ed91d5c321c1d9975bb476c4ccc1cf4e54a115e64f`.

CTest proof binds the runtime, all test executables, affected source/patch and
cache hashes before/after, commands and log hash. All remain identical.
`private/team/epoch-integration/ctest-definition.json` is raw stdout from
`ctest --test-dir build/windows-bridge/vulkan --show-only=json-v1`, not a hash
of `CTestTestfile.cmake`. Its thirteen commands and 125 current test/runtime
source hashes were captured after tests; this post-test source inventory is
explicitly separate from the before/after executable/affected-source proof.

The loader's expected-error exits are normal terminal exits, not game success.
Actual runtime pointers/domain and API sizes were verified; pre-init begin and
unacquired end refused without mutation. Begin also refuses a wrong base after
initialization, so the pre-init conclusion relies on source ordering plus the
tested runtime hash, not only a zero return. The loader gate does not acquire an
initialized lease. See [loader/REPORT.md](loader/REPORT.md) for exact argv, PIDs,
logs, fixture DLL hashes and timing.

## Reproduction and retained failures

Working directory is `D:/ACNH_Decomp/acnh-research`. Pinned llvm-mingw
20261006/UCRT Clang 23.1.3, existing VS CMake/Ninja and bundled Python are used;
executable SHA256 and CMake cache hash are in the snapshot. This was an
incremental build against the preserved local private generated sources. A
clean build or byte-identical reproduction across machines was not performed;
the inherited `-march=native`/`-mtune=native` flags also bind code generation to
host CPU capabilities.

```powershell
& scripts/build_windows_bridge.ps1 -PatchCheckOnly
& 'C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe' --build build/windows-bridge/vulkan --parallel 4
# Save the epoch runtime separately before later restoring the default.
& scripts/build_windows_game.ps1 -Jobs 4 -OutputDirectory 'D:/ACNH_Decomp/acnh-research/private/windows/bridge-epoch-candidate' -RuntimePath 'D:/ACNH_Decomp/acnh-research/private/windows/runtime-epoch-candidate/scarletnx.exe'
```

The runtime configuration was reused rather than rerunning NativeAOT dependency
restore; unchanged native audio/VP9 dependencies remain existing private inputs.
Thirteen CTests ran with the llvm bin on PATH, normal NTFS system TEMP/TMP and
normal driver access. exFAT workspace hard-link limitations make workspace TEMP
unsuitable for the existing filesystem fixtures. Exact argv for all twelve
main gates and their input hashes are retained in `delivery.json` and individual
`private/team/epoch-integration/*.json`. Loader commands are in its report.

An initial layered reverse-check did not match v1 context after v2 insertion;
the source was not reset. An initial PowerShell chunk-loop construction used a
nested array and failed; it was corrected to the flattened additive-block
verification and the patch check then passed. Those early diagnostics remain in
the task transcript; dedicated log files were not captured for them. A later
child PowerShell invocation failed before execution because of its default
execution policy. Its failed JSON/log are retained as
`patch-check-policy-failure.*`; an explicitly process-local `-ExecutionPolicy
Bypass` invocation passed without changing machine policy. All final corpus,
build, coverage and runtime test gates passed. Optional documentation/schema
inspection commands that returned missing-path/key errors were corrected and
are not counted as validation gates.

## Coverage and next integration

The four private NSOs and all nonoverlapping body intervals were independently
rehash/decompression verified in memory. Coverage remains **14 entries / 2,212
of 44,815,680 .text bytes = 0.004935772479632129%**. One partial region, two
guarded entries, imported dependencies, infrastructure, automatic lifting and
all isolated candidates are excluded. Public metadata now binds this candidate
DLL; it does not prove that the preserved default DLL contains epoch v2.

The coordinator can select `bridge-epoch-candidate` and the explicit saved
`runtime-epoch-candidate/scarletnx.exe` for its controlled startup comparison.
The coordinator owns the timing lease, game launch and terminal/visual/audio
evidence. No default promotion follows from this delivery. The source files
shared with generator/CMake/runtime are exclusive to this integration; player
groups need a separate coordinated candidate, regenerated provenance and fresh
gates. Arbitrary host mutations outside wrapped guest mapping routes, live API
replacement, nonlocal scope recovery, object/data lifetime, Vulkan contention,
original backends, real tutorial/input/audio and save/reload remain unproved.
The full native Windows reconstruction objective is unchanged and incomplete.
