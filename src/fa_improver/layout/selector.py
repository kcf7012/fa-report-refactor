"""智慧 layout 選擇器"""

from __future__ import annotations

from pptx import Presentation
from pptx.slide import SlideLayout


def find_content_layout(prs: Presentation) -> SlideLayout:
    """自動尋找適合「標題+內容」的 layout

    原則:
    1. 跳過 Cover/封面類型
    2. 優先選名稱含 'Topic' / 'Content' / '標題' 的 layout
    3. 必須有 >= 2 個 placeholder(標題+內文)
    """
    candidates = []
    for i, layout in enumerate(prs.slide_layouts):
        name_lower = layout.name.lower()
        if "cover" in name_lower or "封面" in layout.name:
            continue
        placeholder_count = len(list(layout.placeholders))
        if placeholder_count < 2:
            continue

        score = 0
        if "topic" in name_lower:
            score += 10
        if "content" in name_lower:
            score += 5
        if "標題" in layout.name:
            score += 3
        if "議程" in layout.name or "agenda" in name_lower:
            score += 1

        candidates.append((score, i, layout.name))

    if candidates:
        candidates.sort(reverse=True)
        return prs.slide_layouts[candidates[0][1]]

    # fallback
    if len(prs.slide_layouts) > 1:
        return prs.slide_layouts[1]
    return prs.slide_layouts[0]
