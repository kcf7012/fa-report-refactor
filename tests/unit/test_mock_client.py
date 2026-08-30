"""Mock LLM Client 測試"""

import pytest

from fa_improver.llm.base import LLMAuthError, LLMError
from fa_improver.llm.mock_client import MockLLMClient


class TestMockLLMClient:
    """Mock Client 測試"""

    def test_default_response(self):
        """無預錄時回傳預設回應"""
        client = MockLLMClient()
        response = client.complete("system", "user")
        assert "Mock" in response.content or "ok" in response.content

    def test_matched_response(self):
        """匹配預錄回應"""
        client = MockLLMClient()
        client.add_response("半導體", '{"score": 90}')
        response = client.complete("這是半導體報告", "user")
        assert response.content == '{"score": 90}'

    def test_call_count(self):
        """呼叫次數計數"""
        client = MockLLMClient()
        client.complete("sys", "user")
        client.complete("sys", "user")
        client.complete("sys", "user")
        assert client.call_count == 3

    def test_token_estimation(self):
        """token 估算"""
        client = MockLLMClient()
        client.add_response("x", "y" * 1000)
        response = client.complete("sys", "user")
        assert response.completion_tokens > 0
        assert response.total_tokens > 0

    def test_response_fn(self):
        """自訂回應函式"""
        def custom_fn(sys_p, user_p, json_mode):
            return f"echo: {user_p}"

        client = MockLLMClient(response_fn=custom_fn)
        response = client.complete("sys", "hello")
        assert response.content == "echo: hello"

    def test_failing_client(self):
        """失敗的 mock(用於錯誤處理測試)"""
        client = MockLLMClient().with_failing(LLMAuthError("bad key"))
        with pytest.raises(LLMAuthError, match="bad key"):
            client.complete("sys", "user")

    def test_response_structure(self):
        """回應結構正確"""
        client = MockLLMClient()
        response = client.complete("sys", "user")
        assert response.model == "mock-gpt-4o"
        assert response.finish_reason == "stop"
        assert isinstance(response.content, str)