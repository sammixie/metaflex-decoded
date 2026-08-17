import glob
import pandas as pd
import xlrd
import openpyxl
from pathlib import Path
from paths import DATA_RAW
from datetime import datetime


RENAME_CGM = {
    'Date' : 'timestamp',
    'CGM (mg / dl)' : 'cgm_mg_dl',
    'CGM ' : 'cgm_mg_dl', #distinct
    'CBG (mg / dl)' : 'cbg_mg_dl',
    'CBG ' : 'cbg_mg_dl', #distinct
    'Blood Ketone (mmol / L)' : 'blood_ketone_mmol_l',
    'Blood Ketone ' : 'blood_ketone_mmol_l', #distinct
    'Dietary intake' : 'dietary_intake',
    '饮食' : 'dietary_intake_zh',
    '进食量' : 'dietary_intake_zh', #distinct
    'Insulin dose - s.c.' : 'insulin_dose_sc',
    'Non-insulin hypoglycemic agents' : 'non_insulin_hypoglycemic_agents',
    'CSII - bolus insulin (Novolin R, IU)' : 'insulin_csii_bolus_r_iu',
    'CSII - bolus insulin (Novolin R  IU)' : 'insulin_csii_bolus_r_iu', #distinct
    'CSII - bolus insulin ' : 'insulin_csii_bolus_r_iu', #distinct
    'CSII - basal insulin (Novolin R, IU / H)' :'insulin_csii_basal_r_iu_h' ,
    'CSII - basal insulin (Novolin R  IU / H)' : 'insulin_csii_basal_r_iu_h', #distinct
    'CSII - basal insulin ': 'insulin_csii_basal_r_iu_h', #distinct
    '胰岛素泵基础量 (Novolin R, IU / H)': 'insulin_csii_basal_r_iu_h', #distinct
    'Insulin dose - i.v.' : 'insulin_dose_iv'
}

RENAME_SUMMARY = {
    'Patient Number' : 'subject',
    'Gender (Female=1, Male=2)' : 'gender',
    'Age (years)' : 'age_years',
    'Height (m)' : 'height_m',
    'Weight (kg)' : 'weight_kg',
    'BMI (kg/m2)' : 'bmi_kg_m2',
    'Smoking History (pack year)' : 'smoking_history_pack_year',
    'Alcohol Drinking History (drinker/non-drinker)' : 'alcohol_history',
    'Type of Diabetes' : 'diabetes_type',
    'Duration of Diabetes  (years)' : 'duration_of_diabetes_years',
    'Duration of diabetes (years)' : 'duration_of_diabetes_years', #for t2
    'Acute Diabetic Complications' : 'acute_diabetic_complications',
    'Diabetic Macrovascular  Complications' : 'diabetic_macrovascular_complications',
    'Diabetic Microvascular Complications' : 'diabetic_microvascular_complications',
    'Comorbidities' : 'comorbidities',
    'Hypoglycemic Agents' : 'hypoglycemic_agents',
    'Other Agents' : 'other_agents',
    'Fasting Plasma Glucose (mg/dl)' : 'fasting_plasma_glucose_mg_dl',
    '2-hour Postprandial Plasma Glucose (mg/dl)' : 'postprandial_2h_glucose_mg_dl',
    'Fasting C-peptide (nmol/L)' : 'fasting_c_peptide_nmol_l',
    '2-hour Postprandial C-peptide (nmol/L)' : 'postprandial_2h_c_peptide_nmol_l',
    'Fasting Insulin (pmol/L)' : 'fasting_insulin_pmol_l',
    '2-hour Postprandial Insulin (pmol/L)' : 'postprandial_2h_insulin_pmol_l',
    '2-hour Postprandial insulin (pmol/L)' : 'postprandial_2h_insulin_pmol_l', #for t2
    'HbA1c (mmol/mol)' : 'hba1c_mmol_mol',
    'Glycated Albumin (%)' : 'glycated_albumin_pct',
    'Total Cholesterol (mmol/L)' :'total_cholesterol_mmol_l',
    'Triglyceride (mmol/L)' : 'triglyceride_mmol_l',
    'High-Density Lipoprotein Cholesterol (mmol/L)' : 'hdl_mmol_l',
    'Low-Density Lipoprotein Cholesterol (mmol/L)' : 'ldl_mmol_l',
    'Creatinine (umol/L)' : 'creatinine_umol_l',
    'Estimated Glomerular Filtration Rate  (ml/min/1.73m2) ' : 'egfr_ml_min_1_73m2',
    'Uric Acid (mmol/L)' : 'uric_acid_mmol_l',
    'Blood Urea Nitrogen (mmol/L)' : 'blood_urea_nitrogen_mmol_l',
    'Hypoglycemia (yes/no)' : 'has_hypoglycemia'
}

#assert len(set(RENAME_CGM.values())) == len(RENAME_CGM)
assert len(RENAME_CGM) - len(set(RENAME_CGM.values())) == 9 
assert len(RENAME_SUMMARY) - len(set(RENAME_SUMMARY.values())) == 2  # the two T1/T2 pairs
 
all_files = sorted(DATA_RAW.rglob("*"))
files = [f for f in all_files if f.is_file()]
summary_files = [f for f in all_files if "summary" in f.name.lower()]
cgm_files = [f for f in files if "summary" not in f.name.lower()
             and f.suffix.lower() in (".xls", ".xlsx")]

def apply_rename(df, mapping, name=""):
    unmapped = [c for c in df.columns if c not in mapping]
    if unmapped:
        raise KeyError(f"{name}: unmapped columns {unmapped}")
    out = df.rename(columns=mapping)
    assert not out.columns.duplicated().any(), out.columns[out.columns.duplicated()]
    return out

def load_summary_file(paths):
    df = pd.read_excel(paths, na_values=["/"])
    source_row = range(len(df))
    df = apply_rename(df, RENAME_SUMMARY, name=Path(paths).name)
    identities = [parse_identity(s) for s in df["subject"]]
    subjects, visits, recording_date = zip(*identities)
    df["subject"] = subjects
    df["visit"] = visits
    df["recording_date"] = pd.to_datetime(recording_date)
    df["source_row"] = source_row
    df["source_file"] = Path(paths).name
    front = ["subject", "visit", "recording_date"]
    back = ["source_row", "source_file"]
    middle = [c for c in df.columns if c not in front and c not in back]
    df = df[front + middle + back]
    return df

def parse_identity(id_string):
    subject, visit_num, date_str = id_string.split("_")
    visit = int(visit_num)
    recording_date = datetime.strptime(date_str, "%Y%m%d").date()
    return int(subject), visit, recording_date

def parse_filename(filename):
    return parse_identity(filename.stem)

#write load cgm_file function: signature, provenance columns, and the filename parse.
def load_cgm_file(paths):
    df = pd.read_excel(paths, na_values=["/"])
    source_row = range(len(df))
    df = apply_rename(df, RENAME_CGM, name=Path(paths).name)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["source_row"] = source_row
    df["source_file"] = Path(paths).name
    subject, visit, recording_date = parse_filename(Path(paths))
    df["subject"] = subject
    df["visit"] = visit
    df["recording_date"] = pd.to_datetime(recording_date)
    front = ["subject", "visit", "recording_date", "timestamp"]
    back = ["source_row", "source_file"]
    middle = [c for c in df.columns if c not in front and c not in back]
    df = df[front + middle + back]
    return df
