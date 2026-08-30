# Python 虛擬環境最佳實踐指南

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

### 使用虛擬環境的好處

✅ **完全隔離**:
```
每個專案獨立環境
不同版本可以共存
互不干擾
```

✅ **保持乾淨**:
```
全局 Python 保持原始狀態
專案環境各自管理
刪除專案 = 刪除環境
```

✅ **無需權限**:
```
創建在用戶目錄
不需要 sudo/admin
安全可靠
```

✅ **可重現**:
```
requirements.txt 記錄依賴
任何人都能重建相同環境
CI/CD 部署一致
```

---

## 🚀 虛擬環境完整指南

### 1. 創建虛擬環境

```bash
# 進入專案目錄
cd ~/.claude/skills/fa-report-improvement

# 創建虛擬環境 (使用 venv 模組)
python -m venv venv

# 或指定 Python 版本
python3.9 -m venv venv

# 創建完成後的目錄結構
# fa-report-improvement/
# ├── venv/              ← 新創建的虛擬環境
# │   ├── bin/          (Linux/macOS)
# │   ├── Scripts/      (Windows)
# │   ├── lib/
# │   └── ...
# ├── SKILL.md
# ├── requirements.txt
# └── ...
```

**只需創建一次**，之後每次使用前啟動即可。

### 2. 啟動虛擬環境

**Linux / macOS**:
```bash
source venv/bin/activate
```

**Windows (CMD)**:
```cmd
venv\Scripts\activate.bat
```

**Windows (PowerShell)**:
```powershell
venv\Scripts\Activate.ps1
```

**成功啟動的標誌**:
```bash
# 提示符前會出現 (venv)
(venv) user@host:~/fa-report-improvement$
```

### 3. 安裝依賴 (在虛擬環境中)

```bash
# 確認在虛擬環境中 (看到 venv 前綴)
(venv) $ pip install -r requirements.txt

# 或執行安裝腳本
(venv) $ python scripts/install.py
```

### 4. 使用 Skill (在虛擬環境中)

```bash
(venv) $ python scripts/improve_fa_report.py input.ppt eval.json output.pptx
```

### 5. 退出虛擬環境

```bash
(venv) $ deactivate

# 提示符恢復正常
user@host:~/fa-report-improvement$
```

---

## 📋 常用命令速查

```bash
# 創建虛擬環境
python -m venv venv

# 啟動虛擬環境
source venv/bin/activate           # Linux/macOS
venv\Scripts\activate              # Windows

# 檢查當前環境
which python                       # 查看 Python 路徑
pip list                          # 查看已安裝套件

# 安裝套件
pip install -r requirements.txt    # 安裝所有依賴
pip install package_name          # 安裝單個套件

# 更新套件
pip install --upgrade package_name

# 導出依賴 (用於分享)
pip freeze > requirements.txt

# 退出虛擬環境
deactivate

# 刪除虛擬環境
rm -rf venv                       # Linux/macOS
rmdir /s venv                     # Windows
```

---

## 🔍 檢查是否在虛擬環境中

### 方法 1: 查看提示符

```bash
# 在虛擬環境中
(venv) user@host:~$

# 不在虛擬環境中
user@host:~$
```

### 方法 2: 檢查 Python 路徑

```bash
which python
# 虛擬環境: /home/user/.claude/skills/fa-report-improvement/venv/bin/python
# 全局環境: /usr/bin/python 或 /usr/local/bin/python
```

```bash
# Windows
where python
# 虛擬環境: C:\Users\user\.claude\skills\fa-report-improvement\venv\Scripts\python.exe
# 全局環境: C:\Python39\python.exe
```

### 方法 3: 使用 Python 代碼

```python
import sys
print(sys.prefix)
# 虛擬環境: /path/to/fa-report-improvement/venv
# 全局環境: /usr 或 /usr/local
```

---

## ⚠️ 常見錯誤與解決

### 錯誤 1: 忘記啟動虛擬環境

**症狀**:
```bash
$ python scripts/install.py
ModuleNotFoundError: No module named 'pptx'
```

**原因**: 在全局環境執行，沒有安裝依賴

**解決**:
```bash
# 啟動虛擬環境
source venv/bin/activate

# 再執行
(venv) $ python scripts/install.py
```

### 錯誤 2: PowerShell 執行策略限制 (Windows)

**症狀**:
```
無法載入檔案 venv\Scripts\Activate.ps1，因為這個系統上已停用指令碼執行。
```

**解決**:
```powershell
# 方法 1: 暫時允許
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# 方法 2: 使用 CMD
venv\Scripts\activate.bat

# 方法 3: 使用繞過
PowerShell -ExecutionPolicy Bypass -File venv\Scripts\Activate.ps1
```

### 錯誤 3: 虛擬環境損壞

**症狀**:
```
Error: Command '...' returned non-zero exit status 1
```

**解決**:
```bash
# 刪除舊環境
rm -rf venv

# 重新創建
python -m venv venv

# 重新安裝
source venv/bin/activate
pip install -r requirements.txt
```

### 錯誤 4: pip 版本過舊

**症狀**:
```
ERROR: Could not find a version that satisfies the requirement...
```

**解決**:
```bash
# 在虛擬環境中升級 pip
(venv) $ python -m pip install --upgrade pip

# 再安裝依賴
(venv) $ pip install -r requirements.txt
```

---

## 🎯 最佳實踐

### 1. 每個專案一個虛擬環境

```
✅ 好的做法
~/projects/
├── project-a/
│   ├── venv/
│   └── ...
├── project-b/
│   ├── venv/
│   └── ...
└── project-c/
    ├── venv/
    └── ...

❌ 不好的做法
~/venv/           # 共用虛擬環境 → 依賴衝突
~/projects/
├── project-a/
├── project-b/
└── project-c/
```

### 2. 虛擬環境目錄命名

```bash
# 推薦命名
venv/            # 標準、簡單
.venv/           # 隱藏目錄，避免干擾
env/             # 也可以
virtualenv/      # 較長但清晰

# 避免
myenv/           # 不夠標準
python-env/      # 太長
test/            # 容易混淆
```

### 3. 將虛擬環境加入 .gitignore

```gitignore
# .gitignore
venv/
.venv/
env/
*.pyc
__pycache__/
```

**為什麼?**
- 虛擬環境是本地的
- 不應該提交到版本控制
- 每個人根據 requirements.txt 重建

### 4. 使用 requirements.txt 管理依賴

```bash
# 導出當前環境依賴
(venv) $ pip freeze > requirements.txt

# 他人重建環境
(venv) $ pip install -r requirements.txt
```

### 5. 定期更新虛擬環境

```bash
# 更新所有套件
(venv) $ pip install --upgrade -r requirements.txt

# 或重建環境
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📊 虛擬環境 vs 全局安裝對比

| 特性 | 虛擬環境 | 全局安裝 |
|------|---------|---------|
| **依賴隔離** | ✅ 完全隔離 | ❌ 共用依賴 |
| **版本衝突** | ✅ 不會衝突 | ❌ 容易衝突 |
| **系統乾淨** | ✅ 不污染系統 | ❌ 污染系統 |
| **需要權限** | ✅ 不需要 | ❌ 需要 sudo/admin |
| **易於刪除** | ✅ 刪除目錄即可 | ❌ 難以清理 |
| **可重現** | ✅ 完全可重現 | ❌ 難以重現 |
| **CI/CD** | ✅ 一致環境 | ❌ 不一致 |
| **多版本共存** | ✅ 支持 | ❌ 不支持 |

---

## 🛠️ 進階技巧

### 1. 指定 Python 版本

```bash
# 使用特定 Python 版本
python3.9 -m venv venv
python3.10 -m venv venv

# 驗證版本
source venv/bin/activate
python --version
```

### 2. 複製虛擬環境

```bash
# 導出依賴
(venv) $ pip freeze > requirements.txt

# 在新機器上重建
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 虛擬環境套在虛擬環境 (不推薦)

```bash
# 不要這樣做!
(venv1) $ python -m venv venv2  # ❌

# 應該先退出
(venv1) $ deactivate
$ python -m venv venv2          # ✅
```

### 4. 使用別名簡化操作

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
alias venv-activate='source venv/bin/activate'
alias venv-create='python -m venv venv'

# 使用
$ venv-create
$ venv-activate
```

---

## 📝 FA Report Improvement Skill 特定指南

### 標準安裝流程

```bash
# 1. 解壓 skill
cd ~/.claude/skills/
unzip fa-report-improvement-v2.0-final.skill
cd fa-report-improvement

# 2. 創建虛擬環境 (只需一次)
python -m venv venv

# 3. 啟動虛擬環境
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 4. 安裝依賴
pip install -r requirements.txt

# 5. 執行安裝腳本 (會檢查虛擬環境)
python scripts/install.py

# 6. 使用 skill
python scripts/improve_fa_report.py input.ppt eval.json output.pptx

# 7. 完成後退出
deactivate
```

### 每次使用流程

```bash
# 進入目錄
cd ~/.claude/skills/fa-report-improvement

# 啟動虛擬環境
source venv/bin/activate

# 使用 skill
python scripts/improve_fa_report.py ...

# 完成後退出
deactivate
```

---

## 🎓 總結

### 核心原則

1. **務必使用虛擬環境** - 不是推薦，是必須
2. **每個專案獨立環境** - 避免依賴衝突
3. **requirements.txt 管理依賴** - 確保可重現
4. **虛擬環境不提交** - 每個人重建
5. **定期更新清理** - 保持環境乾淨

### 一句話總結

> **使用虛擬環境是 Python 開發的最佳實踐，務必遵守，可以避免 90% 以上的依賴問題!** 🎯

---

## 📚 延伸閱讀

- [Python 官方文檔 - venv](https://docs.python.org/3/library/venv.html)
- [pip 用戶指南](https://pip.pypa.io/en/stable/user_guide/)
- [Python 虛擬環境指南](https://realpython.com/python-virtual-environments-a-primer/)

---

**務必使用虛擬環境!** 🛡️

**版本**: 2.1.3  
**最後更新**: 2026-01-28
