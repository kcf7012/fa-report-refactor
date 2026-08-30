#!/usr/bin/env python3
"""
PPT 到 PPTX 轉換工具 v2.1.0
支持 LibreOffice 和 Windows COM 兩種方法
Updated: 2026-01-28
"""

import subprocess
import os
from pathlib import Path
from typing import Optional
import sys

# 強制 stdout/stderr 使用 utf-8 編碼 (解決 Windows cp950 問題)
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


class PPTConverter:
    def __init__(self):
        self.temp_files = []
    
    def convert_ppt_to_pptx(self, ppt_path: str) -> Optional[str]:
        """嘗試將 .ppt 轉換為 .pptx
        
        Args:
            ppt_path: .ppt 文件路徑
            
        Returns:
            轉換後的 .pptx 文件路徑，失敗返回 None
        """
        pptx_path = ppt_path.rsplit('.', 1)[0] + '_converted.pptx'
        
        # 方法 1: 嘗試使用 LibreOffice
        try:
            # 檢查 LibreOffice 是否安裝
            libreoffice_paths = [
                'libreoffice',
                '/Applications/LibreOffice.app/Contents/MacOS/soffice',  # macOS
                '/usr/bin/libreoffice',  # Linux
                'C:\\Program Files\\LibreOffice\\program\\soffice.exe',  # Windows
                'C:\\Program Files (x86)\\LibreOffice\\program\\soffice.exe',  # Windows 32-bit
            ]
            
            libreoffice_cmd = None
            for path in libreoffice_paths:
                try:
                    if os.path.exists(path) or subprocess.run(
                        [path, '--version'], 
                        capture_output=True, 
                        timeout=2
                    ).returncode == 0:
                        libreoffice_cmd = path
                        break
                except:
                    continue
            
            if libreoffice_cmd:
                print(f"✓ 找到 LibreOffice，進行轉換...")
                output_dir = os.path.dirname(ppt_path) or '.'
                result = subprocess.run(
                    [
                        libreoffice_cmd,
                        '--headless',
                        '--convert-to', 'pptx',
                        '--outdir', output_dir,
                        ppt_path
                    ],
                    capture_output=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    # LibreOffice 會生成與原文件同名但副檔名為 .pptx 的文件
                    auto_pptx = ppt_path.rsplit('.', 1)[0] + '.pptx'
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
        if os.name == 'nt':
            try:
                import win32com.client
                print(f"✓ 使用 PowerPoint COM 進行轉換...")
                
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


if __name__ == "__main__":
    converter = PPTConverter()
    
    ppt_file = r"C:\Users\KennyKang\Desktop\VibeCodingProj\fa-report-improvement-skill\ASUS NR2203_AUO_3pcs_NG_PCBA_Report_20220711.ppt"
    
    if os.path.exists(ppt_file):
        print(f"開始轉換: {ppt_file}\n")
        pptx_file = converter.convert_ppt_to_pptx(ppt_file)
        
        if pptx_file:
            print(f"\n✓ 轉換成功!")
            print(f"輸出文件: {pptx_file}")
        else:
            print(f"\n✗ 轉換失敗!")
    else:
        print(f"✗ 找不到文件: {ppt_file}")
