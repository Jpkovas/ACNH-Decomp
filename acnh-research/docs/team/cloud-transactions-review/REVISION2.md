# C11 transaction revision 2 review

The received revision 2 resolves the prior dangling outputs, invalid-argument output initialization and missing-license delivery problems. **It is still not ready for integration.** The unchanged imported source fails the strict Windows build, and a new write cycle reproduced loss of a recently committed key after a transient CURRENT read failure.

This review uses own host data and adds zero ACNH coverage. No game, proprietary input, ResultFs ABI, real save/reload or power-loss durability was tested. Imports, revision1/receipts, catalogue, runtime/defaults, generator and the separate FS transaction producer were preserved. No stage, commit, push or upload occurred.

## Exact delivery and license change

ZIP: 103,363 bytes, SHA256 `eb9e0b04bac14d74be9ea430d59246f3d70bbf81a214beb28283f2b746b40725`. All received SHA256SUMS entries were checked before and after execution. Entry points and cleanup were read before executing anything. The imported Python matrices remove only generated temporary fixtures, but this review did not run them or their recursive cleanup; the own runner preserves bounded scratch and executable/report evidence.

| Imported file | SHA256 |
| --- | --- |
| tx.c | ceea757382d7fd9a41ca43e2884475762dc32df8a00245fa84fe9fe1b7932532 |
| tx.h | 6fe59c55ed670c415dbdd932a95d8a65a4c0b0891bb0d81e9a9c9c7213e947db |
| driver.c | 8a82e8e014f39480292537958df8e9c57a684c73ba548ba7ffcb2bd6c7591e1a |
| LICENSE | cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30 |
| NOTICE | 040434d50f44f33bb3df97ecb9f9ab17b59060c7406600ef316866f2c065ec6b |
| PROVENANCE.md | be57f8d09cc9622387feee4a1ea5be851073c2a05e31ad15f724f529062c8ab9 |

R2 includes standard Apache-2.0 text, source SPDX declarations, copyright notice and an explicit producer grant covering its own current and historical implementation/documentation/fixtures. The structural missing-license blocker in the previous review is resolved by this delivery. Authorship and the no-third-party-code assertion remain producer declarations rather than independently verified history. The unchanged historical ZIP remains preserved; the grant supplements it without rewriting original bytes. The new review harness remains separately own GPL-3.0-or-later code.

Cloud JSONs reconcile **1,419 main + 305 first-generation + 168 error/output = 1,892 reported Linux cases**, with corresponding sanitized matrices. Main has 732 fail-closed cases; initial has 299 UNAVAILABLE cases. ASan/UBSan, GCC analyzer and remote execution claims were read, not rerun or independently certified here. Sanitizer commands disable leak detection, so they are not a leak-exhaustiveness proof. Linux case counts are not native Windows results.

## Fixes confirmed

Source review confirms `readfile` keeps the buffer local until successful complete read and close. `tx_snapshot_read`, `tx_open_current` and `tx_begin` initialize every provided output slot before argument rejection. Native targeted probes confirmed NULL/0 after real short-fread instrumentation, persistent read/open/seek/fread/close errors, malloc/calloc failures and invalid argument/absent-key cases. The imported `state()` caller safely frees the cleared error outputs in these probes.

The error hooks are synthetic callback failures, not actual device errors or exhausted memory. Once hooks are disabled, the own root's valid state remained readable. An API return -1 with cleared outputs is a failure contract, not a restored save. UNAVAILABLE before first publication or for damaged authorities is separate from that output contract.

## P1: transient CURRENT failure can lose a recent key

The same cycle was reproduced on exFAT and NTFS in the private minimally repaired Windows copy:

1. Commit an old generation.
2. Commit a new valid CURRENT containing an additional key `extra` with own `LIFElatest` bytes; confirm the key is readable.
3. Fail exactly one `read.fread` event during the next `tx_begin`. The failure is transient and the current generation remains intact on disk.
4. `tx_open_current` falls back to PREVIOUS; `tx_begin` returns 0 with the older contents cloned.
5. Disable the fault. Write an unrelated key and commit. Commit returns 0.
6. A fresh snapshot cannot read `extra`: return -1, NULL/0. The key that existed in healthy CURRENT has been omitted from the new published generation.

Relevant unchanged R2 control flow is `tx.c:146,169,176`: loading failures are collapsed into one generic failure and PREVIOUS is selected, then a partial write can publish that older base. Commit can reload the newer current only to make it PREVIOUS; it does not merge that generation's omitted keys into the stale transaction. This behavior is consistent with the declared read fallback policy, but makes ordinary writes silently roll back unrelated recent changes after transient OOM/read failures. It is an integration blocker even though it is not an output-lifetime violation.

Recommendation: distinguish validated corruption/absent authority from operational read/OOM errors. A writer must fail closed on inability to read CURRENT, or require an explicit recovery result and caller authorization to write from an older base. Track the selected base authority/generation and refuse publication if it cannot be reconciled with current state. Do not hide rollback as an ordinary successful begin/commit. Add this complete begin→partial-write→commit regression to the producer's suite, including transient payload reads and allocation failure positions.

## P2: strict Windows build remains broken

The received `tx.c:104` still compares signed32 `long z` with unsigned32 MAX_BYTES. The unchanged import failed Clang C11/O2/Wall/Wextra/Wpedantic/Werror with Wsign-compare. **No diagnostic waiver was used.** To continue the bounded runtime review while preserving the import, each test batch made a separately named private source copy with one local correction:

```c
(z=ftell(f))<0 || (uint64_t)z>(uint64_t)MAX_BYTES
```

The negative-size guard remains first. The copied module's SHA256 is `698ef58b886a3fd85054e857a3d1dc4d66b1374b36f38dc1d1e1d266f1181b96`; the original module hash is different and remains unchanged. That local copy passed the same strict flags without warnings/waiver. All native runtime results below belong to **R2 plus this one cast**, not to a successful strict build of the delivered R2. The new key-loss cycle does not depend on the size comparison; it uses ten-byte own payloads and unchanged authority-selection/publication paths.

## Native Windows scope and reproduction

The final own matrix ran separately on D: exFAT and C: NTFS, verified with GetVolumeInformationW. **Each filesystem has 215 cases: 214 contracts passed and one key-loss defect reproduced.** There are 430 native case executions across the two filesystems, not 430 distinct algorithms or reconstructed routines.

| Group per filesystem | Cases |
| --- | ---: |
| Original review contracts, with both prior bug probes now fixed | 175 |
| Expanded invalid arguments and persistent read/close/OOM output probes | 33 |
| Corrupt CURRENT combined with persistent read/OOM recovery failures | 6 |
| Transient CURRENT failure→successful stale write→lost key | 1 |

The 175 repeated contracts include 46 update boundary occurrences and 28 initial occurrences, each exercised with process crash and returned error; eight recovery publication boundaries with both failure modes; five individual truncation fallbacks; cross-process writer refusal/release/process death, retained OLD reader versus newly published NEW reader, key/path validation and ordinary publication. The six extra recovery cases close the imported error matrix's healthy-CURRENT-only gap: persistent injected errors return -1 while no authority is readable; after clearing the hook, recovery uses valid PREVIOUS and yields OLD.

The own runner checks `private/team/TIMING-LOCK.json` before compilation and every subprocess batch. It executes no imported cleanup script. It first compiles the unchanged import strictly; without the explicit local-candidate flag it stops and preserves the failure report. Commands:

```powershell
# Expected strict failure for the received R2:
& private/tools/python/python.exe scripts/cloud_transactions_team_candidate_r2_review.py

# Isolated one-cast candidate, exFAT scratch under private/team:
& private/tools/python/python.exe scripts/cloud_transactions_team_candidate_r2_review.py --local-signed32-candidate

# Same candidate, NTFS own-data scratch in the known writable C: workspace:
& private/tools/python/python.exe scripts/cloud_transactions_team_candidate_r2_review.py --local-signed32-candidate --scratch-parent 'C:/Users/Joniy/.codex/visualizations/2026/10/13/01a13734-dae4-73f2-87e4-e4a88be7d1da'
```

Compiler flags remain `-std=c11 -O2 -Wall -Wextra -Wpedantic -Werror -D_CRT_SECURE_NO_WARNINGS`. Sources/binaries/reports stay in the private review tree. The C: scratch contains only invented OWN!/LIFE payloads and protocol metadata. The first attempt to use the sandbox C: temp path failed at init and was not counted; the known writable NTFS workspace succeeded. No scratch was recursively removed.

Machine-readable final reports: `private/team/cloud-transactions-review/revision2/latest-review-exfat.json`, `latest-review-ntfs.json` and `delivery-manifest.json`. They identify executable hashes, exact commands, timing, source hashes, native results, imported Linux counts and data/evidence scratch separately. Full invocation logs remain private. The previous R2 attempts are retained rather than overwritten.

## Independent read-only review and remaining limits

An independent subagent reviewed source/API/license/fixtures without writing, compiling or executing. It confirmed the old memory/output fixes and license grant, and identified the stale-base write risk before the principal's native reproduction. It also identified the healthy-CURRENT-only error-recovery fixture gap; the six new native combined cases address that narrow gap. It observed stale README text saying read/allocation failures were not injected, despite the new TX_TESTING hooks.

The read-only review noted POSIX WRITER.lock opens lack O_CLOEXEC/FD_CLOEXEC, so a fork/exec child retaining the descriptor may outlive the writer and contradict release-on-process-death wording. This is a static/platform inference, not reproduced here, and does not apply directly to Windows CreateFileA with NULL security attributes.

Process crashes and observed pointer replacement do not prove power-cut durability. Windows directory sync remains a no-op. Same-volume MoveFileExA/FlushFileBuffers and cooperative locking passed the bounded namespace/process tests; actual ENOSPC, device faults, reboots, power loss, sharing races, antivirus interference, long/Unicode paths, hostile reparse points, non-cooperative writers, reclamation and quota enforcement remain unproved. ASan/UBSan/TSan were not run on Windows. ResultFs mapping, catalogue lifecycle, raw save images and Commit/MultiCommit integration remain outside this work.

Forward the strict-build and lost-key findings with the private proofs to the host FS integrator. Obtain a producer revision that incorporates the type repair and explicitly prevents silent stale-base writes, then rerun gates before adoption. Zero ACNH coverage and no real save/reload validation remain unchanged.
