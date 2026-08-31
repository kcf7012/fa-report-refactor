"""OpenAI API Client"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

from tenacity import (
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from .base import LLMAuthError, LLMError, LLMRateLimitError, LLMResponse, LLMTimeoutError

logger = logging.getLogger(__name__)


@dataclass
class OpenAIClient:
    """OpenAI API Client(也相容於其他 OpenAI 相容 API)

    支援環境:
    - 官方 OpenAI API
    - Azure OpenAI
    - Groq、Together、OpenRouter 等 OpenAI 相容介面

    使用方式:
        client = OpenAIClient(api_key="sk-...", model="gpt-4o-mini")
        response = client.complete(system, user, json_mode=True)

    或從環境變數讀取:
        export OPENAI_API_KEY=sk-...
        client = OpenAIClient()  # 自動讀取
    """

    api_key: str | None = None
    model: str = "gpt-4o-mini"
    base_url: str | None = None  # 自訂 endpoint(用於相容 API)
    timeout: float = 60.0  # 秒
    max_retries: int = 3
    redact_pii_before_send: bool = False  # 是否在送出前遮罩個資(預設關閉,保持向後相容)

    # 統計
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_redactions: int = 0

    skip_dotenv: bool = False  # 測試用:跳過 .env 載入

    # 客戶端延遲初始化(避免 import 失敗時整個套件掛掉)
    _client: Any = field(default=None, init=False, repr=False)

    def _get_api_key(self) -> str:
        """取得 API key,優先使用傳入值,其次環境變數,最後 .env 檔案"""
        if self.api_key:
            return self.api_key

        # 嘗試從 .env 載入(除非明確跳過,例如測試)
        if not self.skip_dotenv:
            try:
                from dotenv import find_dotenv, load_dotenv

                dotenv_path = find_dotenv(usecwd=True)
                if dotenv_path:
                    load_dotenv(dotenv_path=dotenv_path)
                else:
                    load_dotenv()  # fallback
            except ImportError:
                pass  # python-dotenv 未安裝,跳過

        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise LLMAuthError(
                "找不到 OpenAI API key。請設定 OPENAI_API_KEY 環境變數、在 .env 檔案中提供，或在初始化時傳入 api_key。"
            )
        return key

    def _get_client(self):
        """取得 OpenAI client(延遲初始化)"""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as e:
                raise LLMError(
                    "OpenAI 套件未安裝。請執行:\n"
                    "  uv pip install 'fa-improver[llm]'\n"
                    "或:\n"
                    "  pip install openai"
                ) from e

            kwargs = {"api_key": self._get_api_key(), "timeout": self.timeout}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = OpenAI(**kwargs)
        return self._client

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """呼叫 OpenAI API

        若 `redact_pii_before_send=True`,會在送出前自動遮罩 system 與 user 提示中的個資。

        重試策略(基於 tenacity):
        - 最大重試次數:`max_retries`(預設 3)
        - 退避策略:exponential(1s, 2s, 4s, ...最大 10s)
        - 認證錯誤(401 / auth / api_key)不重試
        - 其他錯誤皆重試,直到達到 max_retries
        """
        # 在送出前遮罩個資(若啟用)
        if self.redact_pii_before_send:
            from .redact import redact_pii_with_stats

            sys_result = redact_pii_with_stats(system_prompt)
            user_result = redact_pii_with_stats(user_prompt)
            system_prompt = sys_result.text
            user_prompt = user_result.text
            self.total_redactions += sys_result.stats.total + user_result.stats.total

        client = self._get_client()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        # 建立 tenacity Retrying 物件
        # retry_if_exception 只匹配「需要重試」的例外:認證錯誤以外的 Exception
        retrying = Retrying(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception(self._should_retry),
            reraise=True,
        )

        # 以迴圈手動驅動 tenacity
        try:
            for attempt in retrying:
                with attempt:
                    try:
                        return self._do_call(client, kwargs)
                    except Exception as e:
                        # 認證錯誤不重試
                        if not self._should_retry(e):
                            classified = self._classify_error(e)
                            raise classified from e
                        logger.warning(
                            "OpenAI 重試 (第 %s 次):%s", attempt.retry_state.attempt_number, e
                        )
                        raise
        except LLMAuthError:
            # 認證錯誤直接向上拋
            raise
        except (LLMRateLimitError, LLMTimeoutError):
            # 重試耗盡
            raise
        except Exception as e:
            # 其他錯誤 — 分類後再拋
            classified = self._classify_error(e)
            raise classified from e

        # 理論上不會到這裡
        raise LLMError(f"OpenAI 重試 {self.max_retries} 次後失敗")

    def _do_call(self, client: Any, kwargs: dict[str, Any]) -> LLMResponse:
        """實際呼叫 OpenAI API(被 tenacity 重試的單次呼叫)"""
        response = client.chat.completions.create(**kwargs)
        self.total_calls += 1

        # 取得 token 使用
        usage = response.usage
        if usage:
            self.total_input_tokens += usage.prompt_tokens
            self.total_output_tokens += usage.completion_tokens

        # 取得內容
        choice = response.choices[0]
        content = choice.message.content or ""

        return LLMResponse(
            content=content,
            model=response.model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            finish_reason=choice.finish_reason or "",
            raw=response.model_dump() if hasattr(response, "model_dump") else {},
        )

    def _classify_error(self, exc: Exception) -> Exception:
        """將原始例外分類為 LLMAuthError / LLMRateLimitError / LLMTimeoutError / LLMError

        Args:
            exc: 原始例外

        Returns:
            對應的 LLM 子類別例外(若適用)
        """
        error_str = str(exc).lower()

        # 認證錯誤(不重試)
        if "auth" in error_str or "api_key" in error_str or "401" in error_str:
            return LLMAuthError(f"OpenAI 認證失敗:{exc}")

        # 速率限制
        if "rate" in error_str or "429" in error_str:
            return LLMRateLimitError(f"OpenAI 速率限制:{exc}")

        # 超時
        if "timeout" in error_str:
            return LLMTimeoutError(f"OpenAI 請求超時:{exc}")

        # 其他錯誤
        return LLMError(f"OpenAI API 錯誤:{exc}")

    def _should_retry(self, exc: Exception) -> bool:
        """判斷錯誤是否應重試

        認證錯誤永不重試;其他錯誤皆重試。
        """
        error_str = str(exc).lower()
        is_auth = "auth" in error_str or "api_key" in error_str or "401" in error_str
        return not is_auth

    @property
    def total_cost_usd(self) -> float:
        """總成本估算(GPT-4o-mini 定價)"""
        input_cost = self.total_input_tokens * 0.15 / 1_000_000
        output_cost = self.total_output_tokens * 0.60 / 1_000_000
        return input_cost + output_cost

    def reset_stats(self) -> None:
        """重置統計"""
        self.total_calls = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_redactions = 0
