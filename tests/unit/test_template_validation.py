"""樣板驗證測試(SlideTemplate.validate() & TemplateSection.validate())

涵蓋所有驗證失敗情境與邊界條件,確保「一張投影片一個主題」原則被嚴格執行。
"""

from __future__ import annotations

import pytest
from fa_improver.domain.template import (
    BUILTIN_TEMPLATES,
    SlideTemplate,
    TemplateSection,
    TemplateValidationError,
    VisualElement,
)


class TestTemplateSectionValidation:
    """TemplateSection.validate() 測試"""

    def test_valid_section(self):
        """合法 section 應通過驗證"""
        section = TemplateSection(
            heading="OK Section",
            max_bullets=4,
            max_words_per_bullet=30,
        )
        section.validate()  # 不應拋出

    def test_max_bullets_too_many_raises(self):
        """max_bullets > 5 且無 placeholder_items 應拋出"""
        section = TemplateSection(
            heading="too many bullets",
            max_bullets=10,
            placeholder_items=[],
        )
        with pytest.raises(TemplateValidationError, match="max_bullets"):
            section.validate()

    def test_max_bullets_5_is_allowed(self):
        """max_bullets = 5(邊界)應通過"""
        section = TemplateSection(heading="borderline", max_bullets=5)
        section.validate()

    def test_max_bullets_6_with_placeholder_allowed(self):
        """max_bullets > 5 但有 placeholder_items(資料表)應通過"""
        section = TemplateSection(
            heading="data table",
            max_bullets=7,
            placeholder_items=["item1", "item2", "item3", "item4", "item5", "item6", "item7"],
        )
        section.validate()

    def test_max_bullets_4_with_placeholder_allowed(self):
        """max_bullets <= 5 + placeholder_items 應通過"""
        section = TemplateSection(
            heading="any",
            max_bullets=4,
            placeholder_items=["a", "b", "c"],
        )
        section.validate()

    def test_placeholder_items_too_many_raises(self):
        """placeholder_items > 10 應拋出"""
        section = TemplateSection(
            heading="too many items",
            placeholder_items=[f"item{i}" for i in range(11)],
        )
        with pytest.raises(TemplateValidationError, match="placeholder_items"):
            section.validate()

    def test_placeholder_items_10_allowed(self):
        """placeholder_items = 10(邊界)應通過"""
        section = TemplateSection(
            heading="exact 10",
            placeholder_items=[f"item{i}" for i in range(10)],
        )
        section.validate()

    def test_placeholder_items_0_allowed(self):
        """placeholder_items = [] 應通過"""
        section = TemplateSection(heading="empty placeholders", placeholder_items=[])
        section.validate()

    def test_max_words_per_bullet_too_long_raises(self):
        """max_words_per_bullet > 50 應拋出(預設視覺元素)"""
        section = TemplateSection(
            heading="too long bullet",
            max_words_per_bullet=51,
        )
        with pytest.raises(TemplateValidationError, match="max_words_per_bullet"):
            section.validate()

    def test_max_words_per_bullet_summary_card_allowed(self):
        """summary_card 視覺元素允許 max_words_per_bullet = 100"""
        section = TemplateSection(
            heading="summary card",
            visual=VisualElement.SUMMARY_CARD,
            max_words_per_bullet=100,
        )
        section.validate()

    def test_max_words_per_bullet_summary_card_too_long_raises(self):
        """summary_card 視覺元素 > 100 仍應拋出"""
        section = TemplateSection(
            heading="too long summary",
            visual=VisualElement.SUMMARY_CARD,
            max_words_per_bullet=101,
        )
        with pytest.raises(TemplateValidationError, match="max_words_per_bullet"):
            section.validate()

    def test_max_words_per_bullet_50_allowed(self):
        """max_words_per_bullet = 50(邊界)應通過"""
        section = TemplateSection(heading="borderline", max_words_per_bullet=50)
        section.validate()


class TestSlideTemplateValidation:
    """SlideTemplate.validate() 測試"""

    def test_valid_template(self):
        """合法 template 應通過"""
        template = SlideTemplate(
            name="valid",
            title="Valid Template",
            sections=[TemplateSection(heading="section 1")],
        )
        template.validate()

    def test_no_sections_raises(self):
        """零 section 應拋出"""
        template = SlideTemplate(name="empty", title="Empty", sections=[])
        with pytest.raises(TemplateValidationError, match="沒有任何 sections"):
            template.validate()

    def test_too_many_sections_raises(self):
        """sections > 5 應拋出"""
        template = SlideTemplate(
            name="too many",
            title="Too Many",
            sections=[TemplateSection(heading=f"section {i}") for i in range(6)],
        )
        with pytest.raises(TemplateValidationError, match="超過 5"):
            template.validate()

    def test_sections_5_allowed(self):
        """sections = 5(邊界)應通過"""
        template = SlideTemplate(
            name="exact 5",
            title="Five Sections",
            sections=[TemplateSection(heading=f"s{i}") for i in range(5)],
        )
        template.validate()

    def test_max_total_words_too_high_raises(self):
        """max_total_words > 300 應拋出"""
        template = SlideTemplate(
            name="too long",
            title="Too Long",
            max_total_words=301,
            sections=[TemplateSection(heading="x")],
        )
        with pytest.raises(TemplateValidationError, match="max_total_words"):
            template.validate()

    def test_max_total_words_300_allowed(self):
        """max_total_words = 300(邊界)應通過"""
        template = SlideTemplate(
            name="exact 300",
            title="Exact",
            max_total_words=300,
            sections=[TemplateSection(heading="x")],
        )
        template.validate()

    def test_max_total_words_default_200_allowed(self):
        """max_total_words = 200(預設)應通過"""
        template = SlideTemplate(
            name="default",
            title="Default",
            sections=[TemplateSection(heading="x")],
        )
        assert template.max_total_words == 200
        template.validate()

    def test_section_validation_called(self):
        """template.validate() 應呼叫 section.validate()"""
        # 建立一個 section 違反 max_words_per_bullet
        bad_section = TemplateSection(heading="bad", max_words_per_bullet=100)
        template = SlideTemplate(
            name="has bad section",
            title="Has Bad Section",
            sections=[bad_section],
        )
        with pytest.raises(TemplateValidationError, match="max_words_per_bullet"):
            template.validate()


class TestBuiltinTemplatesValidation:
    """內建樣板都應通過驗證"""

    def test_all_builtin_templates_pass_validation(self):
        """所有內建樣板應通過 validate()"""
        for name, template in BUILTIN_TEMPLATES.items():
            try:
                template.validate()
            except TemplateValidationError as e:
                pytest.fail(f"內建樣板 '{name}' 驗證失敗:{e}")

    def test_basic_info_with_7_items_passes(self):
        """basic_info 有 7 個 placeholder items 應通過(資料表)"""
        template = BUILTIN_TEMPLATES["basic_info"]
        template.validate()
        assert len(template.sections[0].placeholder_items) == 7

    def test_executive_summary_has_summary_card(self):
        """executive_summary 應有 SUMMARY_CARD 視覺元素 section"""
        template = BUILTIN_TEMPLATES["executive_summary"]
        template.validate()
        assert any(s.visual == VisualElement.SUMMARY_CARD for s in template.sections)


class TestTemplateInheritance:
    """樣板繼承後仍應通過驗證"""

    def test_extended_template_validates(self):
        """繼承的樣板應通過驗證"""
        from copy import deepcopy

        base = BUILTIN_TEMPLATES["basic_info"]
        extended = deepcopy(base)
        # 加上更多 section 但仍 < 5
        extended.sections.append(TemplateSection(heading="extra section"))
        extended.validate()
        assert len(extended.sections) == 3

    def test_extended_too_many_sections_raises(self):
        """繼承後 sections > 5 應拋出"""
        from copy import deepcopy

        base = BUILTIN_TEMPLATES["basic_info"]
        extended = deepcopy(base)
        # 加到 6 個
        for i in range(5):
            extended.sections.append(TemplateSection(heading=f"extra {i}"))
        with pytest.raises(TemplateValidationError, match="超過 5"):
            extended.validate()


class TestTemplateValidationError:
    """TemplateValidationError 測試"""

    def test_error_has_message(self):
        """錯誤應包含訊息"""
        try:
            section = TemplateSection(heading="x", max_bullets=100)
            section.validate()
        except TemplateValidationError as e:
            assert "x" in str(e)  # 應包含 section heading
            assert "max_bullets" in str(e)

    def test_error_is_exception(self):
        """TemplateValidationError 應是 Exception 子類別"""
        assert issubclass(TemplateValidationError, Exception)
