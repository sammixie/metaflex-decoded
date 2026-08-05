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
