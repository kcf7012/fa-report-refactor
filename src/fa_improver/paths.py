"""專案路徑解析 —— 套件內**唯一**的路徑事實來源。

v3.1.5 新增(跨平台遷移 P1)。在此之前有三套互不相干的路徑機制:
`tests/conftest.py` 的向上搜尋、`tests/integration/_fixture_resolver.py` 的
硬編候選清單、以及各 script 各自寫死的絕對路徑。三者行為不一致,且都在
WSL → macOS 遷移後失效。

放在 `src/` 而非 `tests/`,是為了讓 scripts 與 tests 都能 import 同一份邏輯。

## 雙倉庫結構

本專案是兩個獨立 git repo 疊在一起,**兩邊都有 `report/`**:

    <PROJECT_ROOT>/                              ← 根倉庫
    ├── report/                                  ← 真實客戶 pptx(機密)
    └── .agents/skills/fa-report-improvement/    ← 技能包(獨立 repo)
        └── report/                              ← CI 動態產生的測試 fixture

所以「向上找第一個有 `report/` 的目錄」會**停在技能包自己身上**,永遠拿不到
根倉庫的真實客戶檔 —— 這正是 `conftest.py` 舊實作的 bug。本模組改用
**雙條件**判定(同時有 `report/` 與 `.agents/skills/fa-report-improvement/`)
來跳過技能包自己的 `report/`。

## 為什麼不寫死路徑

歷史教訓:第一輪稽核抓到 16 個測試硬編某台開發機的專案絕對路徑,
當時的「修正」只是把該字面值**搬進** resolver 的預設清單,沒有真正消除。
結果失效方式從「看得見的 skip」變成「看不見的靜默降級」(測試照跑照過,
只是資料悄悄換成較弱的合成 fixture),連續三輪稽核都沒發現。

因此本模組**不含任何絕對路徑字面值**,一律靠 `__file__` 錨定或環境變數。
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path

__all__ = [
    "SKILL_ROOT",
    "SKILL_REPORT_DIR",
    "PROJECT_ROOT_ENV_VAR",
    "candidate_project_roots",
    "find_project_root",
    "get_report_dir",
    "resolve_report_file",
]

# 技能包根目錄 —— 含 src/、tests/、pyproject.toml 的那一層。
# paths.py 位於 <SKILL_ROOT>/src/fa_improver/paths.py,故往上三層。
SKILL_ROOT = Path(__file__).resolve().parents[2]

# 技能包自己的 report/(測試 fixture),**不是**根倉庫放真實客戶檔的那個
SKILL_REPORT_DIR = SKILL_ROOT / "report"

# 覆寫搜尋根目錄用;多個路徑以 os.pathsep 分隔(POSIX 是 ":",Windows 是 ";")
PROJECT_ROOT_ENV_VAR = "FA_REPORT_PROJECT_ROOT"

# 根倉庫的辨識標記:技能包所在的相對位置
_SKILL_REL_PATH = Path(".agents") / "skills" / "fa-report-improvement"


def _looks_like_project_root(path: Path) -> bool:
    """雙條件判定:同時有 report/ 與技能包目錄,才是根倉庫。

    只檢查 `report/` 會誤判技能包自己(它也有 report/)。
    """
    return (path / "report").is_dir() and (path / _SKILL_REL_PATH).is_dir()


def _env_roots(var: str) -> list[Path]:
    """讀環境變數並以 os.pathsep 切開(不要寫死 ":",那是 Windows 地雷)。

    指定了卻不存在的路徑會發出 warning 而非靜默忽略 —— 打錯字的環境變數
    被無聲吞掉,正是本模組要根除的那種失效方式。
    """
    raw = os.environ.get(var, "")
    roots = []
    for entry in raw.split(os.pathsep):
        entry = entry.strip()
        if not entry:
            continue
        path = Path(entry).expanduser()
        if not path.is_dir():
            warnings.warn(
                f"{var} 指定的路徑不存在,已略過:{entry}",
                RuntimeWarning,
                stacklevel=3,
            )
            continue
        roots.append(path)
    return roots


def candidate_project_roots(start: Path | None = None) -> list[Path]:
    """依優先序回傳所有可能的專案根目錄(去重、只留實際存在的目錄)。

    優先序:
      1. ``FA_REPORT_PROJECT_ROOT`` 環境變數(可指定多個,os.pathsep 分隔)
      2. ``GITHUB_WORKSPACE`` 環境變數 —— 取代舊版硬編的 ubuntu runner
         workspace 絕對路徑,這樣 ubuntu 與 macOS runner 都正確
      3. 從 ``start``(預設 ``SKILL_ROOT``)逐層向上,找符合雙條件的目錄

    明確指定的環境變數**不套用雙條件**:使用者的明示意圖優先,
    找不到 `report/` 時應該讓呼叫端看見錯誤,而不是靜默換掉根目錄。
    """
    roots: list[Path] = []

    def _add(path: Path) -> None:
        if path.is_dir():
            resolved = path.resolve()
            if resolved not in roots:
                roots.append(resolved)

    for path in _env_roots(PROJECT_ROOT_ENV_VAR):
        _add(path)
    for path in _env_roots("GITHUB_WORKSPACE"):
        _add(path)

    current = (start or SKILL_ROOT).resolve()
    for candidate in [current, *current.parents]:
        if _looks_like_project_root(candidate):
            _add(candidate)

    return roots


def find_project_root(start: Path | None = None) -> Path | None:
    """找專案根目錄(放真實客戶 `report/` 的那一層)。

    Returns:
        最高優先的根目錄;都找不到時回傳 ``None``。

    ``None`` 是正常情況 —— 技能包被 `pip install` 獨立安裝、或被單獨
    clone 出來稽核時,外層根倉庫本來就不存在。呼叫端必須能優雅降級。
    """
    roots = candidate_project_roots(start)
    return roots[0] if roots else None


def get_report_dir() -> Path:
    """取得存放報告檔的 `report/` 目錄。

    找得到根倉庫就用它的 `report/`(真實客戶檔);找不到就退回技能包自己的
    `report/`,讓 CI 與獨立安裝的情境仍然可用。
    """
    root = find_project_root()
    return root / "report" if root is not None else SKILL_REPORT_DIR


def resolve_report_file(name: str) -> Path | None:
    """在所有候選根目錄的 `report/` 底下找指定檔名。

    Args:
        name: 檔名(含副檔名),如 ``"260811_Kobo_ZHT_RA6080_SPcomFailI.pptx"``

    Returns:
        第一個命中的路徑;都找不到回傳 ``None``。

    搜尋順序與 :func:`candidate_project_roots` 相同,最後才試技能包自己的
    `report/` —— 這樣技能包被單獨 clone 時仍找得到它自帶的測試檔。
    """
    for root in candidate_project_roots():
        candidate = root / "report" / name
        if candidate.exists():
            return candidate

    fallback = SKILL_REPORT_DIR / name
    return fallback if fallback.exists() else None
