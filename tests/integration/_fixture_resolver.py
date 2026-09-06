"""測試 fixture 路徑解析器

v3.1.4 新增(稽核 #2):讓 test_visual_quality.py 與 test_slide_rendering.py
在 CI 環境(沒有真實客戶 pptx)能跑。

v3.1.5 改寫(跨平台遷移 P1):**刪除硬編候選路徑清單**,改為 delegate 給
`fa_improver.paths`。原本的 `_DEFAULT_ROOTS` 直接寫死兩條 Linux 絕對路徑,
在別台機器上兩條都 miss,導致真實客戶檔明明存在卻被靜默換成合成 fixture。

策略(不變):
  1. 優先找真實客戶 pptx(根倉庫 `report/`,由 `fa_improver.paths` 動態解析)
  2. 找不到時,fallback 到 `tests/integration/_synthetic_fixtures/` 的合成 pptx

合成 fixture 設計:
  - synthetic_A_vertical.pptx:layout 含「Vertical」,觸發 Bug 3 防護測試
  - synthetic_B_single_placeholder.pptx:小 textbox placeholder,觸發 v3.1.3 修正
  - synthetic_C_decoration.pptx:母片含左上裝飾,觸發 TITLE_SAFE_LEFT_INCH 修正

CI 情境:
  `GITHUB_WORKSPACE` 由 GitHub Actions 設定,`fa_improver.paths` 會讀它,
  所以 ubuntu 與 macOS runner 都正確(不再假設 runner 的 workspace 絕對路徑)。
  但 `.gitignore` 排除 `report/*.pptx`,CI 仍然只會拿到合成 fixture。

⚠️ **降級是靜默的**:找不到真實檔時不報錯、不 skip,只是換用較弱的 fixture。
加測試時要確認它在兩種來源下都有意義。用 :func:`describe_fixture_sources`
可以印出當下每個 stem 實際解到哪一種來源。

公開安全:
  合成 fixture 完全去識別化(無 ELAN logo、無真實客戶名稱、無機密文字),
  公開放在 tests/integration/_synthetic_fixtures/ 是安全的。
"""

from __future__ import annotations

from pathlib import Path

from fa_improver.paths import find_project_root as _find_project_root
from fa_improver.paths import get_report_dir as _get_report_dir
from fa_improver.paths import resolve_report_file

__all__ = [
    "SYNTHETIC_FIXTURE_DIR",
    "FIXTURE_FALLBACKS",
    "find_project_root",
    "get_report_dir",
    "resolve_input_pptx",
    "resolve_eval_json",
    "is_synthetic",
    "describe_fixture_sources",
]

# 技能包內 fixture 目錄(以本檔案錨定,不依賴 cwd)
SYNTHETIC_FIXTURE_DIR = Path(__file__).resolve().parent / "_synthetic_fixtures"

# 真實 pptx → 對應的合成 pptx fallback 對應表
# (測試中以「邏輯角色」找 fixture,不直接寫檔名)
FIXTURE_FALLBACKS = {
    # 真實 pptx stem → 合成 pptx 檔名
    "260811_Kobo_ZHT_RA6080_SPcomFailI": "synthetic_A_vertical.pptx",
    "MS_Meishan_ADO_445239_260716": "synthetic_C_decoration.pptx",
    "N160JCN-EEK project 1pcs NG sample analysis report 260810": "synthetic_B_single_placeholder.pptx",
}


def find_project_root() -> Path | None:
    """找專案根目錄(有 report/ 的那一層)。

    v3.1.5:改為 delegate 給 `fa_improver.paths`,不再自己維護候選清單。

    Returns:
        找到的根目錄,或 None(都找不到,例如技能包被單獨 clone)
    """
    return _find_project_root()


def resolve_input_pptx(stem: str) -> Path | None:
    """根據邏輯 pptx stem 找實際檔案路徑

    優先順序:
      1. 真實客戶 pptx(根倉庫 `report/{stem}.pptx`)
      2. 合成 fixture(`_synthetic_fixtures/{fallback_name}`)

    Args:
        stem: pptx 檔名不含副檔名(如 "260811_Kobo_ZHT_RA6080_SPcomFailI")

    Returns:
        找到的 Path,或 None(兩個來源都沒有)
    """
    real = resolve_report_file(f"{stem}.pptx")
    if real is not None:
        return real

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
    real = resolve_report_file(f"fa_report_{stem}.json")
    if real is not None:
        return real

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
      1. 動態找的 PROJECT_ROOT/report(見 `fa_improver.paths.get_report_dir`)
      2. fallback 到 SYNTHETIC_FIXTURE_DIR(讓技能包單獨 clone 時仍可寫入)
    """
    if _find_project_root() is not None:
        return _get_report_dir()
    return SYNTHETIC_FIXTURE_DIR


def is_synthetic(path: Path | None) -> bool:
    """判斷解出來的 fixture 是否為合成檔(而非真實客戶檔)。"""
    if path is None:
        return False
    return SYNTHETIC_FIXTURE_DIR in path.resolve().parents


def describe_fixture_sources() -> list[str]:
    """回傳每個已知 stem 目前解到哪一種來源,供診斷輸出使用。

    存在的理由:降級是靜默的。第一輪稽核的修正把硬編路徑「搬家」而非消除,
    失效方式因此從「看得見的 skip」變成「看不見的降級」,連續三輪稽核都沒
    發現。把來源印出來,是讓這種失效重新變得看得見的最低成本作法。
    """
    lines = []
    for stem in FIXTURE_FALLBACKS:
        path = resolve_input_pptx(stem)
        if path is None:
            source = "缺少"
        elif is_synthetic(path):
            source = "合成 fixture"
        else:
            source = "真實客戶檔"
        lines.append(f"{stem[:46]:48s} {source}")
    return lines
