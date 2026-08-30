"""PPT 到 PPTX 轉換工具"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


class PPTConverter:
    """PPT (.ppt) 到 PPTX (.pptx) 轉換工具

    支援 LibreOffice(跨平台)與 pywin32(Windows only)兩種方法。
    """

    def __init__(self):
        self.temp_files: list[Path] = []

    def convert_if_needed(self, file_path: Path) -> Optional[Path]:
        """若輸入是 .ppt,自動轉換為 .pptx;.pptx 則直接返回"""
        file_ext = file_path.suffix.lower()

        if file_ext == ".pptx":
            return file_path

        if file_ext == ".ppt":
            return self.convert_ppt_to_pptx(file_path)

        # 其他副檔名:嘗試以 pptx 處理(可能會失敗,讓上層處理)
        return file_path

    def convert_ppt_to_pptx(self, ppt_path: Path) -> Optional[Path]:
        """嘗試將 .ppt 轉換為 .pptx"""
        pptx_path = ppt_path.with_suffix(".pptx")

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

    def _try_libreoffice(self, ppt_path: Path) -> Optional[Path]:
        """使用 LibreOffice 轉換"""
        libreoffice_paths = [
            "libreoffice",
            "/usr/bin/libreoffice",
            "/usr/bin/soffice",
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",  # macOS
        ]

        for cmd_path in libreoffice_paths:
            try:
                result = subprocess.run(
                    [cmd_path, "--version"],
                    capture_output=True,
                    timeout=3,
                )
                if result.returncode == 0:
                    # 找到 LibreOffice,執行轉換
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
                continue

        return None

    def _try_pywin32(self, ppt_path: Path) -> Optional[Path]:
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