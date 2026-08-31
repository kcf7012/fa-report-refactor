"""LLM 整合層

提供可抽換的 LLM Client 抽象,支援:
- OpenAI API(官方與相容介面)
- Mock Client(離線測試用)
- 未來可擴充 Anthropic、Ollama 等

個資遮罩:
- 在送出前自動遮罩電話、Email、中文姓名、IP、工號、身分證、信用卡
- 使用方式:`from fa_improver.llm.redact import redact_pii`
"""

from .base import LLMClient, LLMError, LLMResponse
from .evaluator import LLMEvaluator
from .mock_client import MockLLMClient
from .redact import (
    RedactionResult,
    RedactionStats,
    is_pii_present,
    redact_pii,
    redact_pii_with_stats,
)

__all__ = [
    "LLMClient",
    "LLMError",
    "LLMResponse",
    "LLMEvaluator",
    "MockLLMClient",
    "RedactionResult",
    "RedactionStats",
    "is_pii_present",
    "redact_pii",
    "redact_pii_with_stats",
]
