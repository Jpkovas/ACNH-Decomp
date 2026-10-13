# Worker delivery contract

Each worker creates a report in its assigned directory and includes:

- Task ID, exact title, scope, ownership, starting Git/source hashes and date.
- Problem, expected contract, mechanism, final implementation and alternatives.
- Exact changed/new file inventory; files copied privately versus shared edits.
- Source, toolchain, artifact and report SHA256; licensing/provenance.
- Reproduction commands, environment, own/original/model fixture distinction.
- Expected/observed results, case counts and failures retained as evidence.
- Guards, register/PC/memory effects, escapes/fallbacks and concurrency limits.
- Integration steps, dependencies, shared-file conflicts and required gates.
- Explicit untested behavior, remaining stubs, risks and blockers.
- Coverage status: isolated zero, or exact distinct original-body intervals
  proposed to the coordinator; never self-count unintegrated bodies.

Also deliver `delivery.json` with `task_id`, `status`, `files`, `source_hashes`,
`artifacts`, `tests`, `limitations`, `integration_steps`, `coverage_increment`,
`gameplay_validated`, `save_reload_validated` and `review_required` fields.

Use `prepared`, `isolated-tested` or `reviewed` status unless the coordinator
confirms actual integration. Tests passed must bind current source/artifact
hashes. Preserve failed logs. Never relabel timeout as normal terminal exit,
model as original callee, primitive assertions as unique ABI cases, or host
synthetic persistence as game save/reload.
