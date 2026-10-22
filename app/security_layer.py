from .security_models import SecurityRequest, SecurityDecision
from .security_rbac import has_role_permission, has_tool_permission
from .security_detection import detect_prompt_injection, redact_sensitive
from .security_validation import validate_input
from .security_audit import AuditLogger

class SecurityLayer:
    def __init__(self, logger: AuditLogger | None = None):
        self.logger = logger or AuditLogger()

    def evaluate(self, req: SecurityRequest) -> SecurityDecision:
        reasons = []
        risk = 0.0

        input_errors = validate_input(req.content, req.metadata.get("content_type", "text/plain"))
        if input_errors:
            reasons.extend(input_errors)
            risk += 0.5

        injections = detect_prompt_injection(req.content)
        if injections:
            reasons.append("prompt_injection_detected")
            risk += 0.5

        if not has_role_permission(req.role, req.action):
            reasons.append("role_not_authorized")
            risk += 0.5

        if req.document_owner and req.document_owner != req.user_id and req.role != "admin":
            reasons.append("document_access_denied")
            risk += 0.5

        if req.tool_name and not has_tool_permission(req.role, req.tool_name):
            reasons.append("tool_not_authorized")
            risk += 0.5

        allowed = len(reasons) == 0
        decision = SecurityDecision(
            allowed=allowed,
            reasons=reasons or ["allowed"],
            risk_score=min(risk, 1.0),
            sanitized_output=redact_sensitive(req.content),
        )
        self.logger.log({
            "user_id": req.user_id,
            "role": req.role,
            "action": req.action,
            "tool_name": req.tool_name,
            "allowed": allowed,
            "reasons": decision.reasons,
            "risk_score": decision.risk_score,
        })
        return decision
