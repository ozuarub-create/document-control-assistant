# AI Gateway Architecture

Application -> AI Gateway API -> Authentication -> Rate Limiter -> Model Router -> Provider Adapter -> Selected Model -> Response

The router scores enabled model configurations using quality, cost, and latency. These values can be populated from Week 25 evaluation results instead of hard-coded application logic.

## Components
- Unified FastAPI endpoint
- API-key authentication
- Sliding-window rate limiting
- Config-driven provider registry
- Quality/cost/latency router
- Provider abstraction
- Retry and fallback
- JSONL usage logging
- Token and cost accounting
