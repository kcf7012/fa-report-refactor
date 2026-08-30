# uv 套件管理整合

> **目標**:用 `uv` 取代 `pip + venv`,讓使用者一鍵執行、不污染全域 Python
> **範圍**:v3.0 全面採用 uv,向後相容保留 `pip` 安裝方式

---

## 一、為什麼選 uv?

| 特性 | pip + venv | uv |
|------|-----------|-----|
| 安裝速度 | 慢(數十秒) | **極快**(通常 < 1 秒) |
| 自動虛擬環境 | ✗(需手動建立) | ✓(`uv run` 自動建立) |
| lockfile | 需 pip-compile | 內建 `uv.lock` |
| 全域污染風險 | 高(忘記 deactivate) | **極低**(預設隔離) |
| 跨平台 | ✓ | ✓(單一二進位) |
| 取代 pip 相容性 | - | ✓(`uv pip` 與 pip 相容) |

---

## 二、整合設計

### 2.1 目錄結構改變

```
fa-report-improvement/
├── pyproject.toml          # ★ 新增:專案設定 + 依賴宣告
├── uv.lock                 # ★ 新增:鎖定版本(自動產生)
├── requirements.txt        # 保留(向後相容)
├── .python-version         # ★ 新增:Python 版本要求
│
├── src/fa_improver/        # 套件原始碼
├── tests/
└── scripts/
```

### 2.2 pyproject.toml 範例

```toml
[project]
name = "fa-improver"
version = "3.0.0"
description = "半導體 FA 報告智慧化改善工具"
readme = "README.md"
requires-python = ">=3.10"
license = { file = "LICENSE" }
authors = [
    { name = "Kenny Kang", email = "kenny.kang@elan.com.tw" },
]
keywords = ["semiconductor", "failure-analysis", "pptx", "llm-agent"]

# 核心依賴(執行必要)
dependencies = [
    "python-pptx>=0.6.21",
    "Pillow>=9.0.0",
    "pydantic>=2.0",
    "typing-extensions>=4.0",
]

# 選擇性依賴(LLM 整合)
[project.optional-dependencies]
llm = [
    "openai>=1.0",
    "anthropic>=0.18",
    "ollama>=0.1",
]
dev = [
    "pytest>=7.4",
    "pytest-cov>=4.1",
    "mypy>=1.7",
    "ruff>=0.1",
    "black>=23.10",
    "pre-commit>=3.5",
    "types-Pillow",
]
docs = [
    "mkdocs>=1.5",
    "mkdocs-material>=9.4",
]

# CLI 入口
[project.scripts]
fa-improve = "fa_improver.cli:main"
fa-agent = "fa_improver.agent:main"

# uv 設定
[tool.uv]
dev-dependencies = [
    "pytest>=7.4",
    "pytest-cov>=4.1",
    "mypy>=1.7",
    "ruff>=0.1",
    "black>=23.10",
]
```

### 2.3 .python-version 範例

```
3.10
```

(uv 會自動偵測並下載/使用此版本)

---

## 三、使用方式

### 3.1 安裝 uv(一次性)

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# macOS (Homebrew)
brew install uv

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# pip(也可以)
pip install uv
```

### 3.2 執行技能包(不需要預先安裝)

```bash
# 直接執行,uv 自動建立虛擬環境並安裝依賴
uv run fa-improve report.pptx eval.json improved.pptx

# 啟用 LLM 支援
uv run --extra llm fa-agent improve report.pptx --llm openai

# 開發模式
uv run --extra dev pytest
uv run --extra dev mypy src/

# 同步所有 extras
uv sync --all-extras
```

### 3.3 對開發者

```bash
# 第一次設定
git clone <repo>
cd fa-report-improvement
uv sync                  # 安裝所有依賴(含 dev)

# 之後每天
uv run pytest           # 跑測試
uv run fa-agent ...      # 執行

# 新增依賴
uv add requests         # 加 runtime 依賴
uv add --dev pytest-mock  # 加 dev 依賴

# 更新 lockfile
uv lock --upgrade
```

---

## 四、向後相容策略

### 4.1 保留 requirements.txt

```txt
# requirements.txt (保留供舊用戶使用)
python-pptx>=0.6.21
Pillow>=9.0.0

# 注意:強烈建議改用 uv,參見 pyproject.toml
# uv 安裝方式:curl -LsSf https://astral.sh/uv/install.sh | sh
# 然後執行:uv run fa-improve ...
```

### 4.2 保留舊的 install.py

`scripts/install.py` 仍可運作(用 pip + venv),但 SKILL.md 會建議優先用 uv。

### 4.3 雙模式 CLI 入口

```python
# scripts/improve_fa_report.py(舊入口,thin wrapper)
#!/usr/bin/env python3
"""向後相容入口 - 自動偵測 uv 或 python 直接執行"""
import sys
import os

def main():
    if "--use-uv" in sys.argv:
        sys.argv.remove("--use-uv")
        # 重新呼叫 uv run
        os.execvp("uv", ["uv", "run", "fa-improve"] + sys.argv[1:])
    else:
        # 直接執行新架構
        from fa_improver.cli import main as cli_main
        sys.exit(cli_main())

if __name__ == "__main__":
    main()
```

---

## 五、CI/CD 整合

### 5.1 GitHub Actions 範例

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run tests
        run: uv run pytest --cov=fa_improver --cov-report=xml

      - name: Type check
        run: uv run mypy src/

      - name: Lint
        run: uv run ruff check src/
```

### 5.2 pre-commit 範例

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace
```

---

## 六、開發者體驗改善

### 6.1 Makefile / Taskfile

```makefile
# Makefile
.PHONY: install test lint format clean run

install:
	uv sync --all-extras

test:
	uv run pytest

lint:
	uv run ruff check src/
	uv run mypy src/

format:
	uv run black src/
	uv run ruff check --fix src/

run:
	uv run fa-agent improve

clean:
	rm -rf .venv dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
```

### 6.2 VS Code 設定

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.testing.pytestEnabled": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit"
    }
  }
}
```

---

## 七、為什麼不破壞原始環境?

### uv 的隔離保證

1. **預設行為**:每個 `uv run` 都會建立 `.venv/`,不會影響全域 Python
2. **無 `activate` 動作**:不需 source/activate,避免忘記 deactivate 導致污染
3. **依賴解析**:uv 用靜態分析找出最小依賴集,避免不必要的套件污染
4. **lockfile**:鎖定版本,不同環境/時間安裝結果一致

### 與現有 venv 共存

如果使用者的 `scripts/install.py` 已經建立了 `venv/`,uv 會自動偵測並使用:

```bash
# 既有 venv/ 會被 uv 識別並使用
$ ls venv/bin/python
/venv/bin/python
$ uv run python -c "print('hello')"
hello  # 使用既有 venv,不會重建
```

---

## 八、實作檢查清單

### Phase 1:基礎(必做)
- [ ] 建立 `pyproject.toml`
- [ ] 建立 `.python-version`
- [ ] 把現有依賴從 `requirements.txt` 搬到 `pyproject.toml`
- [ ] 執行 `uv lock` 產生 lockfile
- [ ] 確認 `uv run` 可正常執行既有功能

### Phase 2:開發體驗
- [ ] 建立 `Makefile`
- [ ] 建立 `.github/workflows/test.yml`
- [ ] 建立 `.pre-commit-config.yaml`
- [ ] 建立 `.vscode/settings.json`

### Phase 3:文件化
- [ ] 更新 `SKILL.md` Quick Start 改用 uv
- [ ] 移除或 deprecate `scripts/install.py`
- [ ] 在 `README.md` 加入 uv 安裝說明

### Phase 4:驗證
- [ ] 在 Linux/macOS/Windows 各測試一次 `uv run`
- [ ] 確認沒有污染系統 Python(`which python` 不應指向 venv)
- [ ] 跑完整測試套件

---

## 九、常見問題 FAQ

### Q:uv 與 pip 衝突嗎?
A:不衝突。`uv pip install` 是 pip 的 drop-in replacement,完全相容。

### Q:可以繼續用 pip 嗎?
A:可以。`requirements.txt` 保留,`scripts/install.py` 仍可用。但 uv 更快、更安全。

### Q:團隊成員一定要裝 uv 嗎?
A:不需要,`requirements.txt` 仍可用。但建議統一用 uv,以避免「在我電腦上可以跑」的問題。

### Q:uv lockfile 要 commit 嗎?
A:建議 commit。這樣整個團隊、CI 環境都用相同版本,避免環境不一致。

### Q:從 pip 遷移會很麻煩嗎?
A:不會。流程是:
```bash
# 1. 刪除舊 venv
rm -rf venv/

# 2. 安裝 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. 同步依賴(uv 會建立新的 .venv)
uv sync

# 4. 驗證
uv run pytest
```
總共 5 分鐘。

---

**整合進度**:本文件補充了 02_refactor_plan.md 的「基礎建設」階段。實作上,Phase 1(基礎)建議在 v3.0 第一個 PR 完成,確保後續所有開發都用 uv 管理依賴。

**下一步**:把 pyproject.toml 加入第一個 PR,然後驗證 `uv run fa-improve` 可正常運作。