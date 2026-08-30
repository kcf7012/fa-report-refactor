"""OpenAI API Client"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .base import LLMAuthError, LLMClient, LLMError, LLMRateLimitError, LLMResponse, LLMTimeoutError


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

    api_key: Optional[str] = None
    model: str = "gpt-4o-mini"
    base_url: Optional[str] = None  # 自訂 endpoint(用於相容 API)
    timeout: float = 60.0  # 秒
    max_retries: int = 3

    # 統計
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    # 客戶端延遲初始化(避免 import 失敗時整個套件掛掉)
    _client: Any = field(default=None, init=False, repr=False)

    def _get_api_key(self) -> str:
        """取得 API key,優先使用傳入值,其次環境變數,最後 .env 檔案"""
        if self.api_key:
            return self.api_key

        # 嘗試從 .env 載入(同時搜尋當前目錄與上層)
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
                "找不到 OpenAI API key。"
                "請設定 OPENAI_API_KEY 環境變數、在 .env 檔案中提供，"
                "或在初始化時傳入 api_key。"
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
        """呼叫 OpenAI API"""
        client = self._get_client()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        # 重試邏輯
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
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
            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                # 認證錯誤(不重試)
                if "auth" in error_str or "api_key" in error_str or "401" in error_str:
                    raise LLMAuthError(f"OpenAI 認證失敗:{e}") from e

                # 速率限制(退避重試)
                if "rate" in error_str or "429" in error_str:
                    if attempt < self.max_retries - 1:
                        wait = 2 ** attempt
                        time.sleep(wait)
                        continue
                    raise LLMRateLimitError(f"OpenAI 速率限制:{e}") from e

                # 超時(重試)
                if "timeout" in error_str:
                    if attempt < self.max_retries - 1:
                        continue
                    raise LLMTimeoutError(f"OpenAI 請求超時:{e}") from e

                # 其他錯誤(重試一次)
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    continue
                raise LLMError(f"OpenAI API 錯誤:{e}") from e

        # 應不會到這裡
        raise LLMError(f"OpenAI 重試 {self.max_retries} 次後失敗:{last_error}")

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