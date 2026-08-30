"""CLI 入口"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pptx import Presentation

from .domain.evaluation import EvaluationResult
from .improvers.orchestrator import ImprovementOrchestrator
from .parsers.evaluation_parser import parse_evaluation


def main() -> int:
    """主入口"""
    parser = argparse.ArgumentParser(
        prog="fa-improve",
        description="半導體 FA 報告智慧化改善工具 v3.0",
    )
    parser.add_argument(
        "input",
        help="輸入 pptx 檔案路徑",
    )
    parser.add_argument(
        "--eval",
        "-e",
        help="評估檔(JSON 或 TXT)。若省略,需搭配 --llm-provider",
    )
    parser.add_argument(
        "--llm-provider",
        choices=["openai", "mock"],
        help="使用 LLM 直接評估(實驗性)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="LLM 模型(預設 gpt-4o-mini)",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="輸出 pptx 檔案路徑",
    )
    parser.add_argument(
        "--template-dir",
        help="自訂樣板目錄(JSON 樣板)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="顯示詳細輸出",
    )
    args = parser.parse_args()

    try:
        return _run(args)
    except Exception as e:
        print(f"✗ 錯誤:{e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def _run(args) -> int:
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"✗ 找不到輸入檔:{input_path}")
        return 1

    # 解析評估結果
    print("📖 解析評估...")
    if args.eval:
        eval_path = Path(args.eval)
        if not eval_path.exists():
            print(f"✗ 找不到評估檔:{eval_path}")
            return 1
        evaluation = parse_evaluation(eval_path)
        print(f"   來源:{eval_path.suffix} 檔案")
    elif args.llm_provider:
        evaluation = _evaluate_with_llm(input_path, args)
    else:
        print("✗ 必須指定 --eval 或 --llm-provider")
        return 1

    print(f"   總分:{evaluation.total_score} ({evaluation.grade})")

    # 載入 pptx
    print(f"📊 載入簡報:{input_path}")
    prs = Presentation(input_path)
    print(f"   投影片數:{len(prs.slides)}")

    # 執行改善
    print(f"🔧 執行改善...")
    orchestrator = ImprovementOrchestrator(evaluation, input_path)

    # 如果有自訂樣板目錄,傳入 TemplateLoader
    if args.template_dir:
        from .templates.loader import TemplateLoader

        template_dir = Path(args.template_dir)
        if template_dir.exists():
            loader = TemplateLoader(custom_template_dir=template_dir)
            orchestrator.template_loader = loader
            print(f"   自訂樣板:{template_dir}")

    result = orchestrator.execute(prs, output_path)

    print(f"\n✅ 完成!")
    print(f"   輸出:{result.output_path}")
    print(f"   投影片:{1 if False else ''}{result.original_slide_count} → {result.final_slide_count}")
    print(f"   母片保護:{'✓' if result.master_preserved else '✗'}")
    print(f"   耗時:{result.duration_seconds:.1f}s")

    # 寫入 manifest
    _write_manifest(output_path, input_path, evaluation, result)

    return 0


def _evaluate_with_llm(input_path: Path, args) -> EvaluationResult:
    """使用 LLM 評估 pptx"""
    print(f"   LLM Provider:{args.llm_provider}")
    print(f"   Model:{args.model}")

    if args.llm_provider == "openai":
        from .llm.openai_client import OpenAIClient

        client = OpenAIClient(model=args.model)
    elif args.llm_provider == "mock":
        from .llm.mock_client import MockLLMClient

        client = MockLLMClient()
    else:
        raise ValueError(f"不支援的 LLM provider: {args.llm_provider}")

    from .llm.evaluator import LLMEvaluator

    evaluator = LLMEvaluator(client)
    return evaluator.evaluate_pptx(input_path)


def _write_manifest(
    output_path: Path,
    input_path: Path,
    evaluation: EvaluationResult,
    result,
) -> None:
    """寫入 manifest"""
    manifest_path = output_path.with_suffix(output_path.suffix + ".manifest.json")
    manifest = {
        "execution_status": "success" if result.master_preserved else "failed",
        "input_file": str(input_path),
        "output_file": str(output_path),
        "original_slide_count": result.original_slide_count,
        "final_slide_count": result.final_slide_count,
        "master_preserved": result.master_preserved,
        "duration_seconds": result.duration_seconds,
        "actions": [a.value for a in result.plan.actions],
        "total_score_before": evaluation.total_score,
        "grade_before": evaluation.grade,
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"   Manifest:{manifest_path}")


if __name__ == "__main__":
    sys.exit(main())