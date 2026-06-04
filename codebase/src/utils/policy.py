"""Load and cache POLICY.md for use in the QA system prompt."""

from pathlib import Path

_POLICY_PATH = Path(__file__).parent.parent.parent / "data" / "POLICY.md"


def _load() -> str:
    if not _POLICY_PATH.exists():
        return ""
    raw = _POLICY_PATH.read_text(encoding="utf-8")
    # Remove duplicate lines (the file has repeated sections)
    seen: set[str] = set()
    lines: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped and stripped in seen:
            continue
        if stripped:
            seen.add(stripped)
        lines.append(line)
    return "\n".join(lines)


POLICY_CONTENT: str = _load()
POLICY_FOR_PROMPT: str = POLICY_CONTENT[:6000] if len(POLICY_CONTENT) > 6000 else POLICY_CONTENT
