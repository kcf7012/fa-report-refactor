# 改善對策投影片設計 — 拆解為多張獨立投影片

> **問題**:v2.3.0 把所有改善對策塞在單一張「長期預防措施與改善對策」投影片
> **現況**:1 張投影片塞了 LLM 評語 + 3 條標準對策
> **改善**:依時間軸與主題拆成 3 張獨立投影片

---

## 一、現況:v2.3.0 改善對策的擠壓問題

### 實際輸出範例(以本次 session 為例)

所有 3 份報告的「長期預防措施與改善對策」投影片都長這樣:

```
┌──────────────────────────────────────────────────┐
│ 長期預防措施與改善對策                            │
│                                                  │
│ ◆ 擬議改善對策項目:                              │
│   • [1 條 LLM 評語直接塞進來]                     │
│                                                  │
│ ◆ [標準化與監測計畫]                             │
│   • 建立入料檢驗 (IQC) SOP 與測試閾值              │
│   • 導入自動化監測設備於生產線                    │
│   • 將此案例納入知識管理資料庫以利後續追蹤        │
└──────────────────────────────────────────────────┘
```

### 三大問題

1. **內容重複且單薄** — 1 條 LLM 評語 + 3 條標準 boilerplate,看起來敷衍
2. **沒有時間軸** — 短期 vs 長期 vs 立即行動混在一起,讀者不知道先做哪個
3. **缺乏具體性** — 「建立 IQC SOP」太空泛,沒有標準、責任人、驗證方式

---

## 二、改善策略:依時間軸 + 主題拆成 3 張

### 新版改善對策結構

| 順序 | 投影片 | 主題 | 內容 |
|------|--------|------|------|
| 1 | **改善對策總覽** | 全貌 | 短期/中期/長期時間軸視覺化 |
| 2 | **IQC 與製程標準化** | 製程端 | 抽樣、測試閾值、SOP 文件化 |
| 3 | **監測與知識管理** | 預防端 | 自動化監測、案例資料庫、訓練 |

---

### 範例:Kobo RA6080 報告 v3.0 設計

#### 投影片 1:改善對策總覽(時間軸視覺化)

```
┌──────────────────────────────────────────────────┐
│ 改善對策總覽                                     │
│                                                  │
│ ┌─────────────────────────────────────────────┐ │
│ │ 立即(本週) → 短期(本月) → 中期(本季) → 長期(年度)│ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│  ⚡ 立即                                         │
│  ──────                                          │
│  □ 補齊 FA 報告批號 (Lot No.) 與失效數量記錄     │
│  □ 確認 IC 供應商(原廠 DVT 規格一致性)           │
│                                                  │
│  📅 短期(1 個月內)                               │
│  ──────                                          │
│  □ 建立金手指 vs IC I/O 對照阻抗表(DVT 基準線) │
│  □ IQC 新增 ESD 測試閾值檢查(±2kV 人體模型)    │
│                                                  │
│  📆 中期(本季)                                   │
│  ──────                                          │
│  □ 對 50 顆同批 IC 執行 5-Why 失效樹分析         │
│  □ SEM 觀察 I/O 內部損傷,建立失效物理圖譜       │
│                                                  │
│  🔄 長期(年度持續)                               │
│  ──────                                          │
│  □ 建立 IC I/O 失效案例資料庫與共用平台          │
│  □ 每月 review 失效趨勢,異常自動通報            │
│  □ 新人教育訓練教材納入此次案例                  │
└──────────────────────────────────────────────────┘
```

**版面特點**:
- 時間軸貫穿全頁,讀者一眼看出優先順序
- 4 個時間區段(立即/短期/中期/長期)各自有 checklist
- 每個項目具體、可執行,不空泛

#### 投影片 2:IQC 與製程標準化

```
┌──────────────────────────────────────────────────┐
│ IQC 與製程標準化                                  │
│                                                  │
│ 1. 入料檢驗 SOP                                   │
│   ┌────────────────────────────────────────┐    │
│   │ 檢驗項目          │ 標準              │    │
│   ├──────────────────┼─────────────────────┤    │
│   │ ESD 耐受測試      │ ±2kV HBM (人體模型)│    │
│   │ I/O 對地阻抗      │ 與 DVT golden ±10% │    │
│   │ SPI 通訊測試      │ 100% 樣品通過      │    │
│   │ 外觀標識檢查      │ 雷刻清晰可辨識    │    │
│   └──────────────────┴─────────────────────┘    │
│                                                  │
│ 2. 抽樣比例與判定                                │
│   • 抽樣比例:AQL 0.65 Level II                  │
│   • 判定標準:任一 FAIL 即整批退回                │
│   • 責任單位:IQC 工程師 + FAE 共同判定          │
│                                                  │
│ 3. 文件化                                        │
│   • SOP 文件編號:ELAN-QA-IQC-XXX                 │
│   • 版本控制:每次修訂需 FAE + QM 雙簽            │
│   • 教育訓練:每位 IQC 人員每年至少 2 次          │
└──────────────────────────────────────────────────┘
```

**版面特點**:
- 表格化的檢驗項目,清楚列出每項標準
- 抽樣比例、判定標準、責任單位都明確
- 文件化要求(編號、版本、教育訓練)具體可追蹤

#### 投影片 3:監測與知識管理

```
┌──────────────────────────────────────────────────┐
│ 持續監測與知識管理                               │
│                                                  │
│ 監測機制                                          │
│ ──────                                           │
│ ┌────────────────────────────────────────┐      │
│ │ 失效趨勢監控:每月統計 IC 失效比例       │      │
│ │ 異常自動通報:當月失效 > 3% 自動寄信     │      │
│ │ 預警指標:連續 3 月 > 2% 啟動專案 review │      │
│ └────────────────────────────────────────┘      │
│                                                  │
│ 知識管理                                          │
│ ──────                                           │
│ • 案例納入資料庫(編號:Kobo-RA6080-2026-08)    │
│ • 建立 Root Cause Wiki,搜尋關鍵字即可調閱        │
│ • 季度失效案例分享會(FA + IQC + 製程共同參與)  │
│                                                  │
│ 教育訓練                                          │
│ ──────                                           │
│ • 新人 FA 訓練教材納入此案例                     │
│ • 每年至少 1 次全員失效分析複訓                  │
│ • 跨部門經驗分享(每季 1 次 lunch seminar)        │
└──────────────────────────────────────────────────┘
```

**版面特點**:
- 監測機制有具體數字閾值(3%、2%)
- 知識管理有具體編號、平台、頻率
- 教育訓練對象、頻率明確

---

## 三、程式碼實作

### 取代 `add_prevention_measures_slide()`

```python
def add_prevention_section(
    prs: Presentation,
    eval_data: EvaluationResult,
    insert_after_idx: int,
) -> None:
    """改善對策區塊:展開為 3 張獨立投影片"""

    # 投影片 1:總覽(時間軸)
    overview_slide = add_prevention_overview_slide(prs, eval_data)
    move_slide_to_position(prs, len(prs.slides) - 1, insert_after_idx + 1)

    # 投影片 2:IQC 與製程標準化
    iqc_slide = add_iqc_standardization_slide(prs, eval_data)
    move_slide_to_position(prs, len(prs.slides) - 1, insert_after_idx + 2)

    # 投影片 3:監測與知識管理
    monitor_slide = add_monitoring_km_slide(prs, eval_data)
    move_slide_to_position(prs, len(prs.slides) - 1, insert_after_idx + 3)


def add_prevention_overview_slide(prs, eval_data) -> Slide:
    """改善對策總覽(時間軸視覺化)"""
    layout = find_content_layout(prs)
    slide = prs.slides.add_slide(layout)

    set_slide_title(slide, "改善對策總覽")

    # 時間軸圖示
    add_timeline_visualization(slide, [
        ("⚡ 立即", RED),
        ("📅 短期", ORANGE),
        ("📆 中期", BLUE),
        ("🔄 長期", GREEN),
    ])

    # 從 LLM 改進建議中,依優先級自動分組
    grouped = group_improvements_by_priority(eval_data.improvements)
    for priority, items in grouped.items():
        add_section(slide, priority_label(priority), items)

    return slide


def add_iqc_standardization_slide(prs, eval_data) -> Slide:
    """IQC 與製程標準化(獨立投影片)"""
    layout = find_content_layout(prs)
    slide = prs.slides.add_slide(layout)

    set_slide_title(slide, "IQC 與製程標準化")

    # 標準表格(可依報告性質類別)
    add_inspection_table(slide, get_inspection_items(eval_data))

    # 抽樣與判定
    add_sampling_criteria(slide)

    # 文件化要求
    add_documentation_requirements(slide)

    return slide


def add_monitoring_km_slide(prs, eval_data) -> Slide:
    """監測與知識管理(獨立投影片)"""
    layout = find_content_layout(prs)
    slide = prs.slides.add_slide(layout)

    set_slide_title(slide, "持續監測與知識管理")

    # 3 個區塊
    add_section(slide, "監測機制", [
        "失效趨勢監控(每月)",
        "異常自動通報閾值",
        "預警指標與啟動條件",
    ])

    add_section(slide, "知識管理", [
        "案例納入資料庫(具體編號)",
        "建立 Root Cause Wiki",
        "季度失效案例分享會",
    ])

    add_section(slide, "教育訓練", [
        "新人 FA 訓練教材納入此案例",
        "每年至少 一次全員複訓",
        "跨部門經驗分享",
    ])

    return slide
```

---

## 四、樣板 JSON 範例

```json
{
  "name": "prevention_overview",
  "title": "改善對策總覽",
  "layout": "content_with_timeline",
  "timeline_phases": [
    {
      "icon": "⚡",
      "label": "立即",
      "timeframe": "本週",
      "color": "#C00000",
      "items_source": "improvements.filter(priority='高').take(2)"
    },
    {
      "icon": "📅",
      "label": "短期",
      "timeframe": "1 個月內",
      "color": "#ED7D31",
      "items_source": "improvements.filter(priority='中').take(2)"
    },
    {
      "icon": "📆",
      "label": "中期",
      "timeframe": "本季",
      "color": "#5B9BD5",
      "items_source": "static.action_items.short_term"
    },
    {
      "icon": "🔄",
      "label": "長期",
      "timeframe": "年度持續",
      "color": "#70AD47",
      "items_source": "static.action_items.long_term"
    }
  ],
  "max_items_per_phase": 3
}
```

---

## 五、測試案例

```python
def test_prevention_adds_three_slides():
    """確認改善對策會展開為 3 張獨立投影片"""
    prs = load_test_fixture("kobo_report.pptx")
    original_count = len(prs.slides)

    add_prevention_section(prs, sample_eval_data, insert_after_idx=5)

    # 應該新增 3 張
    assert len(prs.slides) == original_count + 3

    # 3 張投影片的標題
    titles = [
        prs.slides[6].shapes.title.text,
        prs.slides[7].shapes.title.text,
        prs.slides[8].shapes.title.text,
    ]
    assert any("改善對策總覽" in t for t in titles)
    assert any("IQC" in t or "製程標準化" in t for t in titles)
    assert any("監測" in t or "知識管理" in t for t in titles)


def test_prevention_no_layout_modification():
    """確認改善對策新增的投影片使用既有 layout"""
    prs = load_test_fixture("kobo_report.pptx")
    original_layout_names = {l.name for l in prs.slide_layouts}

    add_prevention_section(prs, sample_eval_data, insert_after_idx=5)

    new_layout_names = {l.name for l in prs.slide_layouts}
    assert new_layout_names == original_layout_names  # 不新增 layout
```

---

## 六、效益對比

| 指標 | v2.3.0 | v3.0 |
|------|--------|------|
| 投影片數 | 1 | 3 |
| 資訊密度 | 高(擠在一起) | 適中(各 3-5 個要點) |
| 時間軸 | 無 | 立即/短期/中期/長期 |
| 具體性 | 空泛 | 有數字、責任人、頻率 |
| 視覺元素 | 純文字 | 時間軸圖、表格、checklist |
| 可執行性 | 低(讀者不知從何開始) | 高(優先順序明確) |

---

## 七、實際範例對照

### v2.3.0 輸出(本次 session)

```
改善對策:1 張投影片,3 條 boilerplate
「建立 IQC SOP」、「自動化監測」、「知識管理」
```

### v3.0 輸出

```
改善對策:3 張投影片,各自聚焦
1. 總覽:時間軸 + 12 條具體行動
2. IQC 標準化:表格 + 抽樣 + 文件化
3. 監測 + KM:3 大主題各 3 條具體做法
```

**結論**:同樣是 3 張投影片,但內容深度、可執行性、視覺品質都大幅提升。

---

**整合進度**:
- 此設計與 `04_summary_design.md` 一致,同樣遵守「一張投影片一個主題」原則
- 程式碼實作在 v3.0 Phase 4(樣板系統)完成
- 樣板 JSON 範例已提供,可直接用於實作

**下一步**:撰寫 `06_template_system.md`,把 Summary + 對策的拆解設計形式化為統一樣板系統。