#a set of functions that take one patient-visit's cleaned CGM trace (from table_a_clean) 
# and turn it into the actual clinical numbers a diabetes reader would look for.
import numpy as np

def mean_glucose(df):
    """
    - one patient-visit's slice of table_a_clean with a resampled 15-min grid
    - use the col cgm_mg_dl
    - skip the gap, don't count
    """
    mean = df["cgm_mg_dl"].mean(skipna=True)
    return mean

def std_glucose(df):
    """
    - one patient-visit's slice of table_a_clean with a resampled 15-min grid
    - use the col cgm_mg_dl
    - divided by n-1 (sample SD)
    - skip the gap, don't count
    """
    std = df["cgm_mg_dl"].std(ddof=1, skipna=True)
    return std

def cv_glucose(df):
    """
    - %CV = (SD / mean) * 100
    - calculate using mean_glucose/std_glucose functions
    """
    cv = (std_glucose(df) / mean_glucose(df)) * 100
    return cv

def cv_instability_flag(df):
    """
    - True if cv_glucose(df) >= 36, a published threshold for glycemic instability
    - False otherwise
    - reuses cv_glucose, no new gap-handling logic of its own
    """
    return cv_glucose(df) >= 36


def tir_glucose(df):
    """
    - glucose band: 70-180
    - drop gap rows
    """
    real_readings = df["cgm_mg_dl"].dropna() #drop empty data
    in_range = (real_readings >= 70) & (real_readings <= 180)
    tir = in_range.mean() * 100
    return tir

def tar_glucose(df):
    """
    - drop gap rows
    - above range set to 180
    """
    real_readings = df["cgm_mg_dl"].dropna()
    above_range = real_readings > 180
    tar = above_range.mean() * 100
    return tar

def tbr_glucose(df):
    """
    - drop gap rows
    - below range set to 70
    """
    real_readings = df["cgm_mg_dl"].dropna()
    below_range = real_readings < 70
    tbr = below_range.mean() * 100
    return tbr


def gmi_glucose(df):
    """
    - GMI (%) = 3.31 + (0.02392 * mean glucose)
    """
    gmi = 3.31 + (0.02392 * mean_glucose(df))
    return gmi

def qualifying_swings(df):
    """
    Turning-point swings exceeding 1xSD (M-005/M-006's boundary/threshold
    logic). Shared by mage_glucose and excursion_count.
    """
    real_readings = df["cgm_mg_dl"].dropna()
    diffs = real_readings.diff()
    diffs_sign = np.sign(diffs)
    turning_point = diffs_sign != diffs_sign.shift(-1)
    turning_point.iloc[0] = True
    turning_point.iloc[-1] = True
    tp_values = real_readings[turning_point]
    tp_diffs = tp_values.diff()
    threshold = std_glucose(df)
    return tp_diffs[tp_diffs.abs() > threshold]


def mage_glucose(df):
    """
    - one patient-visit's slice of table_a_clean with a resampled 15-min grid
    - use the col cgm_mg_dl
    - drop gaps
    - filter turning-point swings to those exceeding 1*SD.
    - if rise/fall count tie, average both directions
    """
    qualifying = qualifying_swings(df)
    rises = qualifying[qualifying > 0]
    falls = qualifying[qualifying < 0]
    if len(rises) > len(falls):
        mage = rises.abs().mean()
    elif len(falls) > len(rises):
        mage = falls.abs().mean()
    else:
        mage = qualifying.abs().mean()
    return mage

def excursion_count(df):
    """
    - count of qualifying glycemic excursions (turning-point swings exceeding 1xSD)
    - both directions counted, not just MAGE's majority direction (M-008)
    - reuses qualifying_swings, same turning-point/threshold logic as mage_glucose
    """
    excursion = qualifying_swings(df)
    return len(excursion)