"""測試 fixture 路徑解析器

v3.1.4 新增(稽核 #2):讓 test_visual_quality.py 與 test_slide_rendering.py
在 CI 環境(沒有真實客戶 pptx)能跑。

策略:
  1. 優先找真實客戶 pptx(/home/elan/fa-report-refactor/report/ 或 GitHub Actions 路徑)
  2. 找不到時,fallback 到 tests/integration/_synthetic_fixtures/ 的合成 pptx

合成 fixture 設計:
  - synthetic_A_vertical.pptx:layout 含「Vertical」,觸發 Bug 3 防護測試
  - synthetic_B_single_placeholder.pptx:小 textbox placeholder,觸發 v3.1.3 修正
  - synthetic_C_decoration.pptx:母片含左上裝飾,觸發 TITLE_SAFE_LEFT_INCH 修正

CI 路徑(由 GitHub Actions 設定):
  ${{ github.workspace }} = /home/runner/work/fa-report-refactor/fa-report-refactor
  但 .gitignore 排除 report/*.pptx,所以 CI 找不到真實 pptx,只能用合成 fixture

公開安全:
  合成 fixture 完全去識別化(無 ELAN logo、無真實客戶名稱、無機密文字),
  公開放在 tests/integration/_synthetic_fixtures/ 是安全的。
"""

from __future__ import annotations

import os
from pathlib import Path

# 可能的 PROJECT_ROOT 位置(優先順序)
# 可用環境變數 FA_REPORT_PROJECT_ROOT 覆蓋(以 : 分隔多個路徑)
_ENV_ROOTS = os.environ.get("FA_REPORT_PROJECT_ROOT", "")
_DEFAULT_ROOTS = [
    "/home/elan/fa-report-refactor",  # 本機 Pi Agent 環境
    "/home/runner/work/fa-report-refactor/fa-report-refactor",  # GitHub Actions
]
_CANDIDATE_ROOTS = [Path(p) for p in (_ENV_ROOTS.split(":") if _ENV_ROOTS else _DEFAULT_ROOTS) if p]


def find_project_root() -> Path | None:
    """動態找專案根目錄(有 report/ 目錄的)

    Returns:
        找到的根目錄,或 None(都找不到)
    """
    for root in _CANDIDATE_ROOTS:
        if (root / "report").is_dir():
            return root
    return None


# 技能包內 fixture 目錄(絕對路徑)
SYNTHETIC_FIXTURE_DIR = Path(__file__).parent / "_synthetic_fixtures"

# 真實 pptx → 對應的合成 pptx fallback 對應表
# (測試中以「邏輯角色」找 fixture,不直接寫檔名)
FIXTURE_FALLBACKS = {
    # 真實 pptx stem → 合成 pptx 檔名
    "260811_Kobo_ZHT_RA6080_SPcomFailI": "synthetic_A_vertical.pptx",
    "MS_Meishan_ADO_445239_260716": "synthetic_C_decoration.pptx",
    "N160JCN-EEK project 1pcs NG sample analysis report 260810": "synthetic_B_single_placeholder.pptx",
}


def resolve_input_pptx(stem: str) -> Path | None:
    """根據邏輯 pptx stem 找實際檔案路徑

    優先順序:
      1. 真實客戶 pptx(report/{stem}.pptx 在任何已知的 PROJECT_ROOT)
      2. 合成 fixture(_synthetic_fixtures/{fallback_name})

    Args:
        stem: pptx 檔名不含副檔名(如 "260811_Kobo_ZHT_RA6080_SPcomFailI")

    Returns:
        找到的 Path,或 None(兩個來源都沒有)
    """
    # 先找真實 pptx
    for root in _CANDIDATE_ROOTS:
        candidate = root / "report" / f"{stem}.pptx"
        if candidate.exists():
            return candidate

    # Fallback 到合成 fixture
    fallback_name = FIXTURE_FALLBACKS.get(stem)
    if fallback_name:
        fallback_path = SYNTHETIC_FIXTURE_DIR / fallback_name
        if fallback_path.exists():
            return fallback_path

    return None


def resolve_eval_json(stem: str) -> Path | None:
    """根據邏輯 pptx stem 找對應的 eval JSON

    真實情境:{stem} 對應 fa_report_{stem}.json
    合成 fixture 情境:合成 pptx 自己有對應 JSON(同 stem 名)

    Args:
        stem: pptx 檔名不含副檔名

    Returns:
        找到的 Path,或 None
    """
    # 先找真實的 fa_report_{stem}.json
    for root in _CANDIDATE_ROOTS:
        candidate = root / "report" / f"fa_report_{stem}.json"
        if candidate.exists():
            return candidate

    # Fallback:合成 fixture 的 eval JSON
    fallback_name = FIXTURE_FALLBACKS.get(stem)
    if fallback_name:
        # 合成 fixture 的 JSON 跟 pptx 同 stem
        synthetic_stem = fallback_name.rsplit(".", 1)[0]  # "synthetic_A_vertical"
        fallback_json = SYNTHETIC_FIXTURE_DIR / f"{synthetic_stem}.json"
        if fallback_json.exists():
            return fallback_json

    return None


def get_report_dir() -> Path:
    """取得寫入改善輸出的 report/ 目錄

    順序:
      1. 動態找的 PROJECT_ROOT/report
      2. fallback 到 SYNTHETIC_FIXTURE_DIR(讓 CI 能跑)
    """
    root = find_project_root()
    if root is not None:
        return root / "report"
    return SYNTHETIC_FIXTURE_DIR
