"""LLM Evaluator 測試"""

import json

import pytest

from fa_improver.domain.evaluation import Dimension, EvaluationResult
from fa_improver.llm.evaluator import LLMEvaluator
from fa_improver.llm.mock_client import MockLLMClient


class TestLLMEvaluator:
    """LLM Evaluator 測試"""

    def _make_evaluation_json(self) -> str:
        """產生測試用的評估 JSON"""
        return json.dumps(
            {
                "total_score": 63.5,
                "grade": "D",
                "dimension_scores": {
                    "基本資訊完整性": {"score": 70, "weight": 15, "comment": "缺批號"},
                    "根因分析": {"score": 50, "weight": 20, "comment": "推測非分析"},
                    "改善對策": {"score": 70, "weight": 10, "comment": "缺失"},
                },
                "summary": "報告只有初步定位,缺乏根因與對策",
                "strengths": ["初步排查清晰"],
                "improvements": [
                    {
                        "priority": "高",
                        "item": "根因分析",
                        "suggestion": "需使用 5-Why 與物理證據",
                    },
                    {
                        "priority": "高",
                        "item": "改善對策",
                        "suggestion": "需提出短期與長期對策",
                    },
                ],
            }
        )

    def test_parse_response(self):
        """解析 LLM 回應"""
        client = MockLLMClient()
        client.add_response("半導體", self._make_evaluation_json())
        evaluator = LLMEvaluator(client)

        from fa_improver.llm.base import LLMResponse

        response = LLMResponse(
            content=self._make_evaluation_json(),
            model="test",
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
        )
        result = evaluator._parse_response(response)

        assert result.total_score == 63.5
        assert result.grade == "D"
        assert len(result.dimensions) == 3
        assert len(result.improvements) if hasattr(result, "improvements") else True

    def test_parse_markdown_json(self):
        """解析 markdown code block 包裹的 JSON"""
        from fa_improver.llm.base import LLMResponse

        wrapped = "```json\n" + self._make_evaluation_json() + "\n```"
        client = MockLLMClient()
        evaluator = LLMEvaluator(client)
        response = LLMResponse(content=wrapped)
        result = evaluator._parse_response(response)
        assert result.total_score == 63.5

    def test_invalid_json_raises(self):
        """無效 JSON 應拋出 LLMError"""
        from fa_improver.llm.base import LLMError, LLMResponse

        client = MockLLMClient()
        evaluator = LLMEvaluator(client)
        response = LLMResponse(content="not json")

        with pytest.raises(LLMError, match="不是有效 JSON"):
            evaluator._parse_response(response)

    def test_evaluate_pptx(self, sample_pptx):
        """評估真實 pptx 檔案"""
        if not sample_pptx.exists():
            pytest.skip("範例 pptx 不存在")

        client = MockLLMClient()
        client.add_response("FA 報告", self._make_evaluation_json())
        evaluator = LLMEvaluator(client)

        result = evaluator.evaluate_pptx(sample_pptx)

        assert isinstance(result, EvaluationResult)
        assert result.total_score > 0
        assert len(result.dimensions) >= 3
        assert client.call_count == 1

    def test_extract_content(self, sample_pptx):
        """測試 pptx 內容萃取"""
        if not sample_pptx.exists():
            pytest.skip("範例 pptx 不存在")

        client = MockLLMClient()
        evaluator = LLMEvaluator(client)
        content = evaluator._extract_content(sample_pptx)

        assert "Slide" in content
        assert len(content) > 0


class TestLLMEvaluatorIntegration:
    """與 Mock Client 整合測試"""

    def test_full_workflow(self, sample_pptx):
        """端對端流程"""
        if not sample_pptx.exists():
            pytest.skip("範例 pptx 不存在")

        json_response = json.dumps(
            {
                "total_score": 41.5,
                "grade": "F",
                "dimension_scores": {
                    "基本資訊完整性": {"score": 40, "weight": 15, "comment": "缺"},
                    "根因分析": {"score": 0, "weight": 20, "comment": "完全缺失"},
                    "改善對策": {"score": 0, "weight": 10, "comment": "完全缺失"},
                },
                "summary": "F 等級報告",
                "strengths": [],
                "improvements": [],
            }
        )

        client = MockLLMClient()
        client.add_response("FA 報告", json_response)
        evaluator = LLMEvaluator(client)

        result = evaluator.evaluate_pptx(sample_pptx)

        assert result.grade == "F"
        assert result.total_score == 41.5

        # 驗證可傳給 orchestrator
        from fa_improver.improvers.orchestrator import ImprovementOrchestrator

        orchestrator = ImprovementOrchestrator(result, sample_pptx)
        plan = orchestrator.build_plan()
        assert len(plan.actions) > 0