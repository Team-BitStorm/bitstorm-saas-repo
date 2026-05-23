def normalize_phone(value: str) -> str:
    """Remove all whitespace (e.g. '+40 740 123 193' -> '+40740123193')."""
    if not value:
        return ""
    return "".join(str(value).split())
