MAX_INPUT_CHARS = 20000
ALLOWED_CONTENT_TYPES = {"text/plain", "application/pdf", "application/json"}

def validate_input(content: str, content_type: str = "text/plain") -> list[str]:
    errors = []
    if len(content) > MAX_INPUT_CHARS:
        errors.append("input_too_large")
    if content_type not in ALLOWED_CONTENT_TYPES:
        errors.append("unsupported_content_type")
    if "\x00" in content:
        errors.append("null_byte_detected")
    return errors
