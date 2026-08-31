# Changelog

All notable changes to fa-improver will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.0] - 2026-08-31

### 🔒 安全強化(LLM PII 個資遮罩)

#### `src/fa_improver/llm/redact.py` — 個資遮罩模組
- **支援遮罩類型**:
  - 電話:`0912-345-678` → `0912-***-678`
  - Email:`alice.wang@x.com` → `alice***@x.com`
  - 中文姓名(需職稱):`張三先生` → `張*先生`
  - IPv4:`192.168.1.100` → `192.168.1.***`
  - 工號:`EMP-12345` → `EMP***`
  - 身分證:`A123456789` → `A1***`
  - 信用卡:`4111 1111 1111 1111` → `**** **** **** 1111`
- **公開 API**:
  - `redact_pii(text)` — 遮罩文字
  - `redact_pii_with_stats(text)` — 遮罩並回傳統計
  - `is_pii_present(text)` — 快速偵測
  - `RedactionStats` — 追蹤各類型遮罩次數
- **OpenAIClient 整合**:`redact_pii_before_send=True` 自動遮罩 prompts
  - `total_redactions` 統計遮罩總數

### 🔄 重試機制(LLM Tenacity)

#### `src/fa_improver/llm/openai_client.py` 重寫 `complete()`
- 使用 `tenacity.Retrying`:
  - `stop_after_attempt(self.max_retries)` — 最多重試 3 次
  - `wait_exponential(multiplier=1, min=1, max=10)` — 指數退避 1s → 2s → 4s ...
  - `retry_if_exception(self._should_retry)` — 認證錯誤(401 / auth / api_key)**不重試**
- 抽出 `_do_call()` 為單次呼叫、`_classify_error()` 統一錯誤分類
- 重試時 `logger.warning` 記錄 `attempt_number`
- 新增 `tenacity>=8.2` 至 `[llm]` optional-dependencies

### 🎨 Improver TemplateLoader 完整整合

#### 7 個 improver 函式統一加入 TemplateLoader 支援
- `basic_info.py` — 標題 + placeholder items 從樣板讀取(7 個基本資料欄位)
- `root_cause.py` — 5_why / statistical 變體標題從樣板讀取
- `prevention.py` — 標題 + sections + placeholder items
- `summary.py` — section headings(Executive Summary / Key Improvements)
- `analysis_method.py` / `problem_definition.py` / `evidence_checklist.py` — 標題優先用樣板
- **完全向後相容**:`template_loader=None` 時自動 fallback 到預設標題

#### `src/fa_improver/improvers/_template_helper.py` 新模組
- `resolve_template(loader, name)` — 載入樣板
- `substitute_placeholders(text, variables)` — `{variable}` 替換
- `get_resolved_placeholders(template, section_index, variables)` — 取得套用變數後的 placeholder

#### `ImprovementOrchestrator` 新增 `template_loader` 參數
- 傳遞給所有 improver,統一管理

### 🎨 視覺元素整合

#### 3 個 improver 加入視覺生成器
- **`basic_info.py`** → `ChecklistGenerator`(checkbox 形式呈現基本資料)
- **`root_cause.py`** → `FlowDiagramGenerator`(5_why variant 呈現推導流程)
- **`prevention.py`** → `TimelineGenerator`(3 階段改善時程:短期 / 中期 / 長期)

### 🖥️ CLI 增強

#### `src/fa_improver/cli.py` 新增 3 個 CLI 參數
- `--api-key <key>` — OpenAI API key(優先於環境變數與 .env)
- `--redact-pii` — 啟用個資遮罩(對應 `redact_pii_before_send=True`)
- `--base-url <url>` — 自訂 API endpoint(Groq / OpenRouter / Azure 等 OpenAI 相容介面)

#### 修復預存 bug
- `f"   投影片:{1 if False else ''}..."` → `f"   投影片:{original} → {final}"`

### 🧪 測試強化

- `tests/unit/test_redact.py` — **35 個**新測試(個資遮罩各類型 + OpenAI 整合)
- `tests/unit/test_openai_client.py` — **10 個**新測試(tenacity 重試 + 錯誤分類)
- `tests/unit/test_template_integration.py` — **21 個**新測試(7 個 improver + 自訂樣板 + 視覺元素)
- `tests/unit/test_cli.py` — **8 個**新測試(argparse + 參數傳遞 + 端對端)
- `tests/unit/test_template_validation.py` — **27 個**新測試(SlideTemplate.validate() 邊界與錯誤情境)

### 📊 測試數據

| 指標 | v3.0.1 | v3.1.0 | 進步 |
|------|--------|--------|------|
| 測試通過 | 102 + 3 skipped | **203 + 3 skipped** | **+101 (+99%)** |
| 覆蓋率 | 85% | **90%** | **+5%** |
| `domain/template.py` 覆蓋 | 76% | **100%** | +24% |
| `cli.py` 覆蓋 | 0% | 78% | +78% |
| `openai_client.py` 覆蓋 | 80% | 88% | +8% |
| `llm/redact.py` 覆蓋 | N/A | 95% | 新模組 |

### 📚 文件

- 更新 `CHANGELOG.md`(本檔)
- 更新 `references/virtual-environment-guide.md`(加上 tenacity 註解)

### 🚀 安裝

```bash
# uv 使用者
uv sync --extra llm  # 新增 tenacity

# pip 使用者
pip install -e ".[dev,llm]"
```

---

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

## [3.1.1] - 2026-08-31

### 🐛 Bug 修正:批次版面渲染問題(v3.1.0 後遺症)

修正 `docs/handoff/2026-08-31-batch-eval-rendering-issues-handoff.md` 記錄的 8 張空白頁與座標錯位問題。

#### 🔴 P0:空白頁真凶是「missing action 分支」

**問題**:當評估結果嚴重度為 SEVERE 或 PREVENTION < 85 時,`build_plan()` 會加入 4 個 action:

```python
SlideAction.ADD_ROOT_CAUSE_CONTROL_GROUP  # SEVERE 時加入
SlideAction.ADD_ROOT_CAUSE_EVIDENCE        # SEVERE 時加入
SlideAction.ADD_IQC_STANDARD              # PREVENTION < 85 時加入
SlideAction.ADD_MONITORING_KM             # PREVENTION < 85 時加入
```

但 `_execute_action()` 沒有對應 elif 分支,導致:
1. `add_slide()` 建立一張新 slide
2. 什麼內容都不加進去
3. slide 被存進 pptx → **完全空白**

3 份報告都觸發,合計 8 張空白頁。

**修正**:
- 補上 4 個 missing action 的實作分支
- 新增 `add_iqc_standard_slide()`、`add_monitoring_km_slide()`(內容:IQC 抽驗比例、AQL 標準、KM 登錄頻率等)
- 新增 `add_5why_slide()` 統一 5_why / control_group / evidence 三個 variant
- 在 `orchestrator._execute_action()` 加 `else: warning`,防止未來又默默新增未實作的 action

#### 🟡 P1:座標超出 slide 邊界(13.33 in 寬螢幕 pptx)

**問題**:所有 improvers 與 visuals 的座標都 hard-coded(`Inches(0.5)`、`Inches(9.0)`),無法適應 MS / N160JCN 的 13.33 in 寬度。

**修正**:
- `orchestrator.execute()` 讀取 pptx 實際 `slide_width` / `slide_height`(EMU 轉 inch)
- 計算 `slide_bounds` 字典傳給每個 improver
- 7 個 improver 全部加 `slide_bounds` 參數支援
- 所有內容區寬度 = `slide_width - 2 * margin`(動態計算)

#### 🟢 其他修正

- **Visual generator Inches 重複套用 bug**:`ChecklistGenerator` / `ComparisonTableGenerator` / `TimelineGenerator` / `FlowDiagramGenerator` 的 `__init__` 內部會呼叫 `Inches(left)`,但幾個 improver 傳 `Inches(margin)`(已轉 EMU 的物件)給它,造成二次轉換 → shape 位置在 10^9 EMU 級別,完全離開 slide。
- **summary.py Executive Summary / Key Improvements 座標超界**:從 `Inches(7.5)` 改成動態右對齊(`content_w - tb_w + 0.5`),確保不超出 slide_width。

#### 🆕 新增工具

- **`src/fa_improver/improvers/_logging.py`** — 統一 logger + `log_action()` 上下文管理器
  - 環境變數 `FA_IMPROVER_DEBUG=1` 開啟 DEBUG log
  - 記錄每個 action 的開始、結束、耗時、失敗原因
  - 不污染 stdout(預設 INFO 寫到 stderr)
- **`tests/integration/test_slide_rendering.py`** — 7 個 smoke test,防止 P0/P1 再次發生:
  - `TestSlideRenderingNoEmptySlides`(3 個):260811 / MS / N160JCN 改善後不應有空白投影片
  - `TestSlideRenderingBounds`:所有 shape 都在 slide 邊界內(0.2 in 容忍)
  - `TestSlideRenderingSlideWidths`:orchestrator 正確讀取真實 slide 寬度
  - `TestSlideRenderingDynamicCoordinates`:content shape 寬度跟著 slide 寬度調整
  - `TestMasterProtectionStillPasses`:回歸測試母片保護仍通過

#### 統計數據

| 指標 | v3.1.0 | v3.1.1 |
|------|--------|--------|
| Unit test | 203 passed + 3 skipped | 203 passed + 3 skipped ✅(不變) |
| 新增 smoke test | 0 | **7 passed** ✅ |
| 總計 | 203 + 3 skipped | **210 + 3 skipped** |
| 覆蓋率 | 87% | **89%** |
| Ruff | 通過 | 通過 ✅ |

#### 真實批次執行結果

| 報告 | 原始 | v3.1.0 產出 | v3.1.1 產出 |
|------|------|-------------|-------------|
| 260811 (10×7.5 in) | 5 張 | 11 張(**3 空白**) | **13 張(全 OK)** ✅ |
| MS (13.33×7.5 in) | 5 張 | 12 張(**2 空白**) | **16 張(無新增空白)** ✅ |
| N160JCN (13.33×7.5 in) | 9 張 | 14 張(**3 空白**) | **18 張(無新增空白)** ✅ |

**原本 8 張空白頁全部消失**。

#### 相關文檔

- 問題分析:`docs/handoff/2026-08-31-batch-eval-rendering-issues-handoff.md`
- LLM vs Bug 修正策略評估:`docs/handoff/2026-08-31-llm-vs-bugfix-decision-handoff.md`(確認採用純修 bug,不安用 LLM)

#### 未修正項目(已記錄於 handoff § 10.5)

- 🟢 MS 原圖 slide 1 的「Prepared by: ELAN」shape 在 `(6.65, 5.99)` 接近右邊界 — 屬 pptx 原始母片設計,非生成 bug
- 🟢 母片覆蓋(文字被裝飾區蓋到)— 需先重新設計 pptx 母片
- 🟢 文字直式排版(autofit)— textbox 已動態 >= 4 in,但若母片設計特殊仍可能觸發

---

## 版本規範

- **Major (X.0.0)**:不相容的 API 變更
- **Minor (0.X.0)**:向下相容的功能新增
- **Patch (0.0.X)**:向下相容的 bug 修正

## 標籤

- `v3.1.1` — 修批次版面渲染問題(8 張空白頁 → 0、座標動態適應、+7 smoke test)
- `v3.1.0` — LLM 安全強化 + TemplateLoader 完整整合 + 視覺元素 + CLI 增強
- `v3.0.1` — Pre-commit + uv 依賴鎖定 + PPT 轉換測試
- `v3.0.0` — 模組化 + 6 維度完整覆蓋
- `v2.3.0` — 原始 baseline(已過時)
- `baseline-v2.3.0` — 對照用 baseline tag
