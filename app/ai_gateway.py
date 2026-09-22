from __future__ import annotations
import time
import uuid
from .gateway_models import GatewayRequest, GatewayResponse
from .gateway_config import load_provider_configs, load_routing_weights
from .model_router import ModelRouter
from .provider_adapters import FixtureProviderAdapter, ProviderError
from .gateway_usage import UsageTracker

class AIGateway:
    def __init__(self, config_path=None, adapter=None, tracker=None, max_attempts: int = 2):
        configs = load_provider_configs(config_path)
        self.router = ModelRouter(configs, load_routing_weights(config_path))
        self.adapter = adapter or FixtureProviderAdapter()
        self.tracker = tracker or UsageTracker()
        self.max_attempts = max_attempts

    @staticmethod
    def _cost(cfg, input_tokens: int, output_tokens: int) -> float:
        return round((input_tokens/1000)*cfg.input_cost_per_1k + (output_tokens/1000)*cfg.output_cost_per_1k, 8)

    def handle(self, request: GatewayRequest) -> GatewayResponse:
        request_id = str(uuid.uuid4())
        candidates = self.router.rank(request.task_type)
        if not candidates:
            raise RuntimeError('No enabled model providers')
        errors = []
        started = time.perf_counter()
        for attempt, cfg in enumerate(candidates[:self.max_attempts], start=1):
            try:
                output, input_tokens, output_tokens, latency_ms = self.adapter.generate(cfg.model, request.prompt, request.max_tokens)
                result = GatewayResponse(
                    request_id=request_id, provider=cfg.name, model=cfg.model, output=output,
                    input_tokens=input_tokens, output_tokens=output_tokens,
                    estimated_cost=self._cost(cfg, input_tokens, output_tokens), latency_ms=round(latency_ms, 2),
                    fallback_used=attempt > 1, attempts=attempt,
                )
                self.tracker.record({'ts': time.time(), 'task_type': request.task_type, **result.to_dict()})
                return result
            except ProviderError as e:
                errors.append(str(e))
        raise RuntimeError('All gateway providers failed: ' + '; '.join(errors))
