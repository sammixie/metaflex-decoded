# Data decisions

Every cleaning and processing decision, with its rationale.
Format: one entry per decision, newest at the bottom. Table above is an index.

| ID | Date | Decision | Phase |
|---|---|---|---|
| D-001 | 2026-08-04 | Grain is patient-visit; subject ID parsed from filename | 0 |
| D-002 | 2026-08-04 | Cross-validation grouped on subject, not visit | 0 |
| D-003 | 2026-08-04 | T1 vs T2 comparisons are descriptive only | 0 |
| D-004 | 2026-08-04 | Using the 2023-10-26 revision of the dataset | 0 |
| D-005 | 2026-08-05 | Hypoglycemia label is chart/questionnaire-derived, not CGM-trace-derived | 0 |
| D-006 | 2026-08-09 | source_row is 0-based pandas position, captured before rename/filter/sort | 1 |
| D-007 | 2026-08-09 | subject (join key) stored as int, parsed from composite identity string | 1 |
| D-008 | 2026-08-09 | 9 CGM header variants confirmed and merged into RENAME_CGM | 1 |
| D-009 | 2026-08-10 | Drop dietary_intake_zh in clean.py — duplicate of dietary_intake | 1 |
| D-010 | 2026-08-10 | CGM/CBG range validation: <30 or >600 mg/dl flagged, not imputed | 1 |
| D-011 | 2026-08-10 | No range-validation flag for blood_ketone_mmol_l | 1 |
| D-012 | 2026-08-10 | CGM gaps flagged with an explicit cgm_gap column, never imputed | 1 |
| D-013 | 2026-08-10 | No gap flag for cbg_mg_dl or blood_ketone_mmol_l | 1 |
| D-014 | 2026-08-11 | Round CGM timestamps to the nearest minute before resampling | 1 |
| D-015 | 2026-08-11 | Resample origin restarts at any non-15-minute-multiple gap, not once per visit | 1 |
| D-016 | 2026-08-11 | Strip whitespace across all text columns in Table B; leave multi-value field order unnormalized | 1 |
| D-017 | 2026-08-11 | cgm_gap moved to run after resample, not before (supersedes D-012's ordering) | 1 |
| D-018 | 2026-08-11 | Relabel uric_acid_mmol_l to uric_acid_umol_l (source header mislabeled) | 1 |
| D-019 | 2026-08-11 | No flag for high eGFR outliers — treated as a known formula limitation | 1 |
| D-020 | 2026-08-11 | Subject 2035's identical fasting/postprandial insulin left untouched, documented | 1 |
| D-021 | 2026-08-11 | insulin_csii_bolus_r_iu / insulin_csii_basal_r_iu_h text values replaced: suspend-delivery → 0, acarbose → null | 1 |
| D-022 | 2026-08-11 | insulin_dose_iv leaked-header value (subject 2027) nulled out | 1 |
| D-023 | 2026-08-12 | GMI vs. HbA1c agreement compared in %, hba1c_mmol_mol converted via IFCC-NGSP master equation | 3 |
| D-024 | 2026-08-13 | Individual-patient discordance threshold is 0.8%, not 0.5% | 3 |
| D-025 | 2026-08-13 | Endpoint stability (guiding question 1) operationalized as split-half agreement within each recording | 3 |
| D-026 | 2026-08-13 | Stability quantified via Intraclass Correlation Coefficient (ICC), not CV% of measurement error | 3 |
| D-027 | 2026-08-13 | cv_instability_flag's split-half stability not separately tested — inherits from cv_glucose's ICC | 3 |
| D-028 | 2026-08-13 | ICC ≥ 0.75 is the cutoff for "stable enough to carry a primary endpoint" | 3 |
| D-029 | 2026-08-13 | T1DM vs. T2DM comparison (guiding question 5) scoped to std, cv, mage only | 3 |
| D-030 | 2026-08-13 | K-means phenotyping (guiding question 4) clusters on cv, mage, tar, tbr — mean/gmi/std/tir excluded | 3 |
| D-031 | 2026-08-13 | K-means features scaled with z-score (StandardScaler), not min-max | 3 |
| D-032 | 2026-08-13 | K selected via silhouette score, not the elbow method | 3 |
| D-034 | 2026-08-13 | k=3 chosen over silhouette-argmax k=2, which failed the physiological check | 3 |
| D-035 | 2026-08-17 | Phase 4 model runs diabetes_type as an ablation (clinical-only vs. clinical+CGM+type), not a fixed include/exclude choice | 4 |
| D-036 | 2026-08-17 | insulin_dose_sc parsed as a Phase 4 feature; insulin_dose_iv deferred | 4 |
| D-037 | 2026-08-17 | GMI-HbA1c disagreement reported as proportional, not flat, bias | 3 |
| D-038 | 2026-08-17 | insulin_dose_sc aggregated as dose/day (Total Daily Dose framing); injection count kept as a secondary feature | 4 |
| D-039 | 2026-08-17 | Visits with no insulin_dose_sc entry get insulin_dose_per_day = 0, not NaN; 5 visits with no medication data at all flagged as a caveat | 4 |

---

### D-001 — Grain is patient-visit; subject ID parsed from filename

**Decision.** The unit of analysis is one patient-visit. Subject ID, visit number and
recording date are parsed from the filename pattern `SSSS_V_YYYYMMDD`.

**Rationale.** 125 CGM files map to 112 distinct subjects: 102 with one visit, 7 with
two, 3 with three. Treating files as patients would overstate the sample by 12%.

**Alternative considered.** Collapse repeat visits into one row per subject. Rejected —
it discards real within-subject variation, and n is small enough that losing 13 rows matters.

**Impact.** All downstream tables carry `subject`, `visit` and `recording_date`.

---

### D-002 — Cross-validation grouped on subject, not visit

**Decision.** Phase 4 uses `GroupKFold` grouped on subject ID.

**Rationale.** Repeat visits from the same person are not independent observations. If
visits from one subject land in both train and test folds, reported performance is
optimistically biased.

**Impact.** Constrains model evaluation design. Noted in threats to validity.

---

### D-003 — T1 vs T2 comparisons are descriptive only

**Decision.** No inferential testing between diabetes types. Distributions shown side by
side, no p-values.

**Rationale.** T1DM n = 12 subjects (16 visits). Any test is underpowered, and a
significant result at this n would be more likely noise than signal.

**Impact.** Guiding question 5 is labelled exploratory throughout.

---

### D-004 — Using the 2023-10-26 revision of the dataset

**Decision.** Analysis uses the revision dated 2023-10-26, which added 188 CGM
measurements across two T2DM files (`2003_0_20210615`, `2029_0_20210526`).

**Rationale.** Version is recorded so results are comparable to the right source.
Published analyses using an earlier version may not reproduce exactly.

**Impact.** Version stated in the README data section.

---

### D-005 — Hypoglycemia label is chart/questionnaire-derived, not CGM-trace-derived

**Decision.** Treat `Hypoglycemia (yes/no)` as an independently-collected clinical
characteristic, not a value computed from the CGM trace.

**Rationale.** Per the dataset's data descriptor (Zhao et al. 2023), hypoglycemia
occurrence was collected via questionnaire/medical-record review, alongside
comorbidities and complications — separate from the CGM device. The paper's own
TIR/TAR/TBR stats are author-computed outputs, not columns in Summary.xlsx. This
rules out the label being a direct formula on the CGM columns used as features.
Exact case definition and time window (this visit vs. history) are unstated, so
CGM-derived features from the same recording period may still be concurrently
associated with the label, even if not mathematically derived from it.

**Alternative considered.** Drop CGM-derived features to guarantee no overlap.
Rejected — it removes the strongest predictors for a risk it doesn't fully close.

**Impact.** Phase 4 model is framed as visit-level *association*, not prospective
prediction, in `findings.md`. `metric-changelog.md` flags features sharing a
recording window with the label.

---

### D-006 — source_row is 0-based pandas position, captured before rename/filter/sort

**Decision.** `source_row` records the 0-based positional index of a row in its
original file, captured immediately after `pd.read_excel()` — before rename,
filtering, or sorting.

**Rationale.** Matches Python/pandas convention: `.iloc`, list indexing, and
`.reset_index()` all start at 0, so `source_row` lines up directly with
`df.iloc[source_row]` for anyone re-deriving a row programmatically. Consistent
with how the rest of the codebase indexes.

**Alternative considered.** 1-based row number matching what a person sees when
opening the file in Excel (with a further +1 offset for the header row).
Rejected — the traceability claim this project makes is "you can pull this exact
row in code," which favors matching Python's own indexing over Excel's on-screen
numbering. Cost: any write-up or figure that cites a specific row must state
"0-based" explicitly, or a reviewer opening the file in Excel will misread it as
the Excel row and land on the wrong line.

**Impact.** All loaders (`load_cgm_file`, `load_summary_file`) capture
`source_row` right after `pd.read_excel()`, before any rename or filtering, so it
reflects original file order.

---

### D-007 — subject (join key) stored as int, parsed from a composite identity string

**Decision.** `subject` — the join key defined in D-001 — is stored as `int` in
both `load_cgm_file` and `load_summary_file`. In both loaders it is obtained by
*parsing* a `SSSS_V_YYYYMMDD` composite identity string, not by casting a plain
number directly.

**Rationale.** Initially assumed `Patient Number` in the summary files was
already a bare patient number, safe to cast straight to `int`. Direct inspection
of both `Shanghai_T1DM_Summary.xlsx` and `Shanghai_T2DM_Summary.xlsx` showed this
was wrong: `Patient Number` actually holds the full `subject_visit_date` string
(e.g. `"1001_0_20210730"`) — the same composite identity encoded in each CGM
filename, not a bare integer. Each row is one patient-visit (matches D-001), and
this column is that row's full identity, not just the subject. So both loaders
need the same split-and-cast logic — one applied to a filename stem, one applied
to a cell value — rather than a plain `int(...)` cast on either side. Once split,
`subject` itself has no leading zeros in either source, so `int` is still the
right dtype for the piece that's actually a number.

**Alternative considered.** String, on the general principle that IDs are safer
as strings. Rejected — no leading-zero risk in this dataset to protect against,
and the two join keys need to match dtype exactly regardless of which is chosen.

**Impact.** `load.py` splits filename-parsing into two functions: `parse_identity(id_string)`,
which does the actual `SSSS_V_YYYYMMDD` split/cast/parse, and `parse_filename(path)`,
a thin wrapper that pulls `.stem` off a `Path` and calls `parse_identity`.
`load_cgm_file` calls `parse_filename` once per file (one identity, broadcast to
every row). `load_summary_file` calls `parse_identity` once per row, since each
row's `Patient Number` cell is its own distinct identity string. Both loaders must
cast `subject` to `int`, or the join between CGM data and Table B will silently
fail to match.

---

### D-008 — 9 CGM header variants confirmed and merged into RENAME_CGM

**Decision.** 9 raw header spellings, found across the 125 CGM files, are mapped
in `RENAME_CGM` to the same canonical target as an already-known header, rather
than treated as separate columns. All 9 were individually confirmed before
merging, not assumed.

**Rationale.** Full-corpus schema fingerprinting (`01_data_audit.ipynb`, cross-checked
by running `apply_rename` against all 125 files) found 5 distinct column-sets, not
1 — `RENAME_CGM` originally only covered the T1DM-file spelling of each column.
The 9 unmapped variants, all from T2DM files, fell into three categories, each
confirmed by a different check before being merged:

1. **Punctuation-only** — `'CSII - bolus/basal insulin (Novolin R  IU...)'`
   (double space, no comma) vs the T1DM spelling `'...(Novolin R, IU...)'`,
   in `2001_0_20201102.xlsx`. Same column, formatting difference — merged on
   inspection alone.
2. **Missing unit suffix** — `'CGM '`, `'CBG '`, `'Blood Ketone '`, `'CSII -
   bolus/basal insulin '` (trailing space, no unit), in `2045_0_20201216.xls`.
   Confirmed same unit, not a silent mmol/L-vs-mg/dl switch, by comparing value
   ranges against normally-labeled files: both files' CGM/CBG values fell in the
   same ~50-390 mg/dl range.
3. **Chinese-only labels for columns that also appear in English elsewhere** —
   `'进食量'` (in place of `'饮食'`) and `'胰岛素泵基础量 (Novolin R, IU / H)'`
   (in place of the English CSII basal header). Confirmed by checking the label
   never coexists with its English counterpart in the same file (one replaces
   the other, not an additional column), and by inspecting cell contents —
   `进食量` held free-text gram-quantity meal entries, the same format expected
   of a dietary-intake field.

**Alternative considered.** Programmatic normalization (strip whitespace/punctuation,
fuzzy-match the Chinese labels) instead of listing each variant explicitly.
Rejected for this dataset size — 125 files is small enough to review every
variant by hand, and the missing-unit and Chinese-label cases needed a semantic
or value-range check, not just string cleanup, which an automated normalization
rule can't safely do on its own.

**Impact.** `RENAME_CGM` has 20 keys mapping to 11 unique target columns (9
duplicate mappings); the assert on line ~74 checks
`len(RENAME_CGM) - len(set(RENAME_CGM.values())) == 9` so this count stays
self-verifying if the dict changes later. Confirmed zero unmapped columns remain
by running `load_cgm_file` across all 125 CGM files with no `KeyError`.

---

### D-009 — Drop `dietary_intake_zh` in `clean.py` — duplicate of `dietary_intake`

**Decision.** `clean.py` drops the `dietary_intake_zh` column from Table A. Only
`dietary_intake` (English) is kept as the dietary-intake field.

**Rationale.** Direct inspection of `Shanghai_T1DM/1006_1_20210209.xlsx` — one of
the files where `Dietary intake` and `饮食` appear as separate columns — showed
both columns have exactly 48 non-null rows, with 100% overlap (every non-null
row in one is non-null in the other, never just one side). Content is a literal
translation, row for row (e.g. `"Marinated egg 23 g\nChicken wing 16 g..."` next
to `"卤蛋23g\n鸡翅16g..."`), including the shared blank-meal placeholder
(`"data not available"` / `"未记录"`). `dietary_intake_zh` (built in `load.py` by
merging the `饮食`/`进食量` spelling variants per D-008) carries no information
beyond `dietary_intake` — it's a genuine duplicate, not a field with distinct
content.

Not independently spot-checked: whether the `进食量` spelling variant (2 files,
per D-008) has the same exact duplicate relationship with `Dietary intake`, or
only `饮食` does. The column-layout audit shows `进食量` also coexists with
`Dietary intake` in those 2 files, the same pattern as `饮食`, so the same
conclusion is assumed to extend — but it hasn't been checked cell-by-cell the
way `饮食` was.

**Alternative considered.** Keep both columns as a translation cross-check.
Rejected — once duplication is confirmed, it adds no analytical value, just an
extra column to carry through every downstream step.

**Impact.** `clean.py` drops `dietary_intake_zh` from Table A. Table A's final
column count is 14, matching what `02_cleaning_pipeline.ipynb`'s Table A
markdown cell already anticipated.

---

### D-010 — CGM/CBG glucose range validation: <30 or >600 mg/dl flagged, not imputed

**Decision.** `clean_cgm` treats any `cgm_mg_dl` or `cbg_mg_dl` reading below
30 or above 600 mg/dl as implausible. The value itself is overwritten to NaN,
and a companion boolean column (`cgm_out_of_range` / `cbg_out_of_range`)
records which rows were flagged, so a flagged NaN stays distinguishable from a
genuine device gap (e.g. the `2029_0` gap under D-0xx, still open).

**Rationale.** Thresholds set from clinical judgment first — severe
hypoglycemia can occur below 60 mg/dl but is implausible below 30 outside
hospitalization; readings above 600 mg/dl are DKA/HHS territory, at the edge
of what's survivable outside intensive care — then checked against the real
data before being finalized. Across all 128,157 CGM readings and 4,019 CBG
readings: the lowest genuine value is 30.6 (`cbg_mg_dl`), the highest is 475.2
(`cgm_mg_dl`) — both comfortably inside the threshold on either end. One
value, 2044.8 mg/dl (`cbg_mg_dl`, subject 2044, file `2044_0_20211101.xls`),
falls far outside it, and numerically resembles the subject ID closely enough
to suggest a transcription error (subject number entered into the glucose
field) rather than a real reading. The threshold catches this one confirmed
error and nothing else, with margin on both sides of the real data's true
range.

**Alternative considered.** A tighter cutoff, or one based on a specific CGM
device's reporting spec. Rejected — no confirmed device model for this
dataset's CGM/CBG source to hang a spec-based cutoff on, and the round-number
cutoff already sits with comfortable margin from every genuine value observed
while still catching the one real error.

**Impact.** `clean_cgm` in `src/clean.py` adds `cgm_out_of_range` and
`cbg_out_of_range` boolean columns and nulls the corresponding value wherever
flagged. Verified against the full 128,170-row `table_a`: 0 CGM readings
flagged, 1 CBG reading flagged (the subject-2044 row above).

---

### D-011 — No range-validation flag for `blood_ketone_mmol_l`

**Decision.** Unlike `cgm_mg_dl`/`cbg_mg_dl` (D-010), `clean_cgm` does not
apply an out-of-range flag to `blood_ketone_mmol_l`. All 58 non-null readings
are left as-is.

**Rationale.** Only 58 non-null ketone readings exist across the whole
cohort; 3 exceed 3.0 mmol/L (4.30, 12.54, 12.90 — the latter two from the same
subject, 2025, close together in time). Unlike the glucose case, an elevated
ketone value isn't physiologically implausible — DKA-range ketones
(>3.0 mmol/L) occur in real, ambulatory T1DM patients, and a value like
12.9 mmol/L likely represents a genuine, clinically significant ketoacidosis
episode captured during the study, not a device or entry error. There's no
corroborating evidence of a transcription error the way subject 2044's
glucose reading had (no numeric resemblance to subject ID or similar tell).
Flagging and nulling these values would risk erasing real clinical signal
rather than catching a mistake.

**Alternative considered.** Apply a 0-3.0 mmol/L range check, same mechanism
as glucose (D-010). Rejected — 3.0 mmol/L is a *clinical* threshold (normal
vs. ketosis), not an implausibility threshold; conflating the two would treat
a real severe finding as if it were bad data.

**Impact.** `blood_ketone_mmol_l` gets no `_out_of_range` column and no NaN
overwrite in `clean_cgm`. A clinical normal/abnormal distinction on this
column, if needed later as a feature, is separate logic from data cleaning
and not part of this decision.

---

### D-012 — CGM gaps flagged with an explicit `cgm_gap` column, never imputed

**Decision.** `clean_cgm` adds a boolean `cgm_gap` column, computed as
`df["cgm_mg_dl"].isna()` at the very start of the function — before the D-010
out-of-range step runs. Gapped readings are flagged and left as NaN; no
interpolation, carry-forward, or fill of any kind.

**Rationale.** An explicit column matches the project rule ("glucose gaps are
flagged, never imputed") more directly than bare NaN, which is
indistinguishable from ordinary missingness to anyone reading `table_a`
without also having found `data/raw/note.txt`. The flag is self-documentation
carried in the data itself. Computing it before the out-of-range step keeps
"missing on arrival" separate from "nulled as implausible by D-010" —
currently zero CGM rows are nulled that way, but that isn't guaranteed to stay
true, and conflating the two would mean the column silently changes meaning
later.

Defining the flag mechanically (`.isna()`) rather than by matching the
specific file is safe here because verification showed the two definitions
select the same rows: 13 NaN CGM readings exist in all of `table_a`, and all
13 are subject 2029, visit 0.

**Alternative considered.** Identify the gap by matching `source_file` and a
timestamp window taken from note.txt. Rejected — produces an identical column
today while hardcoding a filename and a date into the cleaning function, which
then has to be maintained if the dataset revision changes.

**Impact.** `clean_cgm` in `src/clean.py` gains a `cgm_gap` boolean column. 13
of 128,170 `table_a` rows flagged (0.01%), all subject 2029 visit 0,
`source_row` 741–753 (= Excel rows 743–755 per note.txt, consistent +2 header
offset). Gap runs 2021-06-03 09:14:00 → 12:46:00, 3 h 32 min: 13 missed
readings at the trace's 15-minute cadence (195 min) plus one 17-minute
interval at the device changeover (212 min total). `t_after` matches note.txt's
stated 12:46 restart of the replacement device exactly. Subject 2029's trace
otherwise shows 843 intervals of exactly 15.0 min and no negative intervals.

**Scope limit.** This covers gaps present as rows with a null value. Gaps
present as *absent rows* are not detected by `.isna()` and are not addressed
here — open item, to be resolved before any time-denominated metric
(TIR/TAR/TBR) is computed.

---

### D-013 — No gap flag for `cbg_mg_dl` or `blood_ketone_mmol_l` (complements D-012)

**Decision.** `clean_cgm` adds no `cbg_gap` or `blood_ketone_gap` column. Null
values in `cbg_mg_dl` and `blood_ketone_mmol_l` are left as bare NaN,
unflagged.

**Rationale.** A gap flag is only meaningful where the absence of a value
indicates a failure to record something that should have been recorded. That
holds for CGM: the device samples on a fixed 15-minute cadence (843 of 844
intervals in subject 2029's trace are exactly 15.0 min, per D-012), so a null
reading means the device stopped when it was supposed to be running.

It does not hold for the intermittent measurements. `cbg_mg_dl` is null in
124,151 of 128,170 rows (96.9%) — only 4,019 fingerstick readings exist.
`blood_ketone_mmol_l` is null in all but 58 rows (per D-011). These columns are
blank by design: a blank means no fingerstick or ketone test was taken at that
timestamp, which is the normal state of an as-needed measurement, not a device
failure. A boolean column that is `True` on 96.9% of rows carries no
information and invites misreading — someone downstream could reasonably
interpret a `cbg_gap` column as marking *problems* rather than *ordinary
absence*, which is the opposite of what D-012's flag is for.

**Alternative considered.** Add `cbg_gap` and `blood_ketone_gap` for symmetry
with `cgm_gap`, on the grounds that consistent structure across the value
columns is easier to reason about. Rejected — symmetry of *form* here would
misrepresent the *meaning*. The three columns differ in sampling design, and
encoding them identically hides that difference rather than documenting it.

**Impact.** Table A carries `cgm_gap` only. `cbg_mg_dl` and
`blood_ketone_mmol_l` keep bare NaN with no companion flag. Any downstream code
counting CBG or ketone availability must use `.notna()` directly rather than a
flag column.

---

### D-014 — Round CGM timestamps to the nearest minute before resampling

**Decision.** `timestamp` is rounded to the nearest minute (`.dt.round("1min")`)
before `.set_index("timestamp")` runs, ahead of the groupby/resample/asfreq chain.

**Rationale.** Subject 2029's file has ~13 intervals off the true 15-minute
cadence by a few milliseconds (e.g. `09:28:59.985`) — a device that doesn't
report sub-minute precision, so the drift is a float artifact of Excel's
date-serial conversion, not a real timing event. Left unrounded, `asfreq()`
requires exact timestamp matches, so these rows fail to align to the
origin-anchored grid: confirmed 91 real `cgm_mg_dl` readings dropped (832 → 741)
for this subject alone before rounding was applied. Scanned all 125 files:
drift is isolated to this one file — no other subject shows sub-minute noise.

**Alternative considered.** Round to the nearest second. Rejected — also fixes
the drift, but has no defensible precision argument: the device never reported
sub-minute data, so "nearest minute" matches its true resolution and "nearest
second" doesn't correspond to anything real.

**Impact.** `clean_cgm` rounds `timestamp` before `set_index`/`resample` run.
Confirmed scope: subject 2029, visit 0 only — the other 124 files are
unaffected. **Correction, logged after implementation:** rounding alone does
*not* restore the 91 dropped readings as originally claimed here — verified
741 real readings both before and after rounding, unchanged. The 91-reading
loss turned out to have a second, separate cause (see D-015): a real device
swap mid-visit, not sub-second noise. Rounding's actual, verified effect is
narrower — it keeps the `segment` column in D-015 accurate. Without rounding,
the same millisecond drift this decision targets gets misread as 13 extra
phase shifts, splitting subject 2029 into 15 segments instead of the true 2
(confirmed by direct comparison). The full 91-reading restoration is D-015's
result, not this decision's alone.

---

### D-015 — Resample origin restarts at any non-15-minute-multiple gap, not once per visit

**Decision.** Within each `(subject, visit)` group, the resample origin
restarts wherever the gap since the previous reading is *not* an exact
multiple of 15 minutes. A new `segment` column (cumulative count of these
restarts) is added to the groupby, alongside `subject` and `visit`, before
`.resample(..., origin="start")` runs.

**Rationale.** `origin="start"` anchored once per visit assumes the entire
trace runs on one continuous clock from the first reading onward. Subject
2029, visit 0 breaks that assumption: it has a real device swap (D-012's
17-minute gap), and the replacement device samples on its own clock, not
phase-locked to the original device's grid. A single visit-wide origin
therefore misaligns every reading after the swap by 2 minutes, silently
dropping 91 real `cgm_mg_dl` values (832 → 741) — confirmed present even
after D-014's rounding fix, since rounding only removes noise, not a genuine
phase shift.

The fix distinguishes a real phase shift from an ordinary missed reading using
gap size: a missed reading (device stayed on the same clock, just skipped a
beat) always lands on a clean multiple of 15 minutes — 30, 45, 60 — verified
across the 6 subjects with genuine absent-row gaps (2095, 2023, 2080, 2084,
1002 visit 1, 2040). A real phase shift doesn't — 2029's gap is 17 minutes.
Restarting the origin only at non-multiples fixes 2029 without touching the
other 6, verified: rows added by the grid stays at 15 (unchanged), `source_row`
nulls still match exactly, and 2029 recovers all 832 real readings.

**Alternative considered.**
1. Hardcode a second origin for subject 2029 at its known 12:46 restart time.
   Rejected — same reasoning D-012 already rejected once: hardcodes a subject
   ID and timestamp into the cleaning function, breaks on any future dataset
   revision or a different subject with the same kind of swap.
2. Restart the origin at *any* gap over 15 minutes, not just non-multiples.
   Tested and rejected — it also restarts at genuine missed-reading gaps,
   which deletes the blank placeholder row that's supposed to represent the
   missed reading. Confirmed: this version produced 0 rows added by the grid
   instead of 15, silently undoing the absent-row-gap detection for all 6
   other affected subjects.

**Impact.** `clean_cgm` sorts by `["subject", "visit", "timestamp"]`, rounds
`timestamp` (D-014), computes `gap_minutes` per group, flags `is_phase_shift` where
`gap_minutes % 15 != 0`, and cumulative-sums that flag into a `segment` column
per `(subject, visit)`. The resample groupby becomes
`["subject", "visit", "segment"]`. Verified against the full 128,170-row
`table_a`: 15 rows added by the grid (matches the 6 known absent-row gaps,
unchanged from before this fix), `source_row` nulls = 15 (matches exactly),
subject 2029 restored to 832/832 real readings, 2 segments detected for 2029
(matches the 1 documented device swap in D-012).

**Open question, not yet decided:** whether the scaffolding `segment` column
should be dropped before `clean_cgm` returns, or kept as a QC signal (e.g. "how
many device changes occurred during this visit"). Not decided here — separate
call.

---

### D-016 — Strip whitespace across all text columns in Table B; leave multi-value field order unnormalized

**Decision.** `clean_summary` strips leading/trailing whitespace from every
`str`-dtype column (`df.select_dtypes(include="str")`), rather than hand-picking
the columns known to have the problem. Separately, comma-separated multi-value
fields (e.g. `diabetic_macrovascular_complications`) are left with their
original token order — no sorting or normalization applied.

**Rationale.** Whitespace: confirmed real, not cosmetic — several free-text
columns had the same value split into multiple categories purely by stray
spaces (`hypoglycemic_agents` 78→66 distinct values after stripping,
`other_agents` 70→68, `comorbidities` 58→57, `diabetic_macrovascular_complications`
8→7). Stripping every text column rather than only the four affected ones
covers any column that's currently clean but could pick up the same issue in a
future data revision.

Order: after stripping, `diabetic_macrovascular_complications` still has one
row reading `"coronary heart disease, peripheral arterial disease"` and another
reading the same two conditions in reverse — 2 of 125 rows. Left as-is:
the sample impact is negligible, and the standard way to use a multi-condition
field like this for modeling is splitting it into individual per-condition
boolean flags in feature engineering (Phase 4), not treating the full string
as one category. Once split, order is irrelevant by construction — normalizing
it here would fix a problem that correct downstream encoding already avoids.

**Alternative considered.** Sort each cell's comma-separated tokens
alphabetically before storing. Rejected — only matters if the field stays a
single string category, which conflicts with the likely Phase 4 encoding
(individual flags), and isn't worth the code for 2 affected rows.

**Impact.** `clean_summary` in `src/clean.py` strips whitespace across every
`str`-dtype column via `select_dtypes(include="str")`. Verified counts:
`hypoglycemic_agents` 66, `other_agents` 68, `comorbidities` 57,
`diabetic_macrovascular_complications` 7 distinct values, all matching target.
`diabetic_macrovascular_complications` order inconsistency (2 of 125 rows)
is documented, not fixed — revisit only if a future step needs the raw field
as a single category rather than split flags.

---

### D-017 — cgm_gap moved to run after resample, not before (supersedes D-012's ordering)

**Decision.** `cgm_gap` is computed after the resample/segment/`asfreq` step,
not "at the very start of the function" as D-012 originally specified. D-012's
core rule stands unchanged — explicit flag, never impute — only the position
in `clean_cgm` changes.

**Rationale.** D-012 placed `cgm_gap = df["cgm_mg_dl"].isna()` at the top of
`clean_cgm`, before any other processing. At the time there was no resample
step, so `.isna()` could only catch gaps that already existed as blank rows in
the raw file (subject 2029's 13-row device-swap gap) — it could not catch
*absent-row* gaps, where the device produced no row at all. D-012's own scope
limit said as much: "gaps present as absent rows are not detected... open item,
to be resolved before any time-denominated metric is computed." D-014/D-015
built the resample step specifically to turn absent-row gaps into real,
null-valued rows — but only rows that exist *after* resampling can be seen by
`.isna()`. Computing `cgm_gap` before resample would mean every grid-inserted
row silently carries whatever value existed before it was created, missing the
entire class of gap the resample step exists to catch.

**Alternative considered.** Keep `cgm_gap` before resample and add a second
column (e.g. `cgm_gap_absent_row`) for grid-inserted gaps. Rejected — two
columns for the same underlying meaning ("no reading here") adds a distinction
the project doesn't need; `source_row.isna()` already separates "raw blank
row" from "grid-inserted," per D-012's own noted plan for that split.

**Impact.** `clean_cgm` computes `cgm_gap` after the resample/segment block.
Verified against the full pipeline: 28 rows flagged (up from 13 pre-resample)
— 13 are the original subject-2029 blank rows (`source_row` present), 15 are
newly-visible absent-row gaps from the 6 subjects identified in D-015
(`source_row` null). `source_row.isna()` correctly separates the two, exactly
as D-012 anticipated.

---

### D-018 — Relabel uric_acid_mmol_l to uric_acid_umol_l (source header mislabeled)

**Decision.** `clean_summary` renames `uric_acid_mmol_l` → `uric_acid_umol_l`.
Values unchanged — only the column name/unit label changes.

**Rationale.** The raw source header literally reads `'Uric Acid (mmol/L)'`
(confirmed in `load.py`'s `RENAME_SUMMARY` mapping). But the actual data ranges
93.4–564.0, matching the normal reference range for uric acid in µmol/L
(~150–450), not mmol/L (~0.15–0.45) — treating the column as mmol/L, as the
source claims, would be off by roughly 1000x. The numbers themselves look
correct; only the unit label the source file assigned is wrong.

**Alternative considered.** Convert the values (÷1000) to match a "mmol/L"
label instead of relabeling. Rejected — the values already sit correctly
within the µmol/L reference range; converting them would push genuine values
*out* of a plausible clinical range, backwards from the actual problem.

**Impact.** `clean_summary` renames the column; no values changed (verified
via `.equals()` against the pre-rename column). Lives in `clean_summary`, not
`load.py`'s rename mapping — `load.py` faithfully carries the source file's
(wrong) unit label, and the correction is a cleaning-stage judgment call.

---

### D-019 — No flag for high eGFR outliers — treated as a known formula limitation

**Decision.** `egfr_ml_min_1_73m2` gets no range-validation flag and no value
changes. Extreme values (up to 286 ml/min/1.73m2) are left as-is.

**Rationale.** Creatinine and eGFR correlate at -0.79 across the cohort — strong,
and in the expected physiological direction — so the outliers aren't
disconnected from the rest of the data. Every high-eGFR row also has
unusually low creatinine (22.6–43.5 µmol/L vs. a typical adult reference of
~60–110), several paired with low body weight (subject 1010: eGFR 286, 35 kg).
eGFR formulas assume average muscle mass; low creatinine from low muscle mass
inflates the calculated eGFR — a known limitation of creatinine-based
formulas, not a data-entry error. Subject 2069's identical eGFR (178.0) across
all three visits is explained the same way: identical creatinine (32.4) at
every visit produces an identical calculated result, consistent with eGFR
being derived, not separately measured.

**Alternative considered.** Flag values above a threshold (e.g. >200) as
implausible, same mechanism as D-010. Rejected — the values are internally
consistent with the rest of the data and have a defensible clinical
explanation; flagging would treat a known formula limitation as bad data, the
same reasoning D-011 already used for high ketone values.

**Impact.** No code change. Note for later: if this column becomes a Phase 4
model feature, a tree-based model handles this kind of outlier without issue;
a linear/distance-based model would need revisiting.

---

### D-020 — Subject 2035's identical fasting/postprandial insulin left untouched, documented as a suspected transcription error

**Decision.** `fasting_insulin_pmol_l` and `postprandial_2h_insulin_pmol_l`
are left unchanged for subject 2035 (both 2089.8 pmol/L). No value nulled, no
flag added.

**Rationale.** Subject 2035 is the only exact fasting/postprandial insulin
match in the cohort — of 64 subjects with both values present, every other
pair differs (median difference 169.3 pmol/L). The rest of this row looks
clinically normal: glucose rises 133.2 → 330.12 mg/dl, c-peptide rises 0.48 →
0.92 nmol/L, both consistent with a real post-challenge response, so this
isn't a whole-row copy error. Insulin and c-peptide are co-secreted and
normally move together; here c-peptide nearly doubles while insulin stays
exactly flat — evidence against a genuine coincidental match. Reads as a
transcription error, but there's no independent source to confirm which value
(if either) is correct.

**Alternative considered.** Null the postprandial value, treating it as
unmeasured. Rejected for now — nulling asserts the suspicion as fact; with no
way to independently confirm it, that's a bigger claim than the evidence
supports.

**Impact.** No code change. Documented so any future analysis using this
column (Phase 3/4) can weigh this caveat rather than treating the number as
fully reliable.

---

### D-021 — insulin_csii_bolus_r_iu / insulin_csii_basal_r_iu_h text values replaced: suspend-delivery → 0, acarbose → null

**Decision.** In both `insulin_csii_bolus_r_iu` and `insulin_csii_basal_r_iu_h`,
`'temporarily suspend insulin delivery'` is replaced with 0. `insulin_csii_bolus_r_iu`'s
`'acarbose 50 mg'` value is replaced with NaN. Both columns are then cast to
numeric. No flag column added.

**Rationale.** Both are meant to be numeric CSII rate fields; writing `table_a`
to parquet failed because a few text values were mixed into otherwise-numeric
columns, and parquet requires one type per column. `'temporarily suspend
insulin delivery'` appears in both (a paused pump affects bolus and basal
together) and describes a real device state — 0 IU delivered, not a missing
measurement. `'acarbose 50 mg'` names a different, oral medication — reads as
a value entered in the wrong field, not a real CSII dose — nulled rather than
guessed at. No flag column: one-off hardcoded string match, not a reusable
rule (contrast D-010); `source_row`/`source_file` already trace back to the
original cell for anyone checking why a value is null.

**Alternative considered.** A boolean flag column, matching D-010. Rejected —
doesn't generalize to a future case, adds nothing beyond the log plus existing
provenance columns.

**Impact.** `clean_cgm` replaces both text values across both columns, casts
both to numeric with `errors="raise"`. Verified: `table_a_clean.to_parquet(...)`
succeeds end to end; both columns confirmed `float64`.

---

### D-022 — insulin_dose_iv leaked-header value (subject 2027) nulled out

**Decision.** In `insulin_dose_iv`, the single value
`'CSII - basal insulin (Novolin R, IU / H)'` (subject 2027, visit 0,
`source_row` 0) is replaced with NaN. Column stays free text otherwise, no
flag column added.

**Rationale.** Traced to the raw file (`2027_0_20210521.xls`): at that row,
the neighbouring column `insulin_csii_basal_r_iu_h` correctly holds `0.6`, a
plausible basal rate, while `insulin_dose_iv` holds the *English name of that
neighbouring column's header* instead of an IV dose value. This is a data
entry error in the source file, not a `load.py` parsing bug — the header row
and column mapping are both correct. The leaked text is not a real IV dose
under any reading, so it's nulled rather than guessed at, same reasoning as
`'acarbose 50 mg'` in D-021. No flag column: one-off hardcoded match, not a
reusable rule (contrast D-010); `source_row`/`source_file` already trace back
to the original cell.

**Alternative considered.** Leave untouched and only document, matching D-020.
Rejected — D-020's ambiguity (two real numbers, no way to know which is
wrong) doesn't apply here: this value is clearly not IV-dose data under any
interpretation, so nulling it loses nothing.

**Impact.** `clean_cgm` nulls this one value in `insulin_dose_iv`. Column
remains free text (`object`/`str` dtype) — this decision doesn't change its
type, only this one cell's content.

---

### D-023 — GMI vs. HbA1c agreement compared in %, hba1c_mmol_mol converted via IFCC-NGSP master equation

**Decision.** The Phase 3 headline comparison (GMI vs. laboratory HbA1c) runs
in %, not mmol/mol. `gmi_glucose` already outputs % by construction (the
Bergenstal formula is defined to produce %). `table_b_clean`'s
`hba1c_mmol_mol` is converted to % for the comparison, using the standard
IFCC-to-NGSP master equation: `% = (mmol/mol ÷ 10.929) + 2.15`. The
underlying `hba1c_mmol_mol` column itself is untouched — the conversion
happens as a new column/variable local to `04_eda_profiles.ipynb`'s analysis,
not a rename or unit change in `clean_summary`.

**Rationale.** % is the commonly-used unit for HbA1c in clinical practice —
the one a clinical reader expects to see a claim reported in. Converting
`hba1c_mmol_mol` to % is also the smaller change: GMI's formula produces %
natively, so only one side of the comparison needs converting, not both.

**Alternative considered.** Convert GMI to mmol/mol instead, leaving HbA1c as
the source column reports it. Not chosen — GMI's formula is defined in % in
the literature it comes from, so converting it would mean carrying a
non-standard GMI definition just for this one comparison.

**Impact.** `04_eda_profiles.ipynb`'s GMI vs. HbA1c section computes an `hba1c_pct`
value from `hba1c_mmol_mol` before any scatter/Bland-Altman work. `table_b_clean`
and `clean_summary` are unaffected — this is an analysis-stage conversion, not
a cleaning-stage one.

---

### D-024 — Individual-patient discordance threshold is 0.8%, not 0.5%

**Decision.** The headline conclusion about individual-patient GMI-vs-HbA1c
discordance (Phase 3, `04_eda_profiles.ipynb`) is anchored to a 0.8
percentage-point (9 mmol/mol) threshold: a patient's `abs(diff)` above 0.8 is
called discordant. The 0.5-point (5 mmol/mol) threshold is also computed and
reported, but explicitly as context, not as an equally-weighted second
answer — labeled as the looser benchmark, not used to state the conclusion.

**Rationale.** The two thresholds answer different questions and come from
different sources:

- **0.8%** is from Lenters-Westra et al. 2025 (*Diabetic Medicine*,
  "Managing discordance between HbA1c and glucose management indicator"),
  built specifically for this comparison — one lab HbA1c value against one
  CGM-derived GMI estimate, the same structure as this project's
  patient-level `diff`. The paper sets it deliberately wider than 0.5% to
  account for HbA1c's own lab-to-lab analytical noise: their cited EQA
  example shows two labs can both pass quality assessment on the same
  sample and still differ by up to 9 mmol/mol (0.8%). Below that width, a
  GMI-HbA1c gap can't be distinguished from ordinary lab measurement
  variation, not a real disagreement.
- **0.5%** comes from a different context — Little, Rohlfing, and Sacks
  2011 (*Clinical Chemistry*, "Status of hemoglobin A1c measurement and
  goals for improvement"), a clinician's rule of thumb for a *visit-to-visit*
  HbA1c change large enough to justify adjusting therapy. Earlier
  GMI-discordance papers (Perlman, Bergenstal) reused this existing number
  for convenience, not because it was derived for a GMI-vs-lab comparison.

Using 0.5% as the primary threshold here would, by Lenters-Westra's own
reasoning, count some patients as "discordant" when the gap is actually
explainable by routine HbA1c lab noise — overstating the problem with a
threshold built for a different question.

**Alternative considered.** Report both thresholds as equally valid, without
naming a primary. Rejected — presenting them side by side with no distinction
implies they're comparably grounded for this comparison, which they aren't.
Also considered: use only 0.5%, since it's the more commonly cited number.
Rejected for the same lab-noise reason above — it would inflate the reported
discordance rate beyond what's defensible for this specific comparison.

**Impact.** `04_eda_profiles.ipynb`'s discordance section reports both counts
— 92/116 (79.3%) above 0.5%, 78/116 (67.2%) above 0.8% — but the paragraph's
stated conclusion — does GMI pass or fail as an individual-patient HbA1c
proxy — is anchored to the 0.8% figure. The 0.5% figure is kept in the
writeup as context, explicitly flagged as the looser, non-analytically-
grounded comparison.

---

### D-025 — Endpoint stability (guiding question 1) operationalized as split-half agreement within each recording

**Decision.** Guiding question 1 — "which CGM-derived endpoints are stable
enough across a recording to carry a primary endpoint" — is tested as
split-half reliability: for each of the 125 subject-visits, the cleaned CGM
trace is split at its temporal midpoint into a first half and a second half,
each Phase 2 metric (`src/metrics.py`) is recomputed independently on each
half, and the two values per metric per subject-visit are compared.

**Rationale.** The question's own wording is "across *a* recording" —
singular, one continuous trace — not across separate visits. Split-half
directly tests that: does a metric computed on one part of a patient's
recording agree with the same metric computed on another part of the same
recording, the CGM equivalent of splitting one blood draw into two tubes and
checking the assay agrees with itself. It also keeps the full n=125 subject-
visits available, rather than collapsing to the much smaller set of subjects
with genuine repeat visits.

**Alternative considered.** Truncated-duration sensitivity — compute each
metric on the first N days vs. the full recording. Not chosen as the primary
method — it answers a related but different question (does the metric depend
on *how much* data you happened to capture), closer to the "methodological
choices" half of the question than the "across a recording" half. Also
considered: test-retest across the 10 subjects with 2-3 repeat visits — the
most literal repeat-measurement reliability check, but rejected as the
primary approach because only 10 of 112 subjects have a repeat visit at all,
too small a sample to draw a real conclusion from; may still be worth a
labelled, secondary/exploratory look later given how directly it maps to the
question.

**Impact.** `04_eda_profiles.ipynb` §2 splits each subject-visit's cleaned
CGM trace at the midpoint and recomputes metrics on each half via
`src/metrics.py`. Midpoint is by elapsed time (confirmed in session, not yet
written up as its own entry — no real ambiguity once split-half itself was
chosen, see D-025's own rationale). What statistic quantifies "agreement"
between the two halves is D-026.

---

### D-026 — Stability quantified via Intraclass Correlation Coefficient (ICC), not CV% of measurement error

**Decision.** "How stable" each metric is (D-025's split-half comparison)
is quantified using the Intraclass Correlation Coefficient (ICC), not a
simpler CV%-of-measurement-error calculation.

**Rationale.** Two candidate methods were on the table. CV% (spread of the
h1-h2 difference, expressed as a percentage of the metric's typical value)
is simple and reuses mean/std already computed — the same concept as
intra-assay CV from lab work — but only normalizes error against one
reference number, not against how much the cohort itself varies. ICC
instead compares within-patient variability (h1 vs. h2 for the same
patient) directly against between-patient variability (how different
patients are from each other), which is the standard tool in the
reliability/test-retest literature for exactly this kind of question, and
gives a single 0–1 number with established rough interpretation bands.
Chosen over CV% specifically because it's the more defensible, field-
standard choice for a stability claim that has to hold up to a clinical
reader.

**Alternative considered.** CV% of measurement error. Rejected as the
primary method — not wrong, just a smaller claim than ICC makes, and this
project's standard is defensibility over simplicity where the two trade off.
May still be reported alongside ICC for intuition (a %-scale number is
easier to read at a glance) if useful once ICC results are in.

**Impact.** `04_eda_profiles.ipynb` §2's stability table reports ICC per
metric (`icc_table`), computed for all 9 continuous metrics via a one-way
variance-decomposition formula: `bms = k * own_mean.var()`,
`wms = 0.5 * ((h1 - h2) ** 2).mean()`, `icc = (bms - wms) / (bms + wms)`.

**ICC form, resolved.** The one-way form was chosen deliberately over a
two-way "consistency" form. The two-way consistency form would factor out
any *systematic* difference between h1 and h2 before scoring reliability —
appropriate when a fixed offset between two raters/methods is expected and
irrelevant to the question being asked. That doesn't apply here: D-024's
own split-half check on `mean` found a real, systematic +10.7 bias (first
half reads higher than second half, on average, across the cohort), and a
metric that predictably drifts within one recording is still not a stable
endpoint — a clinical reader shouldn't get a free pass on "it's consistently
wrong in the same direction." The one-way form used here folds any such
systematic drift into the reliability penalty rather than excusing it,
which matches what "stable enough to carry a primary endpoint" actually
needs to mean.

**Results (all 125 subject-visits, 9 continuous metrics):** excursion_count
0.878, tbr 0.773, mean 0.703, gmi 0.703, tar 0.680, tir 0.671, cv 0.655, std
0.652, mage 0.618. Using the standard rough interpretation bands (<0.5
poor, 0.5–0.75 moderate, 0.75–0.9 good, >0.9 excellent — band boundaries
sourced from general reliability-literature convention, not independently
verified against a single citation), every metric in this cohort lands
moderate-to-good; none reach excellent. `mage` is weakest, `excursion_count`
strongest. `mean` and `gmi` landed on the identical ICC value (0.703155) —
confirmed mathematically necessary, not a bug: GMI is an affine
transformation of mean glucose (M-004), and ICC as a variance ratio is
invariant under affine transformation of the input.

---

### D-027 — cv_instability_flag's split-half stability not separately tested — inherits from cv_glucose's ICC

**Decision.** `cv_instability_flag` (boolean, CV ≥ 36%) does not get its own
split-half reliability statistic. Its stability is treated as following
directly from `cv_glucose`'s own ICC (0.655, D-026).

**Rationale.** `cv_instability_flag` is a direct threshold applied to
`cv_glucose` — not an independent measurement. ICC itself is built for
continuous data; a binary flag's agreement is normally assessed with a
different statistic (e.g. Cohen's kappa, percent agreement), which would be
new machinery introduced for one derived column. Since the flag adds no
information beyond thresholding a metric that's already been tested, a
separate statistic wasn't judged worth the added complexity.

**Alternative considered.** Compute a binary-agreement statistic (Cohen's
kappa or simple percent agreement between h1's flag and h2's flag)
specifically for `cv_instability_flag`. Not chosen — the flag's derivation
from `cv_glucose` makes a separate test redundant with information already
in hand.

**Impact.** `04_eda_profiles.ipynb` §2's `icc_table` covers the 9
continuous metrics only. `cv_instability_flag`'s stability claim in any
write-up is stated as inherited from `cv_glucose`'s ICC, not independently
measured.

---

### D-028 — ICC ≥ 0.75 is the cutoff for "stable enough to carry a primary endpoint"

**Decision.** A metric is called "stable enough to carry a primary
endpoint" (guiding question 1's own phrase) if its split-half ICC is ≥ 0.75
— the boundary between the "moderate" and "good" bands on the standard
rough interpretation scale (D-026). Against this cohort's results, only
`excursion_count` (0.878) and `tbr` (0.773) clear it. `mean`, `gmi`, `tar`,
`tir`, `cv`, `std`, and `mage` (0.618–0.703) do not — moderate, not
disqualifying, but not strong enough alone to carry a primary endpoint by
this standard.

**Rationale.** The alternative — a ≥0.5 ("moderate or better") cutoff —
would clear all 9 metrics and effectively say nothing, since nothing in
this cohort measured below 0.618. That answers a much weaker question
("is anything unusably noisy") than the one guiding question 1 actually
asks ("which endpoints can carry a primary endpoint"). ≥0.75 was chosen to
match the standard this project already held itself to for the GMI/HbA1c
individual-level claim (D-024's 0.8% threshold was picked specifically
because it was the analytically-grounded, harder-to-clear bar, not the
looser one available) — consistent rigor across both stability claims in
Phase 3, not a stricter bar for one and a looser one for the other.

**Alternative considered.** ≥0.5 cutoff. Rejected for the reason above —
too weak a claim to answer the actual guiding question.

**Impact.** `04_eda_profiles.ipynb` §2's write-up states `excursion_count`
and `tbr` as stable enough to carry a primary endpoint on their own; the
remaining 7 continuous metrics (plus `cv_instability_flag`, inheriting from
`cv`'s ICC per D-027) are not, by this standard — usable descriptively or
in aggregate, but not defensible as a single-number primary endpoint from
one recording alone.

---

### D-029 — T1DM vs. T2DM comparison (guiding question 5) scoped to std, cv, mage only

**Decision.** The T1DM-vs-T2DM glycemic variability comparison
(`04_eda_profiles.ipynb` §3, guiding question 5) compares `std_glucose`,
`cv_glucose`, and `mage_glucose` only — not all 9 continuous Phase 2
metrics.

**Rationale.** The guiding question asks specifically about "glycemic
variability," which in the CGM literature has a standard, narrower meaning
than "every computed metric": SD, %CV, and MAGE. TIR/TAR/TBR describe time
spent in glycemic ranges (control, not variability), and GMI is an
average-glucose proxy (central tendency, not variability) — both answer a
different question than the one guiding question 5 poses. Including them
would drift the comparison away from what was actually asked.

**Alternative considered.** Compare all 9 continuous metrics across the two
groups. Rejected — broader, but not what the guiding question asks;
diagnostic/control metrics like TIR would be presented under a
"variability" heading they don't belong to.

**Impact.** `04_eda_profiles.ipynb` §3 computes and plots T1DM-vs-T2DM
distributions for `std`, `cv`, and `mage` only, per D-003's descriptive-
only, no-p-values framing. Confirmed cohort counts match D-003 exactly:
T1DM 12 subjects / 16 visits, T2DM 100 subjects / 109 visits.

---

### D-030 — K-means phenotyping (guiding question 4) clusters on cv, mage, tar, tbr — mean/gmi/std/tir excluded

**Decision.** The exploratory k-means phenotyping section
(`04_eda_profiles.ipynb` §4, guiding question 4 — "are there distinct
metabolic phenotypes visible in glucose behaviour alone?") clusters on
four features: `cv_glucose`, `mage_glucose`, `tar_glucose`,
`tbr_glucose`. `mean_glucose`, `gmi_glucose`, `std_glucose`, and
`tir_glucose` are all deliberately left out. `cv_instability_flag`
(binary) and `excursion_count` (a count, not a rate) are also excluded,
as neither fits k-means' continuous-distance assumption cleanly.

**Rationale.** Two separate redundancy problems, found in this order:

`mean_glucose` and `gmi_glucose` are a fixed linear transform of each
other (established in D-026: identical ICC, invariant under affine
transformation) — including both would double-weight the same "average
glucose level" axis in the distance calculation without deciding to.
Excluding average level from the feature set entirely, rather than
including `mean_glucose` once, is a scoping decision: phenotypes here are
defined by the *shape* of glycemic control (how much/where glucose
swings, how much time is spent in/out of range) rather than by average
level. Noted explicitly: this scoping is incomplete in practice, since
`tar`/`tbr` are defined against the fixed clinical thresholds 70/180
mg/dL, not each patient's own mean the way `cv_glucose` is — so some
average-level information still leaks into the clustering through those
two even with `mean_glucose` excluded.

A correlation check across the originally-considered six features (`std,
cv, mage, tir, tar, tbr`, all 125 subject-visits) then found real,
measured redundancy among the remaining four, not just a theoretical
concern:

- `tir + tar + tbr = 100.0` exactly, every row — a hard linear
  constraint, not an approximate relationship. `tir`, `tar`, `tbr` are
  therefore two degrees of freedom, not three; `tir` is fully recoverable
  as `100 - tar - tbr` and carries no information the other two don't
  already have. Including all three in Euclidean distance would give the
  "time above/below range" axis roughly 1.5x the weight of any feature
  without this redundancy, purely as an artifact of column count.
- `std` and `mage` correlate at 0.92 — both measure absolute-mg/dL
  variability magnitude, differing mainly in algorithm (simple spread vs.
  qualifying-excursion detection) rather than in what they capture.
  Including both would double-weight that same axis a second way.

Net effect of the original six: roughly 3 independent axes of real
variation (raw variability magnitude, time-above/below-range shape, and
`tbr` largely on its own — it correlates near-zero with `std`/`mage`, the
most independent feature in the set) were being represented by 6 columns,
which would silently overweight the first two axes and underweight
`tbr` — the reverse of what's clinically useful, since hypoglycemia time
is arguably the sharpest signal here. `mage` was kept over `std` because
it's the more specific, episodic-excursion-based metric — the one D-026
already called the most established glycemic-variability measure in the
CGM literature — not just a duplicate of the same "how much spread"
signal. `tar`/`tbr` were kept over `tir` because they're directional
(distinguish hyper- from hypo-glycemic time), where `tir` collapses that
distinction into a single number `tar` and `tbr` can already reconstruct.

**Alternative considered.** Add `mean_glucose` back in as a fifth
feature, making average level an explicit part of what defines a
phenotype. Rejected — chose shape-only clustering. Also considered:
keep all six original features (`std, cv, mage, tir, tar, tbr`).
Rejected once the correlation check above showed real double-counting,
not just a theoretical risk. Also considered: PCA or another automated
dimensionality reduction instead of hand-picking four. Rejected — this
section's own framing requires clusters "described in physiological
terms" (build plan, guiding question 4); PCA components are linear
combinations of the inputs and don't map cleanly onto a single clinical
concept the way "keep mage, drop std" does.

**Impact.** `04_eda_profiles.ipynb` §4's k-means feature matrix is
`[cv, mage, tar, tbr]`. `mean_glucose`, `gmi_glucose`, `std_glucose`, and
`tir_glucose` remain used elsewhere in the notebook (§1's GMI/HbA1c
agreement uses `gmi`/`mean`; §3's T1/T2 comparison uses `std`) but play
no role in the clustering. Scaling method (D-031) and k-selection
(D-032) apply to this four-feature set.

---

### D-031 — K-means features scaled with z-score (StandardScaler), not min-max

**Decision.** The four D-030 clustering features (`cv`, `mage`, `tar`,
`tbr`) are standardized with z-score scaling (subtract each feature's
mean, divide by its own standard deviation) before k-means runs. Min-max
scaling was considered and rejected.

**Rationale.** K-means clusters on raw Euclidean distance, which requires
comparable feature scales — non-negotiable for a distance-based method,
same category of requirement as not feeding a model a leaked label. Which
*scaling method* is the real choice, and it was checked against this
cohort's actual distribution rather than assumed: an IQR outlier check
(run when six candidate features were still under consideration, before
D-030 narrowed to four) found `tbr` heavily skewed (median 0.49, tail out
to 67.25, 17 of 125 visits flagged as outliers), with `tar` and `mage`
each showing a couple of outliers too. Min-max anchors its 0–1 range to a
feature's single min and max, so `tbr`'s one extreme value (67.25) would
become "1.0" and compress the 100+ typical patients (clustered between 0
and 2) into a tiny sliver near 0 — erasing real variation among typical
patients on that feature. Z-score is nudged by outliers too, but doesn't
hard-anchor the whole scale to one point the way min-max does, and is the
field-standard default for k-means generally.

**Alternative considered.** Min-max scaling. Rejected for the `tbr`
compression failure above. Also considered, and explicitly not chosen:
log-transform or robust/median-based scaling to address `tbr`'s skew more
directly — z-score alone does not fully resolve it. Not pursued because
this section is exploratory (D-003/D-030), not a headline claim; the
added preprocessing complexity isn't justified by what this analysis is
claiming. Logged as a disclosed limitation instead of solved.

**Impact.** `04_eda_profiles.ipynb` §4 applies `StandardScaler` (or
equivalent manual z-score) to the four D-030 features before k-means.
Write-up for this section must disclose that `tbr`'s skew is not fully
corrected by z-score alone — clusters may still be influenced by its
long tail.

---

### D-032 — K selected via silhouette score, not the elbow method

**Decision.** The number of clusters (*k*) for the D-030/D-031 k-means
phenotyping is chosen by running k-means across a range of candidate *k*
values, computing the average silhouette score for each, and selecting
the *k* that maximizes it. The elbow method (within-cluster sum of
squares vs. *k*, read for a bend) was considered and not used as the
primary method.

**Rationale.** Both methods are standard for choosing *k*; the difference
is how much subjective judgment each requires. Elbow needs a visual call
about where a curve's "bend" is, which is genuinely ambiguous on a small,
noisy cohort (125 subject-visits, several with meaningful skew per
D-031) — the flattening point can be read differently by two people
looking at the same plot. Silhouette produces one explicit number per
candidate *k*, directly comparable, removing that ambiguity.

The statistic is the *first* check, not the only one. Per the build
plan's own framing for this guiding question — phenotypes "described in
physiological terms" — whichever *k* silhouette selects still has to be
validated by looking at what the resulting clusters actually look like
clinically (e.g., does a cluster read as "high and swingy," is it mostly
one diabetes type) before being treated as a real finding, the same
physiology-first check D-019 applied to the eGFR outliers rather than
trusting a formula's output blindly.

**Alternative considered.** Elbow method — rejected as primary for the
subjectivity reason above; could still be plotted alongside as a visual
cross-check, not as the deciding method. Also considered: compute both
and require agreement between them before trusting a *k*. Not adopted as
a hard rule, but the physiological sanity-check step above serves a
similar cross-checking purpose.

**Impact.** `04_eda_profiles.ipynb` §4 runs k-means for a candidate range
of *k* (e.g. 2–8) on the D-031-scaled features, computes mean silhouette
score per *k*, and selects the maximizing value. The chosen *k*'s
clusters are then described in physiological terms (mean/behavior per
cluster, diabetes-type composition) before any claim is made about
distinct phenotypes.

**Addendum, added same session.** Silhouette (and the clustering itself)
is computed on all 125 subject-visits, but 10 of the 112 subjects
contribute 2–3 visits each (23 of 125 rows are repeat visits from the
same person, not independent draws — same non-independence D-002 already
accounts for in Phase 4's cross-validation design). A subject's repeat
visits will tend to land in the same cluster simply because they're the
same physiology measured twice, which can make clusters look tighter/
more separable than they would on genuinely independent data. Added as a
robustness check, not a change to the primary method: after selecting
*k* and fitting the final clustering on all 125 rows, rerun on a
reduced one-visit-per-subject set (112 rows) and confirm the same *k*
and broadly the same cluster shapes hold up. **Resolved:** the reduced
set keeps each subject's first visit only (by `visit` number/earliest
`recording_date`) — deterministic and reproducible without a random
seed, appropriate for a secondary robustness check rather than the
primary analysis. Random-per-subject and averaging-across-visits were
the alternatives on the table; not chosen, for simplicity given this is
a supporting check, not the headline method.

---

### D-034 — k=3 chosen over silhouette-argmax k=2, which failed the physiological check

**Decision.** The k-means phenotyping (§4) uses **k=3**, not k=2 — the
value that actually maximized silhouette score (0.744 vs. 0.425 at
k=3). D-032 already built in a physiological sanity check on top of the
raw statistic; this decision records that the check was applied, it
failed for k=2, and k=3 (the next candidate down) was substituted
instead.

**Rationale.** k=2 produced a 124-vs-1 split. The lone member of the
second "cluster" is subject 2077, visit 0 — whose `tbr` (67.25) is the
single highest value in the entire 125-row cohort (rank 125/125), the
same extreme point D-031 already flagged as a risk when it noted
z-score alone doesn't fully correct `tbr`'s skew. A cluster of one isn't
a phenotype; it's an outlier that k-means and silhouette both have a
structural bias toward isolating — a lone point has ~zero within-cluster
distance and maximal between-cluster distance, which inflates silhouette
regardless of whether the split means anything. Confirmed this wasn't a
one-off: re-running k=2 through k=8 showed silhouette scores dropping
sharply after k=2 (0.744 → 0.425 → 0.412 → ...) and k=8 also produced a
singleton cluster — the statistic keeps rewarding outlier-isolation
whenever it's available as an option.

k=3, by contrast, produced three interpretable, non-degenerate groups:
a well-controlled cluster (n=72, low on all four features), a
poorly-controlled/hyperglycemia-leaning cluster (n=49, high mage/tar,
low tbr), and a small hypoglycemia-prone cluster (n=4, high tbr, low
tar — including subject 2077, no longer isolated, now grouped with 3
physiologically similar patients). That third cluster splits evenly
across diabetes type (2 T1DM, 2 T2DM) — a phenotype grouping that cuts
across the existing diagnostic label, which is the actual thing guiding
question 4 asks about ("phenotypes visible in glucose behaviour alone"),
and exactly the kind of result k=2 hid entirely.

**Alternative considered.** Take k=2 as-is, since it's what the stated
method (D-032, silhouette-argmax) literally selects. Rejected — D-032's
own text says the statistic is "the first check, not the only one" and
requires the resulting clusters to be validated physiologically before
being trusted; a 124-vs-1 split fails that validation outright, so
taking it anyway would mean writing D-032's own safeguard and then
ignoring it. Also considered: fix the root cause instead of overriding
the k choice — cap/transform `tbr` before scaling (revisiting D-031) so
the outlier can't dominate distance in the first place, then re-run
silhouette selection fresh. Not chosen for this pass — bigger
intervention than an exploratory section needs, and D-031 already
disclosed this exact risk rather than claiming to have solved it; k=3
resolves the practical problem (a usable, interpretable clustering)
without reopening the scaling decision.

**Impact.** `04_eda_profiles.ipynb` §4's final k-means fit uses
`n_clusters=3`. Cluster composition (means per feature, diabetes-type
counts) is reported in the section's interpretation, including the
cross-diagnosis hypoglycemia-prone cluster as the section's most
notable exploratory finding. **Resolved, same session:** the repeat-visit
robustness check (D-032's addendum) was re-run against k=3 on the reduced
112-subject (one-visit-each) set — all three cluster shapes and their
approximate proportions reproduced closely (well-controlled 57.1%,
hyperglycemia-leaning 40.2%, hypoglycemia-prone 2.7%, vs. 57.6%/39.2%/3.2%
on the full 125-row set), and the cross-diagnosis mixing in the smallest
cluster survived — the structure isn't an artifact of the 10 subjects
contributing repeat visits.

---

### D-035 — Phase 4 model runs diabetes_type as an ablation (clinical-only vs. clinical+CGM+type), not a fixed include/exclude choice

**Decision.** The hypoglycemia risk model (Phase 4) does not simply
include or exclude `diabetes_type` as a feature. It is compared across
(at least) two feature sets: clinical + CGM features without
`diabetes_type`, and the same set with `diabetes_type` added.

**Rationale.** `diabetes_type` is close to a direct proxy for the label
in this cohort: T1DM is 14/16 visits (87.5%) hypoglycemia-positive,
T2DM is 10/109 (9.2%) — confirmed directly from `table_b_clean`, same
pattern L-008 flagged earlier from the raw summary sheets. A model
given `diabetes_type` can likely score well by mostly re-deriving "is
this patient T1DM" rather than learning the clinical/glucose drivers
the guiding question actually asks about ("what clinical and glucose
features predict hypoglycemia"). Excluding it outright would lose real
information too — diabetes type is a legitimate clinical variable, not
a data leak in the sense D-005 uses the term. Running both keeps the
model honest about which result is which: what performance
near-free diagnosis information buys, reported separately from what
the harder within-type signal buys.

**Alternative considered.** Include `diabetes_type` as an ordinary
feature, no ablation. Rejected — SHAP would very likely surface it as
the dominant driver, and the write-up would end up saying little about
actual clinical risk factors. Also considered: exclude it entirely.
Rejected — discards a genuine clinical predictor for the sake of a
cleaner-looking model.

**Impact.** `05_modeling.ipynb` fits and evaluates the model at least
twice — once on clinical+CGM features without `diabetes_type`, once
with it added — and reports both side by side rather than picking one
silently.

---

### D-036 — insulin_dose_sc parsed as a Phase 4 feature; insulin_dose_iv deferred

**Decision.** `insulin_dose_sc` (subcutaneous insulin injections, free
text like `"Novolin R, 4 IU"`) is parsed into a per-visit numeric
feature for Phase 4. `insulin_dose_iv` (IV insulin, free text like
`"500ml 0.9% sodium chloride, 12 IU Novolin R, 10 ml 10% potassium
chloride"`) is left out of the v1 model.

**Rationale.** `insulin_dose_sc` covers 67 of 125 visits (54%) — the
injection log for patients on multiple daily injections rather than a
CSII pump — and insulin dose is one of the more directly mechanistic
drivers of hypoglycemia available in this dataset, worth the parsing
effort. `insulin_dose_iv` covers only 10 of 125 visits (8%) and reads
as a fixed inpatient DKA-management infusion recipe (glucose/saline +
potassium chloride + insulin) rather than routine dosing — lower
expected value for a first modeling pass, and too rare for a model to
learn much from regardless.

Both columns log doses on the same CGM timeline the hypoglycemia label
covers, which raises the same association-vs-prediction caveat D-005
already flagged for CGM-derived features generally — sharing a
recording window with the label means a feature can be concurrently
associated without being genuinely predictive. This cuts sharper here
than for routine glucose metrics: an insulin dose logged shortly
before a recorded hypo event is close to circular. Mitigated, not
solved, by aggregating `insulin_dose_sc` to a per-visit summary rather
than reading-level detail — flagged for the Phase 4 write-up.

**Alternative considered.** Parse and use both columns. Rejected for
now — `insulin_dose_iv`'s coverage and acute-care framing make it
lower priority; revisit as a second pass if the v1 model needs more
signal. Also considered: defer both. Rejected — `insulin_dose_sc`'s
coverage and clinical relevance are too central to a hypoglycemia
model to skip in the first pass.

**Impact.** Feature engineering (`src/features.py`, Phase 4) will parse
`insulin_dose_sc` into drug name + IU dose, aggregated per
subject-visit — exact aggregation (total daily dose vs. injection
count vs. something else) not yet decided, to be resolved when
`features.py` is drafted. `insulin_dose_iv` is left untouched, not
used as a Phase 4 feature; no change to `clean.py`.

---

### D-037 — GMI-HbA1c disagreement reported as proportional, not flat, bias

**Decision.** The §1 GMI vs. HbA1c agreement finding is characterized
as a *proportional* bias — the gap between GMI and lab HbA1c widens as
glucose level rises — not as a single flat average (-2.31%) applying
uniformly across the range. The flat bias/LoA numbers from D-023/D-024
(n=116, bias -2.31%, LoA -6.79 to +2.16%) are kept and still reported,
but framed explicitly as a cohort average that masks range-dependent
behavior, not as the headline claim standing alone.

**Rationale.** Regressing the GMI-HbA1c difference against laboratory
HbA1c gave slope -0.87, r=-0.96, p≈1.6×10⁻⁶³ (n=116) — strong and
highly significant. Checked for mathematical coupling (the standard
critique of Bland-Altman's mean-of-two x-axis) by rerunning against
HbA1c alone instead of the pair mean; the pattern held and got
stronger, ruling that out as the explanation. Checked whether it was
outlier-driven: HbA1c > 8% is 67 of 116 patients (58%, not a rare
tail); quintile-binned mean diff moves smoothly from -0.31 to -6.03
points across the range with no single bin doing all the work; the
slope survives (though weaker) even restricted to HbA1c ≤ 8% alone
(slope -0.35, p=0.0019). Likely mechanism: GMI is a fixed linear
transform of mean CGM glucose, and a linear transform of one variable
can't spread out more than that variable does — GMI's std (0.73) is
roughly a third of lab HbA1c's (2.51) across this cohort, so GMI is
structurally compressed and can't represent the full range of
glycemic control lab HbA1c can, especially at the severe end.

**Alternative considered.** Report only the flat bias/LoA, as
originally written. Rejected — it states an average as if it were the
answer everywhere, when the disagreement demonstrably depends on where
a patient sits in the range. Also considered: compute regression-based
(non-constant-width) limits of agreement, the standard Bland-Altman
extension for exactly this situation. Not pursued — bigger statistical
machinery than this section needs; reporting the regression
slope/r/p alongside the existing flat bias is honest about the pattern
without it.

**Impact.** `04_eda_profiles.ipynb` §1 gains two new code cells (the
two `linregress` checks) and a rewritten interpretation cell. The hero
figure (§5) is the same underlying scatter, so its write-up should
carry the same caveat once §5 is drafted — not resolved by this entry.

---

### D-038 — insulin_dose_sc aggregated as dose/day (Total Daily Dose framing); injection count kept as a secondary feature

**Decision.** `insulin_dose_sc` is aggregated to one primary per-visit
feature: total parsed IU summed across the visit, divided by the
visit's monitored duration in days — i.e. average daily insulin dose,
the Total Daily Dose (TDD) concept from diabetes management.
Injection count (how many `insulin_dose_sc` entries were logged in the
visit) is kept as a second, secondary feature alongside it, not as a
replacement.

**Rationale.** TDD is the standard clinical framing for insulin
regimen intensity and hypoglycemia risk — physicians size a regimen
and judge whether it's aggressive relative to a patient's needs in
these terms, and higher TDD (especially relative to body weight) is a
recognized hypoglycemia risk marker in the literature. Raw total dose
summed across the whole visit was rejected as the primary feature
because it conflates *how much insulin* with *how long the visit
happened to run* — a 5-day recording accumulates more total IU than a
1-day one on an identical regimen, a visit-length artifact rather than
a real difference in risk. Dividing by visit duration removes that
artifact. Injection count alone was rejected as a standalone primary
feature because it discards dose size entirely — 3 injections of 2 IU
each and 3 injections of 20 IU each are different risk profiles that a
count can't distinguish — but it isn't dropped outright, since dosing
frequency (more injections, more chances for timing error or dose
stacking) is a real, separate mechanism from dose size, not fully
redundant with it.

**Alternative considered.** Raw total dose per visit (no time
normalization). Rejected for the visit-length confound above.
Injection count as the sole feature. Rejected — loses the mechanistic
link between dose size and hypoglycemia risk. Both considered as
equally-weighted primary features with no secondary/primary
distinction — not chosen, since dose/day is the one with the direct
clinical-concept mapping (TDD) and should carry the interpretation
weight.

**Impact.** `src/features.py` will compute a per-subject-visit dose/day
feature from `insulin_dose_sc` (drug name + IU, D-036) plus a separate
injection-count feature. Two mechanics remain open, to be resolved
when `features.py` is actually drafted, not decided here: how visit
duration in days is computed (basis: first-to-last CGM timestamp for
that subject-visit), and the free-text parsing problems already found
in this column — typos (`insulin glarigine`), multi-drug single-cell
entries (`insulin glargine, 14 IU, Humulin 70/30`), and rows that don't
match the `"drug, N IU"` pattern at all (17 of 1,199 non-null rows,
e.g. `'Humulin 70/30  8 IU'` with a missing comma).

---

### D-039 — Visits with no insulin_dose_sc entry get insulin_dose_per_day = 0, not NaN; 5 visits with no medication data at all flagged as a caveat

**Decision.** For the 58 of 125 subject-visits with zero `insulin_dose_sc`
entries in `table_a_clean`, `insulin_dose_per_day` (D-038) is set to `0`,
not `NaN`. 5 of those 58 visits — the ones with no entry in *any*
diabetes-medication column at all — are flagged as a documented caveat
on this choice, not resolved differently.

**Rationale.** Checked what the 58 "blank" visits actually have instead
of just assuming missingness: 13 are on a CSII pump (`insulin_csii_bolus_r_iu`
and/or `insulin_csii_basal_r_iu_h` populated — SC insulin genuinely
doesn't apply, they're dosed a different way), and 49 have
`non_insulin_hypoglycemic_agents` entries (managed on oral agents,
genuinely no SC insulin). Together that accounts for 53 of the 58 (some
overlap) — for these visits, a blank `insulin_dose_sc` is a real
clinical fact (not on SC insulin), not a gap in recording, so `0` is
the correct value, not "unknown." Only 5 of 125 visits (4%) have
nothing recorded across `insulin_dose_sc`, CSII, `insulin_dose_iv`, or
`non_insulin_hypoglycemic_agents` — for those, `0` could mean "genuinely
on no diabetes medication" or "medication data simply wasn't captured
for this visit," and there's no way to tell which from what's in the
file. Small enough a slice (4%) not to let it dictate the design of the
whole column — treated as a documented caveat rather than a reason to
default the whole column to `NaN`, the same proportionality D-020 used
for the subject 2035 insulin duplicate.

**Alternative considered.** Default all 58 to `NaN`. Rejected — would
mark 53 genuinely-zero visits as unknown, which is a worse
misrepresentation than the actual gap (5 visits, 4%) the `NaN` framing
was meant to protect against. Also considered: try to resolve the 5
ambiguous visits individually (e.g. check `diabetic_macrovascular_complications`
or other chart fields for a hint). Not pursued — no clear independent
signal identified yet; left as an open, named caveat instead of an
unsupported guess.

**Impact.** `src/features.py`'s `build_insulin_features` fills
`insulin_dose_per_day` and `insulin_injection_count` with `0` (not
`NaN`) for subject-visits with no `insulin_dose_sc` entries. The 5
ambiguous subject-visits (no entry in `insulin_dose_sc`, CSII, IV, or
non-insulin agent columns) are noted in the feature-table docstring/
write-up as a disclosed limitation on this column, not resolved
further at this time.
