#!/usr/bin/env python3
"""
FA Report Improvement Skill - Installation Script v2.1.0
跨平台安裝腳本
Updated: 2026-01-28
"""

import os
import sys
import subprocess
import platform

# 強制 stdout/stderr 使用 utf-8 編碼 (解決 Windows cp950 問題)
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def print_header(text):
    """打印標題"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def check_virtual_environment():
    """檢查是否在虛擬環境中"""
    print_header("檢查虛擬環境")
    
    in_venv = (
        hasattr(sys, 'real_prefix') or  # virtualenv
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)  # venv
    )
    
    if in_venv:
        print("✓ 當前在虛擬環境中")
        print(f"  Python 路徑: {sys.prefix}")
        return True
    else:
        print("⚠️  當前不在虛擬環境中")
        print(f"  Python 路徑: {sys.prefix}")
        print("\n❗ 強烈建議使用虛擬環境安裝")
        print("\n為什麼需要虛擬環境:")
        print("  • 避免依賴衝突")
        print("  • 保持系統乾淨")
        print("  • 易於管理和刪除")
        print("  • 不需要 root 權限")
        
        print("\n創建虛擬環境:")
        print("  python -m venv venv")
        print("\n啟動虛擬環境:")
        if platform.system() == 'Windows':
            print("  venv\\Scripts\\activate")
        else:
            print("  source venv/bin/activate")
        
        # 詢問是否繼續
        print("\n")
        response = input("是否仍要繼續安裝到全局環境? (y/N): ").strip().lower()
        if response != 'y':
            print("\n已取消安裝。請創建虛擬環境後重試。")
            return False
        
        print("\n⚠️  將安裝到全局環境...")
        return True

def check_python_version():
    """檢查 Python 版本"""
    print_header("檢查 Python 版本")
    version = sys.version_info
    print(f"Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ 需要 Python 3.7 或更高版本")
        return False
    
    print("✓ Python 版本符合要求")
    return True

def install_python_packages():
    """安裝 Python 套件"""
    print_header("安裝 Python 套件")
    
    try:
        print("執行: pip install -r requirements.txt")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print("✓ Python 套件安裝成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 安裝失敗: {e}")
        print(e.stderr)
        return False

def check_libreoffice():
    """檢查 LibreOffice 是否安裝"""
    print_header("檢查 LibreOffice")
    
    libreoffice_paths = [
        'libreoffice',
        'soffice',
        '/Applications/LibreOffice.app/Contents/MacOS/soffice',  # macOS
        '/usr/bin/libreoffice',  # Linux
        'C:\\Program Files\\LibreOffice\\program\\soffice.exe',  # Windows
    ]
    
    for path in libreoffice_paths:
        try:
            result = subprocess.run(
                [path, '--version'],
                capture_output=True,
                timeout=3,
                text=True
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"✓ 找到 LibreOffice: {version}")
                return True
        except:
            continue
    
    print("⚠️  未找到 LibreOffice")
    return False

def check_powerpoint():
    """檢查 PowerPoint 是否安裝 (Windows only)"""
    if platform.system() != 'Windows':
        return False
    
    print_header("檢查 PowerPoint")
    
    try:
        import win32com.client
        try:
            powerpoint = win32com.client.Dispatch("PowerPoint.Application")
            version = powerpoint.Version
            powerpoint.Quit()
            print(f"✓ 找到 PowerPoint: 版本 {version}")
            return True
        except:
            print("⚠️  PowerPoint 未安裝或無法訪問")
            return False
    except ImportError:
        print("⚠️  pywin32 未安裝")
        return False

def print_installation_guide():
    """打印安裝指南"""
    system = platform.system()
    
    print_header("轉換工具安裝指南")
    
    if system == 'Windows':
        print("\n【Windows 用戶】")
        print("\n選項 A: 安裝 PowerPoint (推薦 - 最佳品質)")
        print("  1. 安裝 Microsoft Office (包含 PowerPoint)")
        print("  2. 安裝 pywin32:")
        print("     pip install pywin32")
        
        print("\n選項 B: 安裝 LibreOffice (免費)")
        print("  1. 下載: https://www.libreoffice.org/")
        print("  2. 執行安裝程式")
        print("  3. 重啟終端機")
        
    elif system == 'Linux':
        print("\n【Linux 用戶】")
        print("\n安裝 LibreOffice:")
        print("  sudo apt install libreoffice")
        print("  # 或")
        print("  sudo yum install libreoffice")
        
    elif system == 'Darwin':  # macOS
        print("\n【macOS 用戶】")
        print("\n安裝 LibreOffice:")
        print("  1. 下載: https://www.libreoffice.org/")
        print("  2. 拖曳到 Applications 資料夾")
        print("  3. 重啟終端機")

def print_summary(has_python, has_packages, has_converter):
    """打印總結"""
    print_header("安裝總結")
    
    print(f"\n✓ Python 版本: {'✓' if has_python else '❌'}")
    print(f"✓ Python 套件: {'✓' if has_packages else '❌'}")
    print(f"✓ 轉換工具: {'✓' if has_converter else '⚠️ 可選但推薦'}")
    
    if has_python and has_packages:
        print("\n🎉 基本安裝完成!")
        
        if not has_converter:
            print("\n⚠️  注意: 未檢測到轉換工具")
            print("   - .pptx 文件: ✓ 可以處理")
            print("   - .ppt 文件: ❌ 需要轉換工具")
            print("\n建議安裝 LibreOffice 或 PowerPoint 以支援 .ppt 格式")
        else:
            print("\n🚀 完整安裝成功! 支援 .ppt 和 .pptx 格式")
            
        print("\n下一步:")
        print("  python scripts/improve_fa_report.py --help")
    else:
        print("\n❌ 安裝未完成，請解決上述問題")

def main():
    """主函數"""
    print_header("FA Report Improvement Skill - 安裝程序")
    print(f"系統: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    
    # 檢查虛擬環境
    in_venv = check_virtual_environment()
    if not in_venv:
        # 用戶選擇不繼續
        sys.exit(1)
    
    # 檢查 Python 版本
    has_python = check_python_version()
    if not has_python:
        sys.exit(1)
    
    # 安裝 Python 套件
    has_packages = install_python_packages()
    
    # 檢查轉換工具
    has_libreoffice = check_libreoffice()
    has_powerpoint = check_powerpoint()
    has_converter = has_libreoffice or has_powerpoint
    
    # 如果沒有轉換工具，顯示安裝指南
    if not has_converter:
        print_installation_guide()
    
    # 打印總結
    print_summary(has_python, has_packages, has_converter)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  安裝被中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
