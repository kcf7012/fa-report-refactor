"""pytest 共用 fixtures"""

import sys
from pathlib import Path

# 確保 src/ 在 Python path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest


@pytest.fixture
def fixtures_dir():
    return ROOT / "tests" / "fixtures"


@pytest.fixture
def sample_pptx():
    return ROOT / "report" / "MS_Meishan_ADO_445239_260716.pptx"


@pytest.fixture
def sample_eval_json():
    return ROOT / "report" / "fa_report_MS_Meishan_ADO_445239_260716.json"


@pytest.fixture
def sample_eval_txt():
    return ROOT / "report" / "fa_report_N160JCN-EEK project 1pcs NG sample analysis report 260810.txt"