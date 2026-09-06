"""pytest 共用 fixtures

設計原則:
1. 完全不寫死路徑 —路徑一律由 `fa_improver.paths` 解析
2. 所有測試獨立(monkeypatch 隔離環境)
3. 自動處理資源存在/不存在的情況
4. 自動 skip 需要範例資料但不存在的測試

v3.1.5(跨平台遷移 P1):原本這裡自己實作「向上找第一個有 *.pptx 的 report/」,
與 `tests/integration/_fixture_resolver.py` 是兩套互不相干的機制,結果不一致
——本檔的向上搜尋會**停在技能包自己的 report/**(因為它有 test_sample.pptx),
永遠拿不到根倉庫的真實客戶檔。現在兩者都 delegate 給 `fa_improver.paths`,
用「同時有 report/ 與 .agents/skills/fa-report-improvement/」的雙條件正確
跳過技能包自己那層。
"""

import sys
from pathlib import Path

import pytest

_THIS_FILE = Path(__file__).resolve()

# 技能包根目錄(包含 src/、tests/ 的目錄)
_SKILL_ROOT = _THIS_FILE.parent.parent

# 確保 src/ 在 Python path。
# 這行不能省:editable install 的 .pth 有可能失效(例如 macOS 上 .pth 檔被設了
# UF_HIDDEN 旗標時,site.addpackage() 會整個跳過它),此時仍要能 import。
_SRC_DIR = _SKILL_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from fa_improver.paths import find_project_root  # noqa: E402

# === 專案根目錄(唯一事實來源:fa_improver.paths) ===
# 找不到時退回技能包自己 —— 技能包被單獨 clone 或 pip install 時的正常情況
_PROJECT_ROOT = find_project_root() or _SKILL_ROOT


# 這些是**改善流程的輸出產物**,不是可以拿來當輸入的評估檔。
# 若不排除,`sample_eval_json` 的 fallback(candidates[0])可能選到它們 ——
# 例如 batch_evaluation_summary.json 的字母序排在 test_eval.json 之前,
# 會讓 test_parse_json_file 解出 total_score=0.0 而失敗。
# (柔伊第五輪查證缺陷 5:v3.1.5 改用 sorted() 之後才穩定觸發;在此之前
#  是靠 glob 的檔案系統順序碰巧避開,本來就是不可靠的。)
_OUTPUT_ARTIFACT_NAMES = {"batch_evaluation_summary.json"}


def _is_output_artifact(path: Path) -> bool:
    """判斷是否為改善流程的輸出,而非可用的輸入樣本。"""
    return (
        path.name in _OUTPUT_ARTIFACT_NAMES
        or path.name.endswith(".manifest.json")
        or "_improved" in path.name
    )


# === 環境資訊偵測 ===
def _detect_report_files() -> dict:
    """動態偵測 report/ 內可用檔案

    v3.1.5:改用 sorted(),讓 `sample_pptx` 等 fixture 取到的「第一個」檔案
    在不同機器上一致。glob() 的順序取決於檔案系統,不排序會讓測試結果隨機器
    飄移(macOS APFS 與 Linux ext4 的目錄順序不同)。
    """
    if _PROJECT_ROOT is None or not (_PROJECT_ROOT / "report").exists():
        return {}
    files = {}
    report_dir = _PROJECT_ROOT / "report"
    # 找出所有 .pptx 與 .json 檔案
    for suffix in ("pptx", "json", "txt"):
        found = sorted(report_dir.glob(f"*.{suffix}"))
        if found:
            files[suffix] = found
    return files


_REPORT_FILES = _detect_report_files()
_HAS_DOTENV = (_SKILL_ROOT / ".env").exists()
print(f"\n[conftest] SKILL_ROOT: {_SKILL_ROOT}")
print(f"[conftest] PROJECT_ROOT: {_PROJECT_ROOT}")
print(f"[conftest] .env exists: {_HAS_DOTENV}")
print(f"[conftest] Available report files: {sum(len(v) for v in _REPORT_FILES.values())} 個")

# 把視覺回歸測試實際用到的 fixture 來源印出來。
# 理由:真實檔缺席時的降級是靜默的(測試照跑照過,只是資料變弱),過去三輪稽核
# 都沒察覺。印出來才看得見。
try:
    from tests.integration._fixture_resolver import describe_fixture_sources

    print("[conftest] 視覺回歸 fixture 來源:")
    for _line in describe_fixture_sources():
        print(f"[conftest]   {_line}")
except Exception as _exc:  # pragma: no cover - 診斷輸出失敗不應影響測試
    print(f"[conftest] fixture 來源偵測失敗: {_exc}")
print()


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
def sample_pptx() -> Path | None:
    """取第一個原始(非 _improved) pptx 檔案

    v3.1.4 修正:找不到時回傳 None(而非 Path(""))。
    原因:Path("").exists() 永遠回傳 True,Path("").resolve() 解析成當前 cwd,
    會導致全新 clone 環境跑 pytest 時,IsADirectoryError 而不是乾淨 skip。
    呼叫端須用 `if sample_pptx is None: pytest.skip(...)` 判斷。
    """
    candidates = _REPORT_FILES.get("pptx", [])
    originals = [p for p in candidates if "_improved" not in p.name]
    if originals:
        return originals[0]
    return None


@pytest.fixture
def sample_eval_json() -> Path | None:
    """取優先符合的 eval JSON 檔案 (fa_report_*.json, 排除 _improved.*)

    v3.1.4 修正:見 sample_pptx docstring。
    """
    candidates = [p for p in _REPORT_FILES.get("json", []) if not _is_output_artifact(p)]
    # 優先選擇 fa_report_ 開頭的 (評估檔),排除 _improved (改善輸出)
    eval_files = [
        p for p in candidates if p.name.startswith("fa_report_") and "_improved" not in p.name
    ]
    if eval_files:
        return eval_files[0]
    # Fallback 不能拿掉:CI 的 create_test_fixtures.py 產生的是 test_eval.json,
    # 沒有 fa_report_*.json,拿掉會讓 CI 的相關測試全部 skip。
    return candidates[0] if candidates else None


@pytest.fixture
def sample_eval_txt() -> Path | None:
    """取優先符合的 eval TXT 檔案 (fa_report_*.txt, 排除 _improved)

    v3.1.4 修正:見 sample_pptx docstring。
    """
    candidates = _REPORT_FILES.get("txt", [])
    eval_files = [
        p for p in candidates if p.name.startswith("fa_report_") and "_improved" not in p.name
    ]
    if eval_files:
        return eval_files[0]
    return candidates[0] if candidates else None


@pytest.fixture
def has_dotenv() -> bool:
    return _HAS_DOTENV


# === 便利 marker ===
needs_pptx = pytest.mark.needs_pptx
needs_json = pytest.mark.needs_json
needs_txt = pytest.mark.needs_txt
needs_dotenv = pytest.mark.needs_dotenv
