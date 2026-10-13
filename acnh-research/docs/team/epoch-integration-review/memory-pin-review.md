# Independent review of the integrated mapping epoch candidate

Reviewer: `memory_pin`, 2026-10-13. Scope: read-only inspection of source,
compiled artifacts and recorded gates. This review did not launch a game,
execute a gate, compile, load a DLL, change shared sources or publish artifacts.
It wrote only its own review and evidence snapshot.

## Decision and artifact scope

No blocker was found for a controlled startup/gameplay experiment with the
specific candidate module/runtime pair below. Source selection, loader table,
module provenance, protection transitions and recorded ABI/runtime gates agree.
The mapping lease is the existing **exclusive g_memlock**, implemented by
PMutex/AcquireSRWLockExclusive. It is not a shared reader lease.

This is not default-promotion approval, startup-regression resolution or proof of
a playable decompiled Windows build. These gates do not complete tutorial,
gameplay or actual save/reload, and they add no reconstructed game-code bytes.
The project remains hybrid; the complete reconstruction objective remains open.

| Artifact | SHA256 |
| --- | --- |
| Candidate game module | 98de63ffcac31d91cdb94d2f147d70741fa320359d195cd7a0ad5bd4e804ff02 |
| Candidate runtime and packaged game executable | 6455fa93bf1378e1edec2334d1bfa52d139d4e7545560f224bcbf8b077e820cd |
| Restored default runtime | dfe9256e44081bdeefa30c6b87e18442c0eade390cc919ff1d401be7c96c7f94 |
| Existing default game module | 2797747f4e69977388ff27cf9d04341b2b55a631a9c739f30351b7101a9a730d |

These hashes were independently recomputed from the current files. The candidate
runtime exists separately under `private/windows/runtime-epoch-candidate`, and
the same bytes were packaged under `private/windows/bridge-epoch-candidate`.
The central build runtime was restored after CTest and loader gates at
2026-10-13T22:45:53.7685435Z. Its current default hash intentionally differs from
the historical gate runtime hash. The preserved default copy matches it.
Future game comparisons must explicitly select the candidate runtime as well
as its candidate GameDirectory; selecting only the module directory can leave
the optional API unavailable on the older default runtime.

## Source selection and provenance

The applied runtime files are mem.c
`d5b5e4a736a159a958b3c212fe30ec190b4bbd8fcc44212e26432235b2e68710`
and main.c
`70115814f028f94a538df6019132c4517cc2e0da4c796398a43909e43fb4f530`.
I independently parsed the patch, checked context/removals against the saved
pre-integration files and applied it in memory only. Both resulting files match
the current sources exactly after normalizing line endings. The patch hash is
`a313c8223584bbd25b7b463feb3ccc865b1fc4b933fcc160d1c2ce3f7558912f`.

The ordinary CMake configuration selects the delegating SaveIO module wrapper,
range-query implementation, epoch provider and epoch context. The diagnostic
SaveIO profile configuration remains separate. The wrapper calls the reviewed
epoch entry; external dependencies keep per-CPU dispatch, while replaced-body
and interior fallbacks retain forced interpretation to avoid wrapper recursion.

The generator binds all sixteen selected SaveIO/provider/header source hashes,
the exact API2 wrapper contract, compiler, isolated body proof and final generated
wrapper hashes. The actual-module validator independently expects that same
source set and contract. All these current hashes matched both recorded module
corpora. The generated provenance JSON equals their compiled-provenance object,
and its literal is present in the candidate DLL without needing to load it.
The generated wrapper files, manifest and provenance source also matched.

## Mapping and lifecycle assessment

All original guest host reserve/commit/decommit sites are wrapped: initial
reservation/page zero, ordinary map, physical-hole commits, failed physical-map
rollback, unmap, heap shrink/growth, kernel stack and TLS allocation. Epoch bumps
precede host attempts under the exclusive mapping lock, including failures and
rollback. Guest permission/attribute changes remain metadata and invent no host
protection epoch. Exhaustion becomes sticky zero, prohibiting reuse while still
allowing fresh leased queries.

The loader negotiates API2 before mem_init and guest startup. Copying its table
uses no mapping lock. Early begin is rejected by the ready flag before touching
an uninitialized mutex; mem_init publishes ready after its locked setup.
The loader's domain is a stable runtime address, separate from a reservation
base. The CPU ABI remains SNX_ABI 3. Missing APIs leave the provider uncached,
and the static-module path does not negotiate this extension.

Cross-entry/callback descriptors remain inert in native-thread TLS. A new window
must reacquire a lease and match base, span, epoch and API identity before reuse.
Every checked request remains bounded by the reservation. NULL/base changes and
reservation ABA cannot restore stale positive permissions. Copied/foreign held
scopes or failed end operations terminate before guest dispatch. No supported
path introduces g_memlock-to-vk_lock: native intervals take g_memlock only;
mapping mutations retain vk_lock-to-g_memlock. SaveIO releases before snx_lookup,
original interpretation or any dynamic dependency and reacquires before its
native suffix. Existing continuation checks prevent replay after applied effects.

## Recorded gates independently checked

| Gate | Reviewed result and limits |
| --- | --- |
| Actual module without API | 150 native cases, 15 guard sentinels, five interior sentinels and six defined original fallbacks: 176 cases |
| Same actual module with API2 fixture | Same 176 cases; 272 unpinned dependency boundaries, seven real protected transitions and seven restores |
| Real candidate runtime loader | Three own scenarios: legacy, accept API2 and reject API2; all expected terminal exit 1, no forced termination |
| Runtime CTest | 13/13 passed, including startup, driver/extraction/loader/recompiler/codegen, filesystem, ASTC, semaphore and Vulkan headless |
| Other module gates | Replacements, event context, flag table, Npad and access-key gates passed on the candidate hash |
| Coverage gate | Fourteen complete entries / 2,212 of 44,815,680 original bytes; no new code coverage |

The two module corpora use the same module, source/provenance set and manifest.
Both retain 22 escapes, five prefix handoffs, full CPU/memory/canary comparisons,
102 populated fixture dispatch calls, interpreter restoration and no entry replay.
The API2 corpus rejects unknown version, short table, absent domain and reinstall.
The repeated modes are protocol configurations, not new distinct recovered bodies.

The API2 corpus uses the own real-mem.c fixture DLL
`12ee06ad733ff0c451bb496df53e267b0c80384e760ba330129daad55596482a`.
Its source/build/private-copy hashes are bound. Protection and restoration are
real VirtualProtect operations through its GPU-begin -> exclusive memlock ->
epoch-bump -> protect -> unlock -> GPU-end route. Tests check the native lease
is absent and the epoch advances. They do not substitute a local fence for a
runtime epoch. Raw VirtualProtect remains only in the explicit no-API corpus.

The loader's own accepting/refusing fixtures check the table's version/size,
main-runtime callback/domain addresses and callable pre-init refusals. They use
an intentionally incompatible module ABI and stop before memory/services/GPU or
guest startup. They establish negotiation and refusal, not a successful live
game-memory lease. Module dependencies retain declared fixture models rather
than executing every original backend. Sentinels establish selection/no effects,
and Vulkan headless CTest does not establish the affected ACNH scene.

I checked every successful gate record's before/after equality, log checksum and
currently available bound files. They matched. All recorded starts had the timing
lease inactive. The candidate runtime was unchanged during CTest and loader
execution; later default restoration is separately recorded. The reviewer makes
no process-absence assertion and executed none of those gates itself.

## Evidence archival note and remaining work

An initial patch-check attempt failed because of PowerShell execution policy
before running the script; the later explicit-policy retry passed. The frozen
failure record still names `patch-check.log`, which the successful retry reused.
Its retained `patch-check-policy-failure.log` has exactly the original recorded
SHA256 `cf1cbf0fd99e5fba3b9ef37869d47da0995518aea36dbb80a7af9678b33677f9`.
The failure is preserved and is not counted as a passing gate. This path alias
is an archival clarification, not lost evidence or a runtime blocker. No producer
record was rewritten by the reviewer.

The frozen runtime-include comment describes loader/init ordering imprecisely;
the actual load_code-before-mem_init order is accounted for above. Arbitrary
unwrapped host mutation, live API changes, object/data races, scope migration or
nonlocal recovery remain outside the supported contract and require a new audit.

The next mandatory evidence is repeated affected startup/gameplay with the exact
candidate pair under real Vulkan, followed by tutorial completion and actual
save/reload. Those remain separate from this source/ABI/build review. The current
execution and broad reconstruction coverage must remain explicitly documented.

The private review snapshot is
`private/team/epoch-integration-review/memory-pin-review.json`. Key reviewed reports:
no-API corpus `7499f8ec8ff5f6d0a5019fbcb2d769f42ecad0f416d1d1954a0675e2acdc29ee`,
API2 corpus `e54e2ecc571c9503d48cd06c34cd894e1d78b444466a4ffd661ff6acb4fd1885`,
loader gate `3007957bc7c968b91e03a5a9c7b4c6d4e31b708a19e6badfd36e2286b513b693`,
and CTest record `a5757854d7553f42f6374315cbdc3d662e4bab02eddcc008b366a6b1e0608283`.
