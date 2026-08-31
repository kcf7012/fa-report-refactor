"""新增 FA 基本資訊投影片

從 TemplateLoader 載入 'basic_info' 樣板取得標題與 placeholder items。
向後相容:若不傳 loader,使用預設載入器。

視覺元素:使用 ChecklistGenerator 呈現基本資料的檢查狀態。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pptx import Presentation
from pptx.util import Inches

from ..domain.evaluation import EvaluationResult
from ..layout.selector import find_content_layout
from ..parsers.filename_parser import FilenameInfo
from ..templates.loader import TemplateLoader
from ..visuals import ELAN_BLUE, ChecklistGenerator
from ._template_helper import get_resolved_placeholders, resolve_template

if TYPE_CHECKING:
    pass


def add_basic_info_slide(
    prs: Presentation,
    evaluation: EvaluationResult,
    filename_info: FilenameInfo,
    template_loader: TemplateLoader | None = None,
    template_name: str = "basic_info",
) -> None:
    """新增 FA 基本資訊投影片

    Args:
        prs: 簡報物件
        evaluation: 評估結果
        filename_info: 檔名解析結果
        template_loader: 樣板載入器(可選,預設使用內建樣板)
        template_name: 樣板名稱(預設 'basic_info')
    """
    layout = find_content_layout(prs)
    slide = prs.slides.add_slide(layout)

    # 載入樣板
    template = resolve_template(template_loader, template_name)

    # 標題(從樣板)
    title_shape = _get_or_create_title(slide)
    title_shape.text_frame.text = template.title

    # 從樣板取得 placeholder items 並套用變數替換
    variables = {
        "fa_id": filename_info.to_fa_id(),
        "customer": filename_info.customer or "N/A",
        "project": filename_info.project or "N/A",
        "date": filename_info.date or "N/A",
    }
    placeholders = get_resolved_placeholders(template, section_index=0, variables=variables)

    # 使用 ChecklistGenerator 呈現基本資料的檢查狀態
    checklist_items = [
        {"text": item, "checked": False, "color": ELAN_BLUE}
        for item in placeholders
    ]
    if checklist_items:
        checklist_gen = ChecklistGenerator(
            slide,
            left=Inches(0.5),
            top=Inches(1.4),
            width=Inches(9.0),
            height=Inches(4.0),
        )
        checklist_gen.generate(checklist_items)

    # 優化建議項目(從 comment 抽取,屬於 section index 1)
    if evaluation.dimensions:
        dim = next((d for d in evaluation.dimensions if d.name.value == "基本資訊完整性"), None)
        if dim and dim.comment:
            # section 1 的標題(從樣板)
            section1 = template.sections[1] if len(template.sections) > 1 else None
            heading = section1.heading if section1 else "優化建議項目"

            # 用 textbox 顯示優化建議(在 checklist 下方)
            body = slide.shapes.add_textbox(
                _Inches(0.5), _Inches(5.5), _Inches(9.0), _Inches(1.5)
            )
            tf = body.text_frame
            tf.word_wrap = True

            p = tf.paragraphs[0]
            p.text = f"[{heading}]"
            p.font.bold = True
            p.font.color.rgb = _COLOR(255, 0, 0)
            p.font.size = _PT(14)

            sub = tf.add_paragraph()
            sub.text = f"• {dim.comment}"
            sub.font.size = _PT(12)


def _get_or_create_title(slide):
    if slide.shapes.title:
        return slide.shapes.title
    for shape in slide.shapes:
        if "title" in shape.name.lower():
            return shape
    return slide.shapes.add_textbox(_Inches(0.5), _Inches(0.3), _Inches(9), _Inches(1))


def _get_or_create_body(slide):
    for shape in slide.placeholders:
        if shape.placeholder_format.idx != 0:
            return shape
    return slide.shapes.add_textbox(_Inches(0.5), _Inches(1.5), _Inches(9), _Inches(5))


# Helper aliases(縮短程式碼)
_Inches = Inches


def _PT(size: int):  # noqa: N802
    from pptx.util import Pt

    return Pt(size)


def _COLOR(r: int, g: int, b: int):  # noqa: N802
    from pptx.dml.color import RGBColor

    return RGBColor(r, g, b)
