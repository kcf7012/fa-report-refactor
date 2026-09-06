#!/usr/bin/env python3
"""
PPT 到 PPTX 轉換工具 v2.1.0
支持 LibreOffice 和 Windows COM 兩種方法
Updated: 2026-01-28
"""

import os
import subprocess
import sys
from pathlib import Path

# 探測邏輯統一由 fa_improver.utils.ppt_converter 提供(v3.1.5 P1)。
# 本腳本是 src/fa_improver/utils/ppt_converter.py 的前身,保留供既有流程呼叫。
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fa_improver.utils.ppt_converter import find_libreoffice  # noqa: E402

# 強制 stdout/stderr 使用 utf-8 編碼 (解決 Windows cp950 問題)
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


class PPTConverter:
    def __init__(self):
        self.temp_files = []

    def convert_ppt_to_pptx(self, ppt_path: str) -> str | None:
        """嘗試將 .ppt 轉換為 .pptx

        Args:
            ppt_path: .ppt 文件路徑

        Returns:
            轉換後的 .pptx 文件路徑，失敗返回 None
        """
        pptx_path = ppt_path.rsplit(".", 1)[0] + "_converted.pptx"

        # 方法 1: 嘗試使用 LibreOffice
        try:
            # 檢查 LibreOffice 是否安裝(共用探測,涵蓋 macOS/Linux/Windows)
            libreoffice_cmd = find_libreoffice()

            if libreoffice_cmd:
                print("✓ 找到 LibreOffice，進行轉換...")
                output_dir = os.path.dirname(ppt_path) or "."
                result = subprocess.run(
                    [
                        libreoffice_cmd,
                        "--headless",
                        "--convert-to",
                        "pptx",
                        "--outdir",
                        output_dir,
                        ppt_path,
                    ],
                    capture_output=True,
                    timeout=30,
                )

                if result.returncode == 0:
                    # LibreOffice 會生成與原文件同名但副檔名為 .pptx 的文件
                    auto_pptx = ppt_path.rsplit(".", 1)[0] + ".pptx"
                    if os.path.exists(auto_pptx):
                        print(f"✓ LibreOffice 轉換成功: {auto_pptx}")
                        self.temp_files.append(auto_pptx)
                        return auto_pptx
                    elif os.path.exists(pptx_path):
                        print(f"✓ LibreOffice 轉換成功: {pptx_path}")
                        self.temp_files.append(pptx_path)
                        return pptx_path
                else:
                    print(f"✗ LibreOffice 轉換返回非零狀態碼: {result.returncode}")
                    if result.stderr:
                        print(f"  錯誤: {result.stderr.decode('utf-8', errors='ignore')}")
        except Exception as e:
            print(f"✗ LibreOffice 轉換失敗: {e}")

        # 方法 2: 在 Windows 上嘗試使用 pywin32
        if os.name == "nt":
            try:
                import win32com.client

                print("✓ 使用 PowerPoint COM 進行轉換...")

                powerpoint = win32com.client.Dispatch("PowerPoint.Application")
                powerpoint.Visible = 1

                # 打開並轉換
                abs_ppt = os.path.abspath(ppt_path)
                abs_pptx = os.path.abspath(pptx_path)

                print(f"  打開: {abs_ppt}")
                deck = powerpoint.Presentations.Open(abs_ppt)

                print(f"  另存為: {abs_pptx}")
                # 24 = ppSaveAsOpenXMLPresentation
                deck.SaveAs(abs_pptx, 24)
                deck.Close()
                powerpoint.Quit()

                if os.path.exists(abs_pptx):
                    print(f"✓ COM 轉換成功: {abs_pptx}")
                    self.temp_files.append(abs_pptx)
                    return abs_pptx
            except Exception as e:
                print(f"✗ COM 轉換失敗: {e}")
                import traceback

                traceback.print_exc()

        return None

    def cleanup(self):
        """清理臨時文件"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"✓ 已清理臨時文件: {temp_file}")
            except Exception as e:
                print(f"✗ 無法刪除 {temp_file}: {e}")
