"""驗證套件本身真的可以 import —— 防止 editable install 靜默失效。

## 為什麼需要這支測試

`tests/conftest.py` 會主動把 `src/` 插進 `sys.path`,所以**即使 editable
install 完全失效,整個測試套件仍然全綠**。但此時:

    $ uv run python -m fa_improver --help
    .venv/bin/python3: No module named fa_improver
    $ uv run fa-improve --help
    ModuleNotFoundError: No module named 'fa_improver'

也就是 `CLAUDE.md` 記載的主要執行指令是壞的,而測試不會告訴你。
這正是柔伊第五輪查證抓到的問題 —— 當時 commit message 還宣稱該指令
「已實測通過」(實測當下為真,但之後環境變了,沒有回頭複驗)。

## 已知成因

專案位於 iCloud Drive 同步範圍內時,venv 裡的 `.pth` 檔會被設上 macOS 的
`UF_HIDDEN` 旗標,而 Python 的 `site.addpackage()` 會**直接跳過** hidden 的
`.pth`(見 CPython `site.py`),於是 editable install 的路徑從未進入
`sys.path`。詳見
`docs/handoff/2026-09-05-execution-findings-for-zoe-handoff.md` 發現 2。

## 這支測試的設計

用**子行程**跑 import,並帶 `-E` 讓它忽略 `PYTHONPATH` 等環境變數 ——
這樣才是在測「套件有沒有真的被安裝好」,而不是在測「conftest 有沒有幫忙
插路徑」。只有在套件確實已安裝(有 dist-info)時才斷言,所以「只用原始碼樹、
沒有 install」的情境會乾淨 skip,不會誤報。
"""

from __future__ import annotations

import subprocess
import sys
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path

import pytest

_DIST_NAME = "fa-improver"


def _is_installed() -> bool:
    """套件是否已安裝進目前的環境(以 dist-info 為準)。

    dist-info 是目錄掃描,不受 `.pth` 是否生效影響 —— 所以「已安裝但
    import 不到」這個組合正好就是我們要抓的故障。
    """
    try:
        distribution(_DIST_NAME)
    except PackageNotFoundError:
        return False
    return True


_needs_install = pytest.mark.skipif(
    not _is_installed(),
    reason=f"{_DIST_NAME} 未安裝進此環境(純原始碼樹執行),此檢查不適用",
)

_REMEDY = (
    "\n\n可能成因:venv 的 .pth 檔被設了 macOS 的 UF_HIDDEN 旗標,"
    "site.addpackage() 因此跳過它。\n"
    "應急:chflags -R nohidden <專案根目錄>\n"
    "根治:把專案搬出 iCloud Drive 同步範圍(~/Desktop 與 ~/Documents 都在範圍內)。"
)


def _run_isolated(args: list[str]) -> subprocess.CompletedProcess[str]:
    """在子行程執行,並忽略 PYTHONPATH/PYTHONHOME(-E)。"""
    return subprocess.run(
        [sys.executable, "-E", *args],
        capture_output=True,
        text=True,
        timeout=60,
    )


class TestPackageIsProperlyInstalled:
    """editable install 健康檢查"""

    @_needs_install
    def test_import_without_syspath_injection(self):
        """不靠 conftest 插路徑,套件也要 import 得到"""
        result = _run_isolated(["-c", "import fa_improver; print(fa_improver.__file__)"])
        assert result.returncode == 0, (
            f"套件已安裝卻 import 不到 —— editable install 失效。\n"
            f"stderr: {result.stderr.strip()}{_REMEDY}"
        )

    @_needs_install
    def test_module_entry_point_runs(self):
        """`python -m fa_improver --help` 要能跑(CLAUDE.md 記載的主要指令)"""
        result = _run_isolated(["-m", "fa_improver", "--help"])
        assert result.returncode == 0, (
            f"`python -m fa_improver --help` 失敗。\nstderr: {result.stderr.strip()}{_REMEDY}"
        )
        assert "usage:" in result.stdout.lower()

    @_needs_install
    def test_imports_the_expected_copy(self):
        """import 到的要是這個工作目錄的 src/,不是別處的另一份

        只驗「import 得到」不夠 —— venv 裡可能躺著 iCloud 產生的 .pth 衝突副本
        (實測看過 `_editable_impl_fa_improver 2.pth`),內容若指向舊路徑,
        Python 會安靜地載入另一份程式碼,而前兩個測試完全抓不到。
        """
        result = _run_isolated(["-c", "import fa_improver; print(fa_improver.__file__)"])
        assert result.returncode == 0, f"import 失敗:{result.stderr.strip()}{_REMEDY}"

        loaded = Path(result.stdout.strip()).resolve()
        expected_dir = (Path(__file__).resolve().parents[2] / "src" / "fa_improver").resolve()
        assert loaded.parent == expected_dir, (
            f"import 到的不是預期的那一份。\n"
            f"  實際:{loaded}\n  預期位於:{expected_dir}\n"
            f"可能是 venv 內有指向舊路徑的 .pth 衝突副本 —— "
            f"檢查 site-packages 裡有沒有「原名 + 空格 + 數字」的 .pth。"
        )
