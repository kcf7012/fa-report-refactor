#!/usr/bin/env python3
"""向後相容入口 — 委派給新的模組化架構

原始呼叫方式仍可運作:
    python improve_fa_report.py input.pptx eval.json output.pptx
"""
import sys
from pathlib import Path

# 加入 src/ 到 Python path
SKILL_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_ROOT / "src"))


def main():
    if len(sys.argv) != 4:
        print("使用方法: python improve_fa_report.py <input.pptx> <eval.json> <output.pptx>")
        print("或使用新 CLI: python -m fa_improver <input.pptx> --eval <eval.json> --output <output.pptx>")
        sys.exit(1)

    # 將位置參數轉為新 CLI 的命名參數
    sys.argv = [
        sys.argv[0],
        sys.argv[1],  # input
        "--eval",
        sys.argv[2],  # eval
        "--output",
        sys.argv[3],  # output
    ]

    from fa_improver.cli import main as cli_main

    sys.exit(cli_main())


if __name__ == "__main__":
    main()