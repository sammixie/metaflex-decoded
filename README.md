# MetaFlex Decoded

**An audited pipeline from raw CGM files to defensible glycemic endpoints — plus a hypoglycemia-risk model.**

> **Status:** in progress — week 1 of 12. Sections marked `[[ PLACEHOLDER ]]` are not yet built. Live demo lands in week 10.

MetaFlex Decoded turns raw continuous-glucose-monitor recordings from a 100+ patient diabetes cohort into the clinical endpoints an evidence package actually reports — Time in Range, glycemic variability, GMI — with every metric definition versioned, unit-tested, and traceable back to the raw reading.

🔗 **Live dashboard:** [metaflex-decoded.streamlit.app](https://metaflex-decoded.streamlit.app/)
📊 **Findings report:** `[[ PLACEHOLDER — reports/findings.md, Phase 6 ]]`
🧪 **Test suite:** `pytest tests/` — `[[ PLACEHOLDER — n tests on metrics.py, Phase 2 ]]`

`[[ PLACEHOLDER — hero figure: one patient's CGM trace with range bands and TIR/CV/GMI cards. Phase 3. ]]`

---

## Why this project exists

CGM data is easy to plot and hard to report. The moment a glucose number leaves an app and enters a clinical claim — a study endpoint, a payer submission, a label — three questions get asked that a notebook cannot answer:

1. **What exactly is this number?** Time in Range computed on a 15-minute grid is not the same number as Time in Range computed on raw irregular timestamps. Both are "TIR."
2. **What happened to the gaps?** A sensor swap mid-recording leaves a hole. Impute it and the variability metrics quietly change. Drop it and the denominator changes.
3. **Can you get back to the source?** If someone challenges a value, can you trace it to a specific reading in a specific raw file?

I spent three years as a clinical research coordinator answering versions of those questions for trial data — including a multi-site study run with Yale — before I wrote a line of this code. This project is what happens when you build a CGM analytics pipeline with those questions assumed from the start rather than bolted on afterwards.

**Metabolic flexibility** — how well a person absorbs a glucose load and returns to baseline — is the through-line. It's the thing the standard metrics are all circling, and it's why this dataset is worth the work.

---

## Questions this project answers

**Pre-specified** — fixed before any modelling:

1. Which CGM-derived endpoints are stable enough across a recording to carry a primary endpoint, and which move too much with methodological choices to be trusted?
2. Does CGM-derived GMI agree with laboratory HbA1c — and where does it diverge? *(Agreement, not correlation: Bland–Altman, with limits of agreement.)*
3. What clinical and glucose features predict hypoglycemia, and how does the model behave at a threshold chosen around real cost — a missed hypo versus a false alarm?

**Exploratory** — findings here are hypothesis-generating, not conclusions:

4. Are there distinct metabolic phenotypes visible in glucose behaviour alone, independent of diabetes type?
5. How does glycemic variability differ between T1DM and T2DM patients, and does the difference survive the small T1DM sample?

---

## Data

Shanghai T1DM & T2DM continuous glucose monitoring dataset.

`[[ PLACEHOLDER — full citation to the Scientific Data paper, DOI, and licence. Phase 0. ]]`

**Two layers, joined into one analysis table.**

| Layer | Grain | Contents |
|---|---|---|
| Summary sheets | one row per patient-visit | 33 clinical columns — demographics, diabetes type and duration, complications, medications, labs (HbA1c, C-peptide, lipids, renal function), and a hypoglycemia flag. T2DM ≈ 100 patients, T1DM ≈ 12 |
| Per-patient CGM files | one reading per ~15 min | glucose, fingerstick CBG, blood ketone, dietary intake, insulin and non-insulin dosing |

**Known data issues, all handled explicitly and documented rather than silently cleaned:**

- Mixed `.xls` / `.xlsx` formats across files
- Bilingual and duplicated column headers
- Appended junk rows in some files
- Patient 2029_0: missing CGM values from a device swap; readings resume 2021-06-03 12:46
- Patient IDs encode visit number (`2001_0`, `2001_1` = same person, two visits) — so rows are **not** independent, which matters for cross-validation

Every one of these is a decision point, and every decision is recorded in [`docs/data-decisions.md`](docs/data-decisions.md).

Raw data is not included in this repository. Download it from the source above and place it in `data/raw/`.

---

## What this would take in a regulated setting

The pipeline in this repo is a portfolio build on a public dataset. If its outputs fed a clinical evidence package — a DiGA submission, a device claim, a trial endpoint — here is what would have to be true, and where this repo stands.

| Requirement | Why it matters | Status |
|---|---|---|
| **Versioned metric definitions** | "TIR" is not a definition. Sampling grid, range boundaries, and gap handling all change the number. A submission has to state which variant it used and stay on it. | Planned — Phase 2. Will live in `src/metrics.py` docstrings and [`docs/metric-changelog.md`](docs/metric-changelog.md) |
| **Traceability to source** | Any reported value must be walkable back to a raw reading, or it cannot survive a query. | Planned — Phase 1. `raw → interim → processed` one-directional; each processed row to carry source file and row index |
| **Documented missing-data strategy** | Imputing glucose invents physiology. Flagging it shrinks the denominator. Either is defensible; silently doing one is not. | Planned — Phase 1. Intent: flag gaps, never impute; rationale in [`docs/data-decisions.md`](docs/data-decisions.md) |
| **Pre-specified vs. exploratory analysis** | A finding discovered while browsing and a finding tested against a stated hypothesis carry different weight. Mixing them is how portfolios and submissions both lose credibility. | Done — questions 1–3 fixed before any modelling; 4–5 labelled exploratory |
| **Reproducibility from a clean state** | If it only runs on your laptop, it isn't evidence. | Planned — Phase 6. Pinned `requirements.txt`, clean-clone run, `pytest` on metric functions |
| **Audit trail** | Someone must be able to see what changed, when, and why. | In progress — meaningful commit history; no silent data edits; all cleaning in code, never by hand in Excel |

**What is deliberately *not* here:** validation to GxP standard, formal QMS documentation, a data management plan, or independent review of the statistical analysis. Those are organisational processes, not repository features, and claiming otherwise would be the exact overreach this section exists to avoid.

---

## Results

### Cohort and data quality
`[[ PLACEHOLDER — Phase 1. Patients retained vs. excluded and why; recording days per patient; % of expected readings present; the device-swap case handled. Attrition table. ]]`

### CGM metrics
`[[ PLACEHOLDER — Phase 2/3. Distribution of TIR, TBR, TAR, CV, GMI, MAGE across the cohort. Note CV ≥ 36% as the instability threshold and how many patients cross it. Figure: metric distributions by diabetes type. ]]`

### GMI vs. laboratory HbA1c
`[[ PLACEHOLDER — Phase 3. Bland–Altman with bias and limits of agreement. State plainly where the two disagree and what that implies for anyone reporting GMI as a proxy endpoint. This is the headline figure. ]]`

### Metabolic phenotypes *(exploratory)*
`[[ PLACEHOLDER — Phase 3. Clustering on glucose behaviour alone. Describe clusters in physiological terms — dawn phenomenon, postprandial excursion size, overnight stability — not just cluster IDs. ]]`

### Hypoglycemia risk model
`[[ PLACEHOLDER — Phase 4. Baseline to tuned model. Report PR-AUC and recall at the chosen threshold, not accuracy; state the class balance. Confusion matrix at the operating point. SHAP summary and 2–3 sentences on whether the drivers are physiologically sensible. ]]`

**Threshold choice:** `[[ PLACEHOLDER — Phase 4. State the operating point and justify it in cost terms: what a missed hypoglycemic episode costs versus what a false alarm costs. Say who should own that decision in a real product — a clinician, not a data scientist. ]]`

---

## Threats to validity

Written in trial language, because that is how these have to be assessed.

- **Sample size.** T1DM n ≈ 12. Any T1 vs. T2 comparison is descriptive, not inferential. `[[ confirm final n, Phase 1 ]]`
- **Single-centre, retrospective.** One Shanghai cohort. Nothing here generalises to a European population, a different CGM device, or a non-diabetic population.
- **Non-independent observations.** Repeat visits from the same patient. `[[ PLACEHOLDER — how this was handled in cross-validation, Phase 4 ]]`
- **Class imbalance.** Hypoglycemia is the minority class. `[[ PLACEHOLDER — state the rate, Phase 4 ]]`
- **No external validation.** The model has never seen a second cohort. Reported performance is an upper bound.
- **Outcome definition.** The hypoglycemia flag comes from the summary sheet, not from an adjudicated event definition. A trial would pre-specify and adjudicate this.
- **Device heterogeneity.** `[[ PLACEHOLDER — any sensor differences across patients, Phase 1 ]]`

---

## Extension: post-listing real-world evidence

Evidence generation does not stop at approval. Manufacturers of reimbursed digital therapeutics in Germany continue to publish real-world analyses of their user base after listing, alongside their randomised trial results.

This pipeline is one step from that shape of work. What would change:

- The unit of analysis moves from patient-visit to **user-episode**, with irregular start dates and heavy dropout
- **Attrition becomes a primary result**, not a footnote — who stops using the product and when
- Metrics get computed **repeatedly over time** per user rather than once, so the pipeline runs on a schedule instead of on demand
- Comparison is against a **pre-post baseline or an external benchmark**, not a randomised control, with all the confounding that implies

`[[ OPTIONAL, buffer weeks — a simulated longitudinal version of the pipeline to demonstrate this, only after the core is solid. ]]`

---

## Repository structure

```
metaflex-decoded/
├── README.md
├── requirements.txt
├── data/
│   ├── raw/          # never edited; not in this repo
│   ├── interim/      # cleaned per-patient parquet
│   └── processed/    # final modelling table, one row per patient-visit
├── notebooks/
│   ├── 01_data_audit.ipynb
│   ├── 02_cleaning_pipeline.ipynb
│   ├── 03_cgm_metrics.ipynb
│   ├── 04_eda_profiles.ipynb
│   └── 05_modeling.ipynb
├── src/
│   ├── load.py       # read and normalise one patient file
│   ├── clean.py      # gaps, resampling, device-change handling
│   ├── metrics.py    # TIR, TBR, TAR, CV, GMI, MAGE, excursions
│   └── features.py   # build the patient-level modelling table
├── dashboard/
│   └── app.py        # Streamlit app
├── docs/
│   ├── data-decisions.md    # every cleaning decision and its rationale
│   └── metric-changelog.md  # versioned metric definitions
├── reports/
│   ├── figures/
│   └── findings.md
└── tests/            # pytest on metrics.py
```

## Running it

```bash
git clone [[ PLACEHOLDER — repo URL ]]
cd metaflex-decoded
pip install -r requirements.txt
[[ PLACEHOLDER — data download step, Phase 0 ]]
pytest tests/
streamlit run dashboard/app.py
```

`[[ PLACEHOLDER — expected runtime for a full pipeline run, Phase 6 ]]`

---

## Skills demonstrated

**Technical**
Python · pandas · numpy · scikit-learn · XGBoost · SHAP · matplotlib / plotly · Streamlit · pytest · Git · parquet
Messy multi-file ingestion at scale · time-series resampling and gap handling · two-layer data joins · domain-specific feature engineering · imbalanced classification with stratified CV and PR-AUC · model interpretability · unsupervised phenotyping · deployment

**Clinical and regulatory**
Clinical trial coordination, including a multi-site study run with Yale · protocol and IRB submission · GCP-governed clinical data handling · source data verification and discrepancy resolution at source · CTMS (OnCore) · cross-disciplinary medical device development, translating clinical requirements into technical specifications

The second block is why the first block is worth reading. Most people who can build this pipeline have never had to defend a data point to a monitor. Most people who have, cannot build the pipeline.

---

## Who built this

Sammi Hsieh — registered nurse, then clinical research coordinator in the Urology Department at National Taiwan University Hospital, coordinating trials and medical device development including a multi-site study with Yale University. Named recipient of the 22nd National Innovation Award (Academic Research Category, 2025) for a water-soluble film urethral catheter developed with NTUH's Department of Chemical Engineering; the programme resulted in US Patent 12,636,465.

Now building the data half.

`[[ PLACEHOLDER — LinkedIn URL and contact email, Phase 6 ]]`

---

## Data citation

`[[ PLACEHOLDER — full citation, DOI, and licence for the Shanghai T1DM/T2DM dataset. Credit the original authors explicitly. Phase 0. ]]`
