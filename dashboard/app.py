"""MetaFlex Decoded — Streamlit dashboard.

Phase 5 deliverable. Layout, styling, and widgets are Claude's to write
per CLAUDE.md's ownership table; every number shown is read live from
`data/interim/` and `data/processed/` — nothing here recomputes a metric
or a decision that Phases 1-4 already made.

Three tabs:
  - Patient explorer: one subject-visit's CGM trace with TIR bands, plus
    that visit's metric cards and clinical context.
  - Cohort view: distribution of the pre-specified metrics across all
    125 subject-visits, T1DM vs T2DM, and the Phase 3 hero figure.
  - Risk view: placeholder. Phase 4 (the hypoglycemia model) hasn't been
    built yet — this tab says so rather than faking a result.
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------------------------
# Paths and data loading
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_INTERIM = REPO_ROOT / "data" / "interim"
DATA_PROCESSED = REPO_ROOT / "data" / "processed"
FIGURES = REPO_ROOT / "reports" / "figures"

TIR_LOW, TIR_HIGH = 70, 180  # mg/dL — same boundaries as src/metrics.py


@st.cache_data
def load_cgm() -> pd.DataFrame:
    return pd.read_parquet(DATA_INTERIM / "table_a_clean.parquet")


@st.cache_data
def load_clinical() -> pd.DataFrame:
    return pd.read_parquet(DATA_INTERIM / "table_b_clean.parquet")


@st.cache_data
def load_metrics() -> pd.DataFrame:
    return pd.read_parquet(DATA_PROCESSED / "summarize_table_a.parquet")


def hba1c_ifcc_to_ngsp(mmol_mol: float) -> float:
    """IFCC mmol/mol -> NGSP % — affine conversion, not a scale factor (L-013)."""
    return mmol_mol / 10.929 + 2.15


DATA_MISSING = not (
    (DATA_INTERIM / "table_a_clean.parquet").exists()
    and (DATA_INTERIM / "table_b_clean.parquet").exists()
    and (DATA_PROCESSED / "summarize_table_a.parquet").exists()
)

st.set_page_config(page_title="MetaFlex Decoded", layout="wide")
st.title("MetaFlex Decoded")
st.caption(
    "Shanghai T1DM/T2DM CGM cohort — audited pipeline, versioned metric "
    "definitions, traceable to source."
)

if DATA_MISSING:
    st.error(
        "Processed data not found under `data/interim/` and "
        "`data/processed/`. Run `notebooks/02_cleaning_pipeline.ipynb` and "
        "`notebooks/03_cgm_metrics.ipynb` first — this dashboard reads "
        "their output, it doesn't regenerate it."
    )
    st.stop()

cgm = load_cgm()
clinical = load_clinical()
metrics = load_metrics()

tab_patient, tab_cohort, tab_risk = st.tabs(
    ["Patient explorer", "Cohort view", "Risk (Phase 4 — not built)"]
)

# ---------------------------------------------------------------------------
# Patient explorer
# ---------------------------------------------------------------------------

with tab_patient:
    subjects = sorted(cgm["subject"].unique())
    col_select_a, col_select_b = st.columns(2)
    with col_select_a:
        subject = st.selectbox("Subject", subjects)

    visits = sorted(cgm.loc[cgm["subject"] == subject, "visit"].unique())
    with col_select_b:
        visit = st.selectbox("Visit", visits)

    trace = cgm[(cgm["subject"] == subject) & (cgm["visit"] == visit)].sort_values(
        "timestamp"
    )
    row_metrics = metrics[(metrics["subject"] == subject) & (metrics["visit"] == visit)]
    row_clinical = clinical[
        (clinical["subject"] == subject) & (clinical["visit"] == visit)
    ]

    st.subheader(f"Subject {subject}, visit {visit}")

    if row_clinical.empty:
        st.warning("No clinical summary row for this subject-visit.")
    else:
        c = row_clinical.iloc[0]
        info_cols = st.columns(5)
        info_cols[0].metric("Diabetes type", c["diabetes_type"])
        info_cols[1].metric("Age", f"{c['age_years']:.0f}" if pd.notna(c["age_years"]) else "—")
        info_cols[2].metric("BMI", f"{c['bmi_kg_m2']:.1f}" if pd.notna(c["bmi_kg_m2"]) else "—")
        hba1c_pct = (
            hba1c_ifcc_to_ngsp(c["hba1c_mmol_mol"]) if pd.notna(c["hba1c_mmol_mol"]) else None
        )
        info_cols[3].metric("Lab HbA1c", f"{hba1c_pct:.1f}%" if hba1c_pct else "not recorded")
        info_cols[4].metric("Hypoglycemia (chart)", c["has_hypoglycemia"])

    if row_metrics.empty:
        st.warning("No metrics row for this subject-visit.")
    else:
        m = row_metrics.iloc[0]
        metric_cols = st.columns(6)
        metric_cols[0].metric("Mean glucose", f"{m['mean']:.0f} mg/dL")
        metric_cols[1].metric("CV%", f"{m['cv']:.1f}%", "unstable" if m["cv instability"] else "stable")
        metric_cols[2].metric("TIR", f"{m['tir']:.1f}%")
        metric_cols[3].metric("TAR / TBR", f"{m['tar']:.1f}% / {m['tbr']:.1f}%")
        metric_cols[4].metric("GMI", f"{m['gmi']:.1f}%")
        metric_cols[5].metric("MAGE", f"{m['mage']:.0f} mg/dL", f"{int(m['excursion'])} excursions")

    if trace.empty:
        st.warning("No CGM readings found for this selection.")
    else:
        # Never draw a line across a flagged gap (D-012/D-015) — plotting
        # straight through it would visually impute readings that were
        # deliberately never filled in.
        plot_df = trace.copy()
        plot_df.loc[plot_df["cgm_gap"], "cgm_mg_dl"] = None

        fig = go.Figure()
        fig.add_hrect(
            y0=TIR_LOW, y1=TIR_HIGH,
            fillcolor="rgba(46, 160, 67, 0.12)", line_width=0,
            annotation_text="Time in Range (70-180 mg/dL)", annotation_position="top left",
        )
        fig.add_trace(
            go.Scatter(
                x=plot_df["timestamp"], y=plot_df["cgm_mg_dl"],
                mode="lines", name="CGM", line=dict(color="#1f77b4", width=1.5),
                connectgaps=False,
            )
        )
        gap_points = trace[trace["cgm_gap"]]
        if not gap_points.empty:
            fig.add_trace(
                go.Scatter(
                    x=gap_points["timestamp"], y=[TIR_LOW] * len(gap_points),
                    mode="markers", name="flagged gap",
                    marker=dict(color="orange", symbol="line-ns", size=8),
                )
            )
        fig.update_layout(
            height=420, margin=dict(l=10, r=10, t=40, b=10),
            xaxis_title="Time", yaxis_title="Glucose (mg/dL)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Gaps are flagged, never imputed — a broken line is a real "
            "missing reading, not a rendering issue."
        )

# ---------------------------------------------------------------------------
# Cohort view
# ---------------------------------------------------------------------------

with tab_cohort:
    n_subjects = cgm["subject"].nunique()
    n_visits = len(metrics)
    type_counts = clinical.drop_duplicates("subject")["diabetes_type"].value_counts()
    hypo_rate = (clinical["has_hypoglycemia"] == "yes").mean()

    cohort_cols = st.columns(4)
    cohort_cols[0].metric("Subjects", n_subjects)
    cohort_cols[1].metric("Subject-visits", n_visits)
    cohort_cols[2].metric(
        "T1DM / T2DM",
        f"{type_counts.get('T1DM', 0)} / {type_counts.get('T2DM', 0)}",
    )
    cohort_cols[3].metric("Hypoglycemia rate", f"{hypo_rate:.1%}")

    joined = metrics.merge(
        clinical[["subject", "visit", "diabetes_type"]], on=["subject", "visit"], how="left"
    )

    st.markdown("#### Metric distributions, T1DM vs T2DM")
    metric_choice = st.selectbox(
        "Metric", ["tir", "tar", "tbr", "cv", "gmi", "mage", "mean"], index=0
    )
    fig_dist = px.box(
        joined, x="diabetes_type", y=metric_choice, color="diabetes_type",
        points="all",
        color_discrete_map={"T1DM": "#d62728", "T2DM": "#1f77b4"},
    )
    fig_dist.update_layout(height=420, showlegend=False, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig_dist, use_container_width=True)
    st.caption(
        "Descriptive only — T1DM is n≈"
        f"{type_counts.get('T1DM', 0)} subjects, too small for inferential "
        "claims (D-003/D-029)."
    )

    st.markdown("#### GMI vs. laboratory HbA1c — the headline agreement result")
    hero_path = FIGURES / "hero_gmi_hba1c_agreement.png"
    if hero_path.exists():
        st.image(str(hero_path), use_container_width=True)
        st.caption(
            "Bland-Altman agreement, GMI vs. lab HbA1c. See "
            "`docs/data-decisions.md` D-023/D-024/D-037 for the full "
            "bias, limits-of-agreement, and proportional-bias analysis."
        )
    else:
        st.warning("Hero figure not found at `reports/figures/hero_gmi_hba1c_agreement.png`.")

# ---------------------------------------------------------------------------
# Risk view — placeholder
# ---------------------------------------------------------------------------

with tab_risk:
    st.info(
        "Phase 4 (the hypoglycemia risk model) hasn't been built yet — "
        "`src/features.py` is still empty and `05_modeling.ipynb` has "
        "section headers only. This tab is a placeholder so the "
        "dashboard's structure is in place ahead of the model, not a "
        "result. It will show predicted risk and top SHAP drivers per "
        "subject-visit once Phase 4 closes."
    )
