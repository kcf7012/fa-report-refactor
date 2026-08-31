"""CLI 參數解析測試"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from fa_improver.cli import main


def _create_test_pptx(path: Path) -> None:
    """建立測試用 pptx"""
    from pptx import Presentation

    prs = Presentation()
    prs.save(path)


def _create_test_eval(path: Path) -> None:
    """建立測試用評估 JSON"""
    import json

    eval_data = {
        "total_score": 75.0,
        "grade": "C",
        "dimensions": {
            "基本資訊完整性": {"score": 70, "weight": 15, "comment": "需補充填寫"},
            "問題描述與定義": {"score": 80, "weight": 15, "comment": "OK"},
            "分析方法與流程": {"score": 75, "weight": 20, "comment": "OK"},
            "數據與證據支持": {"score": 80, "weight": 20, "comment": "OK"},
            "根因分析": {"score": 70, "weight": 20, "comment": "需加強 5-Why"},
            "改善對策": {"score": 80, "weight": 10, "comment": "OK"},
        },
        "improvements": [{"item": "基本資訊", "suggestion": "補充填寫", "priority": "HIGH"}],
        "summary": "整體報告分析尚可",
        "strengths": ["完整 8D 流程"],
    }
    path.write_text(json.dumps(eval_data), encoding="utf-8")


class TestCLIBasicArgs:
    """基本 CLI 參數測試"""

    def test_help(self, capsys):
        """--help 應輸出說明"""
        with (
            pytest.raises(SystemExit) as exc_info,
            patch("sys.argv", ["fa-improve", "--help"]),
        ):
            main()
        assert exc_info.value.code == 0

    def test_missing_output_returns_error(self, capsys):
        """缺少 --output 應回傳 argparse 錯誤(SystemExit 2)"""
        with (
            pytest.raises(SystemExit) as exc_info,
            patch("sys.argv", ["fa-improve", "input.pptx"]),
        ):
            main()
        assert exc_info.value.code == 2

    def test_missing_input_returns_error(self):
        """輸入檔不存在應回傳 1"""
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch(
                "sys.argv",
                [
                    "fa-improve",
                    str(Path(tmp) / "nonexistent.pptx"),
                    "--eval",
                    "eval.json",
                    "--output",
                    str(Path(tmp) / "out.pptx"),
                ],
            ),
        ):
            result = main()
        assert result == 1


class TestCLIApiKey:
    """--api-key 參數測試"""

    def test_api_key_arg_accepted(self):
        """--api-key 應被 argparse 接受"""
        from fa_improver.cli import main

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "input.pptx"
            output_path = tmp_path / "output.pptx"
            eval_path = tmp_path / "eval.json"
            _create_test_pptx(input_path)
            _create_test_eval(eval_path)

            with patch(
                "sys.argv",
                [
                    "fa-improve",
                    str(input_path),
                    "--eval",
                    str(eval_path),
                    "--output",
                    str(output_path),
                    "--api-key",
                    "sk-test-from-cli",
                ],
            ):
                result = main()
            # 應該成功
            assert result == 0

    def test_api_key_passed_to_openai_client(self):
        """--api-key 應傳給 OpenAIClient"""
        from fa_improver.cli import _evaluate_with_llm

        with patch("fa_improver.llm.openai_client.OpenAIClient") as mock_client:
            mock_client.return_value = MagicMock()
            from argparse import Namespace

            args = Namespace(
                llm_provider="openai",
                model="gpt-4o",
                api_key="sk-cli-key",
                base_url=None,
                redact_pii=False,
            )

            with tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                pptx_path = tmp_path / "test.pptx"
                _create_test_pptx(pptx_path)
                # patch evaluator 避免真實呼叫
                with patch("fa_improver.llm.evaluator.LLMEvaluator") as mock_eval:
                    mock_eval.return_value.evaluate_pptx.return_value = MagicMock()
                    _evaluate_with_llm(pptx_path, args)

            # 檢查 OpenAIClient 收到正確的 api_key
            call_kwargs = mock_client.call_args.kwargs
            assert call_kwargs.get("api_key") == "sk-cli-key"

    def test_redact_pii_flag_passed(self):
        """--redact-pii 應傳給 OpenAIClient"""
        from fa_improver.cli import _evaluate_with_llm

        with patch("fa_improver.llm.openai_client.OpenAIClient") as mock_client:
            mock_client.return_value = MagicMock()
            from argparse import Namespace

            args = Namespace(
                llm_provider="openai",
                model="gpt-4o",
                api_key="sk-test",
                base_url=None,
                redact_pii=True,
            )

            with tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                pptx_path = tmp_path / "test.pptx"
                _create_test_pptx(pptx_path)
                with patch("fa_improver.llm.evaluator.LLMEvaluator") as mock_eval:
                    mock_eval.return_value.evaluate_pptx.return_value = MagicMock()
                    _evaluate_with_llm(pptx_path, args)

            assert mock_client.call_args.kwargs.get("redact_pii_before_send") is True

    def test_base_url_arg_passed(self):
        """--base-url 應傳給 OpenAIClient"""
        from fa_improver.cli import _evaluate_with_llm

        with patch("fa_improver.llm.openai_client.OpenAIClient") as mock_client:
            mock_client.return_value = MagicMock()
            from argparse import Namespace

            args = Namespace(
                llm_provider="openai",
                model="gpt-4o",
                api_key="sk-test",
                base_url="https://api.groq.com/openai/v1",
                redact_pii=False,
            )

            with tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                pptx_path = tmp_path / "test.pptx"
                _create_test_pptx(pptx_path)
                with patch("fa_improver.llm.evaluator.LLMEvaluator") as mock_eval:
                    mock_eval.return_value.evaluate_pptx.return_value = MagicMock()
                    _evaluate_with_llm(pptx_path, args)

            assert mock_client.call_args.kwargs.get("base_url") == "https://api.groq.com/openai/v1"


class TestCLIEndToEnd:
    """CLI 端對端測試"""

    def test_full_pipeline_success(self):
        """完整流程成功"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "input.pptx"
            output_path = tmp_path / "output.pptx"
            eval_path = tmp_path / "eval.json"
            _create_test_pptx(input_path)
            _create_test_eval(eval_path)

            with patch(
                "sys.argv",
                [
                    "fa-improve",
                    str(input_path),
                    "--eval",
                    str(eval_path),
                    "--output",
                    str(output_path),
                ],
            ):
                result = main()
            assert result == 0
            assert output_path.exists()
            # manifest 應產生
            manifest_path = Path(str(output_path) + ".manifest.json")
            assert manifest_path.exists()


from unittest.mock import MagicMock  # noqa: E402
