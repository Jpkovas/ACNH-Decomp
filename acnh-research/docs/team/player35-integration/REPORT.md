# Player35 integrated candidate

Task `player35-integration`, thread `01a13760-cf3c-7953-b7c6-f1d5a26365a6`,
2026-10-13, Windows x64 / PowerShell. Coordinator:
`01a13734-dae4-73f2-87e4-e4a88be7d1da`.

The separate candidate selects the existing fourteen complete bodies plus four
player banks and seventeen resolution-tree bodies. Fresh group, player,
loader and runtime gates pass against its exact artifacts. The private byte
proxy verifies 35 nonoverlapping original-body intervals / 4,696 bytes. Public
coverage remains 14 / 2,212 bytes, with zero increment from this delivery until
coordinator acceptance. No game process, default promotion, commit or push was
performed by this thread. Gameplay/tutorial and real save/reload remain required.

## Frozen candidate and preservation

Paths are relative to `D:/ACNH_Decomp/acnh-research`.

| Artifact | SHA256 |
| --- | --- |
| `private/windows/bridge-player35-candidate/ACNH_1_0_0_code.dll` | `5829252d9988715a4727ed015f216675b0b0b3ac06c8a639caac65afeb09cd9b` |
| `private/windows/runtime-player35-candidate/scarletnx.exe` | `df489bdd58d0304bd0f924cd9a753ec67d52ca0e28a47562251b2fa695083658` |
| `private/windows/bridge-player35-candidate/ACNH_1_0_0.exe` | same player35 runtime hash |
| Private candidate manifest | `a72b4aa84de92d854e0e857cdb5417ecb50fac68c689e0482feadc9d07784983` |
| Preserved default code DLL | `2797747f4e69977388ff27cf9d04341b2b55a631a9c739f30351b7101a9a730d` |
| Restored default runtime | `dfe9256e44081bdeefa30c6b87e18442c0eade390cc919ff1d401be7c96c7f94` |
| Preserved epoch14 code DLL | `98de63ffcac31d91cdb94d2f147d70741fa320359d195cd7a0ad5bd4e804ff02` |
| Preserved epoch14 runtime | `6455fa93bf1378e1edec2334d1bfa52d139d4e7545560f224bcbf8b077e820cd` |

Runtime CTest and loader execution bound `df489bdd...` before/after, while that
candidate remained at the shared runtime build path. DFE was restored after
all thirteen CTests and four loader cases completed, at
`2026-10-13T23:31:53.5654856Z`. The packaged game EXE was explicitly replaced
with the saved player35 runtime after the parallel module/runtime builds; its
hash matches that runtime. Select the saved runtime explicitly for reproduction.

Eight accepted public14 manifest/proof/coverage files remain byte-identical.
The source snapshots preserve their historical validator versions as well as
the uncommitted pre-integration sources. Shared generated14 files and donor
objects were not rewritten. The default-OFF generator test in a private clone
produced the exact accepted14 manifest and identical bytes for all 363 generated
source files. CLI path additions do not retrospectively relabel the frozen14
reports as proofs from the newly edited validators.

The starting snapshot is `private/team/player35-integration/starting-snapshot.json`,
SHA256 `6f094740907003d0be444fd4d24e022abc7262c5feebbac82497b6f432507e71`.
The final snapshot is `private/team/player35-integration/final-snapshot.json`,
SHA256 `05d8258a85d0b7a77850fa6ef60a2aa65a84f5d2ef954fb38bbdc55d4b951004`.
It binds 33 source inputs, eighteen generated bindings, thirteen newly compiled
objects, 376 reused objects, fifteen main gate records/logs, the runtime fixture
inputs, loader proof, candidate manifest and preserved artifacts/public14 files.
The shared build window is released; no heavy work remains in this front.

## Implementation and shared-file inventory

Starting project HEAD was `72da3e52ed78b344bff74c991a418df4c649f53d`; vendor
HEAD remains `ac54f1124ad02381a9c2d98bde6c5a4f44bae6da`. No reset, clean,
staging or unrelated edit was performed. Owned edits:

- `vendor/ScarletNX/runtime/core/main.c`: optional player epoch setter only.
- `windows_bridge/CMakeLists.txt`: `ACNH_PLAYER_CONNECTED`, conditional player
  sources and optional hash-verified external object selection.
- `scripts/build_windows_game.ps1`, `build_windows_bridge.ps1`,
  `replace_bridge_routines.py`, `report_decompilation_byte_coverage.py`.
- Existing core/context/flag/AccessKey/Npad/SaveIO validators: explicit private
  manifest/generated/report controls; Npad/SaveIO public-report suppression.
- New `scripts/prepare_player35_cache.py`, `verify_player35_runtime_patch.py`,
  `validate_player35_module.py`, `report_player35_candidate_coverage.py` and
  `patches/scarletnx-player-connected-epoch.patch`.

The bank/tree/context/epoch helper sources, semantic adapters, CPU header and
production `mem.c` are frozen and unchanged. The new loader patch SHA256 is
`fb426fcd7ab7e816bd443fc0c2a0dc8938e5ae857ed2f8b75a4413a191515685`.
It creates one immutable API2 table/domain outside the generic-setter condition,
then independently negotiates generic SaveIO and optional player factories once
each. V1 negotiation remains afterward. Missing exports are compatible; each
setter refusal aborts before guest startup. The player-only export receives a
valid API even without a generic setter. The generic setter is never reinstalled
to configure player policy.

Relocating the table changes the old epoch reverse-patch context. The builder
recognizes the exact new layer, reverses it only in memory, and requires exact
LF-normalized audited epoch14 `main.c`/`mem.c` preimage hashes. It neither
modifies the historical epoch patch nor silently replaces its hunks with text
presence checks. A fresh base applies/checks the older stack before this layer.

`-PlayerConnected` selects a separate output, generated source tree, manifest
and CMake build directory. OFF retains14. Player plus diagnostic SaveIoProfile
is explicitly rejected. The generator calls the frozen player replacement
helper **before** SaveIO replacement, rehashes all records after shared-file
mutations, then emits final player provenance. `code_125.c` contains both groups;
its final hash is compiled into both provenances. Context/index/Npad/guarded
provenances remain bound to their final unchanged units.

The player worker's earlier full-module DLL `91d3cabe...` and 246-case proof are
historical supporting evidence, not transferred to this DLL. It reused 377
donor objects and deliberately carried older non-player provenance. This final
build excludes the old SaveIO provenance object, reuses 376 exact donor objects,
and compiles six changed TUs, five player C/C++ sources and two provenance TUs.
All thirteen new objects are hashed. Donor source/object hashes are checked
before and after build and at final freeze. The baseline cache remains intact.

Optional cached-object selection is a private incremental research mode. CMake
without `ACNH_BASELINE_REUSE_CMAKE` compiles all private generated sources. A
clean whole-module build was not performed here. Inherited `-march=native` and
`-mtune=native` also prevent a cross-machine byte-identity claim. This is still
a hybrid translated/reconstructed module; lifted code does not count as
reconstructed source.

## Fresh gates and model boundaries

| Gate | Result and scope |
| --- | --- |
| Core | 1088 hash, 4 zero, 272 FullKey; actual module dispatch; initializer callback remains a model |
| Context | 11571 original ARM64/native comparisons across four leaves |
| Flag index/default | 3930 / 6319 primary cases plus actual fallback/interior selection; default is guarded |
| AccessKey | 193 native / 9 original fallback / 4 guard decisions; guarded and excluded from complete-body bytes |
| Npad | 401: 218 complete / 56 escapes / 37 rejects / 90 interiors; six dependencies remain models |
| SaveIO API and no API | Same 176-case corpus in separate processes: 150 native / 15 guard sentinels / 5 interior sentinels / 6 defined original fallbacks |
| Player API and no module API | Same 246-case corpus in separate processes: 186 terminal / 60 prefixes; all ordinary expected PCs explicitly asserted |
| Runtime | 13/13 CTests; exact runtime/affected sources/test executables before and after |
| Loader | 4/4 own missing/accept/reject/player-only scenarios; expected natural error exits before guest execution |
| OFF and patch stack | Exact14 private regeneration; in-memory reverse/hash verification passed |
| Private byte proxy | All four NSO .text hashes and35 nonoverlapping bodies reverified; 4696 /44815680 bytes |

Player's 57 containing-interior invocations are subsets of246. Its 126 NULL
mem/rt interpreter observers are separate selection/handoff assertions; they
never execute undefined original guest memory effects. The imported worker
case logic, 101 defined original fallback paths and external dependency trace
subsequences retain their original scope. Prefixes remain authoritative at
CPU.pc, with no replay or hidden cleanup. Native external traces cannot observe
original-generated internal static calls; ordered subsequences are claimed.
No 648/215 isolated-source corpus is labeled an actual-module corpus.

Both fresh player processes observed213 factory begin/finish pairs with
balanced acquisitions/releases and no held lease on finish. Nested invocations
retain distinct caller-owned storage and restore dispatch/code bounds. In the
API process, generic SaveIO is installed once, reinstallation is refused, and
player uses the same actual production-memory fixture API. Its player-baseline
mode clears only player hooks; generic SaveIO remains epoch-enabled. In the
separate no-module-API process, neither context installs an API, and custom
factory init also receives NULL. Kernel-only lease/ABA/protection/exhaustion
primitives still use the real API explicitly and remain separate from the
module-provider cases.

The production-memory fixture DLL is `f0506b1d7aa6794a28565ccc90c80c52b4838d0d9340091cb9b9aa0490db49a4`.
It includes unchanged actual `mem.c`, real Windows SRW/VM operations and the
reviewed epoch include/header. Five compiled fixture inputs and its immutable
build report are hash-bound. GPU mapping-boundary callbacks, platform plumbing,
logging/fatal and low-address setup pages are explicit fixture scope. Fourteen
imported Python helper sources are bound before/after the fresh player gates.
Fixture concurrency is not a real Vulkan/title contention proof.

SaveIO still distinguishes unmodified original RET/RET0 instructions, modeled
caller imports, populated fixture dispatch callbacks and rejection sentinels.
API2 observes272 released callback boundaries and seven locked epoch protection
mutations/restorations each, plus version/size/domain/reinstallation refusal.
Escapes22 and post-effect handoffs5 are subsets of150, not extra cases.

The loader fixtures check one call per present setter, shared API2
begin/end/user/domain, distinct correct V1 ABI callbacks, refusal before V1 and
safe pre-init begin/end refusal. Their descriptor ABI is deliberately invalid;
natural exit1 is expected-error termination, not a game result. See
[loader/REPORT.md](loader/REPORT.md). Independent final source/evidence review
is in [review/REVIEW.md](review/REVIEW.md).

## Reproduction, failures and acceptance

Use the existing llvm-mingw 20261006/UCRT Clang23.1.3, VS CMake/Ninja and bundled
Python. Exact executable hashes/commands/cache selection are retained in the
starting/final snapshots and gate records. Paths and commands are local only.

```powershell
& scripts/build_windows_bridge.ps1 -PatchCheckOnly
# Cached runtime build; preserve candidate before restoring the default.
& 'C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe' --build build/windows-bridge/vulkan --parallel 4
& scripts/build_windows_game.ps1 -PlayerConnected -Jobs 4 -OutputDirectory 'D:/ACNH_Decomp/acnh-research/private/windows/bridge-player35-candidate' -RuntimePath 'D:/ACNH_Decomp/acnh-research/private/windows/runtime-player35-candidate/scarletnx.exe'
& 'private/tools/python/python.exe' -B scripts/report_decompilation_byte_coverage.py --player-connected --module private/windows/bridge-player35-candidate/ACNH_1_0_0_code.dll --manifest private/windows/bridge-player35-candidate/reconstructed-replacements.json --generated-directory private/windows/bridge-player35-candidate/ACNH_1_0_0_build --validation-directory private/team/player35-integration/reports --report private/team/player35-integration/reports/coverage-private.json
```

Runtime tests use normal NTFS system TEMP/TMP and driver access; exFAT workspace
hard-link semantics do not support those filesystem fixtures. Audio/VP9 inputs
are unchanged cached native dependencies. No NativeAOT restore was rerun.

An initial player harness invocation failed at import with ModuleNotFoundError,
before any corpus/DLL execution. Its original `player-api.json` gate record/log
remain untouched. Adding the explicit scripts import path fixed packaging;
no source/artifact/provenance assertion was weakened. Successful pre-binding
reports were preserved separately, then both processes reran after adding
before/after imported-helper bindings. The loader worker retained an initial
compiler warning failure/source/log and its conditional snapshot correction.
An early shell-embedded builder edit failed at PowerShell parsing and performed
no edit; the transformation was moved to a saved Python file. This parser
diagnostic remains in the task transcript. All final fifteen main gates passed.

Candidate scope is35 /4696, about0.0104784754% of44815680 original .text bytes.
The proposed addition is21 /2484, split bank4 /728 and tree17 /1756. Guards,
partial region, provider repeats, models, original dependencies outside35,
observers, primitives and automatically lifted code remain excluded. Public
metadata is not advanced by this private candidate report. Coordinator review
and real startup comparison must precede any promotion or publication.

Private inventories include source/proof snapshots, all new/reused object
hashes, raw CTest definition JSON, fixture bindings, failed/successful records,
candidate sources/artifacts/reports and restoration/release records. Copyleft
source notices and SwitchRecomp/MZ Labs Apache notices remain intact. Dumps,
keys, firmware, assets, generated/lifted code and binaries remain private;
public delivery contains aggregates, paths and hashes only. Elysium and3.0.3
analysis are unchanged.

Untested: real player35 startup/Vulkan contention, lazy allocation modes,
original object types/lifetime and guest permissions, clean full-source or
cross-machine reproduction, tutorial/gameplay/input/audio progression and
actual save/reload in another process. The native Windows reconstruction goal
remains unchanged and incomplete.
