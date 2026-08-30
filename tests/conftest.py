"""pytest 共用 fixtures

設計原則:
1. 完全不寫死路徑 —動態向上搜尋專案根目錄
2. 所有測試獨立(monkeypatch 隔離環境)
3. 自動處理資源存在/不存在的情況
4. 自動 skip 需要範例資料但不存在的測試
"""

import os
import sys
from pathlib import Path

# === 動態尋找專案根目錄(完全動態) ===
_THIS_FILE = Path(__file__).resolve()
_CURRENT = _THIS_FILE.parent

# 從當前檔案往上找,找到第一個有 *.pptx 檔案的「report/」目錄
_PROJECT_ROOT = None
_candidate = _CURRENT
while _candidate != _candidate.parent:
    _candidate = _candidate.parent
    _report_dir = _candidate / "report"
    if _report_dir.is_dir():
        # 確認裡面有 pptx 檔案
        if any(_report_dir.glob("*.pptx")):
            _PROJECT_ROOT = _candidate
            break

if _PROJECT_ROOT is None:
    # 都找不到,使用當前目錄的祖父目錄作為最後 fallback
    _PROJECT_ROOT = _CURRENT.parent.parent

# 技能包根目錄(包含 src/、tests/ 的目錄)
_SKILL_ROOT = _THIS_FILE.parent.parent

# 確保 src/ 在 Python path
_SRC_DIR = _SKILL_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))


# === 環境資訊偵測 ===
def _detect_report_files() -> dict:
    """動態偵測 report/ 內可用檔案"""
    if _PROJECT_ROOT is None or not (_PROJECT_ROOT / "report").exists():
        return {}
    files = {}
    report_dir = _PROJECT_ROOT / "report"
    # 找出所有 .pptx 與 .json 檔案
    for p in report_dir.glob("*.pptx"):
        files.setdefault("pptx", []).append(p)
    for p in report_dir.glob("*.json"):
        files.setdefault("json", []).append(p)
    for p in report_dir.glob("*.txt"):
        files.setdefault("txt", []).append(p)
    return files


_REPORT_FILES = _detect_report_files()
_HAS_DOTENV = (_SKILL_ROOT / ".env").exists()
print(f"\n[conftest] SKILL_ROOT: {_SKILL_ROOT}")
print(f"[conftest] PROJECT_ROOT: {_PROJECT_ROOT}")
print(f"[conftest] .env exists: {_HAS_DOTENV}")
print(f"[conftest] Available report files: {sum(len(v) for v in _REPORT_FILES.values())} 個\n")

import pytest


# === 自動 Skip 機制 ===
def pytest_collection_modifyitems(config, items):
    """根據環境資源自動 skip 不可執行的測試"""
    skip_dotenv = pytest.mark.skip(reason="需要 .env 但不存在")
    skip_pptx = pytest.mark.skip(reason="需要範例 pptx 但不存在")
    skip_json = pytest.mark.skip(reason="需要範例 eval JSON 但不存在")
    skip_txt = pytest.mark.skip(reason="需要範例 eval TXT 但不存在")

    for item in items:
        if "needs_dotenv" in item.keywords and not _HAS_DOTENV:
            item.add_marker(skip_dotenv)
        if "needs_pptx" in item.keywords and not _REPORT_FILES.get("pptx"):
            item.add_marker(skip_pptx)
        if "needs_json" in item.keywords and not _REPORT_FILES.get("json"):
            item.add_marker(skip_json)
        if "needs_txt" in item.keywords and not _REPORT_FILES.get("txt"):
            item.add_marker(skip_txt)


# === 共用 Fixtures ===
@pytest.fixture
def skill_root() -> Path:
    return _SKILL_ROOT


@pytest.fixture
def project_root() -> Path:
    return _PROJECT_ROOT


@pytest.fixture
def fixtures_dir() -> Path:
    return _SKILL_ROOT / "tests" / "fixtures"


@pytest.fixture
def sample_pptx() -> Path:
    """取第一個原始(非 _improved) pptx 檔案"""
    candidates = _REPORT_FILES.get("pptx", [])
    originals = [p for p in candidates if "_improved" not in p.name]
    if originals:
        return originals[0]
    return candidates[0] if candidates else Path("")


@pytest.fixture
def sample_eval_json() -> Path:
    """取優先符合的 eval JSON 檔案 (fa_report_*.json, 排除 _improved.*)"""
    candidates = _REPORT_FILES.get("json", [])
    # 優先選擇 fa_report_ 開頭的 (評估檔),排除 _improved (改善輸出)
    eval_files = [
        p
        for p in candidates
        if p.name.startswith("fa_report_") and "_improved" not in p.name
    ]
    if eval_files:
        return eval_files[0]
    return candidates[0] if candidates else Path("")


@pytest.fixture
def sample_eval_txt() -> Path:
    """取優先符合的 eval TXT 檔案 (fa_report_*.txt, 排除 _improved)"""
    candidates = _REPORT_FILES.get("txt", [])
    eval_files = [
        p
        for p in candidates
        if p.name.startswith("fa_report_") and "_improved" not in p.name
    ]
    if eval_files:
        return eval_files[0]
    return candidates[0] if candidates else Path("")


@pytest.fixture
def has_dotenv() -> bool:
    return _HAS_DOTENV


# === 便利 marker ===
needs_pptx = pytest.mark.needs_pptx
needs_json = pytest.mark.needs_json
needs_txt = pytest.mark.needs_txt
needs_dotenv = pytest.mark.needs_dotenv