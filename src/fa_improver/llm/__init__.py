"""LLM 整合層

提供可抽換的 LLM Client 抽象,支援:
- OpenAI API(官方與相容介面)
- Mock Client(離線測試用)
- 未來可擴充 Anthropic、Ollama 等
"""

from .base import LLMClient, LLMError, LLMResponse
from .evaluator import LLMEvaluator
from .mock_client import MockLLMClient

__all__ = ["LLMClient", "LLMError", "LLMResponse", "LLMEvaluator", "MockLLMClient"]
