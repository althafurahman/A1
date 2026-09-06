"""Tinker sampling client for the fixed competition model or a fine-tuned checkpoint
(tinker://.../sampler_weights/...). Requires TINKER_API_KEY and TINKER_PROJECT_ID.
"""

import asyncio
import time

TRACE_PROMPT_CAP = 20_000  # SUBMISSION.md allows truncating workbook serialisations in traces


class LLMError(Exception):
    pass


# The team's Tinker project. Not a secret (unusable without the API key); hardcoded as the
# default per organiser instruction so judges run with only TINKER_API_KEY set, exactly as
# we do. An explicit TINKER_PROJECT_ID env var still overrides it.
TEAM_PROJECT_ID = "75fc4e61-fc39-485f-bed1-b79f2591ab24"


class TinkerClient:
    def __init__(self, base_model: str, model_path: str | None = None):
        import os
        os.environ.setdefault("TINKER_PROJECT_ID", TEAM_PROJECT_ID)
        import tinker
        from tinker import types
        from tinker_cookbook import renderers
        from tinker_cookbook.model_info import get_recommended_renderer_name
        from tinker_cookbook.tokenizer_utils import get_tokenizer

        self.model = model_path or base_model
        self._types = types
        self._sampler = tinker.ServiceClient().create_sampling_client(
            base_model=base_model, model_path=model_path)
        self._renderer = renderers.get_renderer(
            get_recommended_renderer_name(base_model), get_tokenizer(base_model))
        self._stop = self._renderer.get_stop_sequences()

    async def close(self):
        pass

    CONTEXT_WINDOW = 65_536  # Tinker serves Qwen3.8-27B with 64k; prompt + max_tokens must fit

    # Qwen3.8-27B's recommended renderer thinks at length: 8192 truncates mid-reasoning,
    # 24576 was validated on the baseline smoke tests. Script-style replies stay well under it.
    async def complete(self, system: str, user: str, max_tokens: int = 24_576) -> dict:
        started = time.time()
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        model_input = self._renderer.build_generation_prompt(messages)
        available = self.CONTEXT_WINDOW - model_input.length - 64
        if available < 6_000:  # not enough room left to think and answer
            raise LLMError(f"prompt too long: {model_input.length} tokens leaves {available} to sample")
        params = self._types.SamplingParams(max_tokens=min(max_tokens, available), temperature=0, stop=self._stop)
        last_err = None
        for attempt in range(3):
            try:
                response = await self._sampler.sample_async(
                    prompt=model_input, num_samples=1, sampling_params=params)
                tokens = response.sequences[0].tokens
                content = self._renderer.parse_response(tokens)[0]["content"]
                if not isinstance(content, str):  # thinking renderers return parts
                    content = "".join(p.get("text", "") for p in content if p.get("type") == "text")
                return {
                    "model": self.model,
                    "prompt": (system + "\n\n" + user)[:TRACE_PROMPT_CAP],
                    "response": content,
                    "input_tokens": model_input.length,
                    "output_tokens": len(tokens),
                    "latency_ms": int((time.time() - started) * 1000),
                    "error": None,
                }
            except Exception as e:
                last_err = e
                await asyncio.sleep(2 ** attempt * 2)
        raise LLMError(f"tinker sampling failed after 3 attempts: {last_err}")
