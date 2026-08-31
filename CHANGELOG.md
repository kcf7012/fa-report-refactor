# Changelog

All notable changes to fa-improver will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2026-08-31

### 🎉 重大重構(正式發布版)

從 783 行單體 `improve_fa_report.py` 重構為模組化架構,改善覆蓋率從 50% 提升到 100%。

### ✨ 新增

#### Phase 1: 模組化 + 母片保護
- **模組化架構**:從單一 783 行檔案拆分為 35 個模組
- **`src/fa_improver/` 結構**:
  - `domain/` — 純資料模型(Dimension, EvaluationResult, SlideTemplate, Improvement)
  - `parsers/` — 輸入解析(JSON / TXT / 檔名)
  - `layout/` — 智慧 layout 選擇 + **母片保護機制**
  - `improvers/` — 8 種改善動作
  - `templates/` — 8 個 JSON 樣板(可自訂)
  - `visuals/` — 5 種視覺元素生成器
  - `llm/` — LLM Client 抽象層 + OpenAI + Mock
  - `utils/` — PPT 轉換等工具
- **母片保護機制** `MasterProtector`:
  - 改善前擷取快照(masters_xml, layouts_xml, image_count)
  - 改善後自動驗證
  - `assert_can_add_slide()` 確保只用既有 layout
  - 4 個專屬單元測試
- **TXT 評估解析**:支援 fa_report_analyzer_v3 格式

#### Phase 2: 樣板系統
- **`SlideTemplate` dataclass**:完整樣板資料模型
- **8 個內建 JSON 樣板**(`templates/builtin/`):
  - `basic_info.json` — FA 基本資訊
  - `problem_definition.json` — 問題描述
  - `analysis_method.json` — 8D 流程
  - `evidence_checklist.json` — 數據證據
  - `root_cause_5why.json` — 5-Why 推導
  - `root_cause_statistical.json` — 統計驗證
  - `prevention_overview.json` — 改善對策
  - `executive_summary.json` — Summary 強化
- **樣板繼承語法**:`extends` 欄位
- **自訂目錄覆寫**:使用者可在不改程式碼下客製
- **品質約束驗證**:max_bullets, max_words, placeholder_items 等

#### Phase 3: LLM Client 抽象層
- **`LLMClient` Protocol**:可抽換的 LLM 介面
- **OpenAI Client**(也相容 Groq / Together / Azure / OpenRouter)
  - 自動重試與退避
  - Token 使用與成本追蹤
  - 環境變數優先,`OPENAI_API_KEY`
- **Mock Client**:離線測試用
- **LLM Evaluator**:從 pptx 評估自動產生 `EvaluationResult`
- **Prompts**:基於 `evaluation-criteria.md` 的 6 維度 System Prompt
- **.env 支援**:`python-dotenv` 自動載入

#### Phase 4: 視覺元素生成
- **5 種視覺元素生成器**:
  - `ChecklistGenerator` — checkbox 列表
  - `FlowDiagramGenerator` — 流程圖
  - `ComparisonTableGenerator` — 對照表
  - `ProgressBarGenerator` — 進度條
  - `TimelineGenerator` — 時間軸
- **ELAN 品牌色**(`visuals/colors.py`)
- **Summary 視覺化**:自動注入 6 維度評分進度條

#### Phase 4.5: 補齊 3 個缺失維度
- **覆蓋率從 50% 提升到 100%**
- 新增 3 個 Improver:
  - `ProblemDefinitionImprover` (問題描述與定義)
  - `AnalysisMethodImprover` (分析方法與流程,含 8D 流程)
  - `EvidenceChecklistImprover` (數據與證據支持,含對照組數據表)
- 觸發門檻從 3 個維度擴充至 6 個

#### Phase 5: 發布準備
- **PPT 自動轉換**:支援 .ppt 輸入(LibreOffice / pywin32)
- **GitHub Actions CI**:
  - 自動跑測試
  - 母片保護驗證
  - Lint 檢查
  - 套件建置
- **端對端測試程式**:
  - `test_api_key.py` — API key 驗證
  - `test_llm_end_to_end.py` — 完整 LLM 評估 + 改善流程
- **動態測試環境**:
  - `conftest.py` 完全動態(不寫死路徑)
  - 自動向上搜尋專案根目錄
  - 自動 skip 不可用資源
- **CHANGELOG.md** (本檔)
- **更新 SKILL.md** 反映 v3.0 新架構

### 🔧 改進

- **觸發門檻**:從 3 個維度擴充至 6 個
- **觸發改善動作**:從 9 個增加至 **12 個**
- **典型觸發**:低分報告從 5 張擴充到 12 張
- **視覺化**:每張投影片至少 1 個非純文字元素
- **錯誤處理**:LLM 4 種錯誤類型,自動重試

### 🐛 修正

- `xml_slides.insert(8, ...)` 邏輯錯誤改為動態計算
- Summary 強化不再誤刪原內容
- 8D 報告不再插入到錯誤位置
- placeholder height=0 導致渲染空白的 bug
- 日期解析從檔名尾部找 6 位數字
- `load_dotenv` 路徑修正(從 `find_dotenv(usecwd=True)`)
- 完全動態 conftest.py(不寫死路徑)
- `test_missing_api_key_raises` 使用 `skip_dotenv=True` 隔離

### 🧹 清理

- 刪除冗餘的 `fa-report-improvement-changelog.md`(已合併)
- 刪除開發文件 `PHASE5_TODO.md`(已搬到 `docs/`)
- 精簡 README.md(只說明技能包使用)

### 📊 測試

- **89 個測試**全部通過(原 0 個)
- **3 個跳過**(無範例資料)
- 母片保護 100% 通過
- 端對端 LLM 測試成功(成本 < $0.01/份報告)

### 📈 效益

| 指標 | v2.3.0 | v3.0.0 |
|------|-------|--------|
| 程式碼行數 | 783 單檔 | 35 模組 |
| 模組化 | ❌ | ✅ |
| 母片保護 | 隱性 | 顯性 + 測試 |
| 觸發改善維度 | 3/6 (50%) | **6/6 (100%)** |
| 觸發權重 | 45% | **100%** |
| 視覺元素 | 純文字 | 5 種生成器 |
| 樣板可配置 | ❌ | ✅ JSON |
| LLM 整合 | ❌ | ✅ OpenAI + Mock |
| .env 支援 | ❌ | ✅ |
| 單元測試 | 0 | **89** |
| PPT 自動轉換 | ❌ | ✅ |
| CI/CD | ❌ | ✅ GitHub Actions |

### 🔄 向後相容

- 舊 CLI 仍可運作:`python improve_fa_report.py input.pptx eval.json output.pptx`
- 新 CLI:`python -m fa_improver input.pptx --eval eval.json --output output.pptx`
- 兩者都委派給相同的底層架構

### 📦 安裝

```bash
# 推薦使用 uv
uv sync

# 或使用 pip
pip install -e ".[dev,llm]"

# 設定 API key(可選)
cp .env.example .env
# 編輯 .env 填入 OPENAI_API_KEY
```

## [2.3.0] - 2026-01-28

### 既有功能
- JSON / TXT 評估檔解析
- 基本資訊、根因分析、改善對策 3 個改善動作
- LibreOffice / pywin32 PPT 轉換
- fa_report_analyzer_v3 相容的評估格式

### 已知問題(已於 v3.0 修正)
- 783 行單檔,難以維護
- 無母片保護測試
- 樣板 hard-coded
- 無 LLM 整合
- 6 維度只覆蓋 3 個

---

## [3.0.1] - 2026-08-31

### ✨ 新增(開發者體驗)

#### Pre-commit + uv + 測試覆蓋強化
- **`.pre-commit-config.yaml`** — Git hooks 設定檔,含 4 大類:
  - `ruff` + `ruff-format` + `black`(格式化與 lint)
  - `pre-commit-hooks`(trailing-whitespace / check-yaml / check-json / detect-private-key 等)
  - `pytest` hook(母片保護 + 89 個測試自動驗證)
- **`uv.lock`** — 鎖定 51 個依賴套件,確保環境可重現(343 KB)
- **`tests/unit/test_ppt_converter.py`** — 新增 13 個 .ppt 轉換測試,涵蓋:
  - 副檔名判斷(.pptx 直通 / .ppt 轉換 / 大小寫不敏感 / 未知副檔名)
  - LibreOffice 整合(timeout / 找不到指令 / 非零退出碼)
  - cleanup 機制(刪除 tracked files / 處理已被刪除 / 權限錯誤 / 空列表)
- **`docs/05_api_reference.md`** — 完整 API 文件(35 模組 × 公開 API)

### 🔧 變更

- **`scripts/install.py`** — 從建議手動 `venv/` 改為推薦 `uv sync`(建立 `.venv/`)
- **`.pre-commit-config.yaml`** pytest hook entry:`venv/bin/python` → `.venv/bin/python`
- **移除舊 `venv/` 目錄**(106 MB 回收,統一用 uv-managed `.venv/`)
- **`docs/USER_GUIDE.md`** § 1.2 新增「執行方式選擇」對照表 + § 2.4 新增「執行方式詳細指令」(4 種方式)
- **`.agents/skills/fa-report-improvement/README.md`** 新增「4. 執行方式選擇」章節,與 USER_GUIDE 同步
- **`.agents/skills/handoff-doc-generator/`** — 新技能包,自動產生 8 大區塊交接文檔

### 📊 測試數據

| 指標 | v3.0.0 | v3.0.1 | 進步 |
|------|--------|--------|------|
| 測試通過 | 92(89 + 3 skipped) | **105**(102 + 3 skipped) | **+13** |
| 覆蓋率 | 83% | **85%** | **+2%** |
| `ppt_converter.py` 覆蓋 | 0% | 64% | +64% |

### 📚 文件

- 新增 `docs/handoff/2026-08-31-complete-phase5-todos-handoff.md`(本次任務交接)
- 新增 `docs/handoff/2026-08-31-rename-root-dir-handoff.md`(從根目錄 HANDOFF.md 搬入歸檔)
- 新增 `docs/handoff/2026-08-31-docs-3-exec-modes-handoff.md`(3 種執行方式文件交接)

---

## 版本規範

- **Major (X.0.0)**:不相容的 API 變更
- **Minor (0.X.0)**:向下相容的功能新增
- **Patch (0.0.X)**:向下相容的 bug 修正

## 標籤

- `v3.0.0` — 模組化 + 6 維度完整覆蓋
- `v2.3.0` — 原始 baseline(已過時)
- `baseline-v2.3.0` — 對照用 baseline tag
