"""評估解析器測試"""

import pytest

from fa_improver.parsers.evaluation_parser import EvaluationParser
from fa_improver.domain.evaluation import Dimension, GapSeverity


class TestJsonParser:
    """JSON 格式解析測試"""

    def test_parse_simple_json(self):
        """測試基本 JSON 解析"""
        json_content = """
        {
            "total_score": 63.5,
            "grade": "D",
            "dimensions": {
                "基本資訊完整性": {"score": 70, "weight": 15, "comment": "缺批號"},
                "根因分析": {"score": 50, "weight": 20, "comment": "推測非分析"},
                "改善對策": {"score": 70, "weight": 10, "comment": "缺失"}
            },
            "summary": "測試摘要",
            "strengths": ["優點1", "優點2"]
        }
        """
        parser = EvaluationParser()
        result = parser.parse_json(json_content)

        assert result.total_score == 63.5
        assert result.grade == "D"
        assert len(result.dimensions) == 3
        assert result.summary == "測試摘要"
        assert len(result.strengths) == 2

    def test_parse_array_format(self):
        """測試陣列格式"""
        json_content = """
        [{
            "total_score": 55.5,
            "grade": "F",
            "dimensions": {
                "根因分析": {"score": 40, "weight": 20}
            }
        }]
        """
        parser = EvaluationParser()
        result = parser.parse_json(json_content)

        assert result.total_score == 55.5
        assert result.grade == "F"

    def test_parse_nested_dimension_scores(self):
        """測試 dimension_scores 巢狀格式"""
        json_content = """
        {
            "total_score": 41.5,
            "grade": "F",
            "dimension_scores": {
                "基本資訊完整性": {"score": 40, "weight": 15},
                "根因分析": {"score": 0, "weight": 20}
            }
        }
        """
        parser = EvaluationParser()
        result = parser.parse_json(json_content)

        assert result.total_score == 41.5
        assert len(result.dimensions) == 2


class TestTxtParser:
    """TXT 格式解析測試"""

    def test_parse_real_txt(self, sample_eval_txt):
        """測試真實 TXT 解析"""
        if not sample_eval_txt.exists():
            pytest.skip("TXT 樣本不存在")

        parser = EvaluationParser()
        result = parser.parse_txt(sample_eval_txt.read_text(encoding="utf-8"))

        assert result.total_score > 0
        assert result.grade in "ABCDF"
        assert len(result.dimensions) >= 5

    def test_gap_severity_calculation(self):
        """測試缺失嚴重度計算"""
        from fa_improver.domain.evaluation import DimensionScore

        assert DimensionScore(
            name=Dimension.BASIC_INFO, score=90, weight=15
        ).gap_severity == GapSeverity.NONE
        assert DimensionScore(
            name=Dimension.BASIC_INFO, score=75, weight=15
        ).gap_severity == GapSeverity.MINOR
        assert DimensionScore(
            name=Dimension.BASIC_INFO, score=60, weight=15
        ).gap_severity == GapSeverity.MODERATE
        assert DimensionScore(
            name=Dimension.BASIC_INFO, score=40, weight=15
        ).gap_severity == GapSeverity.SEVERE


class TestAutoDetection:
    """自動格式偵測測試"""

    def test_parse_json_file(self, sample_eval_json, tmp_path):
        """測試從 JSON 檔案自動解析"""
        if not sample_eval_json.exists():
            pytest.skip("JSON 樣本不存在")

        parser = EvaluationParser()
        result = parser.parse(sample_eval_json)

        assert result.total_score > 0

    def test_parse_txt_file(self, sample_eval_txt):
        """測試從 TXT 檔案自動解析"""
        if not sample_eval_txt.exists():
            pytest.skip("TXT 樣本不存在")

        parser = EvaluationParser()
        result = parser.parse(sample_eval_txt)

        assert result.total_score > 0
        assert len(result.dimensions) >= 5

    def test_unsupported_format(self, tmp_path):
        """測試不支援的格式"""
        bad_file = tmp_path / "test.xyz"
        bad_file.write_text("dummy")

        parser = EvaluationParser()
        with pytest.raises(ValueError, match="不支援"):
            parser.parse(bad_file)