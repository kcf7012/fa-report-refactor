"""新增根因分析相關投影片

從 TemplateLoader 載入 'root_cause_5why' 或 'root_cause_statistical' 樣板取得標題。
向後相容:若不傳 loader,使用預設載入器。
"""

from __future__ import annotations

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

from ..domain.evaluation import EvaluationResult
from ..layout.selector import find_content_layout
from ..templates.loader import TemplateLoader
from ._template_helper import get_resolved_placeholders, resolve_template


def add_statistical_analysis_slide(
    prs: Presentation,
    evaluation: EvaluationResult,
    suggestions: list[str],
    variant: str = "statistical",
    template_loader: TemplateLoader | None = None,
) -> None:
    """新增根因分析投影片

    Args:
        prs: 簡報物件
        evaluation: 評估結果
        suggestions: 建議清單
        variant:
            - "5_why": 5-Why 推導流程
            - "statistical": 統計驗證方法
        template_loader: 樣板載入器(可選)
    """
    # 載入對應樣板
    template_name = "root_cause_5why" if variant == "5_why" else "root_cause_statistical"
    template = resolve_template(template_loader, template_name)

    layout = find_content_layout(prs)
    slide = prs.slides.add_slide(layout)

    # 標題(從樣板)
    title = _get_or_create_title(slide)
    title.text_frame.text = template.title

    # 內容
    if not suggestions:
        suggestions = ["建議加強對照組設定與數據統計驗證以支撐根因發現。"]

    body = _get_or_create_body(slide)
    tf = body.text_frame
    tf.clear()

    # section 0 的標題
    section0 = template.sections[0] if template.sections else None
    heading0 = section0.heading if section0 else "針對問題點之深度分析建議"

    p = tf.paragraphs[0]
    p.text = f"{heading0}:"
    p.font.bold = True
    p.font.size = Pt(18)
    p.font.color.rgb = RGBColor(0, 112, 192)

    # 限制在 max_bullets
    max_bullets = section0.max_bullets if section0 else 4
    for sug in suggestions[:max_bullets]:
        p = tf.add_paragraph()
        p.text = sug
        p.font.size = Pt(14)

    # section 1 的標題(若存在)
    section1 = template.sections[1] if len(template.sections) > 1 else None
    if section1:
        p = tf.add_paragraph()
        p.text = f"\n[{section1.heading}]"
        p.font.bold = True

        # 從樣板讀取 placeholder_items
        placeholders = get_resolved_placeholders(template, section_index=1)
        if placeholders:
            for item in placeholders:
                p = tf.add_paragraph()
                p.text = f"• {item}"
                p.font.size = Pt(12)
        else:
            # fallback:統計驗證預設 actions
            for action in [
                "設定 DVT 正常品 vs PVT 異常品之對照組",
                "使用獨立樣本 t 檢定驗證參數顯著性 (p < 0.05)",
                "確保統計證據支持最終提到的根本原因",
            ]:
                p = tf.add_paragraph()
                p.text = f"• {action}"
                p.font.size = Pt(12)


def _get_or_create_title(slide):
    if slide.shapes.title:
        return slide.shapes.title
    for shape in slide.shapes:
        if "title" in shape.name.lower():
            return shape
    return slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(1))


def _get_or_create_body(slide):
    for shape in slide.placeholders:
        if shape.placeholder_format.idx != 0:
            return shape
    return slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(9), Inches(5))
