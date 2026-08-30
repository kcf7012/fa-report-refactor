# FA Report Improvement Skill — v3.0 重構計畫

> **目標版本**:v3.0.0
> **基線**:`baseline-v2.3.0`(git tag)
> **預估工時**:42 工時
> **重構原則**:**所有操作必須保留下游設計師精心設計的母片樣式**

---

## 🛡️ 第一原則:母片保護 (Master Slide Preservation)

### 為什麼這是首要原則?

本技能包的使用情境是:**半導體失效分析報告**。這類報告屬於公司品管文件,有統一的母片設計:
- ELAN Microelectronics 公司 Logo
- 「Enrich your life with fingertouch」標語
- 公司專屬的雲霄建築底圖
- 機密等級標示(Confidential Information)
- 各部門自訂的色系與字型

**任何破壞母片的動作都會讓報告失去公司品牌識別與機密標示**,這在實務上不可接受。

### 重構時必須驗證的事項

每次新增/修改投影片後,以下檢查必須**全部通過**:

#### 自動檢查項目
```python
# 1. 母片本身不變
assert slide_masters_xml == original_masters_xml, "Master modified!"

# 2. 母片所有 layout 不變
assert len(prs.slide_layouts) == original_layout_count

# 3. 新投影片使用的 layout 必須是原本已存在的 layout
assert new_slide.slide_layout in original_layouts

# 4. 不可刪除任何原始投影片
assert all_original_slides_preserved(prs)

# 5. 不可新增 placeholder 到母片
assert no_placeholders_added_to_masters(prs)

# 6. 圖片、母片圖片、背景圖不變
assert all_master_images_preserved(prs)
```

#### 手動視覺檢查
每張投影片 PDF 渲染後:
- [ ] 抬頭圖片/標語與原報告一致
- [ ] 左/右側裝飾線條/圖示保留
- [ ] 頁尾機密標示/編號保留
- [ ] 字型、色系、Logo 位置一致
- [ ] 投影片編號區(若有)位置正確

### 程式碼層級的防護

#### 1. 不可變的母片參考
```python
@dataclass(frozen=True)
class MasterTemplate:
    """母片保護:封裝原始母片狀態,所有改善操作不得修改"""
    masters_xml: bytes
    layouts: List[LayoutSnapshot]
    images: Dict[str, bytes]
    fonts: List[str]
    
    def verify_unchanged(self, prs: Presentation) -> None:
        """驗證母片從改善開始到結束都未被修改"""
        ...
```

#### 2. 投影片新增 helper
```python
def add_new_slide_preserving_master(
    prs: Presentation,
    layout_name: str,
    title: str,
    content_bullets: List[str]
) -> Slide:
    """新增投影片,強制使用已存在的 layout,絕不建立新 layout"""
    layout = find_existing_layout(prs, layout_name)
    slide = prs.slides.add_slide(layout)  # 必須是既有 layout
    # 後續只填入 placeholder,絕不修改 layout 本身
    ...
```

#### 3. 禁止的操作清單
```python
FORBIDDEN_OPERATIONS = [
    "prs.slide_masters.add()",          # 新增母片
    "prs.slide_layouts.add()",          # 新增 layout
    "layout.element.clear()",           # 清空 layout
    "master.shapes[i].delete()",        # 從母片刪 shape
    "master.background.fill.background()",  # 修改母片背景
]
```

---

## 📐 第二原則:模組化 (Decomposition)

### 目標檔案結構

```
fa-report-improvement/
├── SKILL.md
├── README.md
├── CHANGELOG.md
├── requirements.txt
├── pyproject.toml                      # 新增:現代 Python 專案設定
├── .pre-commit-config.yaml             # 新增:pre-commit hooks
├── pytest.ini                          # 新增:測試設定
├── .gitignore
│
├── docs/                               # 評估與設計文件
│   ├── 01_assessment.md
│   ├── 02_refactor_plan.md             # 本文件
│   ├── 03_llm_integration.md
│   ├── 04_template_system.md
│   └── 05_api_reference.md
│
├── references/                         # 領域知識(只讀)
│   ├── evaluation-criteria.md
│   ├── improvement-templates.md
│   ├── statistical-methods.md
│   ├── ppt-conversion-guide.md
│   └── virtual-environment-guide.md
│
├── src/                                # ★ 新增:原始碼結構
│   └── fa_improver/
│       ├── __init__.py
│       ├── __main__.py                 # CLI 入口
│       ├── cli.py                      # argparse 介面
│       │
│       ├── domain/                     # 領域模型(純資料)
│       │   ├── __init__.py
│       │   ├── evaluation.py           # EvaluationResult, Dimension dataclass
│       │   ├── suggestion.py          # Suggestion, Improvement dataclass
│       │   └── template.py             # TemplateConfig dataclass
│       │
│       ├── parsers/                    # 輸入解析
│       │   ├── __init__.py
│       │   ├── evaluation_parser.py    # 解析 JSON/TXT 評估
│       │   ├── pptx_parser.py          # 解析 pptx 結構
│       │   └── filename_parser.py      # 從檔名提取 FA 編號/客戶
│       │
│       ├── llm/                        # ★ 新增:LLM 整合
│       │   ├── __init__.py
│       │   ├── base.py                 # LLMClient Protocol
│       │   ├── openai_client.py        # OpenAI 相容 API
│       │   ├── anthropic_client.py     # Anthropic Claude
│       │   ├── ollama_client.py        # 本地 LLM
│       │   ├── mock_client.py          # 測試用
│       │   ├── prompts.py              # System/User prompt 樣板
│       │   └── evaluator.py            # 將 LLM 結果轉為 EvaluationResult
│       │
│       ├── improvers/                  # 改善動作
│       │   ├── __init__.py
│       │   ├── base.py                 # BaseImprover 抽象
│       │   ├── basic_info.py           # 新增基本資訊投影片
│       │   ├── root_cause.py           # 新增根因分析投影片
│       │   ├── prevention.py           # 新增改善對策投影片
│       │   ├── summary.py              # 強化 Summary 投影片
│       │   └── orchestrator.py         # 編排多個 improver
│       │
│       ├── layout/                     # 版面處理
│       │   ├── __init__.py
│       │   ├── selector.py             # find_content_layout 智慧選擇
│       │   ├── mapper.py               # placeholder 位置調整
│       │   └── protector.py            # ★ 母片保護檢查
│       │
│       ├── templates/                  # ★ 新增:樣板系統
│       │   ├── __init__.py
│       │   ├── builtin.py              # 內建樣板
│       │   ├── basic_info.json         # Template 1
│       │   ├── root_cause.json         # Template 2
│       │   ├── prevention.json         # Template 3
│       │   └── summary.json            # Template 4
│       │
│       └── utils/                      # 公用工具
│           ├── __init__.py
│           ├── logging.py              # 結構化日誌
│           ├── ppt_converter.py        # .ppt → .pptx
│           └── validators.py           # 資料驗證
│
├── tests/                              # ★ 新增:測試
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_evaluation_parser.py
│   │   ├── test_filename_parser.py
│   │   ├── test_layout_selector.py
│   │   ├── test_layout_protector.py   # 母片保護測試
│   │   ├── test_improvers.py
│   │   └── test_llm_clients.py        # mock client 測試
│   ├── integration/
│   │   ├── test_full_workflow_json.py
│   │   ├── test_full_workflow_txt.py
│   │   └── test_full_workflow_llm.py
│   └── fixtures/
│       ├── sample_report.pptx
│       ├── sample_eval.json
│       ├── sample_eval.txt
│       └── expected_outputs/
│
└── scripts/                            # 維持向後相容的 CLI 入口
    ├── improve_fa_report.py            # 改為薄殼,委派給 src/fa_improver
    ├── install.py                      # 不變
    └── ppt_converter.py                # 委派給 src/fa_improver/utils/
```

---

## 🔄 第三原則:向後相容性

### 既有 CLI 必須保留
```bash
# 原本的呼叫方式必須仍可運作
python improve_fa_report.py input.pptx eval.json output.pptx
python improve_fa_report.py input.ppt eval.json output.pptx  # 自動轉換
```

### 內部實作
```python
# scripts/improve_fa_report.py (改為 thin wrapper)
"""向後相容入口 - 委派給新架構"""
import sys
from fa_improver.cli import main

if __name__ == "__main__":
    # 將舊的位置參數轉換成新 CLI
    if len(sys.argv) == 4 and not sys.argv[1].startswith("-"):
        sys.argv = [sys.argv[0], "improve", sys.argv[1],
                   "--eval", sys.argv[2], "--output", sys.argv[3]]
    sys.exit(main())
```

---

## 📦 重構階段(分 5 個 PR)

### Phase 1:基礎建設(不破壞既有功能)
- [ ] 加入 pyproject.toml
- [ ] 建立 src/ 目錄骨架
- [ ] 把現有函數**複製**到新模組,**完全不改行為**
- [ ] 改寫 scripts/improve_fa_report.py 為 thin wrapper
- [ ] 驗證既有 3 份報告改善結果完全相同(位元組比較 XML)

### Phase 2:加入 .txt 解析
- [ ] 實作 `parsers/evaluation_parser.py` 支援 JSON/TXT 雙格式
- [ ] TXT 格式契約定義(從 SKILL.md 與實際範例推導)
- [ ] 加入 `tests/test_evaluation_parser.py`
- [ ] 更新 SKILL.md 移除含糊的 "text feedback" 描述

### Phase 3:加入 LLM 整合
- [ ] 實作 `llm/base.py` Protocol
- [ ] 實作 `llm/openai_client.py`
- [ ] 實作 `llm/mock_client.py`(離線/測試)
- [ ] 設計 `llm/prompts.py`(基於 evaluation-criteria.md)
- [ ] 實作 `llm/evaluator.py`(LLM result → EvaluationResult)
- [ ] CLI 加入 `--llm-provider`、`--api-key`、`--model` 參數
- [ ] 加入 `.env.example` 與 `python-dotenv` 支援
- [ ] 加入安全機制:個資遮罩、timeout、重試

### Phase 4:樣板系統
- [ ] 設計 `TemplateConfig` JSON schema
- [ ] 把現有 hard-coded 內容轉成 5 個 JSON 樣板
- [ ] 實作 `templates/builtin.py`(載入內建樣板)
- [ ] 實作 `improvers/*.py` 使用樣板而非硬編碼
- [ ] CLI 加入 `--template-dir` 支援自訂樣板

### Phase 5:品質提升
- [ ] 加入完整型別提示 + mypy 設定
- [ ] 加入 logging(取代 print)
- [ ] 加入 pytest + coverage 設定
- [ ] 達到 ≥80% 測試覆蓋率
- [ ] 加入 pre-commit + ruff + black
- [ ] 加入 GitHub Actions CI
- [ ] 寫完 `docs/05_api_reference.md`

---

## 🎨 第四原則:版面呼吸感 (Visual Pacing)

### 目前問題:改善內容擠在一起

觀察 v2.3.0 baseline 的輸出,3 份改善報告都有同一個問題:

**根因驗證及統計分析投影片**:
- 一張投影片同時塞了:針對問題點的深度分析、3-4 條 LLM 評語、[建議執行動作] 3 條建議
- 字級小、段落密、看起來像「罰寫」而不是「專業報告」

**長期預防措施與改善對策投影片**:
- 同樣是:LLM 評語 1 條 + [標準化與監測計畫] 3 條
- 大量留白但內容還是很擠

**Summary 強化**:
- 分析優點 / Executive Summary / Key Improvements 三塊文字堆在同一張投影片
- 右側三塊文字框互相緊貼

### 設計原則:**一張投影片只講一件事**

```
❌ 錯誤:一張投影片寫 6 個 LLM 評語 + 4 個標準動作
✅ 正確:一張投影片 = 一個明確主題,只顯示 2-3 個要點
```

### 改善策略:拆解內容為多張投影片

原本 1 張「根因驗證及統計分析」應該拆成:

| 投影片 | 主題 | 內容 |
|--------|------|------|
| 新增 #1 | **為何需要統計驗證** | 為什麼「推測」不是分析;統計方法的角色 |
| 新增 #2 | **5-Why 推導流程** | 用 5 個 Why 引導讀者思考;每個 Why 一行 |
| 新增 #3 | **對照組與統計方法** | DVT 正常品 vs PVT 異常品;t-test、α=0.05、CI |
| 新增 #4 | **關鍵驗證證據** | 需要哪些物理/數據證據(SEM、X-ray、Decap) |

原本 1 張「長期預防措施」應該拆成:

| 投影片 | 主題 | 內容 |
|--------|------|------|
| 新增 #5 | **改善對策總覽** | 短期 vs 長期;各 2 個要點 |
| 新增 #6 | **IQC 與製程標準化** | 入料檢驗 SOP、測試閾值 |
| 新增 #7 | **持續監測與知識管理** | 自動化監測、案例資料庫 |

原本 Summary 強化應該拆成:
- **Summary 報告總結**(原本 Summary 內容)
- **Executive Summary**(LLM 評估的詳細說明,獨立投影片)
- **Key Improvements**(改進建議的視覺化檢查清單)

### 設計語彙:專業報告的視覺標準

| 元素 | 標準 | 範例 |
|------|------|------|
| 字級 | 標題 28-32pt,內文 16-18pt | 不要小於 14pt |
| 留白 | 每張投影片至少 30% 留白 | 不要填滿 |
| 圖示 | 每張至少 1 個視覺元素 | 圖表、流程圖、checklist |
| 段落 | 不超過 5-6 行/區塊 | 超過就要拆 |
| 字數 | 單張投影片 < 200 字 | 重要資訊用粗體+圖示輔助 |
| 顏色 | ELAN 主色系(深藍 #1F4E79、輔助藍 #5B9BD5、強調紅 #C00000) | 維持品牌一致 |

### 程式碼層級的實作

#### 樣板系統驅動的版面設計
```python
@dataclass
class SlideTemplate:
    """定義單張投影片的版面與內容上限"""
    title: str
    max_bullets: int = 4
    max_words_per_bullet: int = 30
    visual_element: Optional[str] = None  # "checklist" | "table" | "flow"
    color_theme: str = "primary"

# 在 improver 內檢查
def validate_slide_content(template: SlideTemplate, content: str) -> None:
    bullets = parse_bullets(content)
    if len(bullets) > template.max_bullets:
        raise TemplateViolationError(
            f"投影片 '{template.title}' 有 {len(bullets)} 個要點,"
            f"超過上限 {template.max_bullets}。"
            f"建議拆分為多張投影片。"
        )
```

#### 拆解邏輯
```python
def split_into_multiple_slides(
    content: List[str],
    max_per_slide: int = 4,
) -> List[List[str]]:
    """把長內容自動拆成多張投影片"""
    if len(content) <= max_per_slide:
        return [content]
    # 計算需要幾張
    n_slides = ceil(len(content) / max_per_slide)
    per_slide = ceil(len(content) / n_slides)
    return [content[i:i+per_slide] for i in range(0, len(content), per_slide)]
```

#### 視覺元素生成
```python
def add_checklist(slide, items: List[str]) -> None:
    """自動產生 checkbox 視覺元素"""
    ...

def add_flow_diagram(slide, steps: List[str]) -> None:
    """自動產生 5-Why 流程圖"""
    ...

def add_comparison_table(slide, normal: dict, failed: dict) -> None:
    """自動產生 DVT vs PVT 對照表"""
    ...
```

---

## 🧪 測試策略

### 必要測試案例

#### 母片保護測試(最關鍵!)
```python
def test_master_not_modified_during_improvement():
    """確認改善前後母片 XML 完全一致"""
    original = load_test_fixture("sample_report.pptx")
    original_master_xml = original.slide_masters[0].element.xml
    
    improved = improve_report(original, eval_data)
    
    assert improved.slide_masters[0].element.xml == original_master_xml
    assert len(improved.slide_masters) == len(original.slide_masters)
    assert len(improved.slide_layouts) == len(original.slide_layouts)

def test_no_new_layouts_added():
    """確認改善未新增任何 layout"""
    original = load_test_fixture("sample_report.pptx")
    improved = improve_report(original, eval_data)
    
    original_layout_names = {l.name for l in original.slide_layouts}
    improved_layout_names = {l.name for l in improved.slide_layouts}
    
    assert improved_layout_names == original_layout_names
```

#### 端對端測試
```python
@pytest.mark.parametrize("report_file,eval_file,expected_slide_count", [
    ("Kobo_ZHT_RA6080_SPcomFailI.pptx", "eval.json", 8),
    ("N160JCN-EEK.pptx", "eval.json", 11),
    ("MS_Meishan_ADO_445239.pptx", "eval.json", 8),
])
def test_full_workflow(report_file, eval_file, expected_slide_count):
    output = improve_workflow(report_file, eval_file)
    assert len(output.slides) == expected_slide_count
    # 母片保護
    assert master_unchanged(report_file, output)
```

#### LLM Client 測試
```python
def test_openai_client_with_mock_response(monkeypatch):
    """使用預錄 response 測試 OpenAI client"""
    mock_response = load_fixture("openai_eval_response.json")
    monkeypatch.setattr(openai, "chat", lambda *_: mock_response)
    
    client = OpenAIClient(api_key="test")
    result = client.evaluate_report(pptx_content="...", rubric="...")
    
    assert isinstance(result, EvaluationResult)
    assert result.total_score > 0
```

---

## 📊 預期效益

| 指標 | 重構前 | 重構後 |
|------|--------|--------|
| 單體檔案行數 | 783 | < 200/檔 |
| 函式平均行數 | 46 | < 30 |
| 型別提示覆蓋率 | < 5% | > 95% |
| 測試覆蓋率 | 0% | > 80% |
| LLM 整合 | ✗ | ✓ |
| .txt 解析 | ✗ | ✓ |
| 樣板可配置 | ✗ | ✓ |
| CLI 子命令 | ✗ | ✓ |
| 結構化日誌 | ✗ | ✓ |
| **母片保護機制** | **隱性** | **顯性 + 測試** |

---

## 🎯 v3.0 成功標準

1. ✅ **母片零修改**:每張原投影片母片 100% 保留(以 XML 比對為證)
2. ✅ **完全向後相容**:舊 CLI 指令仍正常運作,輸出結果位元組相同
3. ✅ **測試覆蓋 ≥80%**:包含母片保護測試
4. ✅ **支援 .txt 評估**:可解析 SKILL.md 提及的所有輸入
5. ✅ **支援 LLM 評估**:至少 OpenAI API + Mock,可用 `--api-key` 直接呼叫
6. ✅ **可配置樣板**:5 個內建樣板 + 支援自訂
7. ✅ **CI 通過**:pre-commit、pytest、mypy 全部綠燈

---

**下一步**:請確認本計畫,接著執行 Phase 1(基礎建設)。