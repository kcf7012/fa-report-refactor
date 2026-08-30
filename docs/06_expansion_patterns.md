# 投影片展開設計模式 — 通用原則

> **目的**:統一所有「把一張擠在一起的投影片展開為多張」的模式
> **適用對象**:Summary、根因分析、改善對策、基本資訊等所有可展開的區塊

---

## 一、通用模式

任何「原本擠在一張」的內容,展開時都遵循以下三步:

### Step 1:識別內容主題

問自己:**這張投影片在講幾件事?**

| 範例 | 原投影片 | 隱含主題數 |
|------|---------|-----------|
| 根因驗證及統計分析 | 5-Why、對照組、統計、執行 | 4 個 |
| 改善對策 | 立即、短期、IQC、監測 | 4 個 |
| Summary 強化 | 原 Summary、LLM評估、改進建議 | 3 個 |

### Step 2:依主題拆分

| 拆分原則 | 說明 |
|---------|------|
| **時間軸優先** | 立即 → 短期 → 中期 → 長期(改善對策類) |
| **流程優先** | Why 1 → Why 2 → Why 3 → ...(根因類) |
| **層次優先** | 總覽 → 細節 → 行動(Summary 類) |

### Step 3:每張投影片套用視覺元素

| 主題類型 | 推薦視覺元素 |
|---------|------------|
| 時間軸 | Timeline |
| 流程 | Flow Diagram |
| 清單 | Checklist |
| 對照 | Comparison Table |
| 評分 | Progress Bars |
| 總覽 | Summary Card |

---

## 二、四種常見展開模式

### 模式 A:Summary 強化(3 張)

| 順序 | 投影片 | 內容 |
|------|--------|------|
| 1 | Summary 報告總結 | 原 Summary 內容(不變) |
| 2 | Executive Summary | LLM 評估總覽(評分雷達圖) |
| 3 | Key Improvements | 改進建議 checklist |

**範例**:見 `VISION.md` §「智慧化決策引擎」

### 模式 B:改善對策(3 張)

| 順序 | 投影片 | 內容 |
|------|--------|------|
| 1 | 改善對策總覽 | 時間軸 + 立即/短期/中期/長期 checklist |
| 2 | IQC 與製程標準化 | 檢驗項目表 + 抽樣 + 文件化 |
| 3 | 持續監測與知識管理 | 監測機制 + KM + 教育訓練 |

**範例**:見 `VISION.md` §「視覺化決策」

### 模式 C:根因分析(4 張)

| 順序 | 投影片 | 內容 |
|------|--------|------|
| 1 | 為何「推測」≠「分析」 | 概念對比表 |
| 2 | 5-Why 推導流程 | 流程圖,標示目前在哪一層 |
| 3 | 統計驗證方法 | DVT vs PVT 對照表 |
| 4 | 關鍵驗證證據 | SEM / X-ray / Decap 視覺方塊 |

### 模式 D:基本資訊(1-2 張)

| 順序 | 投影片 | 內容 |
|------|--------|------|
| 1 | FA 基本資訊 | FA 編號、工程師、客戶、專案、日期 + 優化建議 |

**通常 1 張就夠**,不需要展開。

---

## 三、共同設計原則

### 1. 一張投影片只講一件事
- ❌ 1 張 7 個 bullet
- ✅ 1 張 2-3 個重點 + 1 個視覺元素

### 2. 視覺元素優先
- 每張投影片至少有 1 個非純文字元素
- 表格、流程圖、checklist、進度條、時間軸

### 3. 留白 ≥30%
- 單張不超過 200 字
- 不要填滿整張投影片

### 4. 母片保護
- 新增投影片使用既有 layout
- 不修改、不新增 layout
- 不修改母片 XML

---

## 四、範本程式碼

```python
def expand_section_to_slides(
    prs: Presentation,
    section_type: SectionType,
    context: ReportContext,
    insert_after_idx: int,
) -> List[Slide]:
    """通用展開模式:把一段內容展開為多張投影片"""
    
    patterns = {
        SectionType.SUMMARY: expand_summary_pattern,
        SectionType.PREVENTION: expand_prevention_pattern,
        SectionType.ROOT_CAUSE: expand_root_cause_pattern,
        SectionType.BASIC_INFO: expand_basic_info_pattern,
    }
    
    pattern_fn = patterns[section_type]
    return pattern_fn(prs, context, insert_after_idx)


def expand_summary_pattern(prs, context, after_idx):
    """模式 A:Summary 展開為 3 張"""
    s1 = add_summary_report_slide(prs, context)  # 原 Summary
    move_to(prs, len(prs.slides) - 1, after_idx + 1)
    
    s2 = add_executive_summary_slide(prs, context)  # LLM 評估
    move_to(prs, len(prs.slides) - 1, after_idx + 2)
    
    s3 = add_key_improvements_slide(prs, context)  # 改進建議
    move_to(prs, len(prs.slides) - 1, after_idx + 3)
    
    return [s1, s2, s3]
```

---

**整合進度**:本文件取代了原本分散在 `04_summary_design.md` 和 `05_prevention_design.md` 的重複內容,以通用模式統一呈現。具體範例可參考 `VISION.md`。