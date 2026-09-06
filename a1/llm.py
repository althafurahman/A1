"""Chat-completions client for the team's model endpoint. Temperature 0, retries, usage.

The team's model access is the GCP credits (e.g. a Vertex AI endpoint serving
qwen3.8-27b on the team project). Point A1_API_BASE at the endpoint's base URL and
A1_API_KEY at its bearer token; any provider speaking the standard chat-completions
schema works unchanged.
"""

import asyncio
import os
import time

import httpx

MODEL = "qwen/qwen3.8-27b"
MAX_RETRIES = 4
TRACE_PROMPT_CAP = 20_000  # SUBMISSION.md allows truncating workbook serialisations in traces


class LLMError(Exception):
    pass


class FatalLLMError(LLMError):
    """Not worth retrying (bad key, bad request)."""


class Client:
    def __init__(self, model: str = MODEL, timeout: float = 420.0):
        key = os.environ.get("A1_API_KEY")
        base = os.environ.get("A1_API_BASE", "").rstrip("/")
        if not key or not base:
            raise LLMError("set A1_API_BASE and A1_API_KEY to the team's model endpoint (see .env.example)")
        self.url = f"{base}/chat/completions"
        self.model = model
        self._http = httpx.AsyncClient(
            timeout=timeout,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )

    async def close(self):
        await self._http.aclose()

    async def complete(self, system: str, user: str, max_tokens: int = 24_576, effort: str | None = None) -> dict:
        """One call. Returns a trace record with text/tokens/latency; raises LLMError after retries."""
        payload = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        started = time.time()
        last_err = None
        for attempt in range(MAX_RETRIES):
            try:
                r = await self._http.post(self.url, json=payload)
                if r.status_code in (429, 500, 502, 503, 529):
                    raise LLMError(f"HTTP {r.status_code}: {r.text[:200]}")
                if 400 <= r.status_code < 500:  # auth/validation: retrying cannot help
                    raise FatalLLMError(f"HTTP {r.status_code}: {r.text[:200]}")
                r.raise_for_status()
                data = r.json()
                if "error" in data:
                    raise LLMError(str(data["error"])[:300])
                choice = data["choices"][0]
                usage = data.get("usage") or {}
                return {
                    "model": self.model,
                    "prompt": (system + "\n\n" + user)[:TRACE_PROMPT_CAP],
                    "response": choice["message"]["content"],
                    "input_tokens": usage.get("prompt_tokens"),
                    "output_tokens": usage.get("completion_tokens"),
                    "latency_ms": int((time.time() - started) * 1000),
                    "error": None,
                }
            except FatalLLMError:
                raise
            except (httpx.HTTPError, LLMError, KeyError) as e:
                last_err = e
                await asyncio.sleep(2 ** attempt * 2)
        raise LLMError(f"gave up after {MAX_RETRIES} attempts: {last_err}")
