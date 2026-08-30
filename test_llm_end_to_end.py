"""LLM 端對端測試 — 用真實 OpenAI API 評估 FA 報告

使用方式:
    python test_llm_end_to_end.py [report.pptx]

說明:
    這個腳本會:
    1. 解析真實的 FA 報告 (.pptx)
    2. 使用 .env 中的 API key 呼叫 OpenAI 進行 6 維度評估
    3. 根據評分結果自動產生改進計畫
    4. 輸出改善後的 pptx
    5. 顯示完整的 token 使用與成本

    預估成本: $0.01-0.05 USD(依報告大小而定)
"""

import sys
from pathlib import Path

# 確保 src/ 在 path 中
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))


def main():
    """主函式"""
    import argparse
    import os

    parser = argparse.ArgumentParser(description="LLM 端對端 FA 報告改善測試")
    parser.add_argument(
        "report",
        nargs="?",
        default=None,
        help="輸入 pptx 報告路徑(預設自動搜尋專案 report/ 目錄)",
    )
    parser.add_argument(
        "--output", "-o",
        default="/tmp/llm_improved.pptx",
        help="輸出 pptx 路徑",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("LLM 端對端 FA 報告改善測試")
    print("=" * 70)
    print()

    # 1. 載入 .env
    from dotenv import load_dotenv

    env_path = ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ 已載入 .env")
    else:
        print(f"⚠️  .env 不存在於 {env_path}")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("✗ OPENAI_API_KEY 未設定")
        return 1

    masked = f"{api_key[:10]}...{api_key[-4:]}"
    print(f"✓ API key: {masked}")
    model = os.environ.get("FA_IMPROVER_MODEL", "gpt-4o-mini")
    print(f"✓ Model: {model}")
    print()

    # 2. 檢查報告檔案
    if args.report:
        report_path = Path(args.report).resolve()
    else:
        # 預設找專案根目錄的 report/ (skill/.agents/skills → 向上 3 層)
        default_report = ROOT.parent.parent.parent / "report" / "MS_Meishan_ADO_445239_260716.pptx"
        report_path = default_report.resolve()

    if not report_path.exists():
        # 嘗試其他報告
        candidates = sorted((ROOT.parent.parent.parent / "report").glob("*.pptx"))
        # 排除 _improved.pptx(只選原始報告)
        original_reports = [c for c in candidates if "_improved" not in c.name]
        if original_reports:
            report_path = original_reports[0]
            print(f"⚠️  預設報告不存在,使用: {report_path.name}")
        else:
            print(f"✗ report/ 目錄無原始 pptx 檔案")
            return 1
    print(f"✓ 報告: {report_path}")
    print(f"  檔案大小: {report_path.stat().st_size / 1024:.1f} KB")
    print()

    # 3. 初始化 OpenAI Client
    print("-" * 70)
    print("初始化 OpenAI Client")
    print("-" * 70)
    from fa_improver.llm.openai_client import OpenAIClient

    client = OpenAIClient(model=model)
    print(f"✓ Client 已就緒 (model={model})")
    print()

    # 4. LLM 評估
    print("-" * 70)
    print("步驟 1/3:LLM 評估 6 維度")
    print("-" * 70)
    print("  (這會花費約 10-30 秒,呼叫 OpenAI API)")
    print()

    from fa_improver.llm.evaluator import LLMEvaluator

    evaluator = LLMEvaluator(client)
    evaluation = evaluator.evaluate_pptx(report_path)

    print(f"✓ LLM 評估完成!")
    print(f"  總分: {evaluation.total_score}")
    print(f"  等級: {evaluation.grade}")
    print()
    print(f"  6 維度評分:")
    for dim in evaluation.dimensions:
        gap_marker = (
            "🔴"
            if dim.score < 50
            else "🟠"
            if dim.score < 70
            else "🟡"
            if dim.score < 85
            else "🟢"
        )
        print(f"    {gap_marker} {dim.name.value}: {dim.score}/100")
    print()

    # 5. Token 使用統計
    if evaluation.token_usage:
        usage = evaluation.token_usage
        in_tok = usage.get("prompt_tokens", 0)
        out_tok = usage.get("completion_tokens", 0)
        total_tok = usage.get("total_tokens", 0)
        print(f"  Token 使用:")
        print(f"    - Prompt: {in_tok}")
        print(f"    - Completion: {out_tok}")
        print(f"    - Total: {total_tok}")
        # 估算成本
        costs = {
            "gpt-4o-mini": (0.15, 0.60),
            "gpt-4o": (2.50, 10.00),
            "o1-mini": (3.00, 12.00),
        }
        if model in costs:
            in_rate, out_rate = costs[model]
            cost = (in_tok * in_rate + out_tok * out_rate) / 1_000_000
            print(f"    - 預估成本: ${cost:.6f} USD")
        print()

    # 6. 改進計畫
    print("-" * 70)
    print("步驟 2/3:產生改進計畫")
    print("-" * 70)
    from fa_improver.improvers.orchestrator import ImprovementOrchestrator

    output_path = Path(args.output)
    orchestrator = ImprovementOrchestrator(evaluation, report_path)
    plan = orchestrator.build_plan()

    print(f"✓ 改進計畫 ({len(plan.actions)} 個動作):")
    for i, action in enumerate(plan.actions, 1):
        print(f"    {i}. {action.value}")
    print()

    # 7. 執行改善
    print("-" * 70)
    print("步驟 3/3:執行改善並輸出 pptx")
    print("-" * 70)

    from pptx import Presentation

    prs = Presentation(report_path)
    original_count = len(prs.slides)

    result = orchestrator.execute(prs, output_path)

    print(f"✓ 改善完成!")
    print(f"  投影片: {original_count} → {result.final_slide_count} 張")
    print(f"  母片保護: {'✓' if result.master_preserved else '✗ 失敗!'}")
    print(f"  輸出: {result.output_path}")
    print(f"  耗時: {result.duration_seconds:.1f}s")
    print()

    # 8. 最終總結
    print("=" * 70)
    print("測試結果總結")
    print("=" * 70)
    print()
    print(f"  評估分數: {evaluation.grade} ({evaluation.total_score}/100)")
    print(f"  改善動作: {len(plan.actions)} 個")
    print(f"  投影片增加: {result.final_slide_count - original_count} 張")
    print(f"  母片保護: {'通過 ✓' if result.master_preserved else '失敗 ✗'}")
    print(f"  改善輸出: {result.output_path}")
    print()
    print("✓ 端對端測試完成!您可以在 OpenAI Dashboard 查看實際用量。")
    print()
    print(f"  Dashboard: https://platform.openai.com/usage")

    return 0


if __name__ == "__main__":
    sys.exit(main())