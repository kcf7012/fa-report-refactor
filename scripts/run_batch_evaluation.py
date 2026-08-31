#!/usr/bin/env python3
"""批次執行 FA 報告改善測試

依序對 report/ 下的 3 個 FA 報告執行完整改善流程,產生:
- 改善後 pptx(原檔名 + _improved)
- manifest.json(執行紀錄)

使用方式:
    python scripts/run_batch_evaluation.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from pptx import Presentation

from fa_improver.improvers.orchestrator import ImprovementOrchestrator
from fa_improver.parsers.evaluation_parser import parse_evaluation

REPORT_DIR = Path("/home/elan/fa-report-refactor/report")

# 3 組測試案例
TEST_CASES = [
    {
        "name": "260811_Kobo_ZHT_RA6080_SPcomFailI",
        "input_pptx": "260811_Kobo_ZHT_RA6080_SPcomFailI.pptx",
        "eval_json": "fa_report_260811_Kobo_ZHT_RA6080_SPcomFailI.json",
        "eval_txt": "fa_report_260811_Kobo_ZHT_RA6080_SPcomFailI.txt",
    },
    {
        "name": "MS_Meishan_ADO_445239_260716",
        "input_pptx": "MS_Meishan_ADO_445239_260716.pptx",
        "eval_json": "fa_report_MS_Meishan_ADO_445239_260716.json",
        "eval_txt": "fa_report_MS_Meishan_ADO_445239_260716.txt",
    },
    {
        "name": "N160JCN-EEK project 1pcs NG sample analysis report 260810",
        "input_pptx": "N160JCN-EEK project 1pcs NG sample analysis report 260810.pptx",
        "eval_json": "fa_report_N160JCN-EEK project 1pcs NG sample analysis report 260810.json",
        "eval_txt": "fa_report_N160JCN-EEK project 1pcs NG sample analysis report 260810.txt",
    },
]


def run_one(case: dict) -> dict:
    """執行單一 FA 報告改善"""
    print(f"\n{'=' * 60}")
    print(f"📊 處理: {case['name']}")
    print(f"{'=' * 60}")

    input_path = REPORT_DIR / case["input_pptx"]
    eval_path = REPORT_DIR / case["eval_json"]
    output_path = REPORT_DIR / case["input_pptx"].replace(".pptx", "_improved.pptx")

    # 1. 確認檔案存在
    if not input_path.exists():
        print(f"❌ 找不到輸入檔:{input_path}")
        return {"name": case["name"], "status": "error", "reason": "input not found"}

    if not eval_path.exists():
        print(f"❌ 找不到評估檔:{eval_path}")
        return {"name": case["name"], "status": "error", "reason": "eval not found"}

    # 2. 解析評估
    print(f"📖 解析評估:{eval_path.name}")
    evaluation = parse_evaluation(eval_path)
    print(f"   總分:{evaluation.total_score} ({evaluation.grade})")
    print(f"   維度數:{len(evaluation.dimensions)}")
    for d in evaluation.dimensions:
        marker = "🔴" if d.score < 70 else ("🟡" if d.score < 80 else "🟢")
        print(f"   {marker} {d.name.value}: {d.score} (權重 {d.weight}%)")

    # 3. 載入 pptx
    print(f"\n📊 載入簡報:{input_path.name}")
    prs = Presentation(input_path)
    original_count = len(prs.slides)
    print(f"   原始投影片數:{original_count}")

    # 4. 執行改善
    print("\n🔧 執行改善...")
    orchestrator = ImprovementOrchestrator(evaluation, input_path)
    plan = orchestrator.build_plan()

    print(f"   預計新增 {len(plan.actions)} 張投影片:")
    for action in plan.actions:
        print(f"     - {action.value}")

    start = time.time()
    result = orchestrator.execute(prs, output_path)
    duration = time.time() - start

    # 5. 結果報告
    print("\n✅ 完成!")
    print(f"   輸出:{result.output_path}")
    print(f"   投影片:{result.original_slide_count} → {result.final_slide_count}")
    print(f"   母片保護:{'✓' if result.master_preserved else '✗'}")
    print(f"   耗時:{duration:.1f}s")

    # 6. 寫入 manifest.json
    _write_manifest(input_path, output_path, evaluation, result)

    return {
        "name": case["name"],
        "status": "success" if result.master_preserved else "failed",
        "input": case["input_pptx"],
        "output": output_path.name,
        "original_score": evaluation.total_score,
        "original_grade": evaluation.grade,
        "actions": [a.value for a in plan.actions],
        "original_slides": result.original_slide_count,
        "final_slides": result.final_slide_count,
        "master_preserved": result.master_preserved,
        "duration_seconds": round(duration, 2),
    }


def _write_manifest(input_path, output_path, evaluation, result):
    """寫入 manifest.json(與 CLI 一致)"""
    import datetime
    import json as json_mod

    manifest_path = Path(str(output_path) + ".manifest.json")
    manifest = {
        "execution_status": "success" if result.master_preserved else "failed",
        "timestamp": datetime.datetime.now().isoformat(),
        "input_file": str(input_path),
        "output_file": str(output_path),
        "original_slide_count": result.original_slide_count,
        "final_slide_count": result.final_slide_count,
        "master_preserved": result.master_preserved,
        "duration_seconds": round(result.duration_seconds, 2),
        "actions": [a.value for a in result.plan.actions],
        "total_score_before": evaluation.total_score,
        "grade_before": evaluation.grade,
    }
    manifest_path.write_text(
        json_mod.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"   Manifest:{manifest_path}")


def main() -> int:
    """批次執行所有測試案例"""
    print("=" * 60)
    print("🚀 FA 報告批次改善測試")
    print("=" * 60)

    if not REPORT_DIR.exists():
        print(f"❌ Report 目錄不存在:{REPORT_DIR}")
        return 1

    results = []
    total_start = time.time()

    for case in TEST_CASES:
        result = run_one(case)
        results.append(result)

    total_duration = time.time() - total_start

    # 總結報告
    print(f"\n\n{'=' * 60}")
    print("📊 批次執行總結")
    print(f"{'=' * 60}")

    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = len(results) - success_count

    print(f"\n總案例:{len(results)}")
    print(f"  ✅ 成功:{success_count}")
    print(f"  ❌ 失敗:{failed_count}")
    print(f"  ⏱️  總耗時:{total_duration:.1f}s")

    print("\n詳細結果:")
    for r in results:
        status = "✅" if r["status"] == "success" else "❌"
        if r["status"] == "success":
            print(f"\n  {status} {r['name']}")
            print(f"     {r['original_score']} ({r['original_grade']}) → 改善完成")
            print(f"     投影片:{r['original_slides']} → {r['final_slides']}")
            print(f"     動作:{', '.join(r['actions'])}")
            print(f"     耗時:{r['duration_seconds']}s")
        else:
            print(f"\n  {status} {r['name']}")
            print(f"     原因:{r.get('reason', 'unknown')}")

    # 儲存批次結果
    summary_path = Path("/home/elan/fa-report-refactor/report/batch_evaluation_summary.json")
    summary_path.write_text(
        json.dumps(
            {
                "total_cases": len(results),
                "success": success_count,
                "failed": failed_count,
                "total_duration": round(total_duration, 2),
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n📄 批次總結:{summary_path}")

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
