"""OpenAI API Key 載入測試 — 確保所有讀取路徑都支援 .env"""

import os
from pathlib import Path

import pytest
from fa_improver.llm.openai_client import OpenAIClient


class TestEnvFileLoading:
    """確認 .env 檔案正確載入"""

    def test_env_file_loaded_for_api_key(self, tmp_path, monkeypatch):
        """從 .env 載入 API key"""
        # 清除環境變數
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        # 建立 .env 檔案
        env_file = tmp_path / ".env"
        env_file.write_text("OPENAI_API_KEY=sk-from-env-file\n")

        # 改變工作目錄到 tmp_path(load_dotenv 預設從當前目錄載入)
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            client = OpenAIClient()
            key = client._get_api_key()
            assert key == "sk-from-env-file"
        finally:
            os.chdir(original_cwd)

    def test_explicit_api_key_overrides_env(self, tmp_path, monkeypatch):
        """明確傳入的 API key 優先於 .env"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        env_file = tmp_path / ".env"
        env_file.write_text("OPENAI_API_KEY=sk-from-env-file\n")

        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            client = OpenAIClient(api_key="sk-explicit")
            key = client._get_api_key()
            assert key == "sk-explicit"
        finally:
            os.chdir(original_cwd)

    def test_env_var_overrides_env_file(self, tmp_path, monkeypatch):
        """環境變數優先於 .env 檔案"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env-var")

        env_file = tmp_path / ".env"
        env_file.write_text("OPENAI_API_KEY=sk-from-env-file\n")

        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            client = OpenAIClient()
            key = client._get_api_key()
            # load_dotenv 預設不覆蓋已有環境變數
            assert key == "sk-from-env-var"
        finally:
            os.chdir(original_cwd)

    def test_missing_api_key_raises(self, monkeypatch):
        """缺少 API key 時應拋出明確錯誤"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        # 使用 skip_dotenv=True 避免 .env 干擾
        client = OpenAIClient(skip_dotenv=True)
        with pytest.raises(Exception) as exc_info:
            client._get_api_key()
        assert "OPENAI_API_KEY" in str(exc_info.value)

    def test_env_file_with_comments(self, tmp_path, monkeypatch):
        """.env 檔案支援註解"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        env_file = tmp_path / ".env"
        env_file.write_text("# 這是註解\nOPENAI_API_KEY=sk-with-comments\n# 另一行註解\n")

        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            client = OpenAIClient()
            key = client._get_api_key()
            assert key == "sk-with-comments"
        finally:
            os.chdir(original_cwd)

    def test_env_file_with_quotes(self, tmp_path, monkeypatch):
        """.env 檔案支援引號"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        env_file = tmp_path / ".env"
        env_file.write_text('OPENAI_API_KEY="sk-with-quotes"\n')

        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            client = OpenAIClient()
            key = client._get_api_key()
            assert key == "sk-with-quotes"
        finally:
            os.chdir(original_cwd)


class TestEnvExampleFile:
    """確認 .env.example 存在且格式正確"""

    def test_env_example_exists(self):
        """.env.example 檔案應存在於專案根目錄"""
        env_example = Path(__file__).parent.parent.parent / ".env.example"
        assert env_example.exists(), f".env.example 不存在於 {env_example}"

    def test_env_example_has_openai_key(self):
        """.env.example 應包含 OPENAI_API_KEY 範例"""
        env_example = Path(__file__).parent.parent.parent / ".env.example"
        content = env_example.read_text(encoding="utf-8")
        assert "OPENAI_API_KEY" in content

    def test_env_example_has_instructions(self):
        """.env.example 應包含設定說明"""
        env_example = Path(__file__).parent.parent.parent / ".env.example"
        content = env_example.read_text(encoding="utf-8")
        # 應有複製說明
        assert "cp" in content.lower() or "copy" in content.lower()


class TestGitignoreProtection:
    """確認 .env 不會被 commit"""

    def test_env_in_gitignore(self):
        """.env 應被 .gitignore 排除"""
        gitignore = Path(__file__).parent.parent.parent / ".gitignore"
        content = gitignore.read_text(encoding="utf-8")
        # 應有 .env 規則
        lines = [
            line.strip()
            for line in content.split("\n")
            if line.strip() and not line.startswith("#")
        ]
        env_rules = [line for line in lines if line.startswith(".env") or ".env" in line]
        assert len(env_rules) > 0, ".env 應在 .gitignore 中排除"
        # .env.example 應明確不被排除
        assert any("!.env.example" in line for line in env_rules), ".env.example 應保留不被忽略"
