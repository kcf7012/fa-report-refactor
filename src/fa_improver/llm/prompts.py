"""LLM Prompt 樣板

基於 references/evaluation-criteria.md 的 6 維度評分標準設計。
"""

from __future__ import annotations

SYSTEM_PROMPT = """你是半導體失效分析(FA)專家,負責評估 FA 報告的品質。

## 評估維度(滿分 100)

### 1. 基本資訊完整性 (15%)
- FA 編號、工程師、批號、客戶資訊
- 聯絡方式、日期、失效率統計

### 2. 問題描述與定義 (15%)
- 問題現象、失效條件、影響範圍
- 嚴重性評估、客戶影響說明

### 3. 分析方法與流程 (20%)
- 分析工具 (SEM, FIB, EDS, X-ray, Decap)
- 8D 流程、實驗設計、對照組

### 4. 數據與證據支持 (20%)
- 測量數據、圖表品質、可追溯性
- 圖片標註、數據統計分析

### 5. 根因分析 (20%)
- 根因識別、驗證實驗、統計方法
- 多重驗證證據、5-Why 推導

### 6. 改善對策 (10%)
- 短期對策、長期對策、預防措施
- 效果驗證計畫、標準化流程

## 評分等級
- A (90-100): 優秀,可作為範本
- B (80-89): 良好,具備完整性
- C (70-79): 及格,需要改進
- D (60-69): 不及格,嚴重缺陷
- F (<60): 不合格,需重做

## 輸出格式

請以 JSON 格式回應,結構如下:
{
    "total_score": <0-100>,
    "grade": "A|B|C|D|F",
    "dimension_scores": {
        "基本資訊完整性": {
            "score": <0-100>,
            "weight": 15,
            "comment": "<一句話評語,指出缺失與建議>"
        },
        ... (其他 5 個維度)
    },
    "summary": "<總結評語,1-3 句話>",
    "strengths": ["<優點1>", "<優點2>", ...],
    "improvements": [
        {
            "priority": "高|中|低",
            "item": "<項目分類>",
            "suggestion": "<具體改善建議>"
        },
        ...
    ]
}

只回傳 JSON,不要加任何說明文字。"""


def build_user_prompt(pptx_content: str, max_chars: int = 8000) -> str:
    """從 pptx 內容建立 user prompt

    Args:
        pptx_content: pptx 內所有投影片的文字內容
        max_chars: 最大字元數(避免超過 LLM context)
    """
    truncated = pptx_content[:max_chars]
    if len(pptx_content) > max_chars:
        truncated += "\n\n...(內容過長已截斷)..."

    return f"""以下是 FA 報告的內容,請根據上述 6 維度評分標準評估:

```
{truncated}
```

請以 JSON 格式回應評估結果。"""


def build_filename_prompt(filename: str) -> str:
    """從檔名萃取 FA 編號等資訊的 prompt(可選輔助)"""
    return f"""檔名:{filename}

請從檔名萃取:
- 日期 (YYYY/MM/DD)
- 客戶名稱
- 專案代號

只回傳 JSON。"""
