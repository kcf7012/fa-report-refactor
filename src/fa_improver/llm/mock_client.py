"""Mock LLM Client — 用於離線測試"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from .base import LLMClient, LLMResponse


@dataclass
class MockLLMClient:
    """Mock LLM Client

    支援預錄回應(基於 prompt 模式匹配)。
    適用於:
    - 單元測試(無需真實 API)
    - 開發期間離線測試
    - Demo 展示
    """

    # 預錄回應:prompt 模式 → 回應
    responses: Dict[str, str] = field(default_factory=dict)

    # 預設回應(無匹配時使用)
    default_response: str = '{"status": "ok", "message": "Mock response"}'

    # 統計
    call_count: int = 0
    total_tokens: int = 0

    # 可選的回應產生函式(動態生成)
    response_fn: Optional[Callable[[str, str, bool], str]] = None

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """回應 prompt(從預錄或動態函式)"""
        self.call_count += 1

        if self.response_fn:
            content = self.response_fn(system_prompt, user_prompt, json_mode)
        else:
            content = self._match_response(system_prompt, user_prompt)

        # 估算 token(粗略)
        estimated_input = (len(system_prompt) + len(user_prompt)) // 4
        estimated_output = len(content) // 4
        self.total_tokens += estimated_input + estimated_output

        return LLMResponse(
            content=content,
            model="mock-gpt-4o",
            prompt_tokens=estimated_input,
            completion_tokens=estimated_output,
            total_tokens=estimated_input + estimated_output,
            finish_reason="stop",
        )

    def _match_response(self, system_prompt: str, user_prompt: str) -> str:
        """從預錄回應中匹配"""
        for pattern, response in self.responses.items():
            if pattern in system_prompt or pattern in user_prompt:
                return response
        return self.default_response

    def add_response(self, pattern: str, response: str) -> None:
        """新增預錄回應"""
        self.responses[pattern] = response

    def with_failing(self, error: Exception) -> "MockLLMClient":
        """設定讓 client 拋出錯誤(用於錯誤處理測試)"""
        original_complete = self.complete

        def failing_complete(*args, **kwargs):
            raise error

        self.complete = failing_complete  # type: ignore[method-assign]
        return self