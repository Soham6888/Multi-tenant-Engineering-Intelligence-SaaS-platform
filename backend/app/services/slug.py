import re
import unicodedata


def make_slug(name: str, suffix: int | None = None) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    base = re.sub(r"[^a-z0-9]+", "-", ascii_name).strip("-")[:63].rstrip("-")
    if not base:
        base = "organization"
    if suffix is None:
        return base
    tail = f"-{suffix}"
    return f"{base[: 63 - len(tail)].rstrip('-')}{tail}"
