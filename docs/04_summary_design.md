# Summary 投影片設計 — 反例與改善

> **問題**:v2.3.0 baseline 的 `fix_summary_slide()` 把所有強化內容塞進既有 Summary 投影片
> **改善方向**:Summary 區塊應該**獨立展開**為多張投影片,而非擠壓

---

## 一、現況:v2.3.0 Summary 強化的問題

### 實際輸出範例(以 N160JCN-EEK 為例)

`fix_summary_slide()` 在既有 Summary 投影片上疊加 4 個文字框:

```
┌─────────────────────────────────────────────────────────┐
│ Summary                                                  │
│                                                          │
│ FPCa 版端狀況確認如下,疑似 IC 有問題。        ┌─────────┐ │
│   1. IC 外觀無異常,但會發燙。                 │Executive │ │
│   2. 電性確認:VH/VOUT 電壓值異常              │Summary   │ │
│      且 VH 二極體特性異常                       │(LLM 評估)│ │
│                                  ←←重疊→→    └─────────┘ │
│ 下一步分析計畫:須進一步分析 IC 端 ┌─────────────────┐    │
│ 是否損壞(新竹 QRA team)          │Key Improvements │    │
│                                  │(改進建議)        │    │
│                                  └─────────────────┘    │
│ ┌─────────────────┐                                       │
│ │ 分析優點與成功驗證│ ←原本 Summary 左下方                │
│ └─────────────────┘                                       │
└─────────────────────────────────────────────────────────┘
```

### 三大問題

#### 1. **資訊擠壓** — 一張投影片塞了 5 個區塊
- 原本的 Summary 內容(2 段結論文字)
- Executive Summary(LLM 評估 300+ 字)
- Key Improvements Required(LLM 改進建議)
- 分析優點與成功驗證(LLM strengths)
- 新增的隱含 review 清單

#### 2. **重疊風險** — 文字框位置依賴手動調整
- 不同模板的 Summary 投影片大小不一樣
- 右側/下方的文字框經常與原本內容重疊(本次 session 已修正過 2 次)
- 即使修正了對這份報告,換一份報告又會遇到新的 layout

#### 3. **閱讀體驗差** — 違反「一張投影片一個主題」
- Summary 變成「雜燴區」
- 原本的 Summary 內容被 LLM 補充內容「淹沒」
- 失去 Summary 應有的「一目了然」特性

---

## 二、改善策略:Summary 應該是 3 張獨立投影片

### 新版 Summary 結構

| 順序 | 投影片 | 內容來源 | 用途 |
|------|--------|---------|------|
| 1 | **Summary 報告總結** | 原 Summary 投影片內容(不變) | 讓讀者快速掌握報告結論 |
| 2 | **Executive Summary** | LLM 評估的詳細摘要 | 給管理層看的高階摘要 |
| 3 | **Key Improvements Required** | LLM 改進建議 + strengths | 給工程師看的行動清單 |

### 範例:MS Meishan 報告 v3.0 設計

#### 投影片 1:Summary 報告總結(原 Summary,保留不動)

```
┌──────────────────────────────────────────────────┐
│ Summary                                          │
│                                                  │
│ 9mm WOT 測試結果:                                 │
│ ┌─────────────────────────────────────────┐      │
│ │ Scenario │ Sequence        │ Status     │      │
│ ├──────────┼─────────────────┼────────────┤      │
│ │ 9mm_WoT  │ tool_replacement │ Pass       │      │
│ │ 9mm_WoT  │ WoT Enable       │ Pass       │      │
│ │ 9mm_WoT  │ wot_suspend_850  │ Pass       │      │
│ │ 9mm_WoT  │ wot_suspend_2000 │ ✗ FAIL    │      │
│ └─────────────────────────────────────────┘      │
│                                                  │
│ 結論:目前僅為「測試紀錄」,尚未進行失效分析       │
└──────────────────────────────────────────────────┘
```

**重點**:只放原本 Summary 的核心結論,不混入 LLM 評估。

#### 投影片 2:Executive Summary(LLM 評估,獨立)

```
┌──────────────────────────────────────────────────┐
│ Executive Summary                                │
│                                                  │
│ 整體評分:F (41.5/100)                            │
│                                                  │
│ 維度評分                                          │
│ ──────                                           │
│ ███░░░░ 基本資訊 (40/100)                        │
│ ████░░ 問題描述 (45/100)                          │
│ ███░░░░ 分析方法 (30/100)                        │
│ █████░ 數據證據 (50/100)                          │
│ ░░░░░░ 根因分析 (0/100) ⚠️                       │
│ ░░░░░░ 改善對策 (0/100) ⚠️                       │
│                                                  │
│ 報告目前狀態:                                     │
│ 「測試紀錄(Test Log)」而非「失效分析報告」       │
└──────────────────────────────────────────────────┘
```

**重點**:
- 用進度條視覺化 6 個維度分數
- 一眼看出哪裡嚴重缺失(根因分析、改善對策 = 0%)
- 給管理層的高階摘要

#### 投影片 3:Key Improvements Required(行動清單,獨立)

```
┌──────────────────────────────────────────────────┐
│ Key Improvements Required                        │
│                                                  │
│ 立即行動 ⚡                                        │
│ ──────                                           │
│ □ 補齊產品基本資訊(型號、客戶、工程師)           │
│ □ 確認測試流程與原 Spec 一致性                   │
│                                                  │
│ 短期對策(本週內) 📅                              │
│ ──────                                           │
│ □ 執行 Robot Log 異常根因調查                    │
│ □ 確認 Suspend Mode 訊號路徑完整性               │
│                                                  │
│ 長期預防 🔄                                       │
│ ──────                                           │
│ □ 建立 Wake-on-Touch 測試 SOP                    │
│ □ 導入監測異常 Robot Log 自動通知                │
│                                                  │
│ 報告分析優點 ✓                                    │
│ ──────                                           │
│ ✓ 測試參數定義表清晰                             │
│ ✓ 測試序列執行時間對照表完整                     │
└──────────────────────────────────────────────────┘
```

**重點**:
- 區分立即 / 短期 / 長期時間軸
- 結合 LLM strengths(優點)與 improvements(改進)
- 視覺化 checklist

---

## 三、程式碼實作:取代 `fix_summary_slide()`

### v3.0 新流程

```python
def enhance_summary_section(
    prs: Presentation,
    eval_data: EvaluationResult,
    original_summary_idx: int,
) -> None:
    """強化 Summary 區塊:不修改原 Summary,改為新增 2 張獨立投影片"""

    # 1. 保留原 Summary 不動(可能位於報告中間或開頭)

    # 2. 在原 Summary 之後新增 Executive Summary 投影片
    exec_slide = add_executive_summary_slide(prs, eval_data)
    move_slide_to_position(prs, len(prs.slides) - 1, original_summary_idx + 1)

    # 3. 在 Executive Summary 之後新增 Key Improvements 投影片
    action_slide = add_key_improvements_slide(prs, eval_data)
    move_slide_to_position(prs, len(prs.slides) - 1, original_summary_idx + 2)


def add_executive_summary_slide(prs, eval_data) -> Slide:
    """新增 Executive Summary 投影片(獨立,不覆蓋任何內容)"""
    layout = find_content_layout(prs)
    slide = prs.slides.add_slide(layout)

    # 標題
    set_slide_title(slide, "Executive Summary", template="summary")

    # 整體評分
    add_score_visualization(slide, eval_data.total_score, eval_data.grade)

    # 6 維度評分(進度條)
    for dim in eval_data.dimensions:
        add_progress_bar(slide, dim.name, dim.score, dim.weight)

    # LLM 評語
    add_text_block(slide, eval_data.summary, style="quote")

    return slide


def add_key_improvements_slide(prs, eval_data) -> Slide:
    """新增 Key Improvements 投影片"""
    layout = find_content_layout(prs)
    slide = prs.slides.add_slide(layout)

    set_slide_title(slide, "Key Improvements Required", template="summary")

    # 立即行動(高優先級 + 高分)
    immediate = [i for i in eval_data.improvements if i.priority == "高"]
    add_section_header(slide, "⚡ 立即行動", color="red")
    add_checklist(slide, [i.suggestion for i in immediate])

    # 中期對策
    mid_term = [i for i in eval_data.improvements if i.priority == "中"]
    if mid_term:
        add_section_header(slide, "📅 中期對策", color="orange")
        add_checklist(slide, [i.suggestion for i in mid_term])

    # 長期預防
    add_section_header(slide, "🔄 長期預防", color="blue")
    add_checklist(slide, [
        "建立測試 SOP 與知識管理資料庫",
        "導入自動化監測與異常通報機制",
    ])

    # 報告優點
    add_section_header(slide, "✓ 報告優點", color="green")
    add_bullet_list(slide, eval_data.strengths)

    return slide
```

### 關鍵設計決策

| 決策 | 原因 |
|------|------|
| **不修改原 Summary** | 保留使用者/分析師原本的結論文字 |
| **新增獨立投影片** | 一張只講 Executive Summary、一張只講 Key Improvements |
| **視覺化評分** | 用進度條取代純文字「40 分」,更直覺 |
| **時間軸分組** | 立即/短期/長期,讓讀者知道優先順序 |
| **優點也保留** | 不只列缺失,也提醒做得好的部分 |

---

## 四、母片保護驗證

新增的 Executive Summary 與 Key Improvements 投影片:
- ✅ 使用既有 layout(`find_content_layout()`),不建立新 layout
- ✅ 只填入 placeholder,不改 layout 結構
- ✅ 不修改母片 XML(以 `MasterTemplate.verify_unchanged()` 測試)
- ✅ 不動到原 Summary 投影片的任何 shape

---

## 五、測試案例

```python
def test_summary_enhancement_adds_two_new_slides():
    """確認 Summary 強化會新增 2 張獨立投影片,不修改原 Summary"""
    prs = load_test_fixture("with_existing_summary.pptx")
    original_summary_idx = find_summary_slide_index(prs)
    original_summary_xml = prs.slides[original_summary_idx].element.xml
    original_slide_count = len(prs.slides)

    enhance_summary_section(prs, sample_eval_data, original_summary_idx)

    # 新增 2 張
    assert len(prs.slides) == original_slide_count + 2

    # 原 Summary 內容未變
    assert prs.slides[original_summary_idx].element.xml == original_summary_xml

    # 新增的兩張投影片在 Summary 之後
    new_slide_1 = prs.slides[original_summary_idx + 1]
    new_slide_2 = prs.slides[original_summary_idx + 2]

    assert "Executive Summary" in new_slide_1.text
    assert "Key Improvements" in new_slide_2.text


def test_summary_enhancement_preserves_master():
    """確認 Summary 強化不會修改母片"""
    prs = load_test_fixture("with_existing_summary.pptx")
    master_template = MasterTemplate.capture(prs)

    enhance_summary_section(prs, sample_eval_data, find_summary_slide_index(prs))

    master_template.verify_unchanged(prs)  # 不應拋出例外
```

---

## 六、效益

| 指標 | v2.3.0 | v3.0 |
|------|--------|------|
| Summary 區塊總投影片數 | 1(擠在一起) | 3(各自獨立) |
| 重疊風險 | 高 | 無(各自獨立版面) |
| 母片保護 | 隱性 | 顯性測試覆蓋 |
| 視覺品質 | 雜亂 | 專業 |
| 可維護性 | 難(每次新報告都要調整座標) | 易(獨立樣板) |

---

**整合進度**:
- 此設計原則已納入 `02_refactor_plan.md` 的「第四原則:版面呼吸感」
- 程式碼實作計畫在 v3.0 Phase 4(樣板系統)一併完成
- 測試覆蓋會在 v3.0 Phase 5(品質提升)加入

**下一步**:撰寫 `05_template_system.md`,把這個設計原則形式化成可配置的 JSON 樣板。