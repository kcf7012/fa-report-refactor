# Phase 5: 最終發布準備 TODO

## 目標
把 v3.0 從「可用」提升為「可發布」,包含 CI/CD、文件、版本標記。

## 子任務

### 5.1 整合 .ppt 轉換支援
- [ ] 讓 CLI 支援 .ppt 輸入(目前只支援 .pptx)
- [ ] LibreOffice / pywin32 自動偵測
- [ ] 轉換失敗時明確錯誤訊息
- [ ] 整合 `scripts/improve_fa_report.py` 為 thin wrapper

### 5.2 uv 整合
- [ ] 執行 `uv lock` 產生 `uv.lock`
- [ ] 確認 `uv sync` 可正常運作
- [ ] 文件化 uv 安裝方式

### 5.3 CI/CD
- [ ] `.github/workflows/test.yml`(跑 pytest)
- [ ] 母片保護必須通過才能 merge
- [ ] 覆蓋率上傳(可選 codecov)

### 5.4 文件化
- [ ] 更新 `SKILL.md` 反映 v3.0 新特性
- [ ] 寫 CHANGELOG.md(正式版)
- [ ] README 加入快速開始指南
- [ ] API 文件(可選)

### 5.5 版本標記
- [ ] 標記 `v3.0.0` tag
- [ ] 移除 `baseline-v2.3.0` tag(已過時)

### 5.6 發布檢查清單
- [ ] 92 個測試全部通過
- [ ] 母片保護 100%
- [ ] 端對端 LLM 測試成功
- [ ] .ppt 轉換支援測試
- [ ] 文件完整
- [ ] pyproject.toml 套件可安裝

## 預估工時
4-6 小時

## 成功標準
- v3.0 可獨立打包分發(uv build)
- CI 自動跑測試並驗證母片保護
- SKILL.md / README 反映 v3.0 新架構
- 任何團隊 clone 後 `uv sync && uv run pytest` 就能運作