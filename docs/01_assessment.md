# FA Report Improvement Skill — 完整評估報告

> **評估對象**:`fa-report-improvement` 技能包 v2.3.0(含本次 session hotfix)
> **評估日期**:2026-08-30
> **Baseline Tag**:`baseline-v2.3.0`
> **評估者**:Claude Code(Kenny Kang 委託)

---

## 一、現況量化指標

| 項目 | improve_fa_report.py | ppt_converter.py | install.py |
|------|---------------------|------------------|------------|
| 行數 | **783** | 151 | 248 |
| 函數 | 17 | 4 | 8 |
| 類別 | **0** | 1 | 0 |
| Hard-coded `Inches()` 座標 | **47** | 0 | 0 |
| Hard-coded `Pt()` 字級 | **19** | 0 | 0 |
| 中文字串字面量 | 約 **60+** | 0 | 30+ |
| 模組化程度 | 單體(monolith) | 單一類別 | 程序式 |

### 模組依賴
```
- python-pptx (核心)
- Pillow (間接,經 python-pptx)
- json, os, re, sys, subprocess, shutil, datetime (stdlib)
- typing.Optional (3.7+ 型別提示)
```

### 檔案結構(重構前)
```
fa-report-improvement/
├── SKILL.md                        # 技能說明(主入口)
├── README.md
├── fa-report-improvement-changelog.md
├── requirements.txt                # 依賴清單
├── .agents/                        # 子目錄(略)
├── docs/                           # 本次新增
├── references/                     # 5 個 markdown 參考文件
│   ├── evaluation-criteria.md
│   ├── improvement-templates.md
│   ├── statistical-methods.md
│   ├── ppt-conversion-guide.md
│   └── virtual-environment-guide.md
└── scripts/
    ├── improve_fa_report.py        # ★ 783 行單體
    ├── ppt_converter.py
    └── install.py
```

---

## 二、發現的問題(依嚴重性排序)

### 🔴 P0 — 必須修正

#### 1. 缺乏 LLM 整合,流程斷裂
- **問題**:腳本**只能接受預先生成的 JSON**,不能自行呼叫 LLM 評估報告
- **影響**:沒有上游 fa_report_analyzer_v3 或其他 LLM 工具就完全無法使用
- **痛點**:SKILL.md `inputs` 只接受 `.json` 檔案,但實際工作流通常是「我有 .pptx,需要先評估再改善」

#### 2. SKILL.md 宣稱支援 `.txt` 但實作不存在
- **問題**:SKILL.md Quick Start 第 2 步寫 "Parse evaluation **JSON or text feedback**",且 README 也寫 "Parse JSON or text feedback",但 `load_evaluation()` **完全沒實作 .txt 解析**
- **證據**:本 session 收到的第二份評估檔就是 `.txt`,必須先手動轉成 `.json` 才能執行
- **影響**:使用者預期與實際行為不符

#### 3. 完全沒有單元測試
- **問題**:無 `tests/` 目錄、無 pytest、無 CI
- **影響**:重構風險極高;本次 session 已修正 5+ 個 bug 都是 ad-hoc 修正
- **缺失覆蓋**:
  - `load_evaluation()` 三種 JSON 格式
  - `extract_suggestions()` 物件陣列 vs 字串陣列
  - `find_content_layout()` 評分啟發式
  - `move_slide_to_position()` 邊界條件
  - 檔名日期解析(本次新邏輯的 6 種邊界)

#### 4. 缺乏結構化日誌與錯誤恢復
- **問題**:全程使用 `print()`,無 logging、無 try/except 細粒度
- **影響**:失敗時難以診斷;部分流程(例如 LibreOffice 轉換失敗後直接 return None)沒有 fallback 策略說明

---

### 🟠 P1 — 應該修正

#### 5. 大量 hard-coded 字串、座標、字級
- **問題**:47 個 `Inches()` 座標、19 個 `Pt()` 字級、60+ 中文字串直接寫死在程式碼
- **範例**:
```python
# 全部 hard-code,沒有樣板系統
p.text = "FA 基本資訊"               # 標題
p.font.size = Pt(28)                  # 字級
title_box.top = Inches(0.85)          # 座標
content.left = Inches(1.6)            # 座標
textbox.position = (Inches(5.5), Inches(2.3))  # 座標
```
- **影響**:
  - 無法在不修改程式碼的情況下調整版型
  - 不同 layout 需要 hard-coded 微調
  - 無法 A/B 測試不同設計

#### 6. 缺乏樣板系統(Templating)
- **問題**:5 個 `references/*.md` 文件定義了「Template 1-5」,但**程式碼完全沒引用這些樣板**
- **影響**:樣板文件與實作脫節,淪為純文件

#### 7. Layout 自動選擇啟發式過於簡單
- **問題**:`find_content_layout()` 只看 layout 名稱是否含 "Topic" / "Content"
- **風險**:某些 pptx 可能會誤選(例如 layout 名稱為英文 "Topic" 但實際是封面)
- **應有**:基於 placeholder 結構(數量、位置)、shape type 統計、實例投影片用法的多特徵評分

#### 8. 沒有型別提示(Type Hints)
- **問題**:除 `Optional` 外,函數參數與返回值完全沒有型別標註
- **影響**:無 IDE 自動完成、無 mypy 檢查、重構風險高

#### 9. 沒有資料類別(Dataclass)封裝
- **問題**:評估結果 `eval_data` 是裸 `dict`,在函數間傳遞時欄位名稱散落各處
- **影響**:typo 不會被偵測;重構時需要全域搜尋

#### 10. 無國際化/在地化(i18n)框架
- **問題**:所有中文訊息、標題、評語都 hard-code
- **影響**:無法服務其他語系使用者;語意改進需要修改程式碼

---

### 🟡 P2 — 建議修正

#### 11. 沒有 CLI 子命令
- **問題**:目前只有 3 個位置參數,沒有 `argparse` 支援
- **影響**:無法 `--dry-run`、無法 `--verbose`、無法選擇 layout

#### 12. 沒有設定檔機制
- **問題**:所有設定(座標、字級、顏色)都寫死
- **影響**:不同團隊/部門/報告類型無法客製化

#### 13. Manifest 格式未標準化
- **問題**:`manifest.json` 是 ad-hoc dict,沒有 schema 驗證
- **影響**:下游自動化消費 manifest 沒有保障

#### 14. 沒有 PDF/PNG 預覽
- **問題**:本次 session 用 `soffice + pdftoppm` 是 ad-hoc 流程
- **影響**:腳本無法直接生成視覺驗證

#### 15. 無 progress bar
- **問題**:大型 pptx 處理時使用者不知道進度
- **影響**:UX 差

#### 16. 無並行處理
- **問題**:批次處理多份報告時只能序列執行
- **影響**:無法利用多核

#### 17. 與上游 fa_report_analyzer_v3 解耦不夠
- **問題**:技能包直接假設輸入是 fa_report_analyzer_v3 的 JSON 格式
- **影響**:換成其他評估工具需要修改 `extract_suggestions()` 邏輯

#### 18. 沒有 CLI 自描述
- **問題**:`--help` 只顯示非常簡短的使用說明
- **影響**:新手不易上手

#### 19. 測試覆蓋率工具缺失
- **問題**:沒有 pytest、coverage.py 設定
- **影響**:無法量化測試覆蓋率

#### 20. 沒有 pre-commit / linting
- **問題**:無 ruff、black、flake8 設定
- **影響**:程式碼風格不一致

---

## 三、評估 LLM 整合可行性

### 目標
讓技能包**不需要預先準備 JSON**,可自行呼叫 LLM 評估 pptx,並產生改善版本。

### 3.1 技術可行性分析

| 項目 | 評估 | 備註 |
|------|------|------|
| LLM API 通用性 | ✅ 完全可行 | OpenAI API 已成業界標準(OpenAI、Azure、Groq、Together、OpenRouter、Anthropic 都有相容介面) |
| pptx 評估準確度 | ✅ 可行 | fa_report_analyzer_v3 已在做同樣的事 |
| 評估 prompt 工程 | ⚠️ 需要 | 需把 evaluation-criteria.md 的 6 維度評分標準翻譯成 system prompt |
| 成本 | ⚠️ 中等 | GPT-4o 評估一份 10 頁報告約 $0.05-0.20 |
| 隱私/資料外洩 | ⚠️ 需注意 | 報告內容會送到第三方 API |
| 本地 LLM 替代 | ✅ 可行 | Ollama + llama3.1-vision 可離線處理 |

### 3.2 架構設計建議

```
使用者輸入 (.pptx + 可選 .json)
        │
        ▼
┌─────────────────┐
│ 1. PPTParser    │ ← 解析所有投影片文字/表格/圖片描述
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Evaluator    │ ← (可選)呼叫 LLM API 進行 6 維度評分
│    (LLM Client) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Improver     │ ← 根據評分 + JSON 決定改善動作
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. ManifestGen  │ ← 產生執行清單
└─────────────────┘
```

### 3.3 LLM 整合設計選項

#### 方案 A:CLI 直接呼叫
```bash
python improve_fa_report.py report.pptx \
    --llm-provider openai \
    --api-key $OPENAI_API_KEY \
    --model gpt-4o-mini
```
**優點**:簡單、低耦合  
**缺點**:每次都要付 API 費用;LLM 結果無法快取

#### 方案 B:兩階段(評估快取)
```bash
# 階段 1:評估,結果存 JSON(可重複使用、版控)
python fa_evaluate.py report.pptx --output eval.json

# 階段 2:改善(沿用現有 JSON 流程)
python fa_improve.py report.pptx eval.json --output improved.pptx
```
**優點**:分離關注點、評估結果可審核、可離線改善  
**缺點**:多一步驟

#### 方案 C:一鍵 + 評估快取(推薦)
```bash
python fa_improve.py report.pptx \
    --llm-api-key $KEY \
    --cache-eval ./evals/  \
    --output improved.pptx
```
**優點**:兼顧便利性與可審核性  
**缺點**:實作稍複雜

### 3.4 LLM Client 抽象層設計

```python
from abc import ABC, abstractmethod
from typing import Protocol

class LLMClient(Protocol):
    """所有 LLM provider 都應實作此介面"""

    def evaluate_report(self, pptx_content: str,
                       rubric: str) -> EvaluationResult:
        """根據 rubric 評估報告,回傳結構化結果"""
        ...

# 具體實作
class OpenAIClient: ...
class AnthropicClient: ...
class OllamaClient: ...  # 本地
class MockClient: ...    # 離線/測試用
```

### 3.5 Prompt 工程建議

需要設計兩個 prompt:
1. **System Prompt**:固定內容,描述 6 維度評分標準(來自 `evaluation-criteria.md`)
2. **User Prompt**:動態內容,包含報告摘要(投影片標題、表格內容、圖片 alt text)

預期 System Prompt 約 1500 tokens,User Prompt 約 500-2000 tokens,完成評估約 800 tokens。

### 3.6 成本估算(以 GPT-4o-mini 為例)

| 報告大小 | 輸入 tokens | 輸出 tokens | 單次成本 |
|---------|-----------|-----------|---------|
| 5 投影片 | ~3K | ~800 | $0.001 |
| 10 投影片 | ~6K | ~800 | $0.002 |
| 30 投影片 | ~18K | ~800 | $0.005 |

對於批次處理(例如每月 100 份),使用 GPT-4o-mini 約 $0.20-$2.00/月,幾乎可忽略。

### 3.7 風險與緩解

| 風險 | 緩解策略 |
|------|---------|
| LLM 評分不穩定 | 使用 temperature=0、固定 seed、JSON mode |
| API 額度耗盡 | 實作重試與退避;支援本地 Ollama fallback |
| 個資外洩 | 自動移除 .pptx 中個資(姓名、電話);提供離線模式 |
| 上游 fa_report_analyzer_v3 改格式 | 提供 adapter 模式 + 版本偵測 |

---

## 四、重構優先順序建議

| 優先級 | 項目 | 預估工時 | 影響 |
|--------|------|---------|------|
| 🔴 P0 | 加入 `.txt` 評估解析 | 2h | 立即修正 SKILL.md 落差 |
| 🔴 P0 | LLM Client 抽象層 + OpenAI 實作 | 8h | 解放沒有上游工具的使用者 |
| 🔴 P0 | 加入單元測試框架 | 4h | 重構安全保障 |
| 🟠 P1 | 重構為模組化結構 | 12h | 解決單體問題 |
| 🟠 P1 | 樣板系統(JSON 定義版型) | 6h | 不改 code 就能調整版型 |
| 🟠 P1 | 完整的型別提示 + dataclass | 3h | 改善 DX |
| 🟡 P2 | CLI argparse 改寫 | 2h | UX |
| 🟡 P2 | 結構化日誌(logging) | 2h | 可觀測性 |
| 🟡 P2 | PDF/PNG 預覽內建 | 2h | 視覺驗證 |
| 🟡 P2 | pre-commit / linting | 1h | 程式碼品質 |

**預估總工時**:約 **42 工時**(約 1 週 sprint)

---

## 五、結論與下一步

### 立即可行(P0)
1. **修正 SKILL.md 落差**:補上 `.txt` 解析或從 SKILL.md 移除「text feedback」字眼
2. **加入 LLM 整合**:這是最重要的競爭力提升,讓技能包可獨立運作

### 中期建議(P1)
3. **重構為模組化架構**(`ppt_parser.py`、`evaluator.py`、`improver.py`、`templates/`、`llm_clients/`)
4. **加入樣板系統**,讓版型可配置

### 長期策略(P2)
5. **建立測試 + CI**,確保每次重構不回歸
6. **考慮支援視覺模型**(GPT-4o-vision、Claude 3.5 Sonnet),讓評估能看圖

---

**詳細重構計畫見**:`02_refactor_plan.md`
**LLM 整合詳細設計**:`03_llm_integration.md`