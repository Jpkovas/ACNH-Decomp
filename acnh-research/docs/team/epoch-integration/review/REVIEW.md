# Independent review of mapping epoch v2 integration

Task: `epoch-integration-review`. Reviewer scope is read-only source and evidence
inspection. The coordinator owns compilation, generated-source selection and
actual module/runtime gates. Review date: 2026-10-13, BRT.

## Current decision

The applied runtime change matches the previously audited patch exactly after
normalizing CRLF/LF. No blocker was found in the supported synchronous
native-entry contract or the exact integrated-candidate evidence reviewed here.
The separate epoch candidate is ready for coordinator-controlled real startup
experiments. Default promotion, startup regression resolution, gameplay and
save/reload remain unproved by this review.

## Ownership and executed checks

The reviewer changed only this report and its own files below
`private/team/epoch-integration-review/`. No game, compiler, runtime or DLL was
launched. No shared source, default binary, report, Git index or publication was
changed by this task. Git HEAD observed:
`a31cfa8e0521323aed1b82f5eca5c4d86d77e357`.

`snapshot_review.py` independently hashes the frozen v2 sources and the fixture
inputs. It parses unified hunks, verifies every context/removal against the
coordinator's saved baseline and applies the patch only in memory. The applied
snapshot is `private/team/epoch-integration-review/applied-patch-read-only.json`.
All four frozen v2 source hashes, the nineteen fixture build inputs, the compiled
private mem-copy hash and the fixture DLL hash matched. The checked patch hash is
`a313c8223584bbd25b7b463feb3ccc865b1fc4b933fcc160d1c2ce3f7558912f`.
Observed applied files:

| File | SHA256 |
| --- | --- |
| runtime/kernel/mem.c | d5b5e4a736a159a958b3c212fe30ec190b4bbd8fcc44212e26432235b2e68710 |
| runtime/core/main.c | 70115814f028f94a538df6019132c4517cc2e0da4c796398a43909e43fb4f530 |
| runtime/abi/cpu.h | f59d908a0baa7e7b7a5a3e84ef104ea6a84beaaa5ce318c943ffc77f1d5523f1 |

The source walk found the closed runtime set of guest host-mutation sites in
mem.c. The applied file contains no direct `plat_vm_reserve`, `plat_vm_commit`
or `plat_vm_decommit` call. Platform functions and fixture-only protection calls
were separately inspected. CIM was unavailable in the reviewer's sandbox; this
review makes no independent process-absence assertion.

## Contract and supported-trace assessment

The v2 API remains a separate optional extension. Its compiled assertions and
the inspected ctypes declaration are 40 bytes for the API and 32 bytes for a
lease. Version 2, nonnull begin/end and a stable runtime domain are required.
The CPU header and `SNX_ABI=3` remain unchanged. The dynamic loader preserves
the old v1 negotiation and installs v2 before guest execution. A static module
skips this negotiation and remains uncached.

Load-code negotiation actually precedes mem_init. Installing the table copies
callbacks/domain without taking the mapping lock. An early begin checks the
atomic ready flag before touching that lock. mem_init initializes the mutex,
locks, invalidates the epoch before reserve/commit attempts, then publishes
ready with release ordering before unlocking. The inherited page-zero commit
return is still unchecked; this does not manufacture positive descriptors.

Every inspected commit/decommit route, including physical-map rollback and
heap/stack/TLS routes, uses the wrappers under the existing mapping lock.
Wrappers bump before a host attempt even on failure. Guest metadata changes do
not invent a host epoch. Counter exhaustion becomes sticky zero and permanently
disables descriptor reuse while allowing fresh leased queries. No reset exists
in production code.

The lease is native-thread-owned and address-owned. A copied, foreign or repeated
end cannot unlock another lease. The provider clears stable-window visibility
before end. Cross-window TLS holds only inert descriptors and API/base/span/epoch
identity, with no retained CPU/runtime pointer. Reacquisition compares all these
identities while holding the mapping lock; NULL/base changes and reservation ABA
cannot revive permissions. Missing/unknown APIs leave checks uncached. A failed
end or an invalid held scope terminates without guest handoff or callbacks.

SaveIO releases before original interpreter fallback, dependency dispatch and
snx_lookup. It reacquires before a native suffix. Adapter checks preserve
callee-saved GPR, stack/base and continuation/escape PC requirements. A rejected
preflight may use whole-entry original execution. A refusal after effects returns
with its original continuation and never replays the applied prefix. The native
leased intervals perform arithmetic, queries and memory access; no new
g_memlock-to-vk_lock edge was found. Mutation retains vk_lock-to-g_memlock.

## Final integrated-candidate evidence

The frozen coordinator snapshot is
`private/team/epoch-integration/final-snapshot.json`, SHA256
`a4054090c3f2b57d05e9b7d615b6c68b19b37acb88271fa0567b6ea75374d470`.
The reviewer independently rehashed its 44 source/report bindings, twelve
generated bindings, six artifacts, eleven reports, six tools and 125 current
runtime/test source bindings. All matched, as did the twelve gate proofs/logs.
The 125-source inventory was captured after the tests; it is not retroactive
before/after evidence for every compilation input. Affected mem/main/API sources
and all thirteen test executables have direct before/after bindings in the gate.

| Artifact | SHA256 |
| --- | --- |
| Separate module DLL | 98de63ffcac31d91cdb94d2f147d70741fa320359d195cd7a0ad5bd4e804ff02 |
| Separate epoch runtime and packaged game EXE | 6455fa93bf1378e1edec2334d1bfa52d139d4e7545560f224bcbf8b077e820cd |
| Generated manifest | 8dae1c62417722dffb65ff559edcefca6ac8011bdb2601d477859fc6166bf8c6 |
| Current SaveIO validator | fd3d10a6e38b4260562181ed91d5c321c1d9975bb476c4ccc1cf4e54a115e64f |
| Restored default runtime | dfe9256e44081bdeefa30c6b87e18442c0eade390cc919ff1d401be7c96c7f94 |
| Preserved default module | 2797747f4e69977388ff27cf9d04341b2b55a631a9c739f30351b7101a9a730d |

The module is in `private/windows/bridge-epoch-candidate`; the runtime is saved
in `private/windows/runtime-epoch-candidate/scarletnx.exe`. The same runtime is
packaged as the candidate directory's ACNH_1_0_0.exe. The independent hash/evidence
report is `private/team/epoch-integration-review/candidate-evidence-review.json`.
No checks failed. The source inventory is
`private/team/epoch-integration-review/final-review-source-snapshot.json`.

Fresh separate processes validated the same actual module with no API and with
API2. Each corpus has 150 native dispatch cases, fifteen rejection sentinels,
five interior sentinels and six defined original fallbacks. Twenty-two escapes
and five prefix handoffs belong to the 150 cases and are not additional cases.
Both reports bind the same DLL/manifest/validator, compare all GPR/NZCV/PC and
full mapped memory/frames/GOT/canaries, retain 102 modeled dependency dispatches,
reject native-entry replay and verify restoration of the actual interpreter hook.

The API2 gate records 272 dependency boundaries with the real mapping lock
released. Seven real late PAGE_NOACCESS operations and seven restores use
`snx_windows_range_epoch_candidate_protect`; both paths verify epoch advancement
and no held lease. The previous protection is queried and restored. Raw
VirtualProtect remains confined to the explicit no-API uncached corpus. The
API2 report binds the fixture DLL, build.json, nineteen source inputs and exact
compiled mem_epoch_test.c. Version 1, short 32-byte API, missing domain and
reinstallation are refused. Four frozen epoch sources and the production-memory
body agree with the isolated fixture, accounting for include spelling and the
retained v1 include.

The prior isolated v2 report still records 434 balanced leases, 83 concurrent
mapping transactions, sticky-zero/ABA/TLS/ownership checks and four terminal fault
children. It is historical evidence with validator hash `f88109f4...`, preserved
at the coordinator's starting-snapshot path. It is not relabeled as validation
of the modified current validator. Current actual-module evidence is separate.

Core, event, flag-table, Npad, guarded AccessKey and coverage gates passed against
the same module. AccessKey's 193 fast-path, nine original-body fallback and four
rejection cases remain guarded/partial scope and add no complete-body bytes.
Coverage remains fourteen complete entries / 2,212 of 44,815,680 original bytes,
about 0.0049357725%. Full runtime compilation passed, and thirteen CTests passed
against runtime `6455fa93...` with unchanged affected-source/executable hashes.

The raw `ctest --show-only=json-v1` output is
`private/team/epoch-integration/ctest-definition.json`, SHA256
`5cc86d8ca2742d64a2f0c6eba666bab1a7472d70559ce3a41807684f4feec728`.
The reviewer independently confirmed the hash, thirteen definitions and each
command's linkage to an executable hashed in runtime-ctest.json. This JSON was
captured after tests; it is distinct from CTestTestfile.cmake. The small separate
review is `private/team/epoch-integration-review/ctest-definition-review.json`.

## Real-runtime synthetic loader gate

The reviewer inspected the independent fixture/harness source, rehashed all
bound sources, three DLLs, build/validation reports and logs, and linked the
tested runtime hash to the compiled/CTest candidate. All three scenarios passed:
missing setter, accepting setter and deliberately refusing setter. The received
table has version 2, API 40 bytes, lease 32 bytes, null user, nonnull domain and
callbacks/domain located in the real runtime executable. Begin before mem_init
returns zero without changing an own nonnull-base lease; end refuses unacquired
and null leases without modifying the unacquired lease.

Begin's zero alone could also be a wrong-base refusal after initialization. The
pre-init conclusion requires the inspected main.c ordering and runtime/source
binding, together with that observation. The three fixture descriptors have
intentional ABI zero. Accepted/legacy cases stop at the expected ABI error;
refusal stops at the earlier loader error. These are expected-error exit-1
terminal outcomes without timeout/forced termination. They prove negotiation
and refusal before memory/services/GPU/guest startup, not successful initialized
leases or a valid game boot. The setter/own module is synthetic and does not
replace the actual production module install gate. Loader validation SHA256 is
`3007957bc7c968b91e03a5a9c7b4c6d4e31b708a19e6badfd36e2286b513b693`.

## Reproduction and patch-stack assessment

The final builder applies data-root, then v1, then epoch v2, and reverse-checks
the epoch patch. Once v2 is present, its adjacent loader insertion invalidates
the old v1 reverse-context check. The fallback verifies every contiguous added
v1 block in its declared file and rejects any nonheader removal line. For the
current additive v1 patch this preserves the original compatibility code and
accepts the already-audited final source. No weakening of epoch hunk validation
or removal of v1 code was found.

This presence check is narrower than a full context/location proof: an identical
block moved elsewhere in a drifted file could satisfy Contains. The current
files are independently proven to equal the exact audited patch over the saved
baseline, so this is not a blocker in this snapshot. Future patch drift needs
renewed review or a stronger baseline/position comparison. PatchCheckOnly skips
compilation/tests but can still apply missing patches; it is not a read-only
command on an unpatched checkout.

The initial patch-check invocation failed because PowerShell execution policy
disabled scripts. The failing report/log is retained; a Bypass invocation
passed. The game builder's explicit RuntimePath packaging passed and produces
the matching private epoch EXE while defaults are restored. An absent RuntimePath
would select the current build path, so candidate reproduction must use the
explicit path shown in module-build-packaging.json. Default restoration followed
CTest and synthetic-loader completion and was independently hash-verified.

To reproduce this review without executing a DLL, game or compiler, run from
the research directory:

```powershell
& 'private/tools/python/python.exe' 'private/team/epoch-integration-review/snapshot_review.py' --label 'repeat-read-only'
& 'private/tools/python/python.exe' 'private/team/epoch-integration-review/evidence_review.py'
```

The scripts write only to the reviewer's private directory. Full artifact hashing
should be scheduled outside the coordinator's active timing lease. The final
full hash review ran before that lease; only small metadata/document reads and
review-document writes continued afterward.

The coordinator's completed `docs/team/epoch-integration/REPORT.md` was reviewed
at SHA256 `a6e8a669d997b84d23d6a91275d6110fb7ab7da17330f727f74f98935abd0d72`.
Its model/sentinel/synthetic distinctions, retained failures, defaults and
candidate-only acceptance limits agree with this review. Its delivery.json was
read at provisional SHA256
`9619cbf494428f20a976a4ae57d61479acba58ead9347327cd211086013f304d`
before the coordinator appends this review. A clean build and byte-identical
cross-machine reproduction were not performed; inherited march/mtune native
flags remain host-dependent. These are explicit remaining goal requirements,
not evidence of final game reconstruction.

## Limits

This assessment assumes synchronous CPU/stack ownership, one-time startup and
trusted loader-only API installation. It does not cover arbitrary unwrapped host
protection/free/remap, live API replacement, object lifetime/data synchronization,
scope migration or nonlocal recovery. Imported callee models do not reconstruct
the original backends; rejection sentinels establish selection/no effects only.

No new reconstructed body is introduced. Coverage increment is zero. All models,
sentinels, infrastructure and synthetic loader scenarios remain separate from
reconstructed complete-entry coverage. Vulkan contention, regression resolution,
tutorial and actual save/reload are unproved by this review. A selected real
startup/gameplay run with the exact runtime/module hashes remains mandatory.
The full Windows reconstruction goal remains incomplete.

## Documentation erratum

The frozen runtime include says API installation follows mem_init, and the patch
comment refers to init preceding the loader. The actual startup ordering is
load_code then mem_init, as accounted above. The ready guard makes this supported
ordering safe. Integration documentation should state the real ordering; this
does not require changing the frozen source in this review.
