ROLE_PERMISSIONS = {
    "admin": {"read_document", "write_document", "run_tool", "search", "summarize"},
    "reviewer": {"read_document", "search", "summarize", "run_tool"},
    "user": {"read_document", "search", "summarize"},
}

TOOL_PERMISSIONS = {
    "admin": {"compare_revisions", "validate_document", "delete_document", "register_document"},
    "reviewer": {"compare_revisions", "validate_document"},
    "user": set(),
}

def has_role_permission(role: str, action: str) -> bool:
    return action in ROLE_PERMISSIONS.get(role, set())

def has_tool_permission(role: str, tool: str) -> bool:
    return tool in TOOL_PERMISSIONS.get(role, set())
