#!/usr/bin/env python3
"""路徑守門 —— 擋掉新增的絕對路徑字面值。

## 為什麼需要這支

這個專案的路徑問題出現過三次,每次都是「修好了」之後再犯:

1. 第一輪稽核抓到 16 個測試硬編 `/home/<user>/fa-report-refactor`
2. 修正只是把該字面值**搬進** resolver 的預設清單 —— 沒有真正消除
3. 於是失效方式從「看得見的 skip」變成「看不見的靜默降級」,連續三輪稽核沒發現

靠人記得是沒有用的。這支腳本是唯一能**機制性**擋住回歸的東西。

## 檢查範圍:只看新增行

不掃既有內容 —— 歷史文件本來就記著當時的真實路徑,那是事實紀錄,不該改。
只要新提交的行裡出現使用者家目錄的絕對路徑就失敗。

## 用法

    python scripts/check_no_hardcoded_paths.py              # 檢查 staged diff(pre-commit)
    python scripts/check_no_hardcoded_paths.py --base main  # 檢查與某個 ref 的差異(CI)
    python scripts/check_no_hardcoded_paths.py --all        # 掃全部追蹤檔(診斷用,會有既有命中)

## 例外

- `docs/handoff/`、`CHANGELOG.md`:歷史紀錄,保留當時的事實
- 行尾加 `# allow-abs-path`(或 `<!-- allow-abs-path -->`):明確豁免單行,
  給「正在說明這個路徑有問題」這類敘述用
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

# 使用者家目錄下的絕對路徑 —— 換一台機器就必定失效的那種
FORBIDDEN_PATTERNS = [
    (re.compile(r"/home/[A-Za-z][\w.-]*/"), "Linux 家目錄絕對路徑"),
    (re.compile(r"/Users/[A-Za-z][\w.-]*/"), "macOS 家目錄絕對路徑"),
    (re.compile(r"[A-Za-z]:\\\\?Users\\\\?"), "Windows 家目錄絕對路徑"),
]

# 歷史紀錄:當時的路徑是當時的事實,不該被改寫
EXEMPT_PREFIXES = (
    "docs/handoff/",
    ".agents/skills/handoff-doc-generator/",
)
EXEMPT_FILES = (
    "CHANGELOG.md",
    "scripts/check_no_hardcoded_paths.py",  # 本檔案自己含有這些 pattern
)

ALLOW_MARKER = "allow-abs-path"


def _is_exempt(path: str) -> bool:
    return path.startswith(EXEMPT_PREFIXES) or path in EXEMPT_FILES


def _added_lines(diff: str) -> list[tuple[str, str]]:
    """從 unified diff 取出 (檔案路徑, 新增行內容)。"""
    results: list[tuple[str, str]] = []
    current: str | None = None
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            # `diff --git a/<path> b/<path>` —— 取 b/ 側
            parts = line.split(" b/", 1)
            current = parts[1] if len(parts) == 2 else None
        elif line.startswith("+++ b/"):
            current = line[len("+++ b/") :]
        elif line.startswith("+") and not line.startswith("+++"):
            if current is not None:
                results.append((current, line[1:]))
    return results


def _run(args: list[str]) -> str:
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"✗ 指令失敗:{' '.join(args)}\n{proc.stderr}", file=sys.stderr)
        sys.exit(2)
    return proc.stdout


def _collect(base: str | None, scan_all: bool) -> list[tuple[str, str]]:
    if scan_all:
        files = _run(["git", "ls-files"]).splitlines()
        pairs = []
        for path in files:
            if _is_exempt(path):
                continue
            try:
                content = _run(["git", "show", f"HEAD:{path}"])
            except SystemExit:
                continue
            pairs.extend((path, line) for line in content.splitlines())
        return pairs
    if base:
        return _added_lines(_run(["git", "diff", "-U0", f"{base}...HEAD"]))
    return _added_lines(_run(["git", "diff", "--cached", "-U0"]))


def main() -> int:
    parser = argparse.ArgumentParser(description="擋掉新增的絕對路徑字面值")
    parser.add_argument("--base", help="與這個 ref 比較(CI 用),預設檢查 staged diff")
    parser.add_argument("--all", action="store_true", help="掃全部追蹤檔(診斷用)")
    args = parser.parse_args()

    violations: list[str] = []
    for path, line in _collect(args.base, args.all):
        if _is_exempt(path) or ALLOW_MARKER in line:
            continue
        for pattern, label in FORBIDDEN_PATTERNS:
            if pattern.search(line):
                violations.append(f"  {path}\n    [{label}] {line.strip()[:120]}")
                break

    if not violations:
        print("✓ 路徑守門:沒有新增的絕對路徑字面值")
        return 0

    print("✗ 路徑守門:偵測到絕對路徑字面值\n", file=sys.stderr)
    for v in violations:
        print(v, file=sys.stderr)
    print(
        "\n請改用 `fa_improver.paths`(SKILL_ROOT / find_project_root / "
        "resolve_report_file)或環境變數,\n"
        "文件裡用 `<PROJECT_ROOT>` 佔位。歷史紀錄請寫在 docs/handoff/ 底下。\n"
        f"確實必要時,可在該行尾端加上 `{ALLOW_MARKER}` 豁免。",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
