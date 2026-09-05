"""Tinker sampling backend: same .complete() contract as llm.Client.

Used for two things: harness development before the endpoint credentials exist, and running
the pipeline against a fine-tuned sampler checkpoint (tinker://.../sampler_weights/...).
Requires TINKER_API_KEY. Install: uv sync --extra tinker
"""

import asyncio
import time

from .llm import LLMError, TRACE_PROMPT_CAP


class TinkerClient:
    def __init__(self, base_model: str, model_path: str | None = None):
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

    async def complete(self, system: str, user: str, max_tokens: int = 16_000) -> dict:
        started = time.time()
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        model_input = self._renderer.build_generation_prompt(messages)
        params = self._types.SamplingParams(max_tokens=max_tokens, temperature=0, stop=self._stop)
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
