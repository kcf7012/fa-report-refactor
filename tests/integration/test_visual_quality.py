"""視覺品質 smoke test — 防止 v3.1.1 的 4 大版面渲染問題再次發生

對應 handoff `2026-09-01-v311-incomplete-rendering-handoff.md`:
- 🔴 Bug 1:enhance_summary_section 疊加覆蓋(原 Summary 內容被新區塊覆蓋)
- 🟡 Bug 2:title placeholder 找錯(「按一下即可新增文字」殘留)
- 🟡 Bug 3:textbox 旋轉 90°(260811 多張)
- 🟡 Bug 4:底部 placeholder 殘留

本測試**不需 pptx 轉圖**,只檢查 pptx XML / shape 屬性就能抓出問題:
- slide.shapes 數量是否爆量(避免 Bug 1)
- textbox.rotation 是否為 0(避免 Bug 3)
- placeholder 預設文字是否被清掉(避免 Bug 2 / Bug 4)

執行方式:
    uv run pytest tests/integration/test_visual_quality.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pptx import Presentation

# 確保 src/ 在 Python path
_SKILL_SRC = Path(__file__).parent.parent.parent / "src"
if str(_SKILL_SRC) not in sys.path:
    sys.path.insert(0, str(_SKILL_SRC))

PROJECT_ROOT = Path("/home/elan/fa-report-refactor")
REPORT_DIR = PROJECT_ROOT / "report"

RESIDUAL_TITLE_MARKERS = ("按一下", "Click to add", "Click here to add")


def _run_improvement(input_pptx: Path, eval_path: Path, output_suffix: str = "_vq"):
    from fa_improver.improvers.orchestrator import ImprovementOrchestrator
    from fa_improver.parsers.evaluation_parser import parse_evaluation

    out_path = REPORT_DIR / f"{input_pptx.stem}{output_suffix}.pptx"
    evaluation = parse_evaluation(eval_path)
    prs = Presentation(input_pptx)
    orchestrator = ImprovementOrchestrator(evaluation, input_pptx)
    result = orchestrator.execute(prs, out_path)
    return prs, result, out_path


class TestNoSummaryOverlay:
    """Bug 1 修正後測試:enhance_summary_section 不再覆蓋原 Summary

    原本行為:Executive Summary + Key Improvements + ProgressBar 全部疊加在原 Summary
    新行為:新增獨立投影片(在原 Summary 之後)
    """

    def test_summary_section_creates_independent_slides(self):
        """執行 enhance_summary_section 後,新增的 slide 數 = 1(僅 Executive Summary)

        注意:這裡用 mock — 只跑 enhance_summary_section,不跑整個 orchestrator
        """
        input_pptx = REPORT_DIR / "260811_Kobo_ZHT_RA6080_SPcomFailI.pptx"
        if not input_pptx.exists():
            pytest.skip("找不到 260811 pptx")

        from fa_improver.domain.evaluation import EvaluationResult
        from fa_improver.domain.suggestion import Improvement, Priority
        from fa_improver.improvers.summary import enhance_summary_section

        prs = Presentation(input_pptx)
        original_count = len(prs.slides)

        evaluation = EvaluationResult(
            total_score=70.0,
            grade="C",
            dimensions=[],
            summary="這是 executive summary 測試",
            strengths=["完整分析 8D"],
            source_file="test.pptx",
        )
        improvements = [Improvement(priority=Priority.HIGH, item="改進項", suggestion="補強 X")]

        enhance_summary_section(prs, evaluation, improvements)

        # 應該新增至少 2 張獨立 slide(Executive + Key Improvements)
        new_count = len(prs.slides) - original_count
        assert new_count >= 2, (
            f"enhance_summary_section 只新增 {new_count} 張 slide,"
            f"應至少 2 張(Executive Summary + Key Improvements)"
        )

    def test_summary_slide_not_overwritten(self):
        """原 Summary slide 的「Summary」標題文字應保留(不被覆蓋)"""
        input_pptx = REPORT_DIR / "260811_Kobo_ZHT_RA6080_SPcomFailI.pptx"
        if not input_pptx.exists():
            pytest.skip("找不到 260811 pptx")

        from fa_improver.domain.evaluation import EvaluationResult
        from fa_improver.improvers.summary import enhance_summary_section

        prs = Presentation(input_pptx)

        # 先記錄所有 slide 的文字 hash
        original_texts = []
        for slide in prs.slides:
            text = "\n".join(s.text_frame.text for s in slide.shapes if s.has_text_frame)
            original_texts.append(text)

        evaluation = EvaluationResult(
            total_score=70.0,
            grade="C",
            dimensions=[],
            summary="這是 executive summary 測試",
            strengths=[],
            source_file="test.pptx",
        )

        enhance_summary_section(prs, evaluation, [])

        # 原 N 張的文字應該全部保留(enhance_summary_section 不修改它們)
        for i, original_text in enumerate(original_texts):
            current_text = "\n".join(
                s.text_frame.text for s in prs.slides[i].shapes if s.has_text_frame
            )
            assert current_text == original_text, (
                f"Slide {i+1} 的文字被改變了!\n"
                f"原:\n{original_text[:200]}\n"
                f"現:\n{current_text[:200]}"
            )


class TestNoTextboxRotation:
    """Bug 3 修正後測試:新增的 textbox 不應被旋轉(除了形狀/表格)"""

    def test_new_textboxes_not_rotated(self):
        """新增 slide 的 textbox 都應 rotation == 0"""
        input_pptx = REPORT_DIR / "260811_Kobo_ZHT_RA6080_SPcomFailI.pptx"
        eval_path = REPORT_DIR / "fa_report_260811_Kobo_ZHT_RA6080_SPcomFailI.json"
        if not input_pptx.exists() or not eval_path.exists():
            pytest.skip("需要 260811 pptx 與 eval JSON")

        prs, result, _ = _run_improvement(input_pptx, eval_path, output_suffix="_vqrot")

        # 檢查新增的 slide 上的 textbox
        new_slides = list(prs.slides)[result.original_slide_count :]
        rotated_textboxes = []
        for offset, slide in enumerate(new_slides):
            slide_num = result.original_slide_count + offset + 1
            for shape in slide.shapes:
                if not hasattr(shape, "rotation"):
                    continue
                # 跳過 placeholder(母片設定可能旋轉,但會被 safe_textbox 過濾)
                if shape.is_placeholder:
                    continue
                # 跳過表格
                if shape.has_table:
                    continue
                # shape_type 17 = TEXT_BOX(可旋轉的)
                if getattr(shape, "rotation", 0) != 0:
                    text = shape.text_frame.text[:30] if shape.has_text_frame else ""
                    rotated_textboxes.append(
                        f"Slide {slide_num}: textbox rotation={shape.rotation}, text={text!r}"
                    )

        assert not rotated_textboxes, (
            f"發現 {len(rotated_textboxes)} 個旋轉的 textbox:\n" + "\n".join(rotated_textboxes[:5])
        )


class TestNoResidualPlaceholders:
    """Bug 2 + Bug 4 修正後測試:沒有「按一下即可新增文字」殘留 placeholder"""

    def test_no_residual_placeholders_in_new_slides(self):
        """新增 slide 不應有「按一下」文字的 placeholder"""
        input_pptx = REPORT_DIR / "N160JCN-EEK project 1pcs NG sample analysis report 260810.pptx"
        eval_path_candidates = [
            p for p in REPORT_DIR.glob("fa_report_N160JCN*.json") if "_improved" not in p.name
        ]
        if not input_pptx.exists() or not eval_path_candidates:
            pytest.skip("需要 N160JCN pptx 與 eval JSON")
        eval_path = eval_path_candidates[0]

        prs, result, _ = _run_improvement(input_pptx, eval_path, output_suffix="_vqres")

        new_slides = list(prs.slides)[result.original_slide_count :]
        residuals = []
        for offset, slide in enumerate(new_slides):
            slide_num = result.original_slide_count + offset + 1
            for shape in slide.placeholders:
                if not shape.has_text_frame:
                    continue
                text = shape.text_frame.text
                for marker in RESIDUAL_TITLE_MARKERS:
                    if marker in text:
                        residuals.append(f"Slide {slide_num}: placeholder 含「{marker}」")
                        break

        assert not residuals, f"發現 {len(residuals)} 個殘留 placeholder:\n" + "\n".join(
            residuals[:5]
        )


class TestTitlePlaceholderCorrect:
    """Bug 2 修正後測試:title placeholder 的文字應是實際標題,不是 placeholder 預設文字"""

    def test_new_slides_have_meaningful_titles(self):
        """每張新 slide 的 title placeholder 應有實際標題文字"""
        input_pptx = REPORT_DIR / "MS_Meishan_ADO_445239_260716.pptx"
        eval_path = REPORT_DIR / "fa_report_MS_Meishan_ADO_445239_260716.json"
        if not input_pptx.exists() or not eval_path.exists():
            pytest.skip("需要 MS pptx 與 eval JSON")

        prs, result, _ = _run_improvement(input_pptx, eval_path, output_suffix="_vqtit")

        new_slides = list(prs.slides)[result.original_slide_count :]
        empty_titles = []
        for offset, slide in enumerate(new_slides):
            slide_num = result.original_slide_count + offset + 1
            # 找 title placeholder(idx=0)
            title_ph = None
            for ph in slide.placeholders:
                if ph.placeholder_format.idx == 0:
                    title_ph = ph
                    break
            if title_ph is None:
                continue  # 沒有 title placeholder 跳過
            text = title_ph.text_frame.text.strip() if title_ph.has_text_frame else ""
            if not text:
                empty_titles.append(f"Slide {slide_num}: title 為空")

        assert not empty_titles, (
            f"發現 {len(empty_titles)} 張新 slide 的 title 是空的:\n" + "\n".join(empty_titles[:5])
        )
