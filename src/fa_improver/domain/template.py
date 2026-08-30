"""樣板系統的資料模型"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class VisualElement(str, Enum):
    """視覺元素類型"""

    NONE = "none"
    BULLET_LIST = "bullet_list"
    CHECKLIST = "checklist"
    FLOW_DIAGRAM = "flow_diagram"
    COMPARISON_TABLE = "comparison_table"
    PROGRESS_BARS = "progress_bars"
    TIMELINE = "timeline"
    SUMMARY_CARD = "summary_card"


class ColorTheme(str, Enum):
    """色系主題"""

    PRIMARY = "primary"  # 深藍(主品牌色)
    ACCENT = "accent"  # 強調色
    WARNING = "warning"  # 警告(紅)
    SUCCESS = "success"  # 成功(綠)
    NEUTRAL = "neutral"  # 中性(灰)


@dataclass
class TemplateSection:
    """投影片的一個區塊"""

    heading: str  # 區塊標題
    visual: VisualElement = VisualElement.BULLET_LIST
    max_bullets: int = 4
    max_words_per_bullet: int = 30
    placeholder_items: List[str] = field(default_factory=list)
    """可被實際內容替換的 placeholder 項目,例如 ['DVT 正常品', 'PVT 異常品']"""

    def validate(self) -> None:
        """驗證品質約束"""
        # 基本資料類型的 section 可以超過 5 bullets(作為資料表)
        # 但 placeholder_items 的長度不能超過 10
        if self.max_bullets > 5 and not self.placeholder_items:
            raise TemplateValidationError(
                f"Section '{self.heading}' 的 max_bullets ({self.max_bullets}) 超過 5。"
                f"違反「一張投影片一個主題」原則。"
            )
        if len(self.placeholder_items) > 10:
            raise TemplateValidationError(
                f"Section '{self.heading}' 的 placeholder_items ({len(self.placeholder_items)}) 超過 10。"
                f"請拆分為多個 section。"
            )
        # summary_card 類型的視覺元素可以較長(因為是摘要文字)
        max_words_allowed = 100 if self.visual == VisualElement.SUMMARY_CARD else 50
        if self.max_words_per_bullet > max_words_allowed:
            raise TemplateValidationError(
                f"Section '{self.heading}' 的 max_words_per_bullet ({self.max_words_per_bullet}) 超過 {max_words_allowed}。"
                f"單個 bullet 太長。"
            )


@dataclass
class SlideTemplate:
    """單張投影片的版面規範"""

    name: str  # 樣板唯一名稱
    title: str  # 投影片標題
    layout_name: str = "2L - Topic"  # 使用的 layout(必須已存在)

    # 內容結構
    sections: List[TemplateSection] = field(default_factory=list)

    # 版面規範
    max_total_words: int = 200
    min_white_space_ratio: float = 0.3

    # 視覺元素
    primary_visual: VisualElement = VisualElement.BULLET_LIST
    color_theme: ColorTheme = ColorTheme.PRIMARY

    # 描述(用於文件)
    description: str = ""

    def validate(self) -> None:
        """驗證整個樣板"""
        if len(self.sections) == 0:
            raise TemplateValidationError(
                f"Template '{self.name}' 沒有任何 sections。"
            )
        if len(self.sections) > 5:
            raise TemplateValidationError(
                f"Template '{self.name}' 有 {len(self.sections)} 個 sections,超過 5。"
                f"請拆分為多個樣板。"
            )
        if self.max_total_words > 300:
            raise TemplateValidationError(
                f"Template '{self.name}' 的 max_total_words ({self.max_total_words}) 超過 300。"
                f"請精簡內容。"
            )
        for section in self.sections:
            section.validate()


class TemplateValidationError(Exception):
    """樣板驗證失敗"""

    pass


# ============================================
# 內建樣板 — 對應 5 種改善動作
# ============================================

BASIC_INFO_TEMPLATE = SlideTemplate(
    name="basic_info",
    title="FA 基本資訊",
    layout_name="2L - Topic",
    description="新增 FA 報告的基本資訊(編號、工程師、客戶、專案、日期等)",
    sections=[
        TemplateSection(
            heading="基本資料",
            visual=VisualElement.BULLET_LIST,
            max_bullets=7,
            max_words_per_bullet=10,
            placeholder_items=[
                "FA 編號: {fa_id}",
                "負責工程師: ELAN FAE",
                "客戶: {customer}",
                "專案名稱: {project}",
                "報告日期: {date}",
                "失效數量: 依評核建議補充填寫",
                "批號 (Lot No.): 依評核建議補充填寫",
            ],
        ),
        TemplateSection(
            heading="優化建議項目",
            visual=VisualElement.BULLET_LIST,
            max_bullets=3,
            max_words_per_bullet=40,
        ),
    ],
    primary_visual=VisualElement.BULLET_LIST,
    max_total_words=150,
)


ROOT_CAUSE_5_WHY_TEMPLATE = SlideTemplate(
    name="root_cause_5why",
    title="5-Why 根因推導",
    layout_name="2L - Topic",
    description="5-Why 推導流程,標示目前推導到哪一層",
    sections=[
        TemplateSection(
            heading="為什麼需要 5-Why",
            visual=VisualElement.COMPARISON_TABLE,
            max_bullets=3,
            max_words_per_bullet=25,
        ),
        TemplateSection(
            heading="推導流程",
            visual=VisualElement.FLOW_DIAGRAM,
            max_bullets=5,  # Why 1-5
            max_words_per_bullet=20,
        ),
        TemplateSection(
            heading="目前缺少的環節",
            visual=VisualElement.CHECKLIST,
            max_bullets=4,
            max_words_per_bullet=30,
        ),
    ],
    primary_visual=VisualElement.FLOW_DIAGRAM,
    max_total_words=180,
)


ROOT_CAUSE_STATISTICAL_TEMPLATE = SlideTemplate(
    name="root_cause_statistical",
    title="根因驗證及統計分析",
    layout_name="2L - Topic",
    description="統計驗證方法:對照組設計與 t-test",
    sections=[
        TemplateSection(
            heading="針對問題點之深度分析建議",
            visual=VisualElement.BULLET_LIST,
            max_bullets=4,
            max_words_per_bullet=30,
        ),
        TemplateSection(
            heading="建議執行動作",
            visual=VisualElement.CHECKLIST,
            max_bullets=3,
            max_words_per_bullet=30,
            placeholder_items=[
                "設定 DVT 正常品 vs PVT 異常品之對照組",
                "使用獨立樣本 t 檢定驗證參數顯著性 (p < 0.05)",
                "確保統計證據支持最終提到的根本原因",
            ],
        ),
    ],
    primary_visual=VisualElement.CHECKLIST,
    max_total_words=180,
)


PREVENTION_OVERVIEW_TEMPLATE = SlideTemplate(
    name="prevention_overview",
    title="長期預防措施與改善對策",
    layout_name="2L - Topic",
    description="改善對策總覽 + 標準化與監測計畫",
    sections=[
        TemplateSection(
            heading="擬議改善對策項目",
            visual=VisualElement.BULLET_LIST,
            max_bullets=3,
            max_words_per_bullet=30,
        ),
        TemplateSection(
            heading="標準化與監測計畫",
            visual=VisualElement.CHECKLIST,
            max_bullets=3,
            max_words_per_bullet=30,
            placeholder_items=[
                "建立入料檢驗 (IQC) SOP 與測試閾值",
                "導入自動化監測設備於生產線",
                "將此案例納入知識管理資料庫以利後續追蹤",
            ],
        ),
    ],
    primary_visual=VisualElement.CHECKLIST,
    max_total_words=180,
)


EXECUTIVE_SUMMARY_TEMPLATE = SlideTemplate(
    name="executive_summary",
    title="Summary 報告總結",
    layout_name="Topic",
    description="保留原 Summary + 強化 Executive Summary 與 Key Improvements",
    sections=[
        TemplateSection(
            heading="原 Summary 內容",
            visual=VisualElement.BULLET_LIST,
            max_bullets=5,
            max_words_per_bullet=30,
        ),
        TemplateSection(
            heading="分析優點與成功驗證",
            visual=VisualElement.CHECKLIST,
            max_bullets=5,
            max_words_per_bullet=30,
        ),
        TemplateSection(
            heading="Executive Summary",
            visual=VisualElement.SUMMARY_CARD,
            max_bullets=1,
            max_words_per_bullet=100,
        ),
        TemplateSection(
            heading="Key Improvements Required",
            visual=VisualElement.CHECKLIST,
            max_bullets=5,
            max_words_per_bullet=30,
        ),
    ],
    primary_visual=VisualElement.SUMMARY_CARD,
    max_total_words=250,
)


# 樣板註冊表
BUILTIN_TEMPLATES = {
    "basic_info": BASIC_INFO_TEMPLATE,
    "root_cause_5why": ROOT_CAUSE_5_WHY_TEMPLATE,
    "root_cause_statistical": ROOT_CAUSE_STATISTICAL_TEMPLATE,
    "prevention_overview": PREVENTION_OVERVIEW_TEMPLATE,
    "executive_summary": EXECUTIVE_SUMMARY_TEMPLATE,
}