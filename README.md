# fa-report-improvement Skill

半導體 **F**ailure **A**nalysis(失效分析)報告智慧化改善工具。

## 版本

**v3.1.0** — PII 個資遮罩 + tenacity 重試 + TemplateLoader 完整整合(7/7) + 視覺元素(Checklist/Flow/Timeline)+ CLI 增強(8 參數)+ 101 個新測試(覆蓋率 85% → 90%)

> 更新紀錄見 [CHANGELOG.md](CHANGELOG.md)

## 快速開始

### 1. 安裝依賴

```bash
# 方式 A:使用 uv(推薦)
uv sync

# 方式 B:使用既有 .venv
python -m venv .venv && source .venv/bin/activate
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

### 4. 執行方式選擇

技能包提供 **3 種執行方式**(+ 1 種安裝後的系統指令):

| # | 方式 | 指令 | 適用情境 |
|---|------|------|---------|
| **1** | **新 CLI**(推薦) | `python -m fa_improver ...` | 日常使用、CI/CD |
| **2** | **傳統腳本** | `python scripts/improve_fa_report.py ...` | 向後相容舊版指令 |
| **3** | **端對端測試** | `python test_llm_end_to_end.py` | 開發測試、展示 |
| 4 | **系統指令** (需 `pip install -e .`) | `fa-improve ...` | 任何目錄、全域使用 |

#### 方式 1: `python -m fa_improver` (新 CLI · 推薦)

完整 argparse 介面、所有選項:

```bash
cd .agents/skills/fa-report-improvement
PYTHONPATH=src python -m fa_improver input.pptx \
    --eval eval.json \
    --output improved.pptx
```

#### 方式 2: `scripts/improve_fa_report.py` (傳統 CLI · 向後相容)

簡單位置參數,舊版用戶無需改指令:

```bash
python scripts/improve_fa_report.py input.pptx eval.json output.pptx
```

內部會自動委派為新 CLI 的命名參數(`--eval` / `--output`)。

#### 方式 3: 端對端測試程式

自動評估+改善+成本報告,適合開發測試與展示:

```bash
# 完整 LLM 評估 + 改善流程
python test_llm_end_to_end.py

# 指定報告
python test_llm_end_to_end.py /path/to/report.pptx

# 只驗證 API key
python test_api_key.py
```

#### 方式 4: 系統層級指令 `fa-improve` (安裝後)

安裝套件後,任何目錄都可以呼叫:

```bash
pip install -e .
fa-improve /path/to/report.pptx --eval /path/to/eval.json --output /path/to/output.pptx
```

#### 執行方式選擇指南

| 情境 | 推薦方式 |
|------|---------|
| 日常使用 | 方式 1 (`python -m fa_improver`) |
| 舊版指令相容 | 方式 2 (傳統腳本) |
| 開發/展示 | 方式 3 (端對端測試) |
| 系統整合 | 方式 4 (`fa-improve`) |

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
# 跑測試(105 個,含 .ppt 轉換、母片保護、LLM、樣板、視覺元素)
.venv/bin/python -m pytest tests/ -q

# 跑特定測試
.venv/bin/python -m pytest tests/unit/test_visual_generators.py -v

# 完整測試含覆蓋率
.venv/bin/python -m pytest tests/ --cov=fa_improver --cov-report=term-missing

# Lint
ruff check src/

# Pre-commit hooks(安裝一次,之後自動跑)
pip install pre-commit
pre-commit install
pre-commit run --all-files

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
├── templates/         # JSON 樣板(8 個內建)
├── visuals/           # 5 種視覺元素
├── llm/               # LLM Client
└── utils/             # 工具(PPT 轉換)

tests/                 # 105 個測試(102 passed + 3 skipped)
├── unit/              # 11 個單元測試模組
└── integration/       # 端對端測試

examples/              # 自訂樣板範例
references/            # 領域知識文件

# 設定檔
pyproject.toml         # 專案設定 + pytest + ruff + mypy + black
uv.lock                # 依賴鎖定(51 套件)
.pre-commit-config.yaml  # Git hooks(ruff / black / pytest)
```

## 授權

MIT License
