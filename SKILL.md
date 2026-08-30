---
name: fa-report-improvement
description: Improve semiconductor failure analysis (FA) reports based on professional 8D evaluation criteria. v3.0 features modular architecture covering all 6 evaluation dimensions (100% trigger coverage), PPT/PPTX input support, JSON/TXT evaluation parsing, LLM integration (OpenAI-compatible), and 5 visual element generators. Master slide protection guaranteed through snapshot verification.
version: 3.0.0
entrypoint: src/fa_improver/__main__.py
inputs:
  - id: report
    label: FA 報告 (.ppt/.pptx)
    type: file
    accept: .ppt,.pptx
    icon: 📊
  - id: evaluation_json
    label: 評核檔案 (.json/.txt)
    type: file
    accept: .json,.txt
    icon: 📜
  - id: prompt
    label: 額外指令 (選填)
    type: text
    placeholder: 例如：用 LLM 評估、覆寫觸發門檻、指定樣板目錄...
    optional: true
---

# FA Report Improvement v3.0

半導體 **F**ailure **A**nalysis 報告的智慧化改善工具,基於 6 維度評分標準。

## ✨ v3.0 新特性

| 改進 | v2.3.0 | v3.0.0 |
|------|--------|--------|
| 架構 | 783 行單檔 | 35 模組化檔案 |
| 觸發改善維度 | 3/6 (50%) | **6/6 (100%)** |
| 母片保護 | 隱性 | 顯性測試驗證 |
| 樣板系統 | hard-coded | JSON 樣板 + 繼承 |
| 視覺元素 | 純文字 | 5 種生成器 |
| LLM 整合 | ❌ | ✅ OpenAI / 相容 API |
| 環境變數 | ❌ | ✅ .env 自動載入 |
| 測試覆蓋 | 0 | **89 個** |
| PPT 輸入 | 手動 | 自動轉換 |

## 🚀 快速開始

```bash
# 1. 安裝依賴(推薦使用 uv)
uv sync

# 2. 設定 API Key(可選,用 LLM 模式時需要)
cp .env.example .env
# 編輯 .env 填入 OPENAI_API_KEY

# 3. 執行
# 方式 A:使用預先生成的評估 JSON(推薦)
python -m fa_improver report.pptx --eval eval.json --output improved.pptx

# 方式 B:讓 LLM 直接評估(需 API key)
python -m fa_improver report.pptx --llm-provider openai --output improved.pptx

# 方式 C:離線測試(無需 API)
python -m fa_improver report.pptx --llm-provider mock --output improved.pptx
```

## 📊 6 維度評估 + 改善對應

| 維度 | 權重 | 觸發門檻 | 改善動作 |
|------|------|---------|---------|
| 基本資訊完整性 | 15% | < 80 | FA 編號、客戶、批號 |
| 問題描述與定義 | 15% | < 70 | 失效率、影響範圍 |
| 分析方法與流程 | 20% | < 70 | 8D 流程、方法對照 |
| 數據與證據支持 | 20% | < 70 | 對照組數據、圖片品質 |
| 根因分析 | 20% | < 80 | 5-Why、統計驗證 |
| 改善對策 | 10% | < 85 | 對策總覽、IQC SOP |

## 🛠️ 核心模組

```
src/fa_improver/         ← 主程式碼
├── domain/              純資料模型
├── parsers/             JSON/TXT/檔名解析
├── layout/              智慧選擇 + 母片保護
├── improvers/           8 種改善動作
├── templates/           8 個 JSON 樣板
├── visuals/             5 種視覺元素
├── llm/                 LLM 抽象 + OpenAI
└── utils/               PPT 轉換等
```

## 🧪 開發

```bash
# 跑測試
pytest tests/

# Lint
ruff check src/

# 端對端測試
python test_api_key.py         # 驗證 API key
python test_llm_end_to_end.py  # 完整 LLM 評估流程
```

## 📝 支援的輸入格式

- **報告**:`.pptx` (PowerPoint 2007+) / `.ppt` (97-2003,自動轉換)
- **評估**:`.json` / `.txt` (fa_report_analyzer_v3 格式)
- **環境**:`.env` 自動載入 (OPENAI_API_KEY 等)

## 🛡️ 設計原則

1. **母片絕對保護** — 自動驗證母片 XML 未變
2. **不破壞既有 layout** — 只用既有 layout 新增投影片
3. **向後相容** — 舊 CLI 仍可運作
4. **可配置** — 樣板可透過 JSON 覆寫
5. **獨立運作** — 任何團隊 clone 後可立即使用

## 📜 變更記錄

詳見 `CHANGELOG.md`。

## 📄 授權

MIT License
