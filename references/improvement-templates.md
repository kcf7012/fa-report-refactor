# FA Report Improvement Templates — v3.1.0 對照

> **本檔為概念性樣板說明**(Template 1-5)
> **實際實作**:8 個 JSON 樣板於 `src/fa_improver/templates/builtin/`
> **詳見**:`docs/10_api_reference.md` § 6 樣板系統

## Template 1: Basic Information Slide
- FA 編號, 負責工程師, 批號
- 客戶, 專案名稱, Touch IC
- 問題/FA 報告日期
- 客戶聯絡人, 失效率
- **實際實作樣板**:`basic_info.json`

## Template 2: Statistical Validation
- 對照組設定 (正常 vs 異常)
- 統計方法 (t-test, α=0.05)
- 分析結果 (mean, SD, t-value, p-value, CI)
- 結論驗證

## Template 3: Prevention Measures
- 製程改善與標準化
- 持續監測機制
- 知識管理

## Template 4: Figure Captions
- 圖表編號與說明
- 觀察結果描述
- 支撐結論的引用

## Template 5: Summary Enhancement
- 根因確認依據 (5項證據)
- Suspected Root Cause
- Action Plan
- **實際實作樣板**:`executive_summary.json`

---

## v3.0.0 新增的 3 個樣板(對應 Phase 4.5)

### Template 6: Problem Definition(問題描述與失效定義)
- 失效現象 vs 失效模式 對照表
- 問題範圍量化(失效率、影響數量)
- 客戶影響評估
- **樣板**:`problem_definition.json`
- **Improver**:`ProblemDefinitionImprover`

### Template 7: Analysis Method(分析方法與 8D 流程)
- 8D 流程檢查清單(D1-D8)
- 分析方法對照表(SEM/FIB/X-ray 適用場景)
- 實驗設計 SOP 範本
- **樣板**:`analysis_method.json`
- **Improver**:`AnalysisMethodImprover`

### Template 8: Evidence Checklist(數據與證據支持)
- 對照組 vs 異常品 數據對照表
- 圖片品質檢查清單
- 數據追溯性指引
- **樣板**:`evidence_checklist.json`
- **Improver**:`EvidenceChecklistImprover`

---
**版本**: 3.1.0
**最後更新**: 2026-08-31
