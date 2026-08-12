import pandas as pd
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from metrics import mean_glucose, std_glucose, cv_glucose, cv_instability_flag, tir_glucose, tar_glucose, tbr_glucose, gmi_glucose, mage_glucose, excursion_count

def test_mean_glucose_basic():
    df = pd.DataFrame({"cgm_mg_dl": [100.0, 200.0, 300.0, float("nan")]})
    assert mean_glucose(df) == 200.0

def test_std_glucose():
    df = pd.DataFrame({"cgm_mg_dl": [100.0, 200.0, 300.0, float("nan")]})
    assert std_glucose(df) == 100.0

def test_cv_glucose():
    df = pd.DataFrame({"cgm_mg_dl": [100.0, 200.0, 300.0, float("nan")]})
    assert cv_glucose(df) == 50.0

def test_cv_instability_flag():
    df = pd.DataFrame({"cgm_mg_dl": [100.0, 200.0, 300.0, float("nan")]})
    assert cv_instability_flag(df) == True

def test_cv_instability_flag_stable():
    df = pd.DataFrame({"cgm_mg_dl": [100.0, 105.0, 95.0, 100.0]})
    assert cv_instability_flag(df) == False

def test_tir_glucose():
    df = pd.DataFrame({"cgm_mg_dl": [100.0, 200.0, 300.0, float("nan")]})
    assert round(tir_glucose(df)) == 33

def test_tar_glucose():
    df = pd.DataFrame({"cgm_mg_dl": [100.0, 200.0, 300.0, float("nan")]})
    assert round(tar_glucose(df)) == 67

def test_tbr_glucose():
    df = pd.DataFrame({"cgm_mg_dl": [100.0, 200.0, 300.0, float("nan")]})
    assert round(tbr_glucose(df)) == 0

def test_gmi_glucose():
    df = pd.DataFrame({"cgm_mg_dl": [100.0, 200.0, 300.0, float("nan")]})
    assert gmi_glucose(df) == 8.094

def test_mage_glucose():
    df = pd.DataFrame({"cgm_mg_dl": [100, 180, 90, 160, 95, 110, 120, 100]})
    assert mage_glucose(df) == 76.25

def test_excursion_count():
    df = pd.DataFrame({"cgm_mg_dl": [100, 180, 90, 160, 95, 110, 120, 100]})
    assert excursion_count(df) == 4
