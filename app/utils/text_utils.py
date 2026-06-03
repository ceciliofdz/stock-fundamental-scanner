import re

def clean_text(text: str) -> str:
    """Simple text cleaning helper."""
    if not text:
        return ""
    # Remove extra whitespace
    return re.sub(r'\s+', ' ', text).strip()
