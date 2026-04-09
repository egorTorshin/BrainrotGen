"""Pick a random gameplay clip from local asset folders (procedural variety)."""

from __future__ import annotations

import os
import random
from pathlib import Path

# Maps API ``background`` field to subdirectory under ASSETS_ROOT
_BACKGROUND_DIRS = {
    "minecraft": "minecraft",
    "subway": "subway",
}


def pick_background_video(assets_root: Path, background: str) -> Path:
    """
    Return a random ``.mp4`` from ``<assets_root>/<minecraft|subway>/``.

    Raises:
        FileNotFoundError: directory missing or contains no ``.mp4`` files.
    """
    key = background.strip().lower() if background else "minecraft"
    sub = _BACKGROUND_DIRS.get(key, "minecraft")
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
