import sys
from pathlib import Path
sys.path.append(str(Path("../src").resolve()))

from load import load_cgm_file, load_summary_file, cgm_files, summary_files
import pandas as pd

table_a = pd.concat([load_cgm_file(f) for f in cgm_files], ignore_index=True)
table_b = pd.concat([load_summary_file(f) for f in summary_files], ignore_index=True)



def clean_cgm(df):
    df = df.drop(columns=["dietary_intake_zh"])  # D-009: duplicate of dietary_intake
    df["insulin_csii_bolus_r_iu"] = df["insulin_csii_bolus_r_iu"].replace("temporarily suspend insulin delivery", 0)
    df["insulin_csii_bolus_r_iu"] = df["insulin_csii_bolus_r_iu"].replace("acarbose 50 mg", pd.NA)
    df["insulin_csii_bolus_r_iu"] = pd.to_numeric(df["insulin_csii_bolus_r_iu"])
    df["insulin_csii_basal_r_iu_h"] = df["insulin_csii_basal_r_iu_h"].replace("temporarily suspend insulin delivery", 0)
    df["insulin_csii_basal_r_iu_h"] = pd.to_numeric(df["insulin_csii_basal_r_iu_h"])
    df["insulin_dose_iv"] = df["insulin_dose_iv"].replace("CSII - basal insulin (Novolin R, IU / H)", pd.NA)
    
    df = df.sort_values(["subject", "visit", "date"])
    df["date"] = df["date"].dt.round("1min")
    gap_minutes = df.groupby(["subject", "visit"])["date"].diff().dt.total_seconds() / 60
    is_phase_shift = (gap_minutes % 15 != 0) & gap_minutes.notna()
    df["segment"] = is_phase_shift.groupby([df["subject"], df["visit"]]).cumsum()
    resampled_df = (df.set_index("date").groupby(["subject", "visit", "segment"]).resample("15min", origin="start").asfreq().reset_index())
    df = resampled_df
    df["cgm_gap"] = df["cgm_mg_dl"].isna()
    cgm_out_of_range = (df["cgm_mg_dl"] < 30) | (df["cgm_mg_dl"] > 600)
    df["cgm_out_of_range"] = cgm_out_of_range                # record which rows got caught, first
    df.loc[cgm_out_of_range, "cgm_mg_dl"] = pd.NA        # then overwrite just those rows

    cbg_out_of_range = (df["cbg_mg_dl"] < 30) | (df["cbg_mg_dl"] > 600)
    df["cbg_out_of_range"] = cbg_out_of_range                # record which rows got caught, first
    df.loc[cbg_out_of_range, "cbg_mg_dl"] = pd.NA
    return df


def clean_summary(df):
    str_cols = df.select_dtypes(include="str").columns
    df[str_cols] = df[str_cols].apply(lambda col: col.str.strip())
    df = df.rename(columns={"uric_acid_mmol_l": "uric_acid_umol_l"})

    return df
