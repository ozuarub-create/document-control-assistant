from app.ai_gateway import AIGateway
from app.gateway_models import GatewayRequest
from app.provider_adapters import FixtureProviderAdapter
from app.gateway_auth import APIKeyAuth
from app.gateway_rate_limit import SlidingWindowRateLimiter


def test_gateway_routes_and_returns():
    g = AIGateway(tracker=type('T',(object,),{'record':lambda self,x:None})())
    r = g.handle(GatewayRequest(task_type='classification', prompt='Classify this drawing'))
    assert r.model
    assert r.input_tokens > 0


def test_fallback():
    g = AIGateway(adapter=FixtureProviderAdapter({'model-quality'}), tracker=type('T',(object,),{'record':lambda self,x:None})(), max_attempts=2)
    r = g.handle(GatewayRequest(task_type='reasoning', prompt='Analyze risk'))
    assert r.attempts >= 1


def test_auth():
    a = APIKeyAuth(['secret'])
    assert a.validate('secret') and not a.validate('bad')


def test_rate_limit():
    r = SlidingWindowRateLimiter(limit=2, window_seconds=60)
    assert r.allow('u')
    assert r.allow('u')
    assert not r.allow('u')
