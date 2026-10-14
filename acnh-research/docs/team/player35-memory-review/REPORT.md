# Independent memory/context review of player35

Reviewer: `memory_pin`, 2026-10-13. This review reads existing sources, binaries,
manifests, logs and producer reports. It runs no compiler, loader, DLL, ABI
corpus, CTest or game. It changes only this review directory and
`private/team/player35-memory-review/`.

**Final source/evidence verdict:** no supported-trace blocker was found for a
controlled startup experiment of the exact candidate pair below. The
coordinator confirmed the producer's source freeze/window release at
23:34:10Z. The default runtime was restored after all runtime/loader gates.
Default promotion and integrated coverage remain coordinator decisions after
real execution. This review establishes no gameplay or save/reload result.

## Bound artifacts and evidence

| Item | SHA-256 |
| --- | --- |
| Actual 35-entry candidate DLL | `5829252d9988715a4727ed015f216675b0b0b3ac06c8a639caac65afeb09cd9b` |
| Candidate runtime and packaged executable | `df489bdd58d0304bd0f924cd9a753ec67d52ca0e28a47562251b2fa695083658` |
| Private final wrapper manifest | `a72b4aa84de92d854e0e857cdb5417ecb50fac68c689e0482feadc9d07784983` |
| Default module, preserved | `2797747f4e69977388ff27cf9d04341b2b55a631a9c739f30351b7101a9a730d` |
| Restored default runtime | `dfe9256e44081bdeefa30c6b87e18442c0eade390cc919ff1d401be7c96c7f94` |
| Player loader main.c | `bd4b24e7e19f0377b72aacc598c9130bcffa2f02cf681b94003fe7353d0955f7` |
| Unchanged epoch memory source | `d5b5e4a736a159a958b3c212fe30ec190b4bbd8fcc44212e26432235b2e68710` |
| Player loader patch | `fb426fcd7ab7e816bd443fc0c2a0dc8938e5ae857ed2f8b75a4413a191515685` |
| Final player validator | `9a4fd0509ce02585edfe0b89f4c265f28f3070ed420763d113dd2d1940cb49ea` |
| Producer final source/evidence snapshot | `05d8258a85d0b7a77850fa6ef60a2aa65a84f5d2ef954fb38bbdc55d4b951004` |
| This review's final evidence snapshot | `40db6f8122f9ecf3805d88162029b817fc1bf105192ad0c586193d89fa6a1e07` |
| Fresh player API2 report | `a7caa95405c13879af4ed4621e736ccdf528134d9b50c10181865aa43942b4af` |
| Fresh player no-API report | `61bb9fc66783eb1523f40a472a0500ba7e0daa563653f8965e50214bc083826a` |
| Four-case real loader fixture report | `d589a28b581662d949141364c35883cf28293983190780f7b4f0bb9220d3e6d6` |
| Private 35-body measurement | `aece9af37b2236111688c32fe4dccb62375511da9ec33464aee8a3d45f54a796` |

The private reviewer snapshot records exact report/log hashes, commands,
before/after inputs, imported validation helpers, manifest/generated bindings,
the 376-object donor ledger, API lifecycle totals and public metadata hashes.
Final rehash confirmed 33 source files, 18 generated/provenance bindings,
13 newly compiled objects, 14 report files and 37 preserved public metadata
files. The final read took 1.2 seconds and ran no new gate under the
coordinator's startup lease. It retained this review's earlier direct rehash
of all 376 donor objects/sources, bound to the unchanged ledger; that large
read was not repeated during the timing lease.

Historical standalone player21 and epoch14 module successes are preparation
evidence. They do not substitute for fresh tests on the DLL in this table.

## API, lock and lifecycle audit

The real memory lock is a Windows PMutex using **AcquireSRWLockExclusive**.
This is not a shared read lock. It is nonreentrant, with per-thread ownership
tracking. GPU mapping transactions acquire `vk_lock` before this memory lock.
The closed host-mutation route remains the previously reviewed epoch source:
init/reserve/commit/decommit/heap/kernel-memory/rollback host operations advance
the global epoch under the memory lock before attempting the operation. Failed
attempts conservatively invalidate. Guest metadata-only permissions/state do
not fabricate host access. Reprotection tests use the actual wrapper's
GPU-begin, memory-lock, epoch-bump, VirtualProtect, unlock, GPU-end transaction.

The loader creates one API2 table and one stable runtime domain outside the
generic SaveIO branch, allowing player-only modules. It invokes generic SaveIO
and player setters once each, with the same begin/end/user/domain identities.
Player owns a distinct copied API table and hook configuration; it does not
reinstall generic SaveIO. Refusal stops loading before guest execution. The
legacy v1 optional negotiation remains after the v2 setters.

Loading/negotiation occurs **before mem_init**. The runtime ready flag rejects
early begin atomically before accessing an uninitialized lock or g_mem; init
completes locked reservation/commit work before publishing readiness. The stale
include comment claiming install after mem_init remains a documented comment
erratum, not a premise of this review.

Each player invocation owns 576 bytes of state on its native stack. API2 is
40 bytes and an address/thread-owned lease is 32 bytes. The hook ABI is 32 bytes
and each native/original policy is 40 bytes. Begin configures policies without
guest effects; every configured path finishes, including failed begin or an
invalid selected policy. Selected-invalid fallback finishes before entering
the original interpreter. The production epoch finish terminates on an
unreleased lease invariant rather than returning to the scheduler with a lock.

Native and original execute hooks release **before snx_lookup** or interpreter
entry, call the dependency without a lease, and reacquire before a source
suffix. Normal dependency dispatch may reach other reconstructed entries.
Whole-original rejection and owned-body interiors suppress the per-CPU dispatch
view for the interpreter call and restore it afterward. Applied prefixes keep
their actual CPU.pc and do not replay the whole entry. Nested factory state is
distinct stack storage, never a copied active lease or singleton active TLS
context.

Only inert positive region descriptors survive in native TLS. Reuse requires
a fresh valid lease, nonzero epoch and equal epoch/base/reservation span/domain/
begin/end/user identities. A NULL or foreign CPU base invalidates/refuses the
leased path. Version/size/domain validation rejects unusable API tables. A
malformed lease cannot publish a positive cache. Epoch exhaustion is sticky
zero and retains checked leased queries without descriptor reuse. These
invariants do not make live install/reset APIs safe: loader-only installation
and validation-only reset with no live threads remain explicit contracts.

## Fresh candidate proof and its limits

The final player validator binds the actual 35-entry DLL, final private
manifest, six generated player TUs, source hashes and imported helpers. Two
separate processes each compare **246 player ABI cases: 186 terminal returns
and 60 prescribed prefixes**. Each includes 101 original-fallback rows and 57
containing-wrapper interior-parameter invocations, already within the 246,
not additional bodies. Original dependency native instructions execute; they
are not replaced with player dependency models. Observed native boundaries
are checked as an ordered subsequence of the original trace because generated
internal static calls bypass per-CPU observers. The report's substituted full
trace must not be described as fully observed trace equality.

The API process installs generic SaveIO once outside player mode loops. Clearing
player hooks makes only player uncached while SaveIO remains installed. The
separate no-API process installs neither setter and gives factory contexts no
API. Direct kernel primitives/exhaustion intentionally still use the real
fixture API in that process; they are separate kernel proofs, not cached
module-provider cases.

For each process, the player proof records 686 observed dependency boundaries,
60 callback mutation cases, 213 factory finishes and a two-deep nested test
with three distinct storage addresses. API2 factory finishes have 495 balanced
acquires/releases, 112 queries and 432 retained windows. No-API factories have
zero leases, 1,151 queries and no retained windows. The 126 NULL-memory/runtime
observer handoffs are explicitly outside defined original memory execution
and outside the 246 ordinary comparison rows. Callback NULL/base changes,
real decommit/ABA and real reprotection preserve prescribed post-effect
continuations; fixture restoration after module return is disclosed.

The actual mem.c fixture is bound to unchanged production memory source and
real reserve/commit/decommit/protect calls. GPU/platform/log/fatal plumbing is
fixture scope, and low ABI addresses are setup-only commits under the real
lock/epoch. No production low-address mapping restriction is removed. Sticky
zero exhaustion and concurrent real unmap blocked by a lease remain kernel
primitives. Provider owner/end failure terminal behavior is supported by the
frozen epoch fault corpus and unchanged source, not newly rerun fault tests on
this final game DLL.

SaveIO is rerun on this DLL in separate API2/no-API processes: **150 native + 15
guard sentinels + 5 interior sentinels + 6 defined original fallback cases**
per process. API2 records 272 unleased callback boundaries and seven real
protection changes/restores; unknown version, short table, missing domain and
reinstallation are rejected. SaveIO still uses its declared original import
models. Npad retains declared SDK dependency models and fallback sentinels.
The core/context/flag/AccessKey/Npad gates bind this same DLL and private
manifest with their existing scope restrictions.

The actual candidate runtime passed all 13 CTests. Four fresh synthetic loader
variants cover missing-player, all-accept, player-refuse and player-only.
Events record one call per setter, runtime-owned callbacks/domain, identical
v2 table identities when both setters exist and pre-init refusal without
consuming lease storage. All children ended naturally with exit 1 at the
expected ABI0 or refused-loader boundary; none ran mem_init or guest gameplay.
Thus loader negotiation is proved, while a successful game-memory lease in a
live Vulkan title still requires the coordinator's runtime experiment.

The initial player validator import failure is retained separately and not
counted as a passing gate. Later bound reruns include imported helper hashes
before/after. Earlier successes before that binding are archived historical
records rather than the final corpus proof.

## Build, preservation and coverage

Player mode is opt-in and isolates generated sources, manifest, build cache,
reports and output. Diagnostic SaveIO and player modes cannot be combined.
All wrapper mutations precede final generated hashes and compiled provenance.
The shared code_125 TU and SaveIO provenance are recompiled after player edits.
The build log shows six changed generated TUs, five player sources and two
provenance TUs compiled, then a link with **376** individually hash-bound donor
objects. The excluded donor is the old SaveIO provenance object. Original
source, candidate source and object hashes all match the donor ledger; build
flags/toolchain remain the pinned O1/native research configuration. This is
an incremental cached build, not a clean whole-game rebuild or cross-machine
reproducibility proof.

The player layer reverses in memory to the exact LF-normalized audited epoch
main.c; current mem.c matches the frozen epoch preimage. This keeps the
historical epoch patch/proof intact instead of transferring its reverse-check
to a changed loader hunk. The preserved default module and every snapshotted
public 1.0.0 metadata file match their starting hashes. A fresh generator-OFF
gate, using a private copy only, produced the identical 14-entry manifest and
identical bytes for all 363 generated source files. The default runtime was
restored at **23:31:53.5654856Z**, after the runtime/loader gates. The CTest
before/after hashes both identify df489bdd; the later current build-path hash
identifies DFE because of that documented restoration. This expected transition
does not invalidate the retained candidate runtime.

The private candidate inventory is **35 distinct bodies / 4,696 original
bytes**: existing 14 / 2,212 plus bank 4 / 728 and resolution 17 / 1,756.
Original intervals do not overlap. The denominator remains 44,815,680 ExeFS
text bytes. Infrastructure, partial regions, guarded entries, duplicated ABI
rows, kernel fixtures and automatic translation contribute **zero** new bytes.
Public coverage remains 14 / 2,212 until the coordinator confirms integration;
this review never writes coverage or publishes a candidate as integrated.

No startup, tutorial/gameplay, real Vulkan contention, audio/input session or
save/reload result follows from these gates. Trusted one-time API installation,
synchronous CPU/stack ownership and closed wrapped host mutations remain
requirements; object lifetime and guest-data synchronization are separate.
The full native Windows reconstruction goal remains unchanged and incomplete.
Elysium and proprietary assets, data, keys and firmware remain excluded.
