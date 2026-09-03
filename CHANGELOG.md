# Changelog

All notable changes to fa-improver will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.4-regression-fix] - 2026-09-04

### 🛡️ 標題偏左回歸修正

Kenny 2026-09-03 視覺驗收 v3.1.4 時回饋「標題又偏左」,本次修正 v3.1.3 修法不完整的系統性問題。

#### 對照檢查結果

`grep -rn "margin = 0\.5" src/fa_improver/improvers/` 結果:**8 個檔案,11 處 `margin = 0.5` 殘留**。

v3.1.3 handoff 只記錄了 `basic_info.py` 一個檔案,實際還有 7 個檔案沒改乾淨:

- `summary.py`(Executive / Key Improvements / Dimension Progress slide)
- `root_cause.py`(5-Why 流程圖 + 根因驗證 slide)
- `analysis_method.py`、`evidence_checklist.py`
- `problem_definition.py`、`prevention.py`

Helper 函式內部還有 8 處 `left=0.5` 寫死(`_add_8d_checklist`、`_add_method_comparison_table` 等),獨立於頂層 margin 修改。

#### 修正策略

用 `TITLE_SAFE_LEFT_INCH - 0.2 = 1.0`(而非 1.2)統一所有 margin:

```python
margin = TITLE_SAFE_LEFT_INCH - 0.2  # = 1.0
if margin < 0.5:
    margin = 0.5
```

**為什麼用 1.0 不是 1.2**:
- 對 10 in 標準寬度 slide(260811):margin=1.0 → content_w=8.0,測試 ≥ 8.0 通過
- 對 13.33 in 寬度 slide(MS、N160JCN):margin=1.0 → content_w=11.33,通過
- 與 `_safe_shape.safe_textbox` fallback 邏輯一致

#### 修改清單(8 個檔案,18 處)

| 檔案 | 修改處 | 改法 |
|------|--------|------|
| `basic_info.py` | L67(頂層 ×1) | `margin = TITLE_SAFE_LEFT_INCH - 0.2` + floor |
| `summary.py` | L116, L163, L213(頂層 ×3) | 同上 |
| `root_cause.py` | L49, L236(頂層 ×2) | 同上 |
| `analysis_method.py` | L54(頂層)+ L83, L104(helper ×2) | 頂層同 + helper 用 `TITLE_SAFE_LEFT_INCH - 0.2` |
| `evidence_checklist.py` | L54(頂層)+ L83, L107(helper ×2) | 同上 |
| `problem_definition.py` | L53(頂層)+ L82, L115(helper ×2) | 同上 |
| `prevention.py` | L46, L205(頂層 ×2)+ L273(helper ×1) | 同上 |
| `root_cause.py` | L189(helper ×1) | `left=TITLE_SAFE_LEFT_INCH - 0.2` |

所有檔案頂部新增 `from ._safe_shape import TITLE_SAFE_LEFT_INCH`。

#### 驗證

- 本機 pytest:233 passed, 3 skipped
- 模擬 CI (`FA_REPORT_PROJECT_ROOT=/nope/1`):233 passed, 3 skipped
  - 包含 `test_260811_standard_width_has_dynamic_shapes` 通過(content_w=8.0 in)
- ruff check:All checks passed
- ruff format:All 39 files formatted
- 母片保護測試:全綠(無 master XML 變動)

#### GitHub Actions CI(Run #25)

| Job | Python | 結果 |
|-----|--------|------|
| Test (Python 3.10) | 3.10 | ✅ success |
| Test (Python 3.11) | 3.11 | ✅ success |
| Test (Python 3.12) | 3.12 | ✅ success |
| Lint & Format | — | ✅ success |
| Build Distribution | — | ✅ success |

URL:https://github.com/kcf7012/fa-report-refactor/actions/runs/33769352155

#### 視覺驗收

3 份報告改善後 pptx → 53 張 PNG,slide-07 範例:

| Shape | 修正前 left | 修正後 left |
|-------|-------------|--------------|
| 標題「分析方法與流程」 | 1.20 in | 1.20 in |
| D1-D8 checkbox | **0.50 in**(被裝飾擋住) | **1.00 in**(對齊) |
| D1-D8 文字 | 0.85 in(被裝飾擋住) | 1.35 in(對齊) |

驗收頁:`docs/handoff/screenshots/v3.1.4-regression-visual-review.html`

#### 排除的問題

- **Kenny 母片層級的「D0/Symptom」標題 left=0.04 in**(母片內建 layout,非 fa_improver 生成) — 需修母片 XML,超出本專案範圍,列入 v3.1.5 backlog
- **`_safe_shape.py:263` 的 `margin = 0.5`**(floor 邏輯) — 保留,合理的下限保護

#### 給未來 Agent 的教訓

1. **不要只信單元測試**:v3.1.4 修正前單元測試全綠,但視覺仍錯。**一定要跑改善 + 截圖驗證**
2. **別只看 Kenny 提到的單檔**:本次 Kenny 只說「標題偏左」,但 grep 整個系統發現 8 檔案都有問題
3. **rebase 衝突 markers 殘留風險**:reset --hard 後必須 `git diff` 確認無衝突 markers,再 force-push
4. **Helper 不應寫死 left=0.5**:應透過參數從頂層傳入,或直接引用模組常數(如 `TITLE_SAFE_LEFT_INCH - 0.2`)

---

## [3.1.4] - 2026-09-03

### 🔍 稽核修正與測試誠實化

依據柔伊 2026-09-02 獨立稽核報告 (`docs/handoff/2026-09-02-fa-report-refactor-audit-handoff.md`),
本次 release 修正了 3 項稽核揭露的問題,並把測試結果的「誠實度」提升一個層級。

#### 1. 🟡 conftest fixture 陷阱修正(`tests/conftest.py`)

**稽核發現**:全新 clone 環境跑 `pytest tests/` 會爆 `IsADirectoryError: Is a directory: '.'`。
**根因**:`sample_pptx/sample_eval_json/sample_eval_txt` 在找不到檔案時回傳 `Path("")`,
而 `Path("").exists()` 永遠回傳 True,`Path("").resolve()` 解析成當前 cwd。

**修法**:
- Fixture 找不到時改回傳 `None`(return type 改為 `Path | None`)
- 13 處呼叫端把 `if not X.exists(): pytest.skip(...)` 改為 `if X is None: pytest.skip(...)`
- 保留原本 fallback 到 `candidates[0]` 的邏輯,只改 `None` fallback

**驗證**:全新 clone(無任何 report 檔案)改完後,**219 passed, 3 skipped, 0 fail**,
且 3 個 skip 都是測試內部動態路徑,不是 IsADirectoryError。

#### 2. 🟡 5-Why fallback 重設計(`src/fa_improver/improvers/root_cause.py`)

**稽核發現**:`_add_5why_flow_diagram()` 有 3 個 bug:
- `s.split("。")[0][:15]` 在沒有「。」時 return 整段,再 `[:15]` 從字中間切
- 15 字太短(中文 15 字差不多一句完整建議,英文 15 char 才 2-3 個單字)
- 強制補滿 5 個步驟(通用「Why 2~5」佔位),與實際內容無關

**修法**:
- 新增 `_truncate_step_text()` helper,同時認中英文句號「。」與「.」
- 若 `len(text) <= max_chars` 原樣返回(不從中間切)
- 若有句號取第一句,無句號才按 max_chars 切
- `_add_5why_flow_diagram()` 重寫 fallback:suggestions 非空時只截斷實際 suggestions,
  suggestions 為空時才 fallback 到預設 5 步(向後相容)

**新增 14 個單元測試**(`tests/unit/test_root_cause.py`):
- TestTruncateStepText(6):短文字/空字串/中文句號/英文句號/無句號/不切中間
- Test5WhyFlowDiagram(8):短建議不切/中文切句/英文切句/2 個建議無假佔位/
  3 個建議/5 個建議/6 個建議截到 5 個/空 suggestions fallback

#### 3. 🔴 視覺回歸測試改用合成 fixture(讓 CI 真在跑)

**稽核發現**:16 個視覺回歸測試(`tests/integration/test_visual_quality.py` + `test_slide_rendering.py`)
寫死 `PROJECT_ROOT = Path("/home/elan/fa-report-refactor")`,依賴的客戶 pptx 被 `.gitignore` 排除。
CI 環境跑這些測試時永遠 skip——安全網形同虛設。

**修法**:
- 新增 `scripts/build_synthetic_fixtures.py`:程式化產生 3 個**完全去識別化**合成 pptx + eval JSON
  - `synthetic_A_vertical`:用 layout[9] "Title and Vertical Text"(含 "Vertical" 關鍵字,觸發 Bug 3 防護)
  - `synthetic_B_single_placeholder`:Blank layout + 0.3 in 小 textbox(< BODY_MIN_HEIGHT,觸發 v3.1.3 修正)
  - `synthetic_C_decoration`:母片含 LeftTopDecoration 矩形(left=0, top=0, w=1in, h=0.5in,觸發 TITLE_SAFE_LEFT_INCH)
- 新增 `tests/integration/_fixture_resolver.py`:動態解析 fixture 路徑
  - 環境變數 `FA_REPORT_PROJECT_ROOT` 可覆蓋路徑(用 `:` 分隔)
  - 預設找 `/home/elan/fa-report-refactor` + GitHub Actions 路徑
  - 找不到真實 pptx 時 fallback 到合成 fixture
- 新增 `tests/integration/_synthetic_fixtures/`(3 個 fixture,公開可見)
- 修改 `tests/integration/test_visual_quality.py`(9 個測試)+ `tests/integration/test_slide_rendering.py`(7 個測試),
  全部改用 `resolve_input_pptx/resolve_eval_json`
- 順手修掉**稽核發現 #1**(`ruff format --check` 卡住的 2 個測試檔)— v3.1.3 以來 CI 一直紅燈的根因

**公開安全**:3 個合成 pptx 完全去識別化(無 ELAN logo、無真實客戶名稱、無機密文字),
使用 python-pptx 預設母片 + 純灰底,公開放在 repo 是安全的。

#### 4. 📝 版本號同步 + CHANGELOG 條目

依據根倉庫 `docs/handoff/2026-08-31-v310-git-push-summary.md §5.3 步驟 4` 發版 checklist:
- `pyproject.toml`: 3.1.0 → 3.1.4
- `src/fa_improver/__init__.py`: 3.0.0 → 3.1.4
- `SKILL.md` frontmatter: 3.1.0 → 3.1.4
- CHANGELOG.md: 新增 v3.1.4 條目(本條目)+ 修正「標籤」表格(見下)

### 📊 v3.1.4 統計

| 指標 | v3.1.3 | v3.1.4 |
|------|--------|--------|
| 測試通過 | 219 | 233(+14:5-Why 新測試) |
| 測試 skip | 3 | 3(都是測試內部動態路徑) |
| 覆蓋率 | 90% | 90% |
| ruff check | ✅ | ✅ |
| ruff format | ❌(CI 從 08-31 起紅燈) | ✅ **稽核發現 #1 順手解決** |
| CI Build Distribution | 一直被 skip | ✅ **v3.1.4 起重跑** |
| CI 狀態 | ❌(自 v3.1.3 起持續紅燈) | ✅ **5/5 jobs success** |
| 視覺回歸測試 CI | ❌ 永遠 skip(硬編路徑 + .gitignore) | ✅ **真在跑**(用合成 fixture) |
| 合成 fixture | — | 3 個(完全去識別化) |

### 🔗 PR & 相關

- PR #1: https://github.com/kcf7012/fa-report-refactor/pull/1
- 稽核報告: `docs/handoff/2026-09-02-fa-report-refactor-audit-handoff.md`
- 改善計畫: `docs/handoff/2026-09-03-audit-remediation-plan-handoff.md`
- 5 commits: 18bb4cd, c87136f, 27495b1, fc521fb, 5b48690

---

## [3.1.3] - 2026-09-02

### 🎨 用戶回饋版面優化 — Kenny 2026-09-02 反饋的 3 個版面問題

#### 1. 修正「簡報標題偏左」(3 份報告)

**位置**:`src/fa_improver/improvers/_safe_shape.py` + `src/fa_improver/improvers/basic_info.py`

**問題**:母片左上角裝飾(深藍直條 + 淺藍色塊位於 x=0.54-0.97 in)
會擋住 title 的第一個字。

**修正**:
- 新增常數 `TITLE_SAFE_LEFT_INCH = 1.2`(避免裝飾區)
- `get_or_create_title()` fallback 的 safe_textbox 從 `left=0.5` 改為 `left=1.2`,height 從 `1.0` 改為 `0.85`
- `basic_info.py` 的 `_get_or_create_title` 統一改用 `_safe_shape.get_or_create_title`(原本 hard-code margin=0.5)

**影響**:3 份報告 title 全部不再被裝飾擋住

#### 2. 修正「標題與內容重疊」(MS Page 10/13/14、N160JCN Page 12/15/16)

**位置**:`src/fa_improver/improvers/_safe_shape.py`

**問題**:`Topic-Numbers` 與 `2L - Topic` layout 的 body placeholder 高度只有 0.51 in,
無法容納 heading + 多個 bullets,造成內容溢出到 title 區。

**修正**:
- 新增常數 `BODY_MIN_HEIGHT_INCH = 1.0`
- `get_body_placeholder()` 當 layout placeholder 高度 < 1.0 in 時,
  return None → fallback 用 `safe_textbox` 重新建立 body(高度 = `sh - 2.0`)
- `get_title_placeholder()` 當 layout 沒有 idx=0 placeholder 且只有 ≤ 1 placeholder 時,
  return None → fallback 用 `safe_textbox` 避免重疊

**影響**:body 區有充足空間容納 heading + bullets,不再與 title 重疊

#### 3. 移除「6 維度評分分析」slide(預設關閉)

**位置**:`src/fa_improver/improvers/summary.py` + `src/fa_improver/improvers/orchestrator.py` + `src/fa_improver/cli.py`

**問題**:Kenny 2026-09-02 反饋:終端用戶不需要看到「6 維度評分分析」slide
(這是內部評分指標)。

**修正**:
- `enhance_summary_section()` 新增 `include_dimension_chart: bool = False` 參數
  (keyword-only,向後相容)
- `ImprovementOrchestrator` 新增 `include_dimension_chart` 屬性
- CLI 新增 `--include-dimension-chart` flag(預設關閉,符合 Kenny 意願)

**用法**:
```bash
# 預設不產生「6 維度評分分析」slide
uv run python -m fa_improver input.pptx --eval eval.json --output out.pptx

# 若需要(opt-in):
uv run python -m fa_improver input.pptx --eval eval.json --include-dimension-chart --output out.pptx
```

#### 4. 新增視覺回歸測試(`tests/integration/test_visual_quality.py`)

新增 4 個測試類別 / 4 個測試方法:

- `TestNoTitleDecorationOverlap::test_title_textbox_safe_left` — 驗證 title textbox left >= 1.2 in
- `TestBodyHasEnoughHeight::test_no_overlap_between_title_and_body` — 驗證 body 不與 title 重疊 + body.height >= 1.0 in
- `TestDimensionChartOptIn::test_dimension_chart_skipped_by_default` — 驗證預設不出現「6 維度評分分析」slide
- `TestDimensionChartOptIn::test_dimension_chart_enabled_with_flag` — 驗證 `--include-dimension-chart` 正常運作

#### 5. 統計

| 指標 | v3.1.2 | v3.1.3 |
|------|--------|--------|
| Unit test | 203 passed | 203 passed ✅(不變) |
| slide_rendering smoke test | 7 passed | 7 passed ✅ |
| visual_quality smoke test | 5 passed | **9 passed** ✅(+4 個 v3.1.3 測試) |
| **總計** | 215 + 3 skipped | **219 + 3 skipped** |
| 覆蓋率 | 89% | **90%** ✅ |
| Ruff | All checks passed | All checks passed ✅ |

#### 6. 真實批次執行

| 報告 | v3.1.2 產出 | v3.1.3 產出 |
|------|-------------|-------------|
| 260811 (10×7.5) | 16 張 | **15 張** ✅(少 1 張 dim chart) |
| MS (13.33×7.5) | 19 張 | **18 張** ✅(少 1 張 dim chart) |
| N160JCN (13.33×7.5) | 21 張 | **20 張** ✅(少 1 張 dim chart) |

**視覺驗證**:透過 `scripts/visual_smoke_test.py` 產出 53 張 PNG(15+18+20),已人工檢查:
- ✅ 標題完整顯示(不被裝飾擋住)
- ✅ 標題與內容不重疊
- ✅ 母片保護 100% 通過(3 份報告)
- ✅ 最後一頁不再是「6 維度評分分析」

詳見 `docs/handoff/2026-09-01-v313-user-feedback-fixes-handoff.md`。

---

## [3.1.2] - 2026-09-01

### 🐛 Bug 修正:v3.1.1 殘留的 4 類版面渲染問題

延續 handoff `2026-09-01-v311-incomplete-rendering-handoff.md` 的 4 大殘留問題:
1. 🔴 Bug 1:`enhance_summary_section` 疊加覆蓋(MS-001、N160JCN-001)
2. 🟡 Bug 2:`_get_or_create_title` 找錯 placeholder(MS / N160JCN 多張)
3. 🟡 Bug 3:textbox / placeholder 被旋轉 90°(260811 多張)
4. 🟡 Bug 4:底部 placeholder 殘留(N160JCN 多張)

加上視覺驗證腳本,避免再次發生。

#### 🔴 Bug 1:`enhance_summary_section` 疊加覆蓋

**位置**:`src/fa_improver/improvers/summary.py`(完整重寫)

**修正策略**:
- 從「疊加在原 Summary 投影片」改為「新增獨立投影片」
- 在原 Summary 之後新增 3 張 slide(Executive Summary / Key Improvements / 6 維度評分進度條)
- 原 Summary 投影片不被修改

#### 🟡 Bug 2:`_get_or_create_title` 找錯 placeholder

**位置**:`src/fa_improver/improvers/_safe_shape.py`(新增)

**修正策略**:
- `get_title_placeholder()` 嚴格用 `placeholder_format.idx == 0`
- 檢查 `slide_layout.name`,若含「直排」或 "Vertical" 則跳過 layout placeholder
- fallback 使用 `safe_textbox()`(帶 `rotation=0` 與 `auto_size=None`)

**影響範圍**:7 個 improvers 改用新 helper(`basic_info`、`analysis_method`、`evidence_checklist`、`problem_definition`、`prevention`、`root_cause`、`summary`)

#### 🟡 Bug 3:textbox / placeholder 被旋轉 90°

**位置**:`src/fa_improver/improvers/_safe_shape.py` 的 `get_body_placeholder()`

**根本原因**:
- 260811 pptx 的某些 layout 名稱含「直排標題及文字」
- body placeholder 的 `orient='vert'`(垂直中文排版)

**修正策略**:
- 在 `get_body_placeholder()` 檢查 layout name 並跳過
- 同時將 placeholder 的 `orient` 改為 `horiz`
- fallback 用 `safe_textbox()`(`rotation=0`)

#### 🟡 Bug 4:底部 placeholder 殘留

**位置**:`src/fa_improver/improvers/_safe_shape.py` 的 `clean_unused_placeholders()` + `orchestrator.py`

**修正策略**:
- `clean_unused_placeholders()` 改為「從 slide 移除整個 placeholder 元素」
- 在 `orchestrator.execute()` 每個 action 結束後自動呼叫

#### 🆕 新增工具

- `src/fa_improver/improvers/_safe_shape.py`(共用 helper,235 行)
- `scripts/visual_smoke_test.py`(視覺驗證腳本,99 行)
- `tests/integration/test_visual_quality.py`(5 個新測試)

#### 統計數據

| 指標 | v3.1.1 | v3.1.2 |
|------|--------|--------|
| Unit test | 203 passed | 203 passed ✅(不變) |
| slide_rendering smoke test | 7 passed | 7 passed ✅ |
| visual_quality smoke test | 0 | **5 passed** ✅ |
| **總計** | 210 + 3 skipped | **215 + 3 skipped** |
| 覆蓋率 | 89% | 89% ✅ |
| Ruff | 通過 | 通過 ✅ |

#### 真實批次執行

| 報告 | 原始 | v3.1.1 產出 | v3.1.2 產出 |
|------|------|-------------|-------------|
| 260811 (10×7.5) | 5 張 | 13 張(含 3 張旋轉) | **16 張(無旋轉)** ✅ |
| MS (13.33×7.5) | 5 張 | 16 張(標題被覆蓋) | **19 張(標題清楚)** ✅ |
| N160JCN (13.33×7.5) | 9 張 | 18 張(疊加、殘留) | **21 張(獨立 slide)** ✅ |

**視覺驗證圖片數**:56 張(260811: 16 + MS: 19 + N160JCN: 21)

詳見 `docs/handoff/2026-09-01-v312-final-fixes-handoff.md`。

---

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

### 📈 效益

v3.1.0 主要提升面向:

- 🛡️ **安全性**:LLM 送出前自動遮罩個資(PII),避免 OpenAI API 讀取敏感資料(電話/Email/中文姓名/IP/工號/身分證/信用卡)
- 🔄 **可靠性**:LLM 瞬時錯誤自動重試(tenacity 指數退避 1s → 2s → 4s),減少手動 retry
- 🎨 **可維護性**:7 個 improver 統一從 JSON 樣板讀取標題與 placeholder items,後續修改只需改 JSON 不用改程式
- 🖥️ **使用者體驗**:CLI 參數從 5 個提升到 8 個(`--api-key`、`--redact-pii`、`--base-url`),支援更多 API 與自訂 endpoint
- 🧪 **測試涵蓋**:203 個測試通過,覆蓋率 90%(較 v3.0.1 提升 5%)

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

| Tag | 對應版本 | GitHub Release | 本地 tag | 重點 |
|-----|---------|----------------|---------|------|
| `v3.1.4` | 2026-09-03 | ✅ | ✅ | 稽核修正 + CI 從紅轉綠 + 視覺回歸測試誠實化 |
| `v3.1.3` | 2026-09-02 | ✅ | ✅ | 修 3 個版面問題(標題偏左/重疊/6 維度圖)+ 加 4 個視覺回歸測試 |
| `v3.1.2` | 2026-09-01 | ✅ | ✅ | 修 v3.1.1 殘留的 4 類版面渲染問題(疊加/placeholder/旋轉/殘留)+ 加視覺驗證腳本 |
| `v3.1.1` | 2026-08-31 | ❌ 已刪 | ❌ 已刪 | **注意**:被 v3.1.2 取代 |
| `v3.1.0` | 2026-08-31 | ✅ | ✅ | LLM 安全強化(PII 遮罩+tenacity 重試)+ TemplateLoader 完整整合 + 視覺元素 + CLI 增強 |
| `v3.0.1` | 2026-08-31 | ❌ | ✅(未 push) | 補 Pre-commit + uv(僅本地) |
| `v3.0.0` | 2026-08-31 | ❌ | ✅(未 push) | 模組化 + 6 維度覆蓋(僅本地) |
| `v2.3.0` | 2026-01-28 | ❌ | ❌ | 不存在(推測應為「原始 baseline」之稱) |
| `baseline-v2.3.0` | — | ❌ | ❌ | 不存在 |
