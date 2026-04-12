"""Pick a random gameplay clip from local asset folders (procedural variety)."""

from __future__ import annotations

import os
import random
from pathlib import Path

# Maps normalized background key to subdirectory under ASSETS_ROOT
_BACKGROUND_DIRS = {
    "minecraft": "minecraft",
    "subway": "subway",
}


def normalize_background_key(background: str | None) -> str:
    """
    Map UI/API labels and legacy strings to ``minecraft`` or ``subway``.

    API uses ``minecraft`` | ``subway``; older rows may contain phrases.
    """
    if not background:
        return "minecraft"
    s = background.strip().lower()
    if s in _BACKGROUND_DIRS:
        return s
    if "subway" in s:
        return "subway"
    if "minecraft" in s:
        return "minecraft"
    return "minecraft"


def pick_background_video(assets_root: Path, background: str) -> Path:
    """
    Return a random ``.mp4`` from ``<assets_root>/<minecraft|subway>/``.

    Raises:
        FileNotFoundError: directory missing or contains no ``.mp4`` files.
    """
    key = normalize_background_key(background)
    sub = _BACKGROUND_DIRS[key]
    folder = assets_root / sub
    if not folder.is_dir():
        raise FileNotFoundError(f"Background folder not found: {folder}")

    clips = sorted(folder.glob("*.mp4"))
    if not clips:
        raise FileNotFoundError(
            f"No .mp4 files in {folder}. Add gameplay clips for '{sub}'."
        )
    return random.choice(clips)


def assets_root_from_env() -> Path:
    return Path(os.environ.get("ASSETS_ROOT", "/app/assets"))
