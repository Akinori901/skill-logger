"""LLM 呼び出しサービス（httpx で直叩き。SDK は導入しない）。

fair-value-calculator/apps/ai の OpenAiClientService / GeminiClientService を
簡素化して移植（申請文生成に必要な chat() のみ）。

`settings.LLM_API_BASE_URL` が設定されていれば OpenAI 互換のベース URL を
上書きできる（eval-proxy 等への切替用）。
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from django.conf import settings

from apps.generation.domain.exceptions import AiApiKeyInvalidError


@dataclass
class LlmResponse:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int


class AbstractLlmClient:
    def chat(self, system_prompt: str, user_prompt: str) -> LlmResponse:
        raise NotImplementedError


class OpenAiClientService(AbstractLlmClient):
    """OpenAI Chat Completions API を httpx で直接呼び出す。"""

    _DEFAULT_BASE_URL = "https://api.openai.com/v1/chat/completions"
    _TIMEOUT = 60.0

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model
        override = getattr(settings, "LLM_API_BASE_URL", "")
        self._base_url = override or self._DEFAULT_BASE_URL

    def chat(self, system_prompt: str, user_prompt: str) -> LlmResponse:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 1500,
        }
        try:
            with httpx.Client(timeout=self._TIMEOUT) as client:
                resp = client.post(self._base_url, json=payload, headers=headers)

            if resp.status_code == 401:
                raise AiApiKeyInvalidError("API キーが無効です。設定ページで正しい API キーを登録してください。")
            resp.raise_for_status()

            data = resp.json()
            choice = data["choices"][0]
            usage = data.get("usage", {})
            return LlmResponse(
                content=choice["message"]["content"],
                model=data.get("model", self._model),
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
            )
        except AiApiKeyInvalidError:
            raise
        except httpx.TimeoutException as e:
            raise TimeoutError("LLM API がタイムアウトしました（60秒）") from e
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"LLM API エラー: {e.response.status_code}") from e


class GeminiClientService(AbstractLlmClient):
    """Google Gemini API を httpx で直接呼び出す。"""

    _BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    _TIMEOUT = 60.0

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    def chat(self, system_prompt: str, user_prompt: str) -> LlmResponse:
        url = f"{self._BASE_URL}/{self._model}:generateContent?key={self._api_key}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048},
        }
        try:
            with httpx.Client(timeout=self._TIMEOUT) as client:
                resp = client.post(url, json=payload)

            if resp.status_code in (401, 403):
                raise AiApiKeyInvalidError("Gemini API キーが無効です。設定ページで正しい API キーを登録してください。")
            resp.raise_for_status()

            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError("Gemini API から応答がありませんでした")
            content = candidates[0]["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})
            return LlmResponse(
                content=content,
                model=self._model,
                prompt_tokens=usage.get("promptTokenCount", 0),
                completion_tokens=usage.get("candidatesTokenCount", 0),
            )
        except AiApiKeyInvalidError:
            raise
        except httpx.TimeoutException as e:
            raise TimeoutError("Gemini API がタイムアウトしました（60秒）") from e
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Gemini API エラー: {e.response.status_code}") from e


class AnthropicClientService(AbstractLlmClient):
    """Anthropic Claude Messages API を httpx で直接呼び出す。

    モデルID例: claude-opus-4-8 / claude-sonnet-5 / claude-haiku-4-5。
    ※申請文生成は短文なので thinking は使わない（Opus 4.8 で budget_tokens は 400）。
    """

    _BASE_URL = "https://api.anthropic.com/v1/messages"
    _API_VERSION = "2023-06-01"
    _TIMEOUT = 60.0

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    def chat(self, system_prompt: str, user_prompt: str) -> LlmResponse:
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": self._API_VERSION,
            "content-type": "application/json",
        }
        payload = {
            "model": self._model,
            "max_tokens": 1500,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        try:
            with httpx.Client(timeout=self._TIMEOUT) as client:
                resp = client.post(self._BASE_URL, json=payload, headers=headers)

            if resp.status_code == 401:
                raise AiApiKeyInvalidError(
                    "Anthropic API キーが無効です。設定ページで正しい API キーを登録してください。"
                )
            resp.raise_for_status()

            data = resp.json()
            # content は複数ブロックの配列。type=="text" を連結する。
            text = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
            usage = data.get("usage", {})
            return LlmResponse(
                content=text,
                model=data.get("model", self._model),
                prompt_tokens=usage.get("input_tokens", 0),
                completion_tokens=usage.get("output_tokens", 0),
            )
        except AiApiKeyInvalidError:
            raise
        except httpx.TimeoutException as e:
            raise TimeoutError("Anthropic API がタイムアウトしました（60秒）") from e
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Anthropic API エラー: {e.response.status_code}") from e


def build_llm_client(provider: str, api_key: str, model: str) -> AbstractLlmClient:
    """provider に応じた LLM クライアントを生成する。"""
    if provider == "gemini":
        return GeminiClientService(api_key=api_key, model=model)
    if provider == "claude":
        return AnthropicClientService(api_key=api_key, model=model)
    return OpenAiClientService(api_key=api_key, model=model)
