"""改善計畫協調器 — 統一編排多個 improver"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from pptx import Presentation

from ..domain.evaluation import Dimension, EvaluationResult, GapSeverity
from ..domain.suggestion import Improvement
from ..layout.protector import MasterProtector
from ..parsers.filename_parser import parse_filename
from ..templates.loader import TemplateLoader
from .analysis_method import add_analysis_method_slide
from .basic_info import add_basic_info_slide
from .evidence_checklist import add_evidence_checklist_slide
from .prevention import add_prevention_measures_slide
from .problem_definition import add_problem_definition_slide
from .root_cause import add_statistical_analysis_slide
from .summary import enhance_summary_section


class SlideAction(str, Enum):
    """可執行的改善動作"""

    ADD_BASIC_INFO = "add_basic_info"
    ADD_PROBLEM_DEFINITION = "add_problem_definition"
    ADD_ANALYSIS_METHOD = "add_analysis_method"
    ADD_EVIDENCE_CHECKLIST = "add_evidence_checklist"
    ADD_ROOT_CAUSE_5_WHY = "add_5_why"
    ADD_ROOT_CAUSE_CONTROL_GROUP = "add_control_group"
    ADD_ROOT_CAUSE_EVIDENCE = "add_evidence"
    ADD_ROOT_CAUSE_STATISTICAL = "add_statistical"
    ADD_PREVENTION_OVERVIEW = "add_prevention_overview"
    ADD_IQC_STANDARD = "add_iqc_standard"
    ADD_MONITORING_KM = "add_monitoring_km"
    ENHANCE_SUMMARY = "enhance_summary"


@dataclass
class ImprovementPlan:
    """改善計畫:列出所有要執行的動作"""

    actions: list[SlideAction] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def add(self, action: SlideAction, note: str = "") -> None:
        self.actions.append(action)
        if note:
            self.notes.append(note)


@dataclass
class ImprovementResult:
    """改善結果"""

    output_path: Path
    plan: ImprovementPlan
    original_slide_count: int
    final_slide_count: int
    master_preserved: bool
    summary: str = ""
    duration_seconds: float = 0.0


class ImprovementOrchestrator:
    """編排整個改善流程"""

    # 各維度觸發改善的閾值
    TRIGGER_THRESHOLDS = {
        Dimension.BASIC_INFO: 80,
        Dimension.PROBLEM_DEF: 70,
        Dimension.METHOD: 70,
        Dimension.EVIDENCE: 70,
        Dimension.ROOT_CAUSE: 80,
        Dimension.PREVENTION: 85,
    }

    def __init__(
        self,
        evaluation: EvaluationResult,
        input_path: Path,
        template_loader: TemplateLoader | None = None,
    ):
        """初始化 orchestrator

        Args:
            evaluation: 評估結果
            input_path: 輸入檔案路徑
            template_loader: 樣板載入器(可選,預設使用內建樣板)
        """
        self.evaluation = evaluation
        self.input_path = Path(input_path)
        self.filename_info = parse_filename(self.input_path)
        self.protector = None  # 在 execute 時建立
        self.template_loader = template_loader  # 可能為 None,improvers 會 fallback

    def build_plan(self) -> ImprovementPlan:
        """根據評估結果決定改善計畫"""
        plan = ImprovementPlan()

        # 基本資訊
        if self._needs_improvement(Dimension.BASIC_INFO):
            plan.add(
                SlideAction.ADD_BASIC_INFO,
                f"基本資訊分數 {self._score(Dimension.BASIC_INFO)} < 80",
            )

        # 問題描述與定義
        if self._needs_improvement(Dimension.PROBLEM_DEF):
            plan.add(
                SlideAction.ADD_PROBLEM_DEFINITION,
                f"問題描述分數 {self._score(Dimension.PROBLEM_DEF)} < 70",
            )

        # 分析方法與流程
        if self._needs_improvement(Dimension.METHOD):
            plan.add(
                SlideAction.ADD_ANALYSIS_METHOD,
                f"分析方法分數 {self._score(Dimension.METHOD)} < 70",
            )

        # 數據與證據支持
        if self._needs_improvement(Dimension.EVIDENCE):
            plan.add(
                SlideAction.ADD_EVIDENCE_CHECKLIST,
                f"數據證據分數 {self._score(Dimension.EVIDENCE)} < 70",
            )

        # 根因分析(嚴重度決定展開數量)
        gap = self.evaluation.gap(Dimension.ROOT_CAUSE)
        if gap == GapSeverity.SEVERE:
            plan.add(SlideAction.ADD_ROOT_CAUSE_5_WHY)
            plan.add(SlideAction.ADD_ROOT_CAUSE_CONTROL_GROUP)
            plan.add(SlideAction.ADD_ROOT_CAUSE_EVIDENCE)
            plan.add(SlideAction.ADD_ROOT_CAUSE_STATISTICAL)
        elif gap == GapSeverity.MODERATE:
            plan.add(SlideAction.ADD_ROOT_CAUSE_5_WHY)
            plan.add(SlideAction.ADD_ROOT_CAUSE_STATISTICAL)
        elif gap == GapSeverity.MINOR:
            plan.add(SlideAction.ADD_ROOT_CAUSE_STATISTICAL)

        # 改善對策
        if self._needs_improvement(Dimension.PREVENTION):
            plan.add(SlideAction.ADD_PREVENTION_OVERVIEW)
            plan.add(SlideAction.ADD_IQC_STANDARD)
            plan.add(SlideAction.ADD_MONITORING_KM)

        # Summary 強化(永遠執行)
        plan.add(SlideAction.ENHANCE_SUMMARY)

        return plan

    def execute(self, prs: Presentation, output_path: Path) -> ImprovementResult:
        """執行改善"""
        import time

        start_time = time.time()
        self.protector = MasterProtector(prs)
        original_count = len(prs.slides)

        plan = self.build_plan()
        suggestions = self._build_suggestions()

        for action in plan.actions:
            self._execute_action(prs, action, suggestions)

        # 驗證母片
        try:
            self.protector.verify_unchanged(prs)
            master_preserved = True
        except Exception:
            master_preserved = False
            raise

        # 儲存
        prs.save(output_path)

        return ImprovementResult(
            output_path=output_path,
            plan=plan,
            original_slide_count=original_count,
            final_slide_count=len(prs.slides),
            master_preserved=master_preserved,
            duration_seconds=time.time() - start_time,
        )

    def _execute_action(self, prs: Presentation, action: SlideAction, suggestions: dict) -> None:
        """執行單一改善動作

        所有 improver 都會傳入 self.template_loader,讓它們可以從樣板讀取標題與結構。
        """
        if action == SlideAction.ADD_BASIC_INFO:
            add_basic_info_slide(
                prs,
                evaluation=self.evaluation,
                filename_info=self.filename_info,
                template_loader=self.template_loader,
            )
        elif action == SlideAction.ADD_PROBLEM_DEFINITION:
            dim = self.evaluation.dimension_dict.get(Dimension.PROBLEM_DEF)
            add_problem_definition_slide(
                prs,
                self.evaluation,
                dim,
                template_loader=self.template_loader,
            )
        elif action == SlideAction.ADD_ANALYSIS_METHOD:
            dim = self.evaluation.dimension_dict.get(Dimension.METHOD)
            add_analysis_method_slide(
                prs,
                self.evaluation,
                dim,
                template_loader=self.template_loader,
            )
        elif action == SlideAction.ADD_EVIDENCE_CHECKLIST:
            dim = self.evaluation.dimension_dict.get(Dimension.EVIDENCE)
            add_evidence_checklist_slide(
                prs,
                self.evaluation,
                dim,
                template_loader=self.template_loader,
            )
        elif action == SlideAction.ADD_ROOT_CAUSE_5_WHY:
            add_statistical_analysis_slide(
                prs,
                evaluation=self.evaluation,
                suggestions=suggestions.get("根因分析", []),
                variant="5_why",
                template_loader=self.template_loader,
            )
        elif action == SlideAction.ADD_ROOT_CAUSE_STATISTICAL:
            add_statistical_analysis_slide(
                prs,
                evaluation=self.evaluation,
                suggestions=suggestions.get("根因分析", []),
                variant="statistical",
                template_loader=self.template_loader,
            )
        elif action == SlideAction.ADD_PREVENTION_OVERVIEW:
            add_prevention_measures_slide(
                prs,
                evaluation=self.evaluation,
                improvements=self.evaluation_improvements(),
                template_loader=self.template_loader,
            )
        elif action == SlideAction.ENHANCE_SUMMARY:
            enhance_summary_section(
                prs,
                evaluation=self.evaluation,
                improvements=self.evaluation_improvements(),
                template_loader=self.template_loader,
            )

    def _needs_improvement(self, dim: Dimension) -> bool:
        score = self._score(dim)
        threshold = self.TRIGGER_THRESHOLDS.get(dim, 80)
        return score < threshold

    def _score(self, dim: Dimension) -> float:
        if dim not in self.evaluation.dimension_dict:
            return 100.0
        return self.evaluation.dimension_dict[dim].score

    def _build_suggestions(self) -> dict[str, list[str]]:
        """從改進建議中提取各維度的建議"""
        suggestions: dict[str, list[str]] = {
            "基本資訊完整性": [],
            "根因分析": [],
            "改善對策": [],
        }
        for imp in self.evaluation_improvements():
            item_lower = imp.item.lower()
            if "基本資訊" in item_lower or "批號" in item_lower:
                suggestions["基本資訊完整性"].append(imp.suggestion)
            elif "根因" in item_lower or "5-why" in item_lower or "分析" in item_lower:
                suggestions["根因分析"].append(imp.suggestion)
            elif "對策" in item_lower or "預防" in item_lower:
                suggestions["改善對策"].append(imp.suggestion)
        return suggestions

    def evaluation_improvements(self) -> list[Improvement]:
        """從 token_usage 結構無法直接取得,需要從 eval_data
        這裡由外部傳入 evaluation 時一併帶入"""
        # 簡化:從 dimension_score.comment 抽取
        improvements: list[Improvement] = []
        for dim_score in self.evaluation.dimensions:
            if dim_score.comment and len(dim_score.comment) > 10:
                from ..domain.suggestion import Priority

                improvements.append(
                    Improvement(
                        priority=(
                            Priority.HIGH if dim_score.gap_severity.value >= 2 else Priority.MEDIUM
                        ),
                        item=dim_score.name.value,
                        suggestion=dim_score.comment,
                    )
                )
        return improvements
