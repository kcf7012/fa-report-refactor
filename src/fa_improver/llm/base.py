"""LLM Client 抽象層"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol


@dataclass
class LLMResponse:
    """LLM 回應結構"""

    content: str  # 主要回應內容(JSON 或文字)
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = ""

    # 原始回應(供除錯)
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def estimated_cost_usd(self) -> float:
        """粗估成本(僅供參考,需依實際定價)

        預設 GPT-4o 定價:
        - input: $2.50 / 1M tokens
        - output: $10.00 / 1M tokens
        """
        input_cost = self.prompt_tokens * 2.50 / 1_000_000
        output_cost = self.completion_tokens * 10.00 / 1_000_000
        return input_cost + output_cost


class LLMClient(Protocol):
    """所有 LLM provider 都應實作此介面"""

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """發送 prompt 並取得回應

        Args:
            system_prompt: 系統指令
            user_prompt: 使用者輸入
            json_mode: 是否要求 JSON 格式輸出
            temperature: 0 = 確定性, 1 = 最大隨機性
        """
        ...


class LLMError(Exception):
    """LLM 錯誤"""

    pass


class LLMAuthError(LLMError):
    """認證錯誤(API key 無效)"""

    pass


class LLMRateLimitError(LLMError):
    """速率限制"""

    pass


class LLMTimeoutError(LLMError):
    """超時"""

    pass