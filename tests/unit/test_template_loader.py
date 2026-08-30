"""樣板系統測試"""

import json
from pathlib import Path

import pytest

from fa_improver.domain.template import (
    BUILTIN_TEMPLATES,
    BASIC_INFO_TEMPLATE,
    ColorTheme,
    SlideTemplate,
    TemplateSection,
    TemplateValidationError,
    VisualElement,
)
from fa_improver.templates.loader import TemplateLoader


class TestBuiltinTemplates:
    """內建樣板測試"""

    def test_basic_info_has_7_items(self):
        """基本資訊樣板應有 7 個欄位"""
        t = BASIC_INFO_TEMPLATE
        assert len(t.sections[0].placeholder_items) == 7

    def test_all_builtin_templates_valid(self):
        """所有內建樣板都應通過驗證"""
        for name, template in BUILTIN_TEMPLATES.items():
            template.validate()  # 不應拋出

    def test_max_bullets_constraint(self):
        """max_bullets 不能超過 5(除非作為資料表)"""
        bad_section = TemplateSection(
            heading="too many",
            max_bullets=10,  # 違規
        )
        with pytest.raises(TemplateValidationError, match="max_bullets"):
            bad_section.validate()

    def test_placeholder_items_constraint(self):
        """placeholder_items 不能超過 10"""
        bad_section = TemplateSection(
            heading="too many items",
            placeholder_items=[f"item{i}" for i in range(20)],
        )
        with pytest.raises(TemplateValidationError, match="placeholder_items"):
            bad_section.validate()

    def test_basic_info_with_placeholder_items_passes(self):
        """基本資料類型可以超過 5 bullets(因為是資料表)"""
        section = TemplateSection(
            heading="基本資料",
            max_bullets=7,  # 超過 5 但有 placeholder_items
            placeholder_items=[f"item{i}" for i in range(7)],
        )
        section.validate()  # 不應拋出

    def test_max_words_constraint(self):
        """max_words_per_bullet 不能超過 50"""
        bad_section = TemplateSection(
            heading="too long",
            max_words_per_bullet=100,  # 違規
        )
        with pytest.raises(TemplateValidationError, match="max_words_per_bullet"):
            bad_section.validate()

    def test_max_total_words_constraint(self):
        """整張 max_total_words 不能超過 300"""
        bad_template = SlideTemplate(
            name="bad",
            title="Bad",
            max_total_words=500,
            sections=[TemplateSection(heading="x")],
        )
        with pytest.raises(TemplateValidationError, match="max_total_words"):
            bad_template.validate()

    def test_too_many_sections(self):
        """sections 數量不能超過 5"""
        bad_template = SlideTemplate(
            name="bad",
            title="Bad",
            sections=[TemplateSection(heading=f"s{i}") for i in range(10)],
        )
        with pytest.raises(TemplateValidationError, match="sections"):
            bad_template.validate()


class TestTemplateLoader:
    """樣板載入器測試"""

    def test_load_builtin(self):
        """載入內建樣板"""
        loader = TemplateLoader()
        t = loader.load("basic_info")
        assert t.name == "basic_info"
        assert t.title == "FA 基本資訊"

    def test_load_unknown_raises(self):
        """找不到樣板應拋出 KeyError"""
        loader = TemplateLoader()
        with pytest.raises(KeyError, match="找不到樣板"):
            loader.load("nonexistent_template")

    def test_list_available(self):
        """列出可用樣板"""
        loader = TemplateLoader()
        names = loader.list_available()
        assert "basic_info" in names
        assert "root_cause_5why" in names
        assert "prevention_overview" in names

    def test_load_from_json(self, tmp_path):
        """從 JSON 檔案載入"""
        template_json = {
            "name": "custom_template",
            "title": "Custom Template",
            "layout_name": "2L - Topic",
            "sections": [
                {
                    "heading": "Section 1",
                    "visual": "checklist",
                    "max_bullets": 3,
                    "placeholder_items": ["item1", "item2", "item3"],
                }
            ],
        }
        path = tmp_path / "custom_template.json"
        path.write_text(json.dumps(template_json), encoding="utf-8")

        loader = TemplateLoader(custom_template_dir=tmp_path)
        t = loader.load("custom_template")
        assert t.name == "custom_template"
        assert t.title == "Custom Template"
        assert len(t.sections[0].placeholder_items) == 3

    def test_load_invalid_json_raises(self, tmp_path):
        """無效 JSON 應拋出 TemplateValidationError"""
        bad_path = tmp_path / "bad.json"
        bad_path.write_text("{invalid json", encoding="utf-8")

        loader = TemplateLoader(custom_template_dir=tmp_path)
        with pytest.raises(TemplateValidationError, match="JSON"):
            loader.load("bad")

    def test_load_json_with_validation_error(self, tmp_path):
        """違反約束的 JSON 應拋出 TemplateValidationError"""
        bad_json = {
            "name": "bad",
            "title": "Bad",
            "sections": [
                {
                    "heading": "x",
                    "max_bullets": 100,  # 違規
                }
            ],
        }
        path = tmp_path / "bad.json"
        path.write_text(json.dumps(bad_json), encoding="utf-8")

        loader = TemplateLoader(custom_template_dir=tmp_path)
        with pytest.raises(TemplateValidationError):
            loader.load("bad")


class TestTemplateInheritance:
    """樣板繼承測試"""

    def test_extends_builtin(self, tmp_path):
        """樣板可繼承內建樣板"""
        custom_json = {
            "extends": "basic_info",
            "name": "custom_basic_info",
            "title": "Custom Basic Info",
            "sections": [
                {
                    "heading": "Extended Section",
                    "visual": "checklist",
                    "max_bullets": 3,
                }
            ],
        }
        path = tmp_path / "extended.json"
        path.write_text(json.dumps(custom_json), encoding="utf-8")

        loader = TemplateLoader(custom_template_dir=tmp_path)
        t = loader.load("extended")
        assert t.title == "Custom Basic Info"
        assert len(t.sections) == 1
        assert t.sections[0].heading == "Extended Section"

    def test_custom_dir_overrides_builtin(self, tmp_path):
        """自訂目錄的同名樣板優先於內建"""
        custom_json = {
            "name": "basic_info",
            "title": "My Custom Basic Info",
            "layout_name": "Topic",
            "sections": [{"heading": "Custom Section"}],
        }
        path = tmp_path / "basic_info.json"
        path.write_text(json.dumps(custom_json), encoding="utf-8")

        loader = TemplateLoader(custom_template_dir=tmp_path)
        t = loader.load("basic_info")
        assert t.title == "My Custom Basic Info"

    def test_load_real_example_custom_template(self):
        """載入實際的範例自訂樣板"""
        from pathlib import Path

        examples_dir = Path(__file__).parent.parent.parent / "examples" / "custom_templates"
        if not examples_dir.exists():
            pytest.skip("範例自訂樣板不存在")

        loader = TemplateLoader(custom_template_dir=examples_dir)
        t = loader.load("prevention_overview_company")
        assert "ELAN" in t.title
        # 應有 4 個 placeholder items
        assert len(t.sections[0].placeholder_items) == 4
        assert "ELAN-QA-IQC-2026" in t.sections[0].placeholder_items[1]