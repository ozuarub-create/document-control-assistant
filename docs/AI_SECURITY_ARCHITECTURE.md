# Week 29 AI Security Architecture

Client -> Security API -> Input Validation -> Prompt Injection Detection -> RBAC/Document ACL -> Tool Permission Check -> AI/Tool Layer -> Output Validation/Redaction -> Audit Log

Security is enforced before any protected document/tool action. Output validation is applied before responses leave the security boundary.
