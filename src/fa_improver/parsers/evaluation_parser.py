"""評估結果解析器(支援 JSON 與 TXT)"""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..domain.evaluation import Dimension, DimensionScore, EvaluationResult
from ..domain.suggestion import Improvement, Priority


class EvaluationParser:
    """解析各種格式的評估結果"""

    def parse(self, file_path: str | Path) -> EvaluationResult:
        """自動偵測格式並解析"""
        path = Path(file_path)
        content = path.read_text(encoding="utf-8")

        if path.suffix.lower() == ".json":
            return self.parse_json(content)
        if path.suffix.lower() == ".txt":
            return self.parse_txt(content)

        raise ValueError(f"不支援的檔案格式: {path.suffix}")

    def parse_json(self, content: str) -> EvaluationResult:
        """解析 JSON 格式"""
        data = json.loads(content)

        # 處理陣列格式
        if isinstance(data, list):
            if not data:
                raise ValueError("JSON 陣列為空")
            data = data[0]

        # 正規化 dimension_scores → dimensions
        if "dimension_scores" in data and "dimensions" not in data:
            data["dimensions"] = data["dimension_scores"]

        return self._from_dict(data)

    def parse_txt(self, content: str) -> EvaluationResult:
        """解析 TXT 格式(來自 fa_report_analyzer_v3 的輸出)"""
        # 解析總分
        score_match = re.search(r"總分[:\s]*(\d+(?:\.\d+)?)", content)
        total_score = float(score_match.group(1)) if score_match else 0.0

        grade_match = re.search(r"等級[:\s]*([A-F])", content)
        grade = grade_match.group(1) if grade_match else "F"

        # 解析各維度
        dimensions = self._parse_dimensions_from_txt(content)

        # 解析優點
        strengths = self._parse_section_bullets(content, r"報告優點")

        # 解析改進建議
        self._parse_improvements_from_txt(content)

        return EvaluationResult(
            total_score=total_score,
            grade=grade,
            dimensions=dimensions,
            strengths=strengths,
        )

    def _from_dict(self, data: dict) -> EvaluationResult:
        """從 dict 建立 EvaluationResult"""
        dimensions: list[DimensionScore] = []

        # 解析維度分數
        dims_data = data.get("dimensions", data.get("dimension_scores", {}))
        for name, dim_data in dims_data.items():
            if isinstance(dim_data, dict):
                dim = self._match_dimension(name)
                dimensions.append(
                    DimensionScore(
                        name=dim,
                        score=float(dim_data.get("score", 0)),
                        weight=int(dim_data.get("weight", dim.weight)),
                        comment=dim_data.get("comment", ""),
                    )
                )
            elif isinstance(dim_data, (int, float)):
                dim = self._match_dimension(name)
                dimensions.append(
                    DimensionScore(
                        name=dim,
                        score=float(dim_data),
                        weight=dim.weight,
                    )
                )

        # 解析改進建議
        data.get("improvements", [])

        return EvaluationResult(
            total_score=float(data.get("total_score", 0)),
            grade=data.get("grade", "F"),
            dimensions=dimensions,
            summary=data.get("summary", ""),
            strengths=data.get("strengths", []),
            source_file=data.get("source_file", ""),
            task_id=data.get("task_id", ""),
            token_usage=data.get("token_usage", {}),
        )

    def _parse_dimensions_from_txt(self, content: str) -> list[DimensionScore]:
        """從 TXT 解析維度分數"""
        dimensions = []
        # 格式範例:
        # 【基本資訊完整性】
        #   得分: 85.0 / 100  (85.0%)
        #   權重: 15%
        #   加權分數: 12.75
        #   評語: ...

        pattern = re.compile(
            r"【(.+?)】\s*\n" r"\s*得分:\s*(\d+(?:\.\d+)?)\s*/\s*100" r".*?\n" r"\s*權重:\s*(\d+)%",
            re.MULTILINE,
        )

        for match in pattern.finditer(content):
            name = match.group(1).strip()
            score = float(match.group(2))
            weight = int(match.group(3))

            # 抓評語(到下一個【之前)
            after = content[match.end() :]
            comment_match = re.search(r"評語:\s*(.+?)(?=\n\s*【|\Z)", after, re.DOTALL)
            comment = comment_match.group(1).strip() if comment_match else ""

            dim = self._match_dimension(name)
            dimensions.append(
                DimensionScore(
                    name=dim,
                    score=score,
                    weight=weight,
                    comment=comment,
                )
            )

        return dimensions

    def _parse_section_bullets(self, content: str, section_name: str) -> list[str]:
        """從 TXT 解析條列式內容"""
        # 找 section 開始位置
        start_match = re.search(rf"{re.escape(section_name)}", content)
        if not start_match:
            return []

        # 找下一個 section
        start = start_match.end()
        end_match = re.search(r"\n-{3,}", content[start:])
        end = start + end_match.start() if end_match else len(content)

        section = content[start:end]

        # 抓 numbered bullets(1. xxx 或 - xxx)
        bullets = []
        for match in re.finditer(r"(?:^|\n)\s*(?:\d+\.|[-*])\s*(.+)", section):
            text = match.group(1).strip()
            if text and len(text) > 5:
                bullets.append(text)

        return bullets

    def _parse_improvements_from_txt(self, content: str) -> list[Improvement]:
        """從 TXT 解析改進建議"""
        # 格式範例:
        # 1. [高] 根因分析深度不足: 目前僅止於...
        items = []
        section = self._find_section(content, r"改進建議")
        if not section:
            return items

        for match in re.finditer(
            r"\d+\.\s*\[(高|中|低)\]\s*([^:]+):\s*(.+)",
            section,
        ):
            priority = Priority(match.group(1))
            item = match.group(2).strip()
            suggestion = match.group(3).strip()
            items.append(
                Improvement(
                    priority=priority,
                    item=item,
                    suggestion=suggestion,
                )
            )
        return items

    def _find_section(self, content: str, section_name: str) -> str | None:
        """找 section 的內容"""
        start_match = re.search(rf"{re.escape(section_name)}", content)
        if not start_match:
            return None
        start = start_match.end()
        end_match = re.search(r"\n-{3,}", content[start:])
        end = start + end_match.start() if end_match else len(content)
        return content[start:end]

    def _match_dimension(self, name: str) -> Dimension:
        """從名稱字串匹配 Dimension enum"""
        for dim in Dimension:
            if dim.value == name or name in dim.value:
                return dim
        # fallback: 嘗試模糊匹配
        name_lower = name.lower()
        for dim in Dimension:
            if any(kw in name_lower for kw in dim.value.lower().split()):
                return dim
        raise ValueError(f"無法識別維度: {name}")


# 便利函式
def parse_evaluation(file_path: str | Path) -> EvaluationResult:
    """解析評估檔(JSON 或 TXT)"""
    return EvaluationParser().parse(file_path)
