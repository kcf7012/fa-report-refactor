- ✅ **多格式 JSON 相容 (v2.3.0)**: 同時支援 `dimensions`（扁平）與 `dimension_scores`（巢狀物件）格式
- ✅ **物件陣列 Improvements (v2.3.0)**: 支援 `improvements` 為字串陣列或物件陣列（含 priority/item/suggestion）
- ✅ **動態建議注入 (v2.2.0)**: 根據 JSON 評核建議動態生成投影片內容
- ✅ **執行回報清單 (v2.2.0)**: 自動產生 .manifest.json 供 LLM 封閉循環驗證
- ✅ **佈局強健性 (v2.1.5)**: 自動補救非標準版面

## 🚀 快速安裝

⚠️ **重要**: 強烈建議使用虛擬環境，避免污染全局 Python 環境和依賴衝突

### 方法 1: 使用 uv 安裝 (最推薦) 🚀

```bash
# 直接使用 uv 執行，無需手動管理虛擬環境
uv run scripts/improve_fa_report.py input.pptx eval.json output.pptx
```

### 方法 2: 使用虛擬環境安裝

```bash
# 1. 解壓 skill 文件
cd ~/.claude/skills/
unzip fa-report-improvement-v2.0.skill
cd fa-report-improvement

# 2. 創建虛擬環境
python -m venv venv

# 3. 啟動虛擬環境
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. 執行安裝腳本 (在虛擬環境中)
python scripts/install.py

# 使用完畢後退出虛擬環境
# deactivate
```

### 方法 2: 直接安裝 (不推薦)

```bash
# ⚠️ 注意: 會安裝到全局 Python 環境
cd ~/.claude/skills/
unzip fa-report-improvement-v2.0.skill
cd fa-report-improvement
python scripts/install.py
```

安裝腳本會自動:
- ✅ 檢查 Python 版本
- ✅ 安裝所有必需套件
- ✅ 檢測轉換工具
- ✅ 提供安裝指引

### 方法 2: 手動安裝

```bash
# 1. 安裝 Python 套件
pip install -r requirements.txt

# 2. 安裝轉換工具 (可選但推薦)

# Windows 用戶 - 選一個:
pip install pywin32              # 如果已有 PowerPoint
# 或從 https://www.libreoffice.org/ 安裝 LibreOffice

# Linux 用戶:
sudo apt install libreoffice

# macOS 用戶:
# 從 https://www.libreoffice.org/ 下載安裝
```

## 📋 依賴項目

### 必需 (Required)
- Python 3.7+
- python-pptx >= 0.6.21
- Pillow >= 9.0.0

### 可選 (Optional - 用於 .ppt 轉換)
- **LibreOffice** (跨平台) - 推薦
- **PowerPoint + pywin32** (Windows only)

## ✅ 驗證安裝

```bash
# 測試基本功能
python scripts/improve_fa_report.py --help

# 測試 .pptx 處理 (無需轉換工具)
python scripts/improve_fa_report.py test.pptx eval.json output.pptx

# 測試 .ppt 處理 (需要轉換工具)
python scripts/improve_fa_report.py test.ppt eval.json output.pptx
```

## 🎯 使用方法

```bash
# 基本用法
python scripts/improve_fa_report.py input.ppt eval.json output.pptx

# 支援的格式
python scripts/improve_fa_report.py report.ppt eval.json improved.pptx   # 自動轉換
python scripts/improve_fa_report.py report.pptx eval.json improved.pptx  # 直接處理
```

## 📚 文檔

- `SKILL.md` - 完整使用說明
- `references/ppt-conversion-guide.md` - PPT 轉換指南
- `references/evaluation-criteria.md` - 評估標準
- 外部文檔見下載包

## 🔒 虛擬環境最佳實踐

### 為什麼務必使用虛擬環境?

✅ **避免依賴衝突**: 不同專案的套件版本隔離  
✅ **保持系統乾淨**: 不污染全局 Python 環境  
✅ **易於管理**: 可以輕鬆刪除和重建環境  
✅ **可重現性**: 確保環境一致性  
✅ **無需 root**: 不需要管理員權限

### 虛擬環境使用流程

```bash
# 創建虛擬環境 (只需一次)
cd ~/.claude/skills/fa-report-improvement
python -m venv venv

# 每次使用前啟動
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 安裝依賴 (在虛擬環境中)
pip install -r requirements.txt

# 使用 skill
python scripts/improve_fa_report.py ...

# 完成後退出
deactivate
```

### 檢查是否在虛擬環境中

```bash
# 方法 1: 查看提示符
# 虛擬環境啟動後會顯示 (venv) 前綴
(venv) user@host:~$

# 方法 2: 檢查 Python 路徑
which python
# 虛擬環境: /path/to/fa-report-improvement/venv/bin/python
# 全局環境: /usr/bin/python 或 /usr/local/bin/python
```

## 🐛 故障排除

### 問題: "ModuleNotFoundError: No module named 'pptx'"

```bash
# 解決方案: 安裝 python-pptx
pip install python-pptx
```

### 問題: "LibreOffice not found"

```bash
# 解決方案: 安裝 LibreOffice
# Linux: sudo apt install libreoffice
# Windows/macOS: https://www.libreoffice.org/
```

### 問題: "COM conversion failed" (Windows)

```bash
# 解決方案: 安裝 pywin32
pip install pywin32
```

### 問題: "UnicodeEncodeError: 'cp950' codec..." (Windows)

```bash
# 解決方案: 腳本已內建 utf-8 強制輸出修正 (v2.1.2)
# 若仍有問題，請確保執行環境支援 UTF-8
```

## 💡 功能特性

- ✅ 支持 .ppt 和 .pptx 格式
- ✅ 自動格式轉換
- ✅ 6 維度評估系統
- ✅ 統計驗證整合
- ✅ 自動內容改善
- ✅ **PPT 佈局強健度優化 (自動處理非標準佈局)**
- ✅ 跨平台支持
- ✅ 支援兩種 JSON 格式 (陣列/物件)

## 📊 JSON 評估格式支援

### 格式 1: 陣列格式 (Array)
```json
[
  {
    "file_name": "report.ppt",
    "total_score": 44.3,
    "dimensions": {...}
  }
]
```

### 格式 2: 物件格式 (Object)
```json
{
  "file_name": "report.ppt",
  "total_score": 55.3,
  "dimensions": {...}
}
```

### 必要欄位
- `dimensions` 或 `dimension_scores` - 6 維度評分 (至少需要其中之一)
- `file_name` - 原始檔案名稱 (選填)
- `employee_name` - 負責工程師 (選填)

### 格式 3: 巢狀維度分數 (v2.3.0 新增)
```json
{
  "dimension_scores": {
    "基本資訊完整性": {"score": 60, "weight": 15, "comment": "..."}
  },
  "improvements": [
    {"priority": "高", "item": "基本資訊", "suggestion": "補填批號..."}
  ]
}
```
腳本會自動偵測並轉換所有格式。

## 📐 改善觸發閾值

| 維度 | 閾值 | 觸發改善 |
|------|------|----------|
| 基本資訊完整性 | < 80 | 添加基本資訊頁 |
| 根因分析 | < 80 | 添加統計驗證分析 |
| 改善對策 | < 85 | 添加長期預防措施 |

## 📞 支援

遇到問題? 查看:
1. 完整的安裝指南 (外部文檔)
2. PPT 轉換指南 (references/)
3. 故障排除指南 (外部文檔)

## 📝 版本

- 版本: 2.3.0
- 發布日期: 2026-02-05
- License: Apache 2.0

### 更新歷史
- **v2.3.0** (2026-02-05): 多格式 JSON 相容性強化。
    - 支援 `dimension_scores`（巢狀物件）自動轉換為 `dimensions`（扁平格式）。
    - 支援 `improvements` 為物件陣列（含 priority/item/suggestion）。
    - 從巢狀物件中自動提取 `comment` 至 `dimension_comments`。
- **v2.2.0** (2026-01-31): 導入動態內容注入與 Success Manifest。
- **v2.1.5** (2026-01-29): 佈局容錯優化。

## 🎉 開始使用

```bash
# 第一次測試
python scripts/improve_fa_report.py \
    /path/to/report.ppt \
    /path/to/evaluation.json \
    /path/to/output.pptx
```

Happy Reporting! 🚀
