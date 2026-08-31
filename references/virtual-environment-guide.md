# Python 虛擬環境最佳實踐指南 — v3.0.1 uv 版

> **適用版本**:v3.0.0(2026-08-31)+ v3.0.1(2026-08-31)
> **工具**:uv 0.12.7+(`uv sync` 取代 `pip + venv`)
> **環境路徑**:`.venv/`(uv-managed)
> **狀態**:✅ **已從 v2.x `pip + venv` 遷移到 v3.0 `uv`**

---

## ⚠️ 為什麼務必使用虛擬環境?

### 不使用虛擬環境的風險

❌ **依賴衝突**:
```
專案 A 需要 python-pptx 0.6.18
專案 B 需要 python-pptx 0.6.21
全局安裝 → 只能保留一個版本 → 某個專案會壞掉
```

❌ **系統污染**:
```
全局安裝幾十個套件 → Python 環境混亂 → 難以維護
系統升級 → 套件不兼容 → 所有專案都壞掉
```

❌ **權限問題**:
```
全局安裝需要 sudo/管理員權限
無法在受限環境中安裝
容易引入安全問題
```

❌ **難以清理**:
```
專案不用了 → 套件還留在系統中
不知道哪些可以刪 → 系統越來越臃腫
```

### 使用 uv 的好處(取代傳統 venv)

✅ **完全隔離**:
```
每個專案獨立 .venv/
不同版本可以共存
互不干擾
```

✅ **保持乾淨**:
```
全局 Python 保持原始狀態
專案環境各自管理
刪除專案 = 刪除 .venv/
```

✅ **無需權限**:
```
uv sync 在用戶目錄建立 .venv/
不需要 sudo/admin
安全可靠
```

✅ **可重現**:
```
uv.lock 鎖定 51 個依賴套件(精確版本)
任何人都能重建相同環境
CI/CD 部署一致
```

✅ **極速安裝**(uv 相比 pip 的最大優勢):
```
uv sync:通常 < 1 秒(pip 需要數十秒)
uv pip install:比 pip 快 10-100 倍
```

✅ **無需 activate**:
```
不需 source .venv/bin/activate
uv run 自動用對的環境
避免忘記 deactivate 導致污染
```

---

## 🚀 uv 環境完整指南(v3.0.1)

### 1. 安裝 uv(一次性)

```bash
# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# macOS(Homebrew)
brew install uv

# Windows(PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# pip(也可以)
pip install uv
```

### 2. 同步依賴(建立 .venv/)

```bash
# 進入技能包目錄
cd .agents/skills/fa-report-improvement

# uv 會自動建立 .venv/ 並安裝所有依賴(含 dev、llm)
uv sync --all-extras

# 完成後的目錄結構
# fa-report-improvement/
# ├── .venv/             ← uv-managed 虛擬環境
# │   ├── bin/           (Linux/macOS)
# │   ├── Scripts/       (Windows)
# │   ├── lib/
# │   └── ...
# ├── SKILL.md
# ├── pyproject.toml      ← 主要依賴宣告
# ├── uv.lock             ← 鎖定 51 個依賴套件
# ├── requirements.txt    ← pip fallback(向後相容)
# └── ...
```

**只需執行一次**,之後每次使用前 `uv sync`(會增量更新)。

### 3. 使用技能包(不需要 activate)

```bash
# 方式 A:直接用 uv run(推薦,不用 activate)
uv run python -m fa_improver input.pptx --eval eval.json --output improved.pptx

# 方式 B:明確指定 .venv/bin/python
.venv/bin/python -m fa_improver input.pptx --eval eval.json --output improved.pptx

# 方式 C:跑測試
uv run pytest tests/ -v

# 方式 D:用 LLM 評估
uv run --extra llm python -m fa_improver report.pptx --llm-provider openai
```

**注意:v3.0.1 不再需要 `source .venv/bin/activate`**(uv 自動管理)

### 4. 退出/切換環境

uv **不需要 deactivate**,每個 `uv run` 都是獨立環境。

### 5. 卸載 uv 環境

```bash
# 刪除 .venv/ 即可完整清除
rm -rf .venv/

# 之後 uv sync 會重建
uv sync
```

---

## 📋 常用命令速查(v3.0.1 uv 版)

```bash
# 安裝所有依賴(含 dev、llm extras)
uv sync --all-extras

# 安裝套件(像 pip add)
uv add requests

# 加 dev 依賴
uv add --dev pytest-mock

# 跑腳本
uv run python -m fa_improver input.pptx --eval eval.json --output out.pptx

# 跑測試
uv run pytest

# 鎖定更新
uv lock --upgrade

# 卸載套件
uv remove requests

# 查看已安裝
uv pip list
```

---

## 🔍 檢查是否使用 uv 環境

### 方法 1:查看 .venv/ 目錄

```bash
ls .venv/bin/python
# 存在 → uv 環境已建立
```

### 方法 2:Python 路徑

```bash
uv run python -c "import sys; print(sys.prefix)"
# 應指向 /path/to/fa-report-improvement/.venv
```

### 方法 3:使用 Python 代碼

```python
import sys
print(sys.prefix)
# uv 環境: /path/to/fa-report-improvement/.venv
# 全局環境: /usr 或 /usr/local
```

---

## ⚠️ 常見錯誤與解決

### 錯誤 1:忘記用 `uv run`

**症狀**:
```bash
$ python -m fa_improver
ModuleNotFoundError: No module named 'fa_improver'
```

**原因**:在全局環境執行,沒有 uv 環境

**解決**:
```bash
# 用 uv run(自動用 .venv/)
uv run python -m fa_improver input.pptx --eval eval.json --output out.pptx

# 或明確指定
.venv/bin/python -m fa_improver ...
```

### 錯誤 2:PowerShell 執行策略限制(Windows)

**症狀**:
```
無法載入檔案,因為這個系統上已停用指令碼執行。
```

**解決**:用 `uv run` 取代直接執行 PowerShell 腳本(uv 會處理)。

### 錯誤 3:.venv/ 損壞

**症狀**:
```
Error: ... returned non-zero exit status 1
```

**解決**:
```bash
# 刪除舊環境
rm -rf .venv/

# 重建
uv sync
```

### 錯誤 4:uv 版本過舊

**症狀**:
```
ERROR: Could not find a version that satisfies the requirement...
```

**解決**:
```bash
# 升級 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或
uv self update
```

---

## 🎯 最佳實踐(v3.0.1)

### 1. 每個專案一個 .venv/(由 uv 管理)

```
✅ 好的做法
~/projects/
├── project-a/
│   ├── .venv/          ← uv-managed
│   ├── pyproject.toml
│   └── uv.lock
└── project-b/
    ├── .venv/          ← uv-managed
    ├── pyproject.toml
    └── uv.lock
```

### 2. 環境目錄統一用 `.venv/`(隱藏目錄)

```bash
# 推薦命名
.venv/           # uv-managed(統一用這個)

# 避免
venv/            # 舊 venv 命名,容易跟 uv 混淆
myenv/           # 不夠標準
```

### 3. 將 .venv/ 加入 .gitignore

```gitignore
# .gitignore
.venv/
*.pyc
__pycache__/
uv.lock          # 或 commit,看團隊政策
```

**為什麼?**
- 虛擬環境是本地的
- 不應該提交到版本控制
- 每個人根據 pyproject.toml + uv.lock 重建

### 4. 用 pyproject.toml + uv.lock 管理依賴

```bash
# 自動從 pyproject.toml 同步
uv sync

# 其他人重建環境
uv sync
```

### 5. 定期更新依賴

```bash
# 更新 uv.lock
uv lock --upgrade

# 同步新版本
uv sync
```

---

## 📊 uv vs 傳統 pip + venv 對比

| 特性 | uv | pip + venv |
|------|-----|------|
| **安裝速度** | ⚡ **< 1 秒** | 🐢 數十秒 |
| **依賴隔離** | ✅ `.venv/` | ✅ `venv/` |
| **lockfile** | ✅ `uv.lock`(51 套件) | ❌ 需 pip-compile |
| **版本衝突** | ✅ 不會衝突 | ✅ 不會衝突 |
| **系統乾淨** | ✅ 不污染系統 | ✅ 不污染系統 |
| **需要 activate** | ✅ **不需要** | ❌ 每次都要 activate |
| **需要權限** | ✅ 不需要 | ✅ 不需要 |
| **CI/CD 一致性** | ✅ 鎖定檔保證 | ⚠️ 需手動管理 |
| **跨平台** | ✅ 單一二進位 | ✅ |

---

## 🛠️ 進階技巧

### 1. 使用額外依賴群組

```bash
# LLM 功能
uv sync --extra llm

# 開發工具
uv sync --extra dev

# 全部
uv sync --all-extras
```

### 2. CI/CD 中的 uv

```yaml
# GitHub Actions
- uses: astral-sh/setup-uv@v1
- run: uv sync --all-extras
- run: uv run pytest --cov=fa_improver
```

### 3. pre-commit 整合

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: pytest
      entry: .venv/bin/python -m pytest tests/ -q
      language: system
      pass_filenames: false
      always_run: true
```

---

## 📝 FA Report Improvement Skill 特定指南(v3.0.1)

### 標準安裝流程

```bash
# 1. 進入技能包目錄
cd .agents/skills/fa-report-improvement

# 2. 安裝 uv(一次性,若尚未安裝)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. 同步依賴(uv 自動建立 .venv/)
uv sync --all-extras

# 4. 設定 API Key(可選,LLM 模式需要)
cp .env.example .env
# 編輯 .env 填入 OPENAI_API_KEY

# 5. 使用技能包
uv run python -m fa_improver input.pptx --eval eval.json --output improved.pptx

# 6. 跑測試
uv run pytest tests/
```

### 每次使用流程

```bash
# 進入目錄
cd .agents/skills/fa-report-improvement

# 直接用 uv run(不需要 activate)
uv run python -m fa_improver input.pptx --eval eval.json --output improved.pptx
```

---

## 🎓 總結

### 核心原則(v3.0.1)

1. **使用 uv**(取代 pip + venv)— 更快、更安全、更簡單
2. **每個專案獨立 .venv/** — 避免依賴衝突
3. **uv.lock 管理依賴** — 確保可重現
4. **.venv/ 不提交** — 每個人重建
5. **不需要 activate** — 用 `uv run` 就好
6. **定期 uv lock --upgrade** — 保持依賴更新

### 一句話總結

> **v3.0.1 起改用 uv:一個指令 `uv sync` 取代 `pip install + venv`,更快更穩定!** 🚀

---

## 📚 延伸閱讀

- [uv 官方文檔](https://docs.astral.sh/uv/)
- [Python 官方文檔 - venv](https://docs.python.org/3/library/venv.html)(向後相容參考)
- [pip 用戶指南](https://pip.pypa.io/en/stable/user_guide/)

---

**務必使用 uv!** 🚀

**版本**: 3.0.1
**最後更新**: 2026-08-31
