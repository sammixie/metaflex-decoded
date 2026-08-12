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

**Decision.** `date` is rounded to the nearest minute (`.dt.round("1min")`)
before `.set_index("date")` runs, ahead of the groupby/resample/asfreq chain.

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

**Impact.** `clean_cgm` rounds `date` before `set_index`/`resample` run.
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

**Impact.** `clean_cgm` sorts by `["subject", "visit", "date"]`, rounds `date`
(D-014), computes `gap_minutes` per group, flags `is_phase_shift` where
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
