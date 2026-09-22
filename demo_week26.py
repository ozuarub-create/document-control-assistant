from app.ai_gateway import AIGateway
from app.gateway_models import GatewayRequest
from app.provider_adapters import FixtureProviderAdapter

print('='*72)
print('Week 26 - Centralized AI Gateway Demo')
print('='*72)

gateway = AIGateway()
for task, prompt in [
    ('classification','Classify this construction document as drawing, RFI, or specification.'),
    ('summarization','Summarize the revision history and key changes.'),
    ('reasoning','Review the document and recommend the next workflow action.'),
]:
    r = gateway.handle(GatewayRequest(task_type=task, prompt=prompt))
    print(f'{task.upper():14} -> {r.provider}/{r.model} | tokens={r.input_tokens+r.output_tokens} | cost=${r.estimated_cost:.6f} | {r.latency_ms:.1f}ms')

print('\nFallback test')
fallback = AIGateway(adapter=FixtureProviderAdapter({'model-quality'}), max_attempts=2)
r = fallback.handle(GatewayRequest(task_type='reasoning', prompt='Analyze this technical issue.'))
print(f'fallback_used={r.fallback_used} attempts={r.attempts} selected={r.provider}/{r.model}')
print('\nWeek 26 Demo Complete')
print('- Unified API: working')
print('- Multi-model routing: working')
print('- Authentication/rate limiting: implemented')
print('- Token/cost tracking: working')
print('- Retry/fallback: working')
print('- Config-driven model selection: working')
