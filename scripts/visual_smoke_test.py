#!/usr/bin/env python3
"""視覺驗證腳本 — 把 pptx 轉成 PNG 圖片,用於人工或自動檢查版面渲染

對應 handoff `2026-09-01-v311-incomplete-rendering-handoff.md`:
v3.1.1 缺少的視覺驗證。

執行方式:
    python scripts/visual_smoke_test.py

輸出:
    report/<pptx_stem>_visual/slide-001.png, slide-002.png, ...

需要:
    libreoffice (apt install libreoffice)
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPORT_DIR = Path("/home/elan/fa-report-refactor/report")
PPT_FILES = [
    "260811_Kobo_ZHT_RA6080_SPcomFailI_improved.pptx",
    "MS_Meishan_ADO_445239_260716_improved.pptx",
    "N160JCN-EEK project 1pcs NG sample analysis report 260810_improved.pptx",
]


def check_libreoffice() -> str:
    """檢查 libreoffice 是否可用"""
    path = shutil.which("libreoffice")
    if path is None:
        print("❌ 找不到 libreoffice,請先安裝:apt install libreoffice")
        sys.exit(1)
    return path


def convert_pptx_to_pdf(lo: str, pptx: Path, out_dir: Path) -> Path:
    """用 libreoffice 把 pptx 轉成 pdf"""
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [lo, "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(pptx)],
        check=True,
        capture_output=True,
        timeout=120,
    )
    return out_dir / (pptx.stem + ".pdf")


def convert_pdf_to_images(pdf: Path, out_dir: Path) -> list[Path]:
    """用 pdftoppm 把 pdf 每頁轉成 png"""
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = out_dir / "slide"
    subprocess.run(
        ["pdftoppm", "-png", "-r", "100", str(pdf), str(prefix)],
        check=True,
        capture_output=True,
        timeout=60,
    )
    return sorted(out_dir.glob("slide-*.png"))


def convert_one(lo: str, pptx_path: Path) -> list[Path]:
    """轉一份 pptx 為 png 列表"""
    visual_dir = REPORT_DIR / f"{pptx_path.stem}_visual"
    if visual_dir.exists():
        shutil.rmtree(visual_dir)
    pdf = convert_pptx_to_pdf(lo, pptx_path, visual_dir)
    images = convert_pdf_to_images(pdf, visual_dir)
    # 清理 pdf(只留圖)
    pdf.unlink()
    return images


def main() -> int:
    parser = argparse.ArgumentParser(description="視覺驗證:把 pptx 轉成 PNG")
    parser.add_argument(
        "--pptx",
        type=Path,
        help="單一 pptx 檔案路徑(預設:批次跑3 份)",
    )
    args = parser.parse_args()

    lo = check_libreoffice()

    pptx_files = [args.pptx] if args.pptx else [REPORT_DIR / name for name in PPT_FILES]

    total_images = 0
    for pptx in pptx_files:
        if not pptx.exists():
            print(f"⚠️  跳過(不存在):{pptx.name}")
            continue
        print(f"🔄 轉換:{pptx.name}")
        images = convert_one(lo, pptx)
        print(f"   ✅ {len(images)} 張圖片 → {pptx.stem}_visual/")
        total_images += len(images)

    print(f"\n總共產出 {total_images} 張圖片")
    print("下一步:手動檢查圖片,或用 OCR / 影像比對自動驗證")
    return 0


if __name__ == "__main__":
    sys.exit(main())
