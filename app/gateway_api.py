from __future__ import annotations
import os
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from .ai_gateway import AIGateway
from .gateway_models import GatewayRequest
from .gateway_auth import APIKeyAuth
from .gateway_rate_limit import SlidingWindowRateLimiter

app = FastAPI(title='Week 26 AI Gateway', version='1.0.0')
gateway = AIGateway()
auth = APIKeyAuth([os.getenv('AI_GATEWAY_API_KEY', 'demo-key')])
limiter = SlidingWindowRateLimiter(limit=int(os.getenv('AI_GATEWAY_RATE_LIMIT', '20')))

class RequestBody(BaseModel):
    task_type: str
    prompt: str
    max_tokens: int = 512

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.post('/v1/ai')
def ai_request(body: RequestBody, x_api_key: str | None = Header(default=None)):
    if not auth.validate(x_api_key):
        raise HTTPException(status_code=401, detail='Invalid API key')
    if not limiter.allow(x_api_key or 'anonymous'):
        raise HTTPException(status_code=429, detail='Rate limit exceeded')
    try:
        return gateway.handle(GatewayRequest(**body.model_dump())).to_dict()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

@app.get('/v1/usage')
def usage(x_api_key: str | None = Header(default=None)):
    if not auth.validate(x_api_key):
        raise HTTPException(status_code=401, detail='Invalid API key')
    return gateway.tracker.summary()
