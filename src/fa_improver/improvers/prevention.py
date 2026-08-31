"""新增改善對策投影片

從 TemplateLoader 載入 'prevention_overview' 樣板取得標題與 placeholder items。
向後相容:若不傳 loader,使用預設載入器。
"""

from __future__ import annotations

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

from ..domain.evaluation import EvaluationResult
from ..domain.suggestion import Improvement
from ..layout.selector import find_content_layout
from ..templates.loader import TemplateLoader
from ._template_helper import get_resolved_placeholders, resolve_template


def add_prevention_measures_slide(
    prs: Presentation,
    evaluation: EvaluationResult,
    improvements: list[Improvement],
    template_loader: TemplateLoader | None = None,
    template_name: str = "prevention_overview",
) -> None:
    """新增長期預防措施與改善對策投影片

    Args:
        prs: 簡報物件
        evaluation: 評估結果
        improvements: 改進建議清單
        template_loader: 樣板載入器(可選)
        template_name: 樣板名稱(預設 'prevention_overview')
    """
    # 載入樣板
    template = resolve_template(template_loader, template_name)

    layout = find_content_layout(prs)
    slide = prs.slides.add_slide(layout)

    # 標題(從樣板)
    title = _get_or_create_title(slide)
    title.text_frame.text = template.title

    body = _get_or_create_body(slide)
    tf = body.text_frame
    tf.clear()

    # section 0:擬議改善對策項目
    section0 = template.sections[0] if template.sections else None
    heading0 = section0.heading if section0 else "擬議改善對策項目"

    p = tf.paragraphs[0]
    p.text = f"{heading0}:"
    p.font.bold = True
    p.font.size = Pt(18)
    p.font.color.rgb = RGBColor(0, 112, 192)

    # 從 improvements 抽取建議,限制在 max_bullets
    if improvements:
        max_bullets = section0.max_bullets if section0 else 3
        for imp in improvements[:max_bullets]:
            p = tf.add_paragraph()
            p.text = imp.suggestion
            p.font.size = Pt(14)

    # section 1:標準化與監測計畫
    section1 = template.sections[1] if len(template.sections) > 1 else None
    if section1:
        p = tf.add_paragraph()
        p.text = f"\n[{section1.heading}]"
        p.font.bold = True

        # 優先用樣板的 placeholder_items
        placeholders = get_resolved_placeholders(template, section_index=1)
        if placeholders:
            for item in placeholders:
                p = tf.add_paragraph()
                p.text = f"• {item}"
                p.font.size = Pt(12)
        else:
            # fallback
            for item in [
                "建立入料檢驗 (IQC) SOP 與測試閾值",
                "導入自動化監測設備於生產線",
                "將此案例納入知識管理資料庫以利後續追蹤",
            ]:
                p = tf.add_paragraph()
                p.text = f"• {item}"
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
