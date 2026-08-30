# FA Report Improvement Skill — 版本差異報告

**舊版本**: v2.0（無明確版號）  
**新版本**: v2.3.0  
**更新日期**: 2026-01-31

---

## 🔑 核心變更摘要

| 類別 | 舊版 | 新版 |
|------|------|------|
| 版本號 | 無版號 | v2.3.0 |
| JSON 格式支援 | 單一格式 | 3 種格式自動識別 |
| 改善建議內容 | 硬寫死靜態文字 | 動態從 LLM 評核 JSON 注入 |
| 執行驗證 | 無 | 自動產生 `_manifest.json` |
| Windows 編碼 | 可能 cp950 錯誤 | 強制 UTF-8 輸出 |
| 主腳本行數 | 429 行 | 611 行（+182 行） |

---

## 📄 SKILL.md 變更

### 新增 Frontmatter 欄位
新版加入了 `version`、`entrypoint`、`inputs` 定義，讓 Skill 支援 UI 表單渲染：
```yaml
version: 2.3.0
entrypoint: scripts/improve_fa_report.py
inputs:
  - id: report        # FA 報告 (.ppt/.pptx)
  - id: evaluation_json  # 評核 JSON
  - id: prompt        # 優化提示詞（選填）
```

### 新增 JSON 格式文件說明
明確列出三種支援的 JSON 輸入格式（Array / Object / Nested dimension_scores），提升使用者理解度。

### 新增改善觸發門檻表
```
| Dimension    | Threshold | Action                          |
|根因分析      | < 80      | 從 LLM 動態注入統計分析建議     |
|改善對策      | < 85      | 從 LLM 動態注入預防措施建議     |
```

### 新增 Manifest 說明章節
說明 `_manifest.json` 的結構與用途（Closed-Loop 驗證機制）。

### 新增 Windows 編碼問題說明
Error Handling 章節新增 cp950 / UTF-8 的處理說明。

---

## 🐍 improve_fa_report.py 變更（v2.0 → v2.1.5）

### 新增函式（4 個）

#### 1. `sanitize_json_content(content)`
清理 AI 產生的 JSON 常見格式問題：
- 移除 Markdown 代碼塊標記（`` ```json ``）
- 移除結尾多餘標點符號（`}.`、`},`）
- 修正物件/陣列結尾的多餘逗號

#### 2. `normalize_improvement_item(imp)`
正規化改善項目格式，支援兩種輸入：
- **格式 A（字串）**: `"[高] 基本資訊: 補填批號..."`
- **格式 B（物件）**: `{"priority": "高", "item": "基本資訊", "suggestion": "補填批號..."}`

#### 3. `extract_suggestions(eval_data)`
從評核 JSON 動態提取 LLM 建議文字，並依維度分類（基本資訊完整性 / 根因分析 / 改善對策 / 圖表品質）。

#### 4. `get_or_create_title(slide)` / `get_or_create_body(slide)`
安全取得或建立投影片的標題與內文區塊，避免 placeholder 存取失敗。

---

### 修改函式（3 個）

#### `load_evaluation(eval_path)`
- **舊版**: 直接 `json.load()`，遇到格式問題會崩潰
- **新版**: 先呼叫 `sanitize_json_content()` 清理，再解析；並自動識別 Array / Object 格式

新增支援 `dimension_scores` 巢狀格式自動轉換為標準 `dimensions` 格式：
```python
# 新版自動正規化
if 'dimensions' not in eval_data and 'dimension_scores' in eval_data:
    # 將 {score, weight, comment} 物件格式轉為標準格式
```

#### `add_statistical_analysis_slide(prs, eval_data)` ← 新增參數
- **舊版**: `add_statistical_analysis_slide(prs)` — 靜態硬寫分析內容
- **新版**: 接收 `eval_data`，從 `extract_suggestions()` 取出 LLM 的具體根因分析建議，動態注入投影片

#### `add_prevention_measures_slide(prs, eval_data)` ← 新增參數
- **舊版**: `add_prevention_measures_slide(prs)` — 靜態硬寫預防措施
- **新版**: 從評核 JSON 動態注入 LLM 建議的改善對策文字

---

### `improve_report()` 新增功能

#### Manifest 自動輸出
執行完成後自動寫出 `[output].manifest.json`，記錄：
```json
{
  "execution_status": "success",
  "added_slides": [{"dimension": "Root Cause", "suggestions_count": 3}],
  "dimensions_improved": ["根因分析", "改善對策"],
  "summary_applied": true
}
```

#### Windows UTF-8 強制設定
腳本頂部加入：
```python
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
```
解決 Windows 終端機 cp950 編碼造成的中文亂碼。

---

## 📚 README.md 變更

版本號從 v2.0 更新至 v2.3.0，新增各版本功能說明章節（v2.1.4 JSON sanitize / v2.2.0 動態注入 + Manifest / v2.3.0 多格式相容）。

---

## 🗂️ References 文件

`evaluation-criteria.md` 與 `improvement-templates.md` 有小幅更新（約各 6 行差異），其餘 references 檔案無變更。

---

## ✅ 升級建議

直接替換 `~/.claude/skills/fa-report-improvement/` 目錄內容即可。  
無需重新安裝 Python 套件（`requirements.txt` 無變更）。
