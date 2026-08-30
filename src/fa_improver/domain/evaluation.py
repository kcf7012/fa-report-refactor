"""評估結果的資料模型"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Dimension(str, Enum):
    """6 個評估維度"""

    BASIC_INFO = "基本資訊完整性"
    PROBLEM_DEF = "問題描述與定義"
    METHOD = "分析方法與流程"
    EVIDENCE = "數據與證據支持"
    ROOT_CAUSE = "根因分析"
    PREVENTION = "改善對策"

    @property
    def weight(self) -> int:
        """權重百分比"""
        weights = {
            Dimension.BASIC_INFO: 15,
            Dimension.PROBLEM_DEF: 15,
            Dimension.METHOD: 20,
            Dimension.EVIDENCE: 20,
            Dimension.ROOT_CAUSE: 20,
            Dimension.PREVENTION: 10,
        }
        return weights[self]


class GapSeverity(int, Enum):
    """缺失嚴重度"""

    NONE = 0  # 完整,不需改善
    MINOR = 1  # 略不足,小幅補充
    MODERATE = 2  # 明顯缺失,新增投影片
    SEVERE = 3  # 嚴重缺失,展開為多張


class FailureType(str, Enum):
    """失效類型"""

    ESD_DAMAGE = "ESD 靜電損傷"
    EOS_DAMAGE = "EOS 過電壓"
    THERMAL = "熱失效"
    MECHANICAL = "機械應力"
    PROCESS_DEFECT = "製程缺陷"
    MATERIAL = "材料問題"
    DESIGN = "設計問題"
    UNKNOWN = "未確定"


class Maturity(str, Enum):
    """報告成熟度"""

    DRAFT = "draft"
    PRELIMINARY = "preliminary"
    FORMAL = "formal"
    FINAL = "final"


class Audience(str, Enum):
    """目標受眾"""

    INTERNAL_QA = "internal_qa"
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    REGULATORY = "regulatory"


@dataclass
class DimensionScore:
    """單一維度的評分"""

    name: Dimension
    score: float  # 0-100
    weight: int  # 百分比
    comment: str = ""

    @property
    def weighted_score(self) -> float:
        return self.score * self.weight / 100

    @property
    def gap_severity(self) -> GapSeverity:
        """根據分數判定缺失嚴重度"""
        if self.score >= 85:
            return GapSeverity.NONE
        if self.score >= 70:
            return GapSeverity.MINOR
        if self.score >= 50:
            return GapSeverity.MODERATE
        return GapSeverity.SEVERE


@dataclass
class EvaluationResult:
    """完整評估結果"""

    total_score: float
    grade: str  # A / B / C / D / F
    dimensions: List[DimensionScore] = field(default_factory=list)
    summary: str = ""
    strengths: List[str] = field(default_factory=list)

    # 元資料
    source_file: str = ""
    task_id: str = ""
    token_usage: dict = field(default_factory=dict)

    @property
    def dimension_dict(self) -> dict[Dimension, DimensionScore]:
        return {d.name: d for d in self.dimensions}

    def gap(self, dim: Dimension) -> GapSeverity:
        """取得指定維度的缺失嚴重度"""
        if dim not in self.dimension_dict:
            return GapSeverity.NONE
        return self.dimension_dict[dim].gap_severity


@dataclass
class ReportContext:
    """報告完整上下文,所有改善決策的基礎"""

    # 基本資訊
    failure_type: FailureType = FailureType.UNKNOWN
    maturity: Maturity = Maturity.PRELIMINARY
    audience: Audience = Audience.INTERNAL_QA

    # 缺失嚴重度(每個維度獨立評估)
    gaps: dict[Dimension, GapSeverity] = field(default_factory=dict)

    # 評估結果(可選)
    evaluation: Optional[EvaluationResult] = None

    def gap_for(self, dim: Dimension) -> GapSeverity:
        return self.gaps.get(dim, GapSeverity.NONE)