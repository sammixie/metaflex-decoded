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
