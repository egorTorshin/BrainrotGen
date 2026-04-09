"""Resolve stored worker output paths safely under the configured media root."""

from pathlib import Path


def resolve_media_file(stored_path: str, media_root: Path) -> Path:
    """
    Resolve *stored_path* to an existing file under *media_root*.

    Tries, in order:

    1. Absolute path, if it resolves inside *media_root* (Docker: ``/app/output/...``).
    2. Path relative to *media_root*.
    3. **Basename only** under *media_root* (host dev when DB still has container paths).

    Rejects paths that escape *media_root* (no ``../`` traversal past root).
    """
    root = media_root.expanduser().resolve()
    raw = Path(stored_path)
    candidates: list[Path] = []
    if raw.is_absolute():
        candidates.append(raw)
    candidates.append(root / raw)
    if raw.name:
        candidates.append(root / raw.name)

    tried: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved in tried:
            continue
        tried.add(resolved)
        try:
            resolved.relative_to(root)
        except ValueError:
            continue
        if resolved.is_file():
            return resolved

    raise FileNotFoundError(stored_path)
