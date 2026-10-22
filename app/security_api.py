from fastapi import FastAPI
from pydantic import BaseModel
from .security_layer import SecurityLayer
from .security_models import SecurityRequest

app = FastAPI(title="Week 29 AI Security Layer")
layer = SecurityLayer()

class RequestModel(BaseModel):
    user_id: str
    role: str
    action: str
    document_owner: str | None = None
    tool_name: str | None = None
    content: str = ""
    content_type: str = "text/plain"

@app.post("/security/check")
def check(req: RequestModel):
    decision = layer.evaluate(SecurityRequest(
        user_id=req.user_id,
        role=req.role,
        action=req.action,
        document_owner=req.document_owner,
        tool_name=req.tool_name,
        content=req.content,
        metadata={"content_type": req.content_type},
    ))
    return decision.__dict__
