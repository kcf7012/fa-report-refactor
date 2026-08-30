"""視覺元素生成器

把純文字 bullets 轉為豐富的視覺元素:
- ChecklistGenerator(checkbox 列表)
- FlowDiagramGenerator(流程圖)
- ComparisonTableGenerator(對照表)
- ProgressBarGenerator(進度條)
- TimelineGenerator(時間軸)

設計原則:
- 母片絕對不修改
- 視覺元素以 PowerPoint 內建 shape 實作(相容性最佳)
- 所有生成器接受統一介面
"""

from .base import (
    ChecklistGenerator,
    ComparisonTableGenerator,
    FlowDiagramGenerator,
    ProgressBarGenerator,
    TimelineGenerator,
    VisualGenerator,
)
from .colors import (
    ELAN_BLUE,
    ELAN_GRAY,
    ELAN_GREEN,
    ELAN_LIGHT_BLUE,
    ELAN_LIGHT_GRAY,
    ELAN_ORANGE,
    ELAN_RED,
)

__all__ = [
    "VisualGenerator",
    "ChecklistGenerator",
    "FlowDiagramGenerator",
    "ComparisonTableGenerator",
    "ProgressBarGenerator",
    "TimelineGenerator",
    "ELAN_BLUE",
    "ELAN_LIGHT_BLUE",
    "ELAN_RED",
    "ELAN_GREEN",
    "ELAN_ORANGE",
    "ELAN_GRAY",
    "ELAN_LIGHT_GRAY",
]
