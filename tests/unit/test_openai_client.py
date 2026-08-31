"""OpenAI Client 測試(使用 Mock,不需要真實 API)"""

from unittest.mock import MagicMock, patch

import pytest
from fa_improver.llm.base import LLMAuthError
from fa_improver.llm.openai_client import OpenAIClient


class TestOpenAIClientBasics:
    """基本測試"""

    def test_init_with_api_key(self):
        """直接傳入 API key"""
        client = OpenAIClient(api_key="sk-test-123")
        assert client.api_key == "sk-test-123"
        assert client.model == "gpt-4o-mini"

    def test_init_custom_model(self):
        """自訂模型"""
        client = OpenAIClient(api_key="sk-test", model="gpt-4o")
        assert client.model == "gpt-4o"

    def test_init_custom_base_url(self):
        """自訂 base URL(用於相容 API)"""
        client = OpenAIClient(
            api_key="sk-test",
            base_url="https://api.groq.com/openai/v1",
        )
        assert client.base_url == "https://api.groq.com/openai/v1"


class TestOpenAIClientAuth:
    """認證測試"""

    def test_missing_api_key_raises(self, monkeypatch):
        """缺少 API key 應拋出 LLMAuthError"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        client = OpenAIClient(skip_dotenv=True)
        with pytest.raises(LLMAuthError, match="找不到"):
            client._get_api_key()

    def test_api_key_from_env(self, monkeypatch):
        """從環境變數讀取 API key"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env")
        client = OpenAIClient()
        assert client._get_api_key() == "sk-from-env"

    def test_api_key_explicit_overrides_env(self, monkeypatch):
        """明確傳入的 key 優先於環境變數"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env")
        client = OpenAIClient(api_key="sk-explicit")
        assert client._get_api_key() == "sk-explicit"


class TestOpenAIClientComplete:
    """complete() 測試(用 Mock 模擬 OpenAI)"""

    @patch("openai.OpenAI")
    def test_successful_call(self, mock_openai_class):
        """成功呼叫"""
        # 設定 mock 回應
        mock_response = MagicMock()
        mock_response.model = "gpt-4o-mini"
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"result": "ok"}'
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150

        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client_instance

        client = OpenAIClient(api_key="sk-test")
        response = client.complete("system", "user", json_mode=True)

        assert response.content == '{"result": "ok"}'
        assert response.prompt_tokens == 100
        assert response.completion_tokens == 50

    @patch("openai.OpenAI")
    def test_auth_error_raises_immediately(self, mock_openai_class):
        """認證錯誤應立即拋出 LLMAuthError(不重試)"""
        # 建立一個會產生認證錯誤的 mock
        mock_client_instance = MagicMock()
        call_count = {"n": 0}

        def raise_auth_error(*args, **kwargs):
            call_count["n"] += 1
            err = Exception("Error code: 401 - Invalid API key")
            raise err

        mock_client_instance.chat.completions.create.side_effect = raise_auth_error
        mock_openai_class.return_value = mock_client_instance

        client = OpenAIClient(api_key="bad-key", max_retries=3)
        with pytest.raises(LLMAuthError):
            client.complete("sys", "user")
        # 認證錯誤不應重試
        assert call_count["n"] == 1

    @patch("openai.OpenAI")
    def test_rate_limit_retries(self, mock_openai_class):
        """速率限制會重試"""
        mock_client_instance = MagicMock()
        call_count = {"n": 0}

        success_response = MagicMock()
        success_response.model = "gpt-4o-mini"
        success_response.choices = [MagicMock()]
        success_response.choices[0].message.content = "ok"
        success_response.choices[0].finish_reason = "stop"
        success_response.usage.prompt_tokens = 10
        success_response.usage.completion_tokens = 5
        success_response.usage.total_tokens = 15

        def maybe_rate_limit(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise Exception("Error code: 429 - Rate limit exceeded")
            return success_response

        mock_client_instance.chat.completions.create.side_effect = maybe_rate_limit
        mock_openai_class.return_value = mock_client_instance

        client = OpenAIClient(api_key="sk-test", max_retries=3)
        response = client.complete("sys", "user")

        assert response.content == "ok"
        assert call_count["n"] == 2


class TestOpenAIClientStats:
    """統計測試"""

    @patch("openai.OpenAI")
    def test_token_stats_accumulate(self, mock_openai_class):
        """Token 統計累積"""
        mock_response = MagicMock()
        mock_response.model = "gpt-4o-mini"
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "ok"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150

        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client_instance

        client = OpenAIClient(api_key="sk-test")
        client.complete("sys", "user")
        client.complete("sys", "user")
        client.complete("sys", "user")

        assert client.total_calls == 3
        assert client.total_input_tokens == 300
        assert client.total_output_tokens == 150
        assert client.total_cost_usd > 0

    def test_reset_stats(self):
        """重置統計"""
        client = OpenAIClient(api_key="sk-test")
        client.total_calls = 5
        client.total_input_tokens = 100
        client.reset_stats()
        assert client.total_calls == 0
        assert client.total_input_tokens == 0


class TestOpenAIClientRetry:
    """重試機制測試(基於 tenacity)"""

    def _make_success_response(self):
        """建立一個成功的 mock response"""
        mock_response = MagicMock()
        mock_response.model = "gpt-4o-mini"
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "ok"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        return mock_response

    @patch("openai.OpenAI")
    def test_tenacity_retries_on_transient_error(self, mock_openai_class):
        """瞬時錯誤應重試(tenacity exponential backoff)"""
        mock_client_instance = MagicMock()
        call_count = {"n": 0}

        success_response = self._make_success_response()

        def transient_then_success(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise Exception("Connection reset by peer")
            return success_response

        mock_client_instance.chat.completions.create.side_effect = transient_then_success
        mock_openai_class.return_value = mock_client_instance

        client = OpenAIClient(api_key="sk-test", max_retries=3)
        response = client.complete("sys", "user")

        assert response.content == "ok"
        # 第 1、2 次失敗,第 3 次成功
        assert call_count["n"] == 3

    @patch("openai.OpenAI")
    def test_tenacity_max_retries_exhausted(self, mock_openai_class):
        """重試耗盡後拋出 LLMError"""
        mock_client_instance = MagicMock()

        def always_fail(*args, **kwargs):
            raise Exception("Server error 500")

        mock_client_instance.chat.completions.create.side_effect = always_fail
        mock_openai_class.return_value = mock_client_instance

        from fa_improver.llm.base import LLMError

        client = OpenAIClient(api_key="sk-test", max_retries=3)
        with pytest.raises(LLMError, match="OpenAI API 錯誤"):
            client.complete("sys", "user")

    @patch("openai.OpenAI")
    def test_tenacity_rate_limit_retries(self, mock_openai_class):
        """速率限制應重試(tenacity)"""
        mock_client_instance = MagicMock()
        call_count = {"n": 0}
        success_response = self._make_success_response()

        def rate_limit_then_success(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise Exception("Error 429 - Rate limit")
            return success_response

        mock_client_instance.chat.completions.create.side_effect = rate_limit_then_success
        mock_openai_class.return_value = mock_client_instance

        client = OpenAIClient(api_key="sk-test", max_retries=3)
        response = client.complete("sys", "user")
        assert response.content == "ok"
        assert call_count["n"] == 2

    @patch("openai.OpenAI")
    def test_tenacious_timeout_retries(self, mock_openai_class):
        """超時錯誤應重試"""
        mock_client_instance = MagicMock()
        call_count = {"n": 0}
        success_response = self._make_success_response()

        def timeout_then_success(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] < 2:
                raise Exception("Request timeout")
            return success_response

        mock_client_instance.chat.completions.create.side_effect = timeout_then_success
        mock_openai_class.return_value = mock_client_instance

        client = OpenAIClient(api_key="sk-test", max_retries=3)
        response = client.complete("sys", "user")
        assert response.content == "ok"
        assert call_count["n"] == 2


class TestOpenAIClientErrorClassification:
    """錯誤分類測試"""

    def test_classify_auth_error(self):
        """認證錯誤分類為 LLMAuthError"""
        from fa_improver.llm.base import LLMAuthError

        client = OpenAIClient(api_key="sk-test")
        classified = client._classify_error(Exception("401 Invalid API key"))
        assert isinstance(classified, LLMAuthError)

    def test_classify_rate_limit_error(self):
        """速率限制分類為 LLMRateLimitError"""
        from fa_improver.llm.base import LLMRateLimitError

        client = OpenAIClient(api_key="sk-test")
        classified = client._classify_error(Exception("429 Too Many Requests"))
        assert isinstance(classified, LLMRateLimitError)

    def test_classify_timeout_error(self):
        """超時分類為 LLMTimeoutError"""
        from fa_improver.llm.base import LLMTimeoutError

        client = OpenAIClient(api_key="sk-test")
        classified = client._classify_error(Exception("Request timeout"))
        assert isinstance(classified, LLMTimeoutError)

    def test_classify_generic_error(self):
        """其他錯誤分類為 LLMError"""
        from fa_improver.llm.base import LLMError

        client = OpenAIClient(api_key="sk-test")
        classified = client._classify_error(Exception("Something went wrong"))
        assert isinstance(classified, LLMError)

    def test_should_retry_skips_auth(self):
        """認證錯誤不重試"""
        client = OpenAIClient(api_key="sk-test")
        assert client._should_retry(Exception("401 Unauthorized")) is False
        assert client._should_retry(Exception("Invalid api_key")) is False

    def test_should_retry_allows_others(self):
        """其他錯誤可重試"""
        client = OpenAIClient(api_key="sk-test")
        assert client._should_retry(Exception("500 Server Error")) is True
        assert client._should_retry(Exception("timeout")) is True
        assert client._should_retry(Exception("rate limit")) is True
