"""建立 shape 的共用 helper(防止 v3.1.1 的殘留版面渲染問題)

修正的 bug:
- Bug 3:textbox 被旋轉 90°(260811 slides 1/3/4/5/6)
- Bug 4:底部 placeholder 殘留「按一下即可新增文字」(N160JCN 多張)
- Bug 2:title placeholder 找不到正確的 title(N160JCN / MS 多張)

設計理由:把所有 shape 建立邏輯統一到 helper,
避免未來 improver 再用 raw `slide.shapes.add_textbox()` 而忘記設定 rotation。
"""

from __future__ import annotations

from pptx.util import Inches, Pt


def safe_textbox(
    slide,
    left: float,
    top: float,
    width: float,
    height: float,
    *,
    text: str | None = None,
    font_size: int | None = None,
    font_bold: bool = False,
    word_wrap: bool = True,
    font_color_rgb: tuple[int, int, int] | None = None,
):
    """建立一個不會旋轉、不會變直式的 textbox

    Args:
        slide: pptx slide
        left/top/width/height: 英寸(float)
        text: 初始文字(可選)
        font_size: 字體大小 pt(可選)
        font_bold: 是否粗體
        word_wrap: 是否自動換行(預設 True)
        font_color_rgb: (R, G, B) tuple(可選)

    Returns:
        textbox shape
    """
    from pptx.dml.color import RGBColor

    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    # 關鍵:防止繼承母片的旋轉屬性(260811 bug)
    tb.rotation = 0

    tf = tb.text_frame
    tf.word_wrap = word_wrap
    # 關鍵:關掉 autofit,防止 textbox 寬度不足時自動縮小變直式
    tf.auto_size = None
    tf.margin_left = Inches(0.05)
    tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)

    if text is not None:
        p = tf.paragraphs[0]
        p.text = text
        if font_size is not None:
            p.font.size = Pt(font_size)
        p.font.bold = font_bold
        if font_color_rgb is not None:
            p.font.color.rgb = RGBColor(*font_color_rgb)

    return tb


def clean_unused_placeholders(slide, *, also_remove: bool = True) -> int:
    """清除未使用的 placeholder(預設文字或空)

    Args:
        slide: pptx slide
        also_remove: 是否從 slide 移除 placeholder(預設 True)
        also_clear_text: 已停用(被 also_remove 取代)

    Returns:
        清除的 placeholder 數量

    Note:
        只清空 placeholder 不夠 — LibreOffice 會 fallback 顯示
        layout 的預設文字(例如「按一下以編輯母片文字樣式」)。
        需要「從 slide 移除 placeholder」才能讓它們在 LibreOffice
        渲染時不顯示出來。

        _safe_shape_v2.py 的修正:從 slide 移除整個 placeholder 元素。
    """
    residual_markers = ("按一下", "Click to add", "Click here to add", "<click")
    cleared = 0
    # 用 list() 複製,避免迭代時改動
    for shape in list(slide.placeholders):
        if not shape.has_text_frame:
            continue
        text = shape.text_frame.text.strip()
        is_residual = not text or any(marker in text for marker in residual_markers)
        if is_residual and also_remove:
            # 從 slide 的 shape tree 中移除這個 placeholder
            sp = shape._element
            sp.getparent().remove(sp)
            cleared += 1
    return cleared


def get_title_placeholder(slide):
    """取得真實的 title placeholder

    修正 Bug 2:嚴格用 placeholder_format.idx == 0,
    而不是只看 shape.name 或 slide.shapes.title(可能在 MS / N160JCN
    母片設計中找到「按一下即可新增文字」副 placeholder)。

    同時檢查 layout name 是否含「直排」,若是則跳過 layout 的
    title placeholder(避免中文直排)。

    Args:
        slide: pptx slide

    Returns:
        title placeholder shape,或 None
    """
    # 先檢查 layout(直排 layout 不應使用其 title placeholder)
    layout_name = slide.slide_layout.name
    if "直排" in layout_name or "Vertical" in layout_name:
        # 跳過 layout placeholder,改用 safe_textbox fallback
        return None

    # 策略 1:用 placeholder_format.idx == 0(最嚴格)
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == 0:
            return ph
    # 策略 2:用 placeholder type 找 TITLE/CENTER_TITLE
    try:
        from pptx.enum.shapes import PP_PLACEHOLDER

        for ph in slide.placeholders:
            if ph.placeholder_format.type in (
                PP_PLACEHOLDER.TITLE,
                PP_PLACEHOLDER.CENTER_TITLE,
            ):
                return ph
    except (AttributeError, ValueError):
        pass
    # 策略 3:fallback — 找名稱含 title 的 shape
    for shape in slide.shapes:
        if shape.has_text_frame and "title" in shape.name.lower():
            return shape
    return None


def get_body_placeholder(slide):
    """取得 body placeholder,優先選擇 rotation == 0 且 orient='horiz' 的(Bug 3 修正)

    260811 的某些 layout body placeholder 被預設為:
    - layout name 含「直排」(例如「直排標題及文字」)
    - orient='vert'(垂直中文排版)
    - rotation=90°

    若直接寫入文字,整頁會變直式。

    修正策略:
    1. 先檢查 layout name 是否含「直排」→ 若是,直接跳過 layout placeholder
    2. 否則用 layout placeholder,但強制 orient='horiz' 與 rotation=0
    """
    # 先檢查 layout
    layout_name = slide.slide_layout.name
    if "直排" in layout_name or "Vertical" in layout_name:
        # 跳過 layout placeholder
        return None

    for shape in slide.placeholders:
        if shape.placeholder_format.idx != 0:
            # 關鍵修正:改為水平 orient(即使原本是 vert)
            import contextlib

            with contextlib.suppress(AttributeError, KeyError):
                ph_elem = shape._element.find(
                    ".//{http://schemas.openxmlformats.org/presentationml/2006/main}ph"
                )
                if ph_elem is not None:
                    ph_elem.set("orient", "horiz")
            # 同時確保 rotation = 0
            with contextlib.suppress(AttributeError):
                shape.rotation = 0
            return shape
    return None


def get_or_create_title(slide, slide_bounds=None):
    """取得 title placeholder,若無則建立新 textbox(Bug 2 + Bug 3 修正)"""
    ph = get_title_placeholder(slide)
    if ph is not None:
        return ph
    sw = slide_bounds["width_inch"] if slide_bounds else 10.0
    margin = 0.5
    return safe_textbox(
        slide,
        left=margin,
        top=0.3,
        width=sw - 2 * margin,
        height=1.0,
    )


def get_or_create_body(slide, slide_bounds=None):
    """取得 body placeholder,若無則建立新 textbox(Bug 3 修正)"""
    ph = get_body_placeholder(slide)
    if ph is not None:
        return ph
    sw = slide_bounds["width_inch"] if slide_bounds else 10.0
    sh = slide_bounds["height_inch"] if slide_bounds else 7.5
    margin = 0.5
    return safe_textbox(
        slide,
        left=margin,
        top=1.5,
        width=sw - 2 * margin,
        height=sh - 2.0,
    )
