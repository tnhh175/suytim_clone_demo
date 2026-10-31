# P1 data contract — review 22222.md, 2026-10-30

## Scope and evidence

Implemented recording structures, not clinical decisions, normal ranges, AI, treatment recommendations, or direct HIS/LIS/PACS integration. The review is the change request. Source evidence inspected: bundled `docs/extracted/TL05.txt` core row 21 (BMI formula but no rounding), HF rows 18–24 (BNP/NT-proBNP, EF, creatinine, eGFR, potassium); `TL04.txt` heart-failure tables; original TL06 metadata preserved in catalog. Source statements about AI or clinical thresholds do not become executable rules.

Catalog retains all 206 original source records and adds 15 scalar children plus one supplemental-results field. Original grouped BP/echo/CAD parents remain unavailable with `supported_by` references: this preserves source traceability rather than reinterpreting a source value. Newly added records explicitly identify their parent or review source; they are not additional TL06 source rows.

## Recording contract

| Review | Contract |
|---|---|
| DL01 | `ha_nam_ngoi_tam_thu`, `ha_nam_ngoi_tam_truong`, `ha_nam_ngoi_tu_the` (`lying`/`sitting`), `ha_nam_ngoi_thoi_diem`, `ha_nam_ngoi_nguon`; standing equivalents `ha_dung_tam_thu`, `ha_dung_tam_truong`, `ha_dung_thoi_diem`, `ha_dung_nguon`. Numeric mmHg, no diagnostic inference or mandatory complete pair for a draft. |
| DL02 | `lvef` numeric %, `sieu_am_tim_bao_cao` original text, `sieu_am_tim_thoi_diem`, `sieu_am_tim_nguon`. No EF phenotype inference, attachment storage, or echo interpretation. |
| DL03/04/12 | Results v2: `test_code`, original `name`, numeric `value`, original `unit`, `observed_at`, `source`. No timestamp default, unit conversion, eGFR computation, or BNP substitution. Value requires explicit source unit; unknown value/time/source remain null. |
| DL05 | `xet_nghiem_bo_sung`: CBC, LIVER, GLUCOSE, HBA1C, TSH, FERRITIN, TSAT, UREA, OTHER. CBC/LIVER rows require exact component in original name. These are local recording identifiers, not asserted standard codes. No automatic orders. |
| DL06 | Medication v2 retains name/ingredient/dose/route/frequency/observed_at and adds strength, dose_value, dose_unit, start_date, end_date, status, category, source. Original dose text is not parsed or replaced. Status is current/planned/stopped; category prescription/otc/supplement/traditional; all nullable with no default. Numeric dose requires unit. End cannot precede start. |
| DL07 | Existing encounter allergy metadata remains unchanged: unknown, confirmed absent, recorded present are distinct; structured ADR is P2. |
| DL08 | `benh_mach_vanh_da_biet` nullable boolean, independent `benh_mach_vanh_chi_tiet` text. Never infer absence from missing details. |
| DL10 | Existing code `thay_doi_nyha` retains I–IV choices; new label/help explicitly means NYHA at this visit, not delta. Old pinned labels unchanged. |
| DL14 | BMI deferred: formula exists but rounding is not agreed. No computed zero or polypharmacy classification. |
| DL18 | Finite numeric types (not bool), nonnegative BP/pulse/respiration, LVEF/SpO2 0–100 physical percentages. No normal-range rejection; e.g. BP 350 is not rejected as merely abnormal. |

## Unit evidence and deliberate remaining gaps

Exact verified units: BNP and NT_PROBNP `pg/mL`; CREATININE `umol/L`; EGFR `mL/min/1.73m2`; K `mmol/L`. No synonym conversion or additional unsupported unit is silently accepted for these codes. An alternate-unit result requires an agreed contract extension; source data should not be replaced with a guessed conversion.

NA, troponin and supplemental analytes have identifiers but no verified unit allowlist in the selected heart-failure source sections. They therefore retain explicitly entered report units (`result_tests[].units = []`), not a fabricated standard. This is a documented partial DL04/05/18 completion, not full terminology/units harmonization or MedSafety readiness. CBC/LIVER are recording groups, not a finalized analyte catalog; demo-case scope and detailed component identifiers remain to be confirmed.

## Versioning, import and provenance boundary

- `contract_version: 2` selects extended structured columns on new definitions. Missing version keeps the exact old row schema; new keys are rejected against old snapshots.
- New definitions, labels, physical limits and catalog metadata must be applied through the explicit catalog-upgrade workflow. Merely editing the JSON does not update a live database. Existing visits/history remain pinned and are never backfilled by this change.
- Existing scalar Excel conversion feeds the shared `value_for` validator. New scalar children use the same path; structured Excel remains blocked until a verified source contract exists. There is no JSON file/paste import.
- Null, false, zero and explicit empty lists remain distinct. Observed/test time is never synthesized from save time. User-entered `source` is reported provenance, not a claim of verification or a signed report.
- No Admin role logic, clinical thresholds, P2/P3 modules, migrations, live database writes, or snapshot mutation is introduced in this data patch.

## Validation

Pure tests `test_review_20261030_data.py` plus existing `test_revision_contract_unit.py`: 16 passed. Covers source count/children, physical boundaries without normal-range limits, original labels/units/time, separate BNP identity, nullable medication state, legacy structured shape and preservation of null/false/zero/empty arrays. No live DB is used.
