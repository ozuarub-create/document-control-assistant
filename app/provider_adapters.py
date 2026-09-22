from __future__ import annotations
import time

class ProviderError(RuntimeError):
    pass

class BaseProviderAdapter:
    def generate(self, model: str, prompt: str, max_tokens: int) -> tuple[str, int, int, float]:
        raise NotImplementedError

class FixtureProviderAdapter(BaseProviderAdapter):
    def __init__(self, fail_models: set[str] | None = None):
        self.fail_models = fail_models or set()

    def generate(self, model: str, prompt: str, max_tokens: int) -> tuple[str, int, int, float]:
        started = time.perf_counter()
        if model in self.fail_models:
            raise ProviderError(f'Provider failure for {model}')
        input_tokens = max(1, len(prompt.split()))
        output = f'[{model}] {prompt[:160]}'.strip()
        output_tokens = max(1, len(output.split()))
        latency_ms = (time.perf_counter() - started) * 1000 + 10
        return output, input_tokens, output_tokens, latency_ms
