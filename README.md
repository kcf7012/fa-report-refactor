# fa-report-improvement Skill

半導體 **F**ailure **A**nalysis(失效分析)報告智慧化改善工具。

## 版本

**v3.0.0** — 模組化架構,6 維度完整覆蓋,LLM 整合

## 快速開始

### 1. 安裝依賴

```bash
# 方式 A:使用 uv(推薦)
uv sync

# 方式 B:使用既有 venv
pip install -e ".[dev,llm]"
```

### 2. 設定 OpenAI API Key(可選,LLM 模式需要)

```bash
cp .env.example .env
# 編輯 .env,填入 OPENAI_API_KEY
```

### 3. 執行

#### 方式 A:預先準備評估 JSON(推薦)

```bash
python -m fa_improver report.pptx \
  --eval eval.json \
  --output improved.pptx
```

#### 方式 B:用 LLM 直接評估(實驗性)

```bash
python -m fa_improver report.pptx \
  --llm-provider openai \
  --output improved.pptx
```

#### 方式 C:離線測試(無需 API)

```bash
python -m fa_improver report.pptx \
  --llm-provider mock \
  --output improved.pptx
```

## 輸入格式

| 副檔名 | 說明 |
|--------|------|
| `.pptx` | PowerPoint 2007+ |
| `.ppt` | PowerPoint 97-2003(自動轉換) |
| `.json` | fa_report_analyzer_v3 評估結果 |
| `.txt` | fa_report_analyzer_v3 文字輸出(已支援) |

## 6 維度評估 + 改善對應

| 維度 | 權重 | 觸發門檻 | 改善動作 |
|------|------|---------|---------|
| 基本資訊完整性 | 15% | < 80 | 新增 FA 基本資訊 |
| 問題描述與定義 | 15% | < 70 | 新增問題描述 |
| 分析方法與流程 | 20% | < 70 | 新增 8D 流程 |
| 數據與證據支持 | 20% | < 70 | 新增證據清單 |
| 根因分析 | 20% | < 80 | 5-Why + 統計驗證 |
| 改善對策 | 10% | < 85 | 改善對策總覽 |

## 開發

```bash
# 跑測試
pytest tests/

# 跑特定測試
pytest tests/unit/test_visual_generators.py -v

# Lint
ruff check src/

# 端對端測試(需要 .env)
python test_api_key.py
python test_llm_end_to_end.py
```

## 結構

```
src/fa_improver/      # 主程式碼(35 模組)
├── domain/            # 純資料模型
├── parsers/           # 輸入解析
├── layout/            # 母片保護
├── improvers/         # 8 種改善動作
├── templates/         # JSON 樣板
├── visuals/           # 5 種視覺元素
├── llm/               # LLM Client
└── utils/             # 工具(PPT 轉換)

tests/                 # 89 個測試
examples/              # 自訂樣板範例
references/            # 領域知識文件
```

## 授權

MIT License
