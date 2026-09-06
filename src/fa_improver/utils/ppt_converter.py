"""PPT 到 PPTX 轉換工具"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

# LibreOffice 執行檔的候選位置(依優先序)。
#
# v3.1.5(跨平台遷移 P1):原本專案內有**四份**互不一致的探測邏輯
# (本檔、scripts/ppt_converter.py、scripts/install.py、scripts/visual_smoke_test.py)。
# 其中 visual_smoke_test.py 只查 `shutil.which("libreoffice")`,而 macOS 的
# LibreOffice 預設不把 `libreoffice` 或 `soffice` 放進 PATH,導致裝了也偵測不到。
# 現在統一由 :func:`find_libreoffice` 提供。
#
# PATH 優先於固定路徑,讓使用者能用自己的安裝覆寫。
_LIBREOFFICE_FIXED_PATHS = (
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",  # macOS(預設不進 PATH)
    "/opt/homebrew/bin/soffice",  # macOS Homebrew(Apple Silicon)
    "/usr/local/bin/soffice",  # macOS Homebrew(Intel)
    "/usr/bin/libreoffice",  # Linux
    "/usr/bin/soffice",  # Linux
    r"C:\Program Files\LibreOffice\program\soffice.exe",  # Windows
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",  # Windows 32-bit
)


def find_libreoffice() -> str | None:
    """找出可用的 LibreOffice 執行檔路徑。

    Returns:
        可執行的路徑字串;找不到時回傳 ``None``。

    先查 PATH(`soffice` 再 `libreoffice`),再依序檢查各平台的預設安裝位置。
    只確認檔案存在且可執行,**不**實際執行 `--version`(啟動 LibreOffice 很慢,
    而且冷啟動時可能超過 timeout 造成偽陰性)。
    """
    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return found

    for candidate in _LIBREOFFICE_FIXED_PATHS:
        path = Path(candidate)
        if path.is_file():
            return str(path)

    return None


def libreoffice_install_hint() -> str:
    """依目前平台回傳正確的 LibreOffice 安裝指令。

    原本各處錯誤訊息一律寫死 `apt install libreoffice`,在 macOS 上是錯的。
    """
    if sys.platform == "darwin":
        return "brew install --cask libreoffice"
    if sys.platform == "win32":
        return "從 https://www.libreoffice.org/download/ 下載安裝"
    return "sudo apt install libreoffice(或使用該發行版的套件管理器)"


class PPTConverter:
    """PPT (.ppt) 到 PPTX (.pptx) 轉換工具

    支援 LibreOffice(跨平台)與 pywin32(Windows only)兩種方法。
    """

    def __init__(self):
        self.temp_files: list[Path] = []

    def convert_if_needed(self, file_path: Path) -> Path | None:
        """若輸入是 .ppt,自動轉換為 .pptx;.pptx 則直接返回"""
        file_ext = file_path.suffix.lower()

        if file_ext == ".pptx":
            return file_path

        if file_ext == ".ppt":
            return self.convert_ppt_to_pptx(file_path)

        # 其他副檔名:嘗試以 pptx 處理(可能會失敗,讓上層處理)
        return file_path

    def convert_ppt_to_pptx(self, ppt_path: Path) -> Path | None:
        """嘗試將 .ppt 轉換為 .pptx"""
        # 方法 1: LibreOffice
        result = self._try_libreoffice(ppt_path)
        if result and result.exists():
            self.temp_files.append(result)
            return result

        # 方法 2: pywin32(Windows only)
        if sys.platform == "win32":
            result = self._try_pywin32(ppt_path)
            if result and result.exists():
                self.temp_files.append(result)
                return result

        return None

    def _try_libreoffice(self, ppt_path: Path) -> Path | None:
        """使用 LibreOffice 轉換

        v3.1.5:探測邏輯改用共用的 :func:`find_libreoffice`(原本這裡自己列
        四個候選路徑,漏了 macOS Homebrew 與 Windows)。
        """
        cmd_path = find_libreoffice()
        if cmd_path is None:
            return None

        try:
            output_dir = ppt_path.parent
            proc = subprocess.run(
                [
                    cmd_path,
                    "--headless",
                    "--convert-to",
                    "pptx",
                    "--outdir",
                    str(output_dir),
                    str(ppt_path),
                ],
                capture_output=True,
                timeout=60,
            )
            if proc.returncode == 0:
                # LibreOffice 會生成同名 .pptx
                converted = ppt_path.with_suffix(".pptx")
                if converted.exists():
                    return converted
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return None

        return None

    def _try_pywin32(self, ppt_path: Path) -> Path | None:
        """使用 pywin32(Windows)"""
        try:
            import win32com.client

            powerpoint = win32com.client.Dispatch("PowerPoint.Application")
            powerpoint.Visible = 1
            abs_ppt = str(ppt_path.absolute())
            abs_pptx = str(ppt_path.with_suffix(".pptx").absolute())

            deck = powerpoint.Presentations.Open(abs_ppt)
            deck.SaveAs(abs_pptx, 24)  # 24 = ppSaveAsOpenXMLPresentation
            deck.Close()
            powerpoint.Quit()

            return ppt_path.with_suffix(".pptx")
        except Exception:
            return None

    def cleanup(self) -> None:
        """清理轉換過程中的臨時檔"""
        for temp_file in self.temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except OSError:
                pass
