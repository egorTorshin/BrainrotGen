"""Tests for safe resolution of worker output paths."""

from pathlib import Path

import pytest

from brainrot_backend.core.media_paths import resolve_media_file


def test_resolves_relative_file_under_root(tmp_path: Path) -> None:
    root = tmp_path / "out"
    root.mkdir()
    f = root / "clip.mp4"
    f.write_bytes(b"x")
    resolved = resolve_media_file("clip.mp4", root)
    assert resolved == f.resolve()


def test_resolves_absolute_inside_root(tmp_path: Path) -> None:
    root = tmp_path / "out"
    root.mkdir()
    f = root / "a.mp4"
    f.write_bytes(b"x")
    resolved = resolve_media_file(str(f.resolve()), root)
    assert resolved == f.resolve()


def test_fallback_basename_when_absolute_missing(tmp_path: Path) -> None:
    """Host API + DB path from container: try same filename under *media_root*."""
    root = tmp_path / "out"
    root.mkdir()
    f = root / "job.mp4"
    f.write_bytes(b"x")
    resolved = resolve_media_file("/app/output/job.mp4", root)
    assert resolved == f.resolve()


def test_raises_when_no_candidate_exists(tmp_path: Path) -> None:
    root = tmp_path / "out"
    root.mkdir()
    with pytest.raises(FileNotFoundError):
        resolve_media_file("missing.mp4", root)


def test_rejects_escape_outside_root(tmp_path: Path) -> None:
    root = tmp_path / "out"
    root.mkdir()
    outside = tmp_path / "secret.mp4"
    outside.write_bytes(b"x")
    with pytest.raises(FileNotFoundError):
        resolve_media_file(str(outside.resolve()), root)
