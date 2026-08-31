"""Improver 與 TemplateLoader 整合的輔助模組

提供給所有 improver 共用:
- 從樣板取得標題與 placeholder items
- 套用變數替換({fa_id}、{customer} 等)
"""

from __future__ import annotations

import re
from typing import Any

from ..domain.template import SlideTemplate
from ..templates.loader import TemplateLoader


def resolve_template(
    loader: TemplateLoader | None,
    template_name: str,
) -> SlideTemplate:
    """載入樣板;若 loader 為 None,使用預設 TemplateLoader

    Args:
        loader: 樣板載入器(可選)
        template_name: 樣板名稱

    Returns:
        載入的 SlideTemplate

    Raises:
        KeyError: 找不到樣板時
    """
    if loader is None:
        loader = TemplateLoader()
    return loader.load(template_name)


def substitute_placeholders(text: str, variables: dict[str, Any]) -> str:
    """替換文字中的 {variable} 佔位符

    Args:
        text: 含 {var} 的文字
        variables: 變數字典(例如 {"fa_id": "FA-001"})

    Returns:
        替換後的文字

    Example:
        >>> substitute_placeholders("FA 編號: {fa_id}", {"fa_id": "FA-001"})
        'FA 編號: FA-001'
    """
    if not text:
        return text
    return re.sub(
        r"\{(\w+)\}",
        lambda m: str(variables.get(m.group(1), m.group(0))),
        text,
    )


def get_resolved_placeholders(
    template: SlideTemplate,
    section_index: int = 0,
    variables: dict[str, Any] | None = None,
) -> list[str]:
    """從樣板取得 section 的 placeholder_items,並套用變數替換

    Args:
        template: 已載入的樣板
        section_index: 第幾個 section(預設 0)
        variables: 變數字典(可選)

    Returns:
        替換後的 placeholder 列表
    """
    if not template.sections or section_index >= len(template.sections):
        return []

    section = template.sections[section_index]
    items = list(section.placeholder_items)

    if variables:
        items = [substitute_placeholders(item, variables) for item in items]

    return items
