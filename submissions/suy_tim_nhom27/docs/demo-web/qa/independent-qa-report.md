# Independent QA review — M1/M2 Excel

Date: 2026-10-24. Agent4, same requested Astra/high configuration. Workspace reviewed: D:/1.TNHH/project/suytim_clone_demo, branch codex/demo-web, remote origin https://github.com/tnhh175/suytim_clone_demo.git. No project source/config changed by this reviewer. Scope excludes JSON import. This is technical QA plus qualitative walkthrough planning, not real-user research or clinical validation.

## Evidence separation

- Independently executed: 19 validator/parser checks, all PASS. Artifact: independent_contract_check.json and executable .py. Uses project .venv Python; default system Python initially lacked FastAPI, then rerun with project runtime. Checks NULL, 0, false, whitespace, numeric type rejection, choices, null versus empty list, timezone/date validation, repeated results, missing medication name, Excel leading zeros, typed values, unit confirmation. No database or HTTP assertions. Parser business_writes:false is only a returned declaration; it does not itself prove database non-mutation.
- Independently executed: exact current save() function in a Node VM with mocked DOM/API, three scenarios all PASS. Artifact: save_guard_retest.json and .js with source SHA256. Saving locks existing controls and restores their prior disabled states. Success advances revision; failed write preserves draft; successful write followed by failed reload keeps confirmed revision and warns. This is not a browser interaction test.
- Source reviewed: forms/router.py, validation.py, imports.py, forms.js, 002_dynamic_forms.sql, test_forms_api.py, test_forms_imports.py. Tests inspected do not imply tests executed by reviewer. Dev owns full PostgreSQL suite, rollback, concurrency and process-restart evidence.
- UI: reviewer CUA returned empty surfaces and IAB unavailable. Root performs UI. Root reported wrong doctor-to-admin rejection, correct doctor login, visible 0/false/null, note save revision3/history manual and Admin-created qa_ui_20261024. These are attributed root observations, not independent screenshots by Agent4. Root subsequently reported doctor saw the new dynamic field as NULL and saved it as revision4. Excel end-to-end remained pending at latest handoff.

## Issue / limitation ledger

Q-SAVE-01 | High: edits could disappear during an in-flight save | source forms.js save() | User edits while pending request | Earlier function awaited save then openVisit(), clearing dirty while controls remained enabled | Expected draft protection and clear saving state per PROMPT_DEV section13 / ui-spec Saving | Current implementation disables controls. Exact-function success/failure/reload-failure harness passed | Verified fixed at source/function level; UI-specific pending-request test not performed here.

Q-IMPORT-02 | Medium candidate: valid draft visit cannot be explicit Excel target without external visit code | source imports.py explicit target branch plus router.py VisitCreate and forms.js newVisit | A visit is created with optional external_id omitted | Source permits creation, but Excel preview rejects selected internal visit_id when external_id is absent. No visit-code edit endpoint/form was found in the reviewed implementation | Expected explicit selection to identify a valid existing target, or disclose/enforce this prerequisite when creating it; PROMPT_DEV sections10 and11.1 allow system/internal identity | Source evidence only; root/Dev notified | Verified fixed at source/function level: explicit UUID now goes through visit_access, blank external_id no longer blocks selection, and content hash includes visit_id. Independent explicit_uuid_retest.json passed three checks: exact target for each of two blank-code visits and propagated scope denial, using mocked DB/access. Dev test test_explicit_known_uuid_with_two_visits_missing_external_codes covers real PostgreSQL commit and dedup; reviewer did not execute that suite. No independent UI reproduction claimed.

Q-EXCEL-LISTS | Coverage limitation | imports.py Excel mapping | medications/results/multiselect targets | Adapter explicitly rejects these structures instead of flattening or taking final row. Structured manual fields work at validator level, but this is not Excel repeated-list support | PROMPT_DEV11.2 requires safe structured handling and permits clearly marking unresolved source structure | tests/fixtures/forms/README.md acknowledges scalar workbook does not validate list adapter | Open disclosed limitation; do not mark all repeated-list Excel support complete.

## Remaining UI checks for root

1. Admin account at doctor portal must be rejected; both logout destinations.
2. Doctor sees qa_ui_20261024 after reloading field catalog, NULL before input; save/read/history value and Admin rename preserves it.
3. Excel source→sheet/header→mapping→preview: correct identities, unknown identity pending/error, wrong type exact location, 0/false and NULL nondelete, conflict defaults keep.
4. Preview cancellation leaves same visit/history; commit explicit synthetic target; open/read/history; repeated/renamed file no duplicate; invalid file does not claim success.
5. Keyboard Tab/Enter through login/form/dialog/import; narrow layout and table scrolling. Root screenshots establish visual state only.
6. Verify absent JSON import navigation/routes. Internal JSON serialization is not a JSON import feature.

Acceptance remains partial until root/Dev attach their actual UI, API/transaction and restart evidence. No clinical readiness or HIS-format compatibility conclusion.

The earlier save_race_check.js artifact is an abandoned harness: source changed during execution and that run failed because the new app dependency was absent in its mocks. Do not cite it as a bug reproduction. Use save_guard_retest.json only for the current guarded implementation.

## Retest artifact

explicit_uuid_retest.json records the 3/3 passing exact-function checks with source hash. The test uses an explicitly synthetic in-memory signing key; it neither reads nor copies a live credential. All JSON artifacts copied to docs/demo-web/qa contain no tokens/passwords/connection strings.
