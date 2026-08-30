# v3.0 願景:智慧化 FA 報告改善

> **目標**:把「自動套樣板」升級為「智慧化評估 + 自動改善」
> **核心**:結合 LLM 推理、樣板系統、視覺設計原則,讓每次改善都是「量身打造」

---

## 一、v2.3.0 vs v3.0 思維差異

### v2.3.0:規則式套版

```
輸入(評估 JSON) → 固定規則 → 固定樣板 → 固定輸出
```

**問題**:
- 所有報告套用同一套樣板,不管報告性質(ESD 失效、機械損壞、製程問題...)
- LLM 評語原封不動塞進投影片,沒有加工
- 無法根據「缺少什麼」決定「加什麼」

### v3.0:智慧化推論

```
輸入(.pptx) 
  → LLM 深度理解(報告內容 + 失效類型 + 缺失維度)
  → 智慧決策引擎(決定加幾張、加什麼內容、用什麼視覺)
  → 樣板系統(提供視覺規範,不提供死板內容)
  → 量身打造的輸出
```

**差異**:
- 根據「失效類型」自動選用對應的專業樣板
- 根據「缺失嚴重度」決定改善力度(輕度補敘 vs 大幅重組)
- 根據「報告用途」(內部品管 vs 客戶報告)決定語氣與詳細程度

---

## 二、智慧化決策引擎設計

### 2.1 多維度分析

```python
@dataclass
class ReportContext:
    """報告的完整上下文,所有改善決策的基礎"""
    
    # 1. 失效類型分類
    failure_type: FailureType  # ESD / MECHANICAL / PROCESS / THERMAL / ...
    
    # 2. 報告成熟度
    maturity: ReportMaturity  # DRAFT / PRELIMINARY / FORMAL / FINAL
    
    # 3. 受眾
    audience: Audience  # INTERNAL_QA / CUSTOMER / SUPPLIER / REGULATORY
    
    # 4. 缺失嚴重度(每個維度獨立評估)
    gaps: Dict[Dimension, GapSeverity]  # NONE / MINOR / MODERATE / SEVERE
    
    # 5. 現有素材豐富度
    assets: AssetInventory  # 有多少圖表、表格、照片可用


class FailureType(Enum):
    ESD_DAMAGE = "ESD 靜電損傷"
    EOS_DAMAGE = "EOS 過電壓"
    THERMAL = "熱失效"
    MECHANICAL = "機械應力"
    PROCESS_DEFECT = "製程缺陷"
    MATERIAL = "材料問題"
    DESIGN = "設計問題"
    UNKNOWN = "未確定"


class GapSeverity(Enum):
    NONE = 0       # 完整,不需改善
    MINOR = 1      # 略不足,小幅補充
    MODERATE = 2    # 明顯缺失,需要新增投影片
    SEVERE = 3     # 嚴重缺失,需要多張投影片展開
```

### 2.2 決策規則範例

```python
def decide_improvements(context: ReportContext) -> ImprovementPlan:
    """根據報告上下文決定改善計畫"""
    plan = ImprovementPlan()
    
    # === 基本資訊 ===
    if context.gaps[Dimension.BASIC_INFO] >= GapSeverity.MODERATE:
        # 嚴重缺失 → 新增 1 張完整的基本資訊投影片
        plan.add(SlideAction.ADD_BASIC_INFO, priority="高")
    
    # === 根因分析 ===
    rc_severity = context.gaps[Dimension.ROOT_CAUSE]
    if rc_severity == GapSeverity.SEVERE:
        # 嚴重缺失 → 展開為 4 張投影片(5-Why、對照組、證據、結論)
        plan.add(SlideAction.ADD_5_WHY_ANALYSIS)
        plan.add(SlideAction.ADD_CONTROL_GROUP_DESIGN)
        plan.add(SlideAction.ADD_EVIDENCE_REQUIREMENTS)
        plan.add(SlideAction.ADD_STATISTICAL_VALIDATION)
    elif rc_severity == GapSeverity.MODERATE:
        # 中度缺失 → 2 張(5-Why + 統計驗證)
        plan.add(SlideAction.ADD_5_WHY_ANALYSIS)
        plan.add(SlideAction.ADD_STATISTICAL_VALIDATION)
    elif rc_severity == GapSeverity.MINOR:
        # 輕微缺失 → 1 張補充
        plan.add(SlideAction.ADD_RCA_SUPPLEMENT)
    
    # === 失效類型專屬樣板 ===
    if context.failure_type == FailureType.ESD_DAMAGE:
        plan.add(SlideAction.ADD_ESD_SPECIFIC_GUIDANCE)
        # 自動加入:ESD 防護設計建議、HBM 模型說明、TVS 選型建議
    elif context.failure_type == FailureType.THERMAL:
        plan.add(SlideAction.ADD_THERMAL_ANALYSIS_TEMPLATE)
        # 自動加入:熱阻分析、散熱設計建議
    
    # === 受眾調整 ===
    if context.audience == Audience.CUSTOMER:
        plan.apply_tone(FormalTone.PROFESSIONAL)
    elif context.audience == Audience.INTERNAL_QA:
        plan.apply_tone(FormalTone.TECHNICAL_DETAILED)
    
    return plan
```

---

## 三、智慧化內容生成

### 3.1 從 LLM 評語到投影片內容

**v2.3.0**:LLM 評語原封不動塞進投影片
```
LLM 評語:
"應使用 5-Why 分析法探討損傷發生的根本原因
(例如:是 ESD 靜電擊穿還是過電壓?),
並提供物理證據(如 SEM 觀察晶片內部燒毀痕跡)。"

v2.3.0 輸出:
• 應使用 5-Why 分析法探討損傷發生的根本原因(...)
```

**v3.0**:LLM 評語經過結構化加工
```python
def structure_llm_feedback(raw_feedback: str, failure_type: FailureType) -> StructuredAction:
    """將 LLM 自然語言評語轉為結構化行動項"""
    
    # 1. 拆解為多個子任務
    actions = extract_action_items(raw_feedback)
    # → ["使用 5-Why 分析", "提供物理證據", ...]
    
    # 2. 標註每個行動的屬性
    structured = []
    for action in actions:
        structured.append(ActionItem(
            action=action,
            priority=infer_priority(action),
            timeframe=infer_timeframe(action),  # 立即/短期/中期/長期
            owner=infer_owner(action),          # FAE/QRA/IQC/PM
            verification=infer_verification(action),  # 如何驗證完成
        ))
    
    # 3. 根據失效類型補充專業建議
    if failure_type == FailureType.ESD_DAMAGE:
        structured.append(ActionItem(
            action="ESD 防護設計 review",
            priority="高",
            timeframe="中期",
            owner="設計工程師",
            verification="HBM 測試通過 ±2kV",
        ))
    
    return structured
```

### 3.2 自動內容豐富化

```python
class ContentEnricher:
    """把簡短的 LLM 建議擴展為具體可執行的內容"""
    
    def enrich_iqc_action(self, brief: str) -> DetailedIQCStandard:
        """「建立 IQC SOP」→ 完整的 IQC 標準"""
        return DetailedIQCStandard(
            inspection_items=[
                InspectionItem("ESD 耐受測試", "±2kV HBM"),
                InspectionItem("I/O 對地阻抗", "與 DVT golden ±10%"),
                # ... 自動從樣板庫擴展
            ],
            sampling=AQL_0_65_Level_II,
            judgment_criteria="任一 FAIL 即整批退回",
            responsible_unit="IQC 工程師 + FAE",
            sop_document_id="ELAN-QA-IQC-XXX",
        )
    
    def enrich_monitoring_action(self, brief: str) -> MonitoringStandard:
        """「自動化監測」→ 完整的監測計畫"""
        return MonitoringStandard(
            metrics=[
                Metric("月度失效比例", threshold=0.03, action="自動通報"),
                Metric("連續 3 月趨勢", threshold=0.02, action="啟動 review"),
            ],
            notification_channels=["email", "Teams"],
            review_cadence="monthly",
        )
```

---

## 四、視覺化決策

### 4.1 自動選擇視覺元素

```python
def choose_visualization(content_type: ContentType, data: Any) -> VisualizationType:
    """根據內容類型自動選擇最適合的視覺元素"""
    
    match content_type:
        case ContentType.PRIORITY_LIST:
            # 優先級清單 → 時間軸圖
            return VisualizationType.TIMELINE
        
        case ContentType.COMPARISON:
            # 對照組 → 並排表格
            return VisualizationType.COMPARISON_TABLE
        
        case ContentType.PROCESS_FLOW:
            # 流程(如 5-Why) → 流程圖
            return VisualizationType.FLOW_DIAGRAM
        
        case ContentType.CHECKLIST:
            # 行動清單 → checkbox 列表
            return VisualizationType.CHECKLIST
        
        case ContentType.SCORES:
            # 評分 → 進度條/雷達圖
            return VisualizationType.PROGRESS_BARS
        
        case ContentType.ACTION_PLAN:
            # 行動計畫 → 時間軸 + checklist 組合
            return VisualizationType.TIMELINE_WITH_CHECKLIST
        
        case _:
            return VisualizationType.BULLET_LIST
```

### 4.2 樣板系統驅動的版面

```python
@dataclass
class SlideTemplate:
    """單張投影片的版面規範"""
    name: str
    title: str
    layout_name: str  # 使用既有 layout 名稱
    
    # 內容結構
    sections: List[Section]
    
    # 版面規範
    max_words_per_section: int = 30
    max_bullets_per_section: int = 5
    
    # 視覺元素
    primary_visual: Optional[VisualizationType] = None
    color_theme: str = "primary"
    
    # 品質約束
    min_white_space_ratio: float = 0.3  # 至少 30% 留白
    max_total_words: int = 200


# 內建樣板庫
BUILTIN_TEMPLATES = {
    "rca_5_why": SlideTemplate(
        name="rca_5_why",
        title="5-Why 根因推導",
        layout_name="2L - Topic",
        sections=[
            Section("為什麼需要 5-Why", max_bullets=3),
            Section("推導流程", visual=VisualizationType.FLOW_DIAGRAM),
            Section("目前缺少的環節", visual=VisualizationType.CHECKLIST),
        ],
        max_total_words=150,
    ),
    
    "prevention_overview": SlideTemplate(
        name="prevention_overview",
        title="改善對策總覽",
        layout_name="2L - Topic",
        sections=[
            Section("時間軸", visual=VisualizationType.TIMELINE),
            Section("立即行動", max_bullets=3),
            Section("短期對策", max_bullets=3),
            Section("中期對策", max_bullets=3),
            Section("長期預防", max_bullets=3),
        ],
        primary_visual=VisualizationType.TIMELINE,
        max_total_words=180,
    ),
    # ... 更多樣板
}
```

---

## 五、智慧化品質驗證

### 5.1 自動檢查清單

```python
class QualityChecker:
    """改善完成後自動品質檢查"""
    
    def check_all(self, original: Presentation, improved: Presentation) -> QualityReport:
        return QualityReport(
            master_preserved=self.check_master_preserved(original, improved),
            layouts_unchanged=self.check_layouts_unchanged(original, improved),
            original_slides_intact=self.check_original_slides(original, improved),
            slide_density_ok=self.check_slide_density(improved),
            visual_elements_present=self.check_visual_elements(improved),
            content_aligned_with_rubric=self.check_content_rubric_alignment(improved),
        )
    
    def check_slide_density(self, prs: Presentation) -> bool:
        """檢查每張投影片的資訊密度,避免再次出現「擠在一起」"""
        for slide in prs.slides:
            text = extract_all_text(slide)
            word_count = len(text.split())
            if word_count > 200:
                return False  # 太多文字,應該拆分
        return True
    
    def check_visual_elements(self, prs: Presentation) -> bool:
        """確認關鍵投影片有視覺元素(不只是純文字)"""
        for slide in prs.slides:
            if is_content_heavy_slide(slide):
                has_visual = any([
                    has_table(slide),
                    has_shape_group(slide),  # 流程圖、checklist
                    has_progress_indicator(slide),
                ])
                if not has_visual:
                    return False
        return True
```

### 5.2 母片保護(更嚴格)

```python
class MasterProtector:
    """三層保護機制,確保母片絕不被破壞"""
    
    def __init__(self, prs: Presentation):
        self.snapshot = self._capture_immutable_state(prs)
    
    def _capture_immutable_state(self, prs: Presentation) -> MasterSnapshot:
        """擷取所有不可變的狀態"""
        return MasterSnapshot(
            masters_xml=[m.element.xml for m in prs.slide_masters],
            layouts_xml=[l.element.xml for l in prs.slide_layouts],
            master_images=self._extract_master_images(prs),
            layout_names=[l.name for l in prs.slide_layouts],
            background_xml=self._extract_background_xml(prs),
        )
    
    def verify_after_improvement(self, prs: Presentation) -> None:
        """改善後驗證母片未被修改"""
        new_snapshot = self._capture_immutable_state(prs)
        if new_snapshot != self.snapshot:
            violations = new_snapshot.diff(self.snapshot)
            raise MasterProtectionError(
                f"母片保護失敗!以下項目被修改:\n{violations}"
            )
```

---

## 六、LLM 深度整合

### 6.1 多階段 LLM 推理

```
階段 1:內容理解(理解報告在做什麼)
    輸入: 整份 pptx 的文字 + 表格 + 圖片描述
    輸出: ReportContext(失效類型、成熟度、受眾、缺失)

階段 2:改善決策(決定加什麼)
    輸入: ReportContext + 評估分數
    輸出: ImprovementPlan(具體行動清單)

階段 3:內容生成(實際生成投影片內容)
    輸入: ImprovementPlan + 樣板
    輸出: 各投影片的結構化內容

階段 4:品質驗證(自動 review)
    輸入: 改善後的 pptx + 樣板 + 評估 rubric
    輸出: 品質報告(可選 LLM 評分)
```

### 6.2 範例:階段 1 的 LLM Prompt

```python
REPORT_ANALYSIS_PROMPT = """你是半導體失效分析(FA)專家。請分析以下 FA 報告內容,並提供結構化評估。

## 報告內容
{pptx_content}

## 評估維度(rubric)
{rubric_criteria}

## 你的任務
1. 識別失效類型(ESD / EOS / 熱 / 機械 / 製程 / 材料 / 設計 / 未確定)
2. 評估報告成熟度(草稿 / 初步 / 正式 / 定稿)
4. 判斷目標受眾(內部品管 / 客戶 / 供應商 / 法規)
5. 列出每個維度的缺失嚴重度(無 / 輕微 / 中度 / 嚴重)
6. 建議改善優先順序

請以 JSON 格式回應:
{{
  "failure_type": "...",
  "maturity": "...",
  "audience": "...",
  "gaps": {{
    "基本資訊完整性": "MODERATE",
    "根因分析": "SEVERE",
    ...
  }},
  "priority_improvements": ["..."]
}}
"""
```

---

## 七、實作路線圖

### Phase 1:基礎(2 週)
- [ ] 評估結果 dataclass 化
- [ ] LLM Client 抽象層 + OpenAI 實作
- [ ] 母片保護機制 + 單元測試

### Phase 2:樣板系統(1.5 週)
- [ ] SlideTemplate 設計 + JSON schema
- [ ] 5 個核心樣板(rca_5_why / prevention_overview / basic_info / monitoring_km / executive_summary)
- [ ] 樣板載入器

### Phase 3:決策引擎(1.5 週)
- [ ] ReportContext 分析
- [ ] 改善計畫決策邏輯
- [ ] 內容豐富化模組

### Phase 4:視覺化(1 週)
- [ ] 自動視覺元素生成(checklist / 流程圖 / 對照表 / 進度條)
- [ ] 樣板驅動的版面渲染

### Phase 5:品質保證(1 週)
- [ ] QualityChecker 完整實作
- [ ] 端對端測試
- [ ] 文件化與範例

**總預估**:7 週(約 35 工作天)

---

## 八、成功指標

| 指標 | v2.3.0 | v3.0 目標 |
|------|--------|-----------|
| 智慧決策 | 0%(固定樣板) | 100%(根據報告性質調整) |
| 視覺元素豐富度 | 純文字 | 每張至少有 1 個視覺元素 |
| 內容具體性 | 空泛 boilerplate | 有數字、責任人、頻率 |
| 母片保護 | 隱性 | 顯性 + 自動化測試 |
| LLM 整合 | 0% | 完整整合(評估+生成+驗證) |
| 可配置性 | 0% | 完全由樣板 JSON 控制 |
| 開發者體驗(DX) | 783 行單體 | 模組化、型別完整、測試覆蓋 |

---

**整合進度**:
- 此願景已取代原本 v3.0 重構計畫的單純「模組化」目標
- 結合了 `02_refactor_plan.md` 的架構 + `03_design_comparison.md` 的視覺原則 + `04_summary_design.md` 和 `05_prevention_design.md` 的具體案例
- 把「不要擠在一起」的設計原則提升為「智慧化、量身打造」

**下一步**:把這份願景作為 v3.0 的指導原則,進入實際開發。