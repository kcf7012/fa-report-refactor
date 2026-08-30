# 自訂樣板範例

這個目錄展示如何建立與使用自訂樣板。

## 檔案說明

- `prevention_overview_company.json` — 基於內建 `prevention_overview` 樣板的客製版本
  - 加入公司專屬的 SOP 編號(ELAN-QA-IQC-2026)
  - 加入每月失效案例分享會
  - 標題改為「ELAN 改善對策總覽」
  - visual 改為 checklist

## 使用方式

```bash
# CLI 指定自訂目錄(待 Phase 5 實作)
python -m fa_improver \
    report.pptx \
    --eval report/eval.json \
    --output improved.pptx \
    --template-dir examples/custom_templates
```

## 樣板繼承語法

```json
{
  "extends": "prevention_overview",  // 繼承哪個內建樣板
  "title": "...",
  "sections": [
    // 覆寫 sections
  ]
}
```

## 驗證規則

| 欄位 | 限制 | 違反訊息 |
|------|------|---------|
| `max_bullets` | ≤ 5(資料表除外) | 「一張投影片一個主題」 |
| `max_words_per_bullet` | ≤ 50(摘要除外) | 單個 bullet 太長 |
| `max_total_words` | ≤ 300 | 請精簡內容 |
| `sections` 數量 | ≤ 5 | 請拆分 |
| `placeholder_items` | ≤ 10 | 請拆分 |

違反任何規則都會在載入時拋出 `TemplateValidationError`。
