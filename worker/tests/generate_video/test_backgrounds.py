# tests/generate_video/test_backgrounds.py
import pytest
import os
from pathlib import Path
from unittest.mock import patch
from src.generate_video.backgrounds import (
    assets_root_from_env,
    normalize_background_key,
    pick_background_video,
)


def test_pick_background_video_returns_random_mp4(tmp_path):
    """Returns a random .mp4 file from the background folder"""
    assets_root = tmp_path / "assets"
    minecraft_dir = assets_root / "minecraft"
    minecraft_dir.mkdir(parents=True)

    video1 = minecraft_dir / "clip1.mp4"
    video2 = minecraft_dir / "clip2.mp4"
    video1.touch()
    video2.touch()

    result = pick_background_video(assets_root, "minecraft")
    assert result in [video1, video2]
    assert result.suffix == ".mp4"


def test_pick_background_video_defaults_to_minecraft(tmp_path):
    """Unknown or missing background falls back to minecraft"""
    assets_root = tmp_path / "assets"
    minecraft_dir = assets_root / "minecraft"
    minecraft_dir.mkdir(parents=True)

    video = minecraft_dir / "default.mp4"
    video.touch()

    result1 = pick_background_video(assets_root, None)
    assert result1 == video

    result2 = pick_background_video(assets_root, "")
    assert result2 == video

    result3 = pick_background_video(assets_root, "unknown_game")
    assert result3 == video


def test_pick_background_video_case_insensitive(tmp_path):
    """Background name matching is case-insensitive"""
    assets_root = tmp_path / "assets"
    subway_dir = assets_root / "subway"
    subway_dir.mkdir(parents=True)

    video = subway_dir / "train.mp4"
    video.touch()

    result1 = pick_background_video(assets_root, "SUBWAY")
    result2 = pick_background_video(assets_root, "SuBwAy")

    assert result1 == video
    assert result2 == video


def test_pick_background_video_raises_if_folder_missing(tmp_path):
    """Missing background folder raises FileNotFoundError"""
    assets_root = tmp_path / "assets"

    with pytest.raises(FileNotFoundError, match="Background folder not found"):
        pick_background_video(assets_root, "minecraft")


def test_pick_background_video_raises_if_no_mp4_files(tmp_path):
    """Folder exists but has no .mp4 files raises FileNotFoundError"""
    assets_root = tmp_path / "assets"
    minecraft_dir = assets_root / "minecraft"
    minecraft_dir.mkdir(parents=True)

    (minecraft_dir / "not_video.txt").touch()

    with pytest.raises(FileNotFoundError, match="No .mp4 files in"):
        pick_background_video(assets_root, "minecraft")


def test_pick_background_video_handles_subway(tmp_path):
    """Subway background selection works"""
    assets_root = tmp_path / "assets"
    subway_dir = assets_root / "subway"
    subway_dir.mkdir(parents=True)

    video = subway_dir / "gameplay.mp4"
    video.touch()

    result = pick_background_video(assets_root, "subway")
    assert result == video


def test_pick_background_video_subway_surfers_label(tmp_path):
    """Streamlit-style label maps to subway folder."""
    assets_root = tmp_path / "assets"
    subway_dir = assets_root / "subway"
    subway_dir.mkdir(parents=True)
    video = subway_dir / "s.mp4"
    video.touch()

    assert normalize_background_key("Subway Surfers") == "subway"
    assert pick_background_video(assets_root, "subway surfers") == video


def test_normalize_background_key_minecraft_parkour():
    assert normalize_background_key("minecraft parkour") == "minecraft"


def test_normalize_background_key_api_values():
    assert normalize_background_key("minecraft") == "minecraft"
    assert normalize_background_key("subway") == "subway"


def test_assets_root_from_env(monkeypatch):
    """Reads ASSETS_ROOT from environment"""
    monkeypatch.setenv("ASSETS_ROOT", "/custom/assets")
    assert assets_root_from_env() == Path("/custom/assets")


def test_assets_root_from_env_default(monkeypatch):
    """Uses default path when ASSETS_ROOT is unset"""
    monkeypatch.delenv("ASSETS_ROOT", raising=False)
    assert assets_root_from_env() == Path("/app/assets")
