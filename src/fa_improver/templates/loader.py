"""從 JSON 檔案或內建字典載入樣板"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ..domain.template import (
    BUILTIN_TEMPLATES,
    ColorTheme,
    SlideTemplate,
    TemplateSection,
    TemplateValidationError,
    VisualElement,
)


class TemplateLoader:
    """樣板載入器

    支援:
    1. 內建樣板(從 domain.template.BUILTIN_TEMPLATES)
    2. JSON 檔案(從使用者指定目錄)
    3. 樣板繼承(基於內建樣板覆寫部分欄位)
    """

    def __init__(self, custom_template_dir: Optional[Path] = None):
        self.custom_template_dir = custom_template_dir

    def load(self, name: str) -> SlideTemplate:
        """依名稱載入樣板(優先自訂,再內建)"""
        # 1. 先試自訂目錄
        if self.custom_template_dir:
            template = self._try_load_custom(name)
            if template:
                return template

        # 2. 找內建
        if name in BUILTIN_TEMPLATES:
            return BUILTIN_TEMPLATES[name]

        raise KeyError(
            f"找不到樣板 '{name}'。"
            f"內建樣板:{list(BUILTIN_TEMPLATES.keys())}"
            + (
                f"\n自訂目錄: {self.custom_template_dir}"
                if self.custom_template_dir
                else ""
            )
        )

    def _try_load_custom(self, name: str) -> Optional[SlideTemplate]:
        """嘗試從自訂目錄載入 JSON"""
        if not self.custom_template_dir:
            return None
        # 支援兩種檔名: name.json 或 name 開頭的檔案
        candidates = [
            self.custom_template_dir / f"{name}.json",
            self.custom_template_dir / f"{name}.template.json",
        ]
        for path in candidates:
            if path.exists():
                return self._from_json(path.read_text(encoding="utf-8"))
        return None

    def _from_json(self, content: str) -> SlideTemplate:
        """從 JSON 字串建立樣板"""
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise TemplateValidationError(f"樣板 JSON 解析失敗:{e}")

        template = self._dict_to_template(data)
        template.validate()
        return template

    def _dict_to_template(self, data: dict) -> SlideTemplate:
        """從 dict 建立 SlideTemplate

        支援繼承:若有 "extends" 欄位,會基於該樣板建立。
        """
        base_name = data.get("extends")
        if base_name:
            base = self.load(base_name)
            # 深拷貝 sections
            import copy

            base = copy.deepcopy(base)

            # 覆寫欄位
            template = SlideTemplate(
                name=data.get("name", base.name),
                title=data.get("title", base.title),
                layout_name=data.get("layout_name", base.layout_name),
                description=data.get("description", base.description),
                max_total_words=data.get("max_total_words", base.max_total_words),
                min_white_space_ratio=data.get(
                    "min_white_space_ratio", base.min_white_space_ratio
                ),
                primary_visual=VisualElement(
                    data.get("primary_visual", base.primary_visual.value)
                ),
                color_theme=ColorTheme(data.get("color_theme", base.color_theme.value)),
            )
            # 合併 sections(如有 override)
            if "sections" in data:
                template.sections = [
                    self._section_from_dict(s) for s in data["sections"]
                ]
            else:
                template.sections = base.sections
            return template

        # 全新樣板
        return SlideTemplate(
            name=data["name"],
            title=data["title"],
            layout_name=data.get("layout_name", "2L - Topic"),
            description=data.get("description", ""),
            max_total_words=data.get("max_total_words", 200),
            min_white_space_ratio=data.get("min_white_space_ratio", 0.3),
            primary_visual=VisualElement(data.get("primary_visual", "bullet_list")),
            color_theme=ColorTheme(data.get("color_theme", "primary")),
            sections=[self._section_from_dict(s) for s in data.get("sections", [])],
        )

    def _section_from_dict(self, data: dict) -> TemplateSection:
        """從 dict 建立 TemplateSection"""
        return TemplateSection(
            heading=data["heading"],
            visual=VisualElement(data.get("visual", "bullet_list")),
            max_bullets=data.get("max_bullets", 4),
            max_words_per_bullet=data.get("max_words_per_bullet", 30),
            placeholder_items=data.get("placeholder_items", []),
        )

    def list_available(self) -> list[str]:
        """列出所有可用樣板名稱"""
        names = set(BUILTIN_TEMPLATES.keys())
        if self.custom_template_dir and self.custom_template_dir.exists():
            for f in self.custom_template_dir.glob("*.json"):
                # 跳過 _example 或 readme
                if f.stem.startswith("_"):
                    continue
                names.add(f.stem)
        return sorted(names)


def load_template(
    name: str, custom_dir: Optional[Path] = None
) -> SlideTemplate:
    """便利函式:載入樣板"""
    return TemplateLoader(custom_dir).load(name)