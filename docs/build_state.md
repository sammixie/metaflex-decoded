# Build state

Living context file. Read at the start of every session, alongside
`docs/data-decisions.md`.

Division of labour with the other docs:

- `MetaFlex_Build_Plan_v2.pdf` — the plan. Fixed. What the project is, who it's
  for, the phases. Doesn't change.
- `docs/data-decisions.md` — the log. Append-only. Every decision and why.
- **this file** — what changes. Where the build actually is right now.

Sections 2 and 4 get rewritten at the end of each phase. Section 3 grows.

Last updated: 2026-08-17

---

## 1. Where this sits against the plan

Phase 3 (Agreement, EDA, phenotypes) — closed. Plan schedules Phase 3 at weeks
6–7 (14, 21 Sep 2026); this closed 17 Aug 2026, roughly 4 weeks ahead of
schedule.

---

## 2. Current state

**Working:**

- `src/load.py` — `load_cgm_file` and `load_summary_file` run across all 125 CGM
  files with no unmapped columns. Provenance columns (`source_row`,
  `source_file`) attached. Identity parsed from filename / `Patient Number`.
- `src/clean.py::clean_cgm` — drops `dietary_intake_zh` (D-009); sorts and
  rounds timestamps to the nearest minute (D-014); resamples each
  patient-visit onto a 15-minute grid, restarting the origin at any real
  device-swap gap rather than once per visit (D-015); computes `cgm_gap` after
  resampling, not before (D-012/D-017); adds `cgm_out_of_range` /
  `cbg_out_of_range` range flags (D-010); replaces known non-numeric text
  values in `insulin_csii_bolus_r_iu` / `insulin_csii_basal_r_iu_h` so both
  cast cleanly to numeric (D-021); nulls the one leaked-header value in
  `insulin_dose_iv` (subject 2027, D-022).
- `src/clean.py::clean_summary` — strips whitespace across every `str`-dtype
  column (D-016); relabels `uric_acid_mmol_l` → `uric_acid_umol_l`, source
  header was wrong (D-018).
- `notebooks/02_cleaning_pipeline.ipynb` — restructured: Setup → Data
  dictionary → Structural integrity → Table A cleaning (calls `clean_cgm`) →
  Table B cleaning (calls `clean_summary`) → Write cleaned tables → Cohort and
  attrition check. Confirmed run top-to-bottom with a restarted kernel
  (2026-08-11); both cleaned tables write to `data/interim/` successfully.
- `requirements.txt` — created (pandas, numpy, openpyxl, xlrd, pyarrow).
- **Environment (two machines)** — `.venv` is the working environment on the
  MacBook Pro, not usable from the MacBook Air (its symlinked interpreter
  points at a `Python.framework` path that doesn't exist on this machine).
  `.venv-air` is the working environment on the MacBook Air — Python 3.14,
  pandas 3.0.5, pyarrow 25.0.1, confirmed working. The earlier note calling
  `.venv-air` non-functional was wrong (or stale for this machine).
- `table_a_clean.to_parquet(...)` / `table_b_clean.to_parquet(...)` — verified
  to succeed end to end, live, via the notebook itself. (The earlier
  "verified" claim in this file was against a version of `clean.py` that
  didn't actually contain the D-021 replacement logic yet — decision was
  logged before the code was written; that gap is what broke it. Now fixed
  and re-verified.)
- Cohort / attrition check — 125 CGM files + 2 summary files → 112 distinct
  subjects (100 T2DM, 12 T1DM) → 125 subject-visits. No subjects, visits, or
  rows are dropped anywhere in the pipeline.
- `docs/data-decisions.md` — D-001 through D-022 logged.
- **Phase 2 (CGM metrics engine) — built and tested (2026-08-12).**
  `src/metrics.py` has all 10 metrics from the plan's actual Phase 2 list:
  `mean_glucose`, `std_glucose`, `cv_glucose`, `cv_instability_flag`
  (CV≥36%), `tir_glucose`, `tar_glucose`, `tbr_glucose`, `gmi_glucose`,
  `mage_glucose` (full classic Service et al. 1970 algorithm — turning-point
  detection, 1×SD threshold, majority-direction averaging), `excursion_count`.
  Shared turning-point/threshold logic factored into `qualifying_swings()`,
  called by both `mage_glucose` and `excursion_count` so they can't drift
  apart. Every function has a docstring stating grid/column/gap-handling.
  `tests/test_metrics.py` — 10 passing hand-computed tests. **Known gap:**
  `cv_instability_flag` only tests the unstable (`True`) direction, not a
  stable (`False`) case.
  `docs/metric-changelog.md` — scaffolded and populated, M-001 through
  M-009, each with rationale and alternative(s) considered. One correction
  made mid-build and applied in place rather than superseded, per explicit
  instruction: M-007's tie-break rule (originally "default to rises",
  corrected to "average both directions on a tie" — rises-only was judged
  arbitrary, the tie case has no real majority).
  `notebooks/03_cgm_metrics.ipynb` — skeleton's markdown/code cell mix-up
  fixed. `groupby(["subject","visit"]).apply(summarize)` applied across all
  125 patient-visits, 0 missing values in any metric column. Sanity-checked
  two independent ways: TIR recomputed via `.between()` (exact match against
  `tir_glucose`'s output), MAGE/`excursion_count` checked visually against a
  plotted trace for subject 2035 visit 0 (11 marked swings matched
  `excursion_count` exactly). Saved to
  `data/processed/summarize_table_a.parquet` — confirmed reproducible by
  deleting the file and regenerating it from a clean run, not just trusting
  a file that was already sitting there.
  `requirements.txt` — added `pytest`, `matplotlib`.
- **Scope correction found this session:** the Phase 2 brief drafted last
  session (seven metrics) undercounted the plan's actual Phase 2 list —
  missed TAR, TBR, and the CV≥36% instability flag. Found by reading
  `MetaFlex_Build_Plan_v2.pdf` directly rather than relying on the brief.
  Closed the gap same session (M-009, TAR/TBR; `cv_instability_flag`).
- **Phase 3 (Agreement, EDA, phenotypes) — analysis and figures complete
  (2026-08-17).** `notebooks/04_eda_profiles.ipynb`: Setup/join → §1 GMI vs.
  HbA1c agreement → §2 endpoint stability → §3 T1DM vs. T2DM distributions →
  §4 K-means phenotyping → §5 hero figure.
  - **§1 headline (D-023/D-024):** GMI bias -2.31% vs. lab HbA1c, 95% LoA
    -6.79 to +2.16% (width 8.95 pts) — ~6x NGSP's 1.5-pt interchangeability
    bar. 78/116 (67.2%) of subject-visits exceed Lenters-Westra's 0.8-pt
    individual discordance threshold. n=116 of 125 (9 missing HbA1c).
    Two-panel figure built: scatter+identity line, and the actual
    Bland-Altman plot.
  - **§2 endpoint stability (D-025–D-028):** split-half ICC (BMS/WMS method)
    computed for all 9 continuous metrics. Cutoff ICC≥0.75. Only
    `excursion_count` (0.878) and `tbr` (0.773) clear it; `mage` lowest
    (0.618) despite being the most established variability measure in the
    literature.
  - **§3 T1DM vs. T2DM (D-003/D-029):** descriptive only, no p-values (n=12
    T1DM subjects). T1DM runs higher on SD/CV/MAGE — expected physiology,
    not a new finding. Boxplot figure built.
  - **§4 K-means phenotyping (D-030–D-032, D-034):** k=3 chosen over
    silhouette-argmax k=2 (k=2 isolated a single outlier, failed the
    physiological check). Three clusters: well-controlled (n=72),
    hyperglycemia-leaning (n=49), hypoglycemia-prone (n=4, splits evenly 2
    T1DM/2 T2DM — cross-diagnosis mixing is the section's headline
    exploratory finding). Robustness-checked against a reduced
    one-visit-per-subject set. Cluster scatter figure (TAR×TBR, colored by
    cluster, shaped by diabetes type) built.
  - **§5 hero figure:** standalone, README-ready version of the
    Bland-Altman plot, exported to
    `reports/figures/hero_gmi_hba1c_agreement.png`.
  - **Bug found and fixed this session:** `bias` was assigned in both §1
    and §2, and because a notebook kernel is one shared namespace, §2's
    assignment silently overwrote §1's — the hero figure briefly rendered
    with the wrong bias line (+10.72 instead of -2.31) before this was
    caught by running the notebook top-to-bottom rather than trusting each
    cell in isolation. Fixed by renaming to `gmi_bias` / `split_half_bias`;
    re-verified via full re-execution.
  - `docs/data-decisions.md`: D-023 through D-034 logged (D-033 number not
    used — skipped, not a gap in the actual decisions).

**Not started:**

- A full unit audit across the rest of Table B's lab columns — only
  `uric_acid_mmol_l` was checked and found wrong (D-018); eGFR, BMI, and the
  subject-2035 insulin duplicate were investigated and left as documented,
  unfixed findings (D-019, D-020), not systematically re-checked against every
  other column.
- A decision on `insulin_dose_sc` / `insulin_dose_iv` as free text (kept
  as-is, parsed, or dropped as a Phase 4 feature) — doesn't block Phase 1,
  needed before either column is used as a model feature.
- Section 5's interpretation markdown — figure is built, write-up isn't.
- The Bland-Altman plot shows a *proportional* bias (disagreement widens at
  higher glucose, not a flat -2.31% offset) — observed while building the
  figure, not yet logged as a decision or discussed in §1's interpretation.

**Repo hygiene:** this directory is not a git repository — no `.git`. The plan's
rule "commit working states only" has nothing to commit to locally.
`notebooks/`, `src/`, `docs/`, and now `requirements.txt` all have real work
in them and none of it is under version control.

---

## 3. Verified facts about the data

Facts established by direct check, not assumption. Each traces to a decision
entry where one exists.

**Cohort and files**

- 125 CGM files → 112 distinct subjects: 102 with one visit, 7 with two, 3 with
  three (D-001).
- `table_a` — all CGM files concatenated — is 128,170 rows.
- `RENAME_CGM` holds 20 keys mapping to 11 unique target columns; 9 header
  spelling variants confirmed by hand (D-008).

**Value counts in `table_a`**

| Column | Non-null | Null |
|---|---|---|
| `cgm_mg_dl` | 128,157 | 13 |
| `cbg_mg_dl` | 4,019 | 124,151 |
| `blood_ketone_mmol_l` | 58 | 128,112 |

**Range validation (D-010, D-011)**

- Lowest genuine glucose value across both columns: 30.6 mg/dl (`cbg_mg_dl`).
  Highest: 475.2 mg/dl (`cgm_mg_dl`).
- `cgm_out_of_range` flags 0 rows. `cbg_out_of_range` flags 1 — subject 2044,
  value 2044.8 mg/dl, numerically resembling the subject ID, treated as a
  transcription error.
- 3 ketone readings exceed 3.0 mmol/L (4.30, 12.54, 12.90). Left unflagged —
  clinically plausible DKA-range values, not data errors.

**The 2029 device-change gap (D-012)**

- All 13 null `cgm_mg_dl` rows in `table_a` are subject 2029, visit 0.
- `source_row` 741–753, matching note.txt's Excel rows 743–755 with a
  consistent +2 header offset.
- Gap runs 2021-06-03 09:14:00 → 12:46:00 = 3 h 32 min = 13 missed readings at
  15 min (195) + one 17-minute interval at the changeover (17).
- `t_after` of 12:46:00 matches note.txt's stated restart time for the
  replacement device exactly.
- Subject 2029's trace is 846 rows: 843 intervals of exactly 15.0 min, one of
  17.0, zero negative. No absent-row gaps in this file.

**Resample / timestamp findings (D-014, D-015)**

- 117 of 125 subject-visit groups start off the quarter-hour clock grid
  (e.g. `09:40` instead of `09:30`/`09:45`) — real device behavior (sensor
  activated whenever, not synced to the clock), not an error. Anchoring the
  resample grid to each group's own first reading (`origin="start"`) handles
  this correctly.
- Subject 2029 additionally has ~13 intervals off by a few milliseconds near
  its documented device-swap gap (D-012) — a float artifact of Excel's
  date-serial conversion, distinct from the real 17-minute gap. Rounding to
  the nearest minute removes it; confirmed isolated to this one file across
  all 125.
- A single visit-wide resample origin silently drops real readings after a
  genuine device swap (91 of subject 2029's 832 real `cgm_mg_dl` values, 832 →
  741) because the replacement device samples on its own clock, not phase-
  locked to the original. Fixed by restarting the origin at any gap that
  isn't a clean multiple of 15 minutes (a real phase shift) while leaving
  ordinary missed-reading gaps (clean multiples: 30/45/60 min) on a single
  origin. Verified: 15 real absent-row gaps found across 6 subjects (2095,
  2023, 2080, 2084, 1002 visit 1, 2040), all correctly preserved; subject 2029
  restored to 832/832 real readings, split into exactly 2 segments (matching
  its 1 documented swap).
- Full-pipeline `cgm_gap` count: 28 (13 original subject-2029 blank rows,
  `source_row` present + 15 newly-visible absent-row gaps, `source_row` null)
  — `source_row.isna()` correctly separates the two, as D-012 anticipated.

**Cohort and attrition (Phase 1 close)**

- 125 CGM files + 2 summary files (`Shanghai_T1DM_Summary.xlsx`,
  `Shanghai_T2DM_Summary.xlsx`) → 112 distinct subjects (100 T2DM, 12 T1DM,
  matching the plan's estimate exactly) → 125 subject-visits. No subjects or
  visits are dropped anywhere in the pipeline.
- `table_a`: 128,170 raw rows → 128,185 in `table_a_clean`. The +15 is
  resample-surfaced absent-row gaps (D-015), not new real readings.
- `table_b`: 125 rows raw and clean, unchanged — `clean_summary` doesn't add
  or drop rows.

**insulin_dose_iv leaked-header value (D-022)**

- Subject 2027, visit 0, `source_row` 0: `insulin_dose_iv` held the string
  `'CSII - basal insulin (Novolin R, IU / H)'` — the English header text of
  the neighbouring `insulin_csii_basal_r_iu_h` column, not a real IV dose.
  Confirmed by inspecting `data/raw/Shanghai_T2DM/2027_0_20210521.xls`
  directly: `load.py`'s header row and column mapping are both correct at
  that row, and the neighbouring column holds a plausible real value (`0.6`).
  Root cause is a data-entry error in the source file, not a parsing bug.
  Nulled per D-022.

**Table B numeric audit (D-018, D-019, D-020)**

- `uric_acid_mmol_l`'s source header is wrong — values (93–564) match the
  normal µmol/L reference range, not mmol/L. Relabeled, values unchanged.
- eGFR outliers (up to 286 ml/min/1.73m²) correlate strongly with low
  creatinine (r = -0.79 cohort-wide) and low body weight — a known formula
  limitation in low-muscle-mass patients, not a data error. Left unflagged.
  Subject 1010 (eGFR 286) also has the cohort's lowest BMI (13.67) —
  independently consistent with the same explanation, not a separate issue.
- Subject 2035 has an exact fasting/postprandial insulin match (2089.8 both)
  — the only exact match among 64 subjects with both values recorded. Reads
  as a likely transcription error but left untouched; no independent way to
  confirm which value (if either) is wrong.

**Phase 2 metrics table (2026-08-12)**

- `groupby(["subject","visit"]).apply(summarize)` on `table_a_clean`
  produces exactly 125 rows (one per subject-visit, matching Phase 1's
  cohort/attrition count) and 0 `NaN` across all 10 metric columns.
- TIR + TAR + TBR sum to exactly 100% by construction (M-009's exclusive
  boundaries on TAR/TBR, complementing TIR's inclusive 70-180) — confirmed
  on the `[100, 200, 300, NaN]` test trace (33 + 67 + 0 = 100), not yet
  spot-checked across the full 125-row table.
- Subject 2035, visit 0 (247 rows, the smallest patient-visit in the
  cohort) spot-checked two independent ways: `tir_glucose` matched a
  separately-written `.between(70,180)` recomputation exactly
  (96.761134...); `mage_glucose`/`excursion_count` (44.1, 11) matched a
  plotted visual count of the trace's turning-point swings exactly.

---

## 4. Immediate next step

Phase 3's analysis and figures are done; two small write-up items remain
before it's fully closed (see Not started, in section 2) — both mine to
review, hers to write: section 5's interpretation, and a decision on the
proportional-bias pattern the Bland-Altman plot surfaced.

Next real phase is **Phase 4 (hypoglycemia risk model)**: baseline logistic
regression, then tree ensembles, grouped cross-validation (subject-level,
per D-002 — repeat visits from the same patient never split across folds),
evaluated on PR-AUC/precision/recall/confusion matrix, a threshold chosen in
cost terms, SHAP for interpretation.

Immediate action before Phase 4 starts: this directory still isn't a git
repository — nothing built so far is under version control (see Open items
below).

Phase 1 is complete per the plan (cleaning, provenance, resample grid,
cleaned tables, cohort/attrition numbers — all done and verified live).
Remaining Phase 1 open items are deferred, not blocking (see Open items
below): the full Table B unit audit, and the `insulin_dose_sc` /
`insulin_dose_iv` free-text decision.

---

## 5. Open items

Things deliberately deferred, so they don't evaporate.

- **`cgm_gap` ordering relative to the out-of-range block is still
  untestable.** `cgm_out_of_range` is 0, so placing `cgm_gap` above or below
  the D-010 range-check block produces an identical column today — the data
  cannot tell you the order is wrong. Phase 2 test in `tests/`.
- **`diabetic_macrovascular_complications` has an unfixed order
  inconsistency** (2 of 125 rows, same conditions listed in different order)
  — documented, not fixed (D-016).
- **Subject 2035's insulin duplicate** — documented, not fixed (D-020).
- **`insulin_dose_sc` / `insulin_dose_iv` are free text, not numeric** —
  remember before any future feature engineering. No decision logged yet on
  how they get treated (kept as-is, parsed, or dropped) before Phase 4.
- **Not under version control.** No `.git` in the project directory.
