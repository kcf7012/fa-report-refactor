"""Domain models - 純資料結構,不含業務邏輯"""

from .evaluation import (
    Dimension,
    DimensionScore,
    EvaluationResult,
    FailureType,
    GapSeverity,
    ReportContext,
)
from .suggestion import (
    ActionItem,
    Improvement,
    Priority,
    Suggestion,
)
from .template import (
    BUILTIN_TEMPLATES,
    BASIC_INFO_TEMPLATE,
    ColorTheme,
    EXECUTIVE_SUMMARY_TEMPLATE,
    PREVENTION_OVERVIEW_TEMPLATE,
    ROOT_CAUSE_5_WHY_TEMPLATE,
    ROOT_CAUSE_STATISTICAL_TEMPLATE,
    SlideTemplate,
    TemplateSection,
    TemplateValidationError,
    VisualElement,
)

__all__ = [
    "Dimension",
    "DimensionScore",
    "EvaluationResult",
    "FailureType",
    "GapSeverity",
    "ReportContext",
    "ActionItem",
    "Improvement",
    "Priority",
    "Suggestion",
    # Template
    "SlideTemplate",
    "TemplateSection",
    "TemplateValidationError",
    "VisualElement",
    "ColorTheme",
    "BUILTIN_TEMPLATES",
    "BASIC_INFO_TEMPLATE",
    "ROOT_CAUSE_5_WHY_TEMPLATE",
    "ROOT_CAUSE_STATISTICAL_TEMPLATE",
    "PREVENTION_OVERVIEW_TEMPLATE",
    "EXECUTIVE_SUMMARY_TEMPLATE",
]