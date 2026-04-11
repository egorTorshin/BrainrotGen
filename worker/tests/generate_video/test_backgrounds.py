# tests/generate_video/test_backgrounds.py
import pytest
import os
from pathlib import Path
from unittest.mock import patch
from src.generate_video.backgrounds import pick_background_video, assets_root_from_env


def test_pick_background_video_returns_random_mp4(tmp_path):
    """Должен вернуть случайный .mp4 файл из папки"""
    assets_root = tmp_path / "assets"
    minecraft_dir = assets_root / "minecraft"
    minecraft_dir.mkdir(parents=True)

    # Создаем тестовые видео
    video1 = minecraft_dir / "clip1.mp4"
    video2 = minecraft_dir / "clip2.mp4"
    video1.touch()
    video2.touch()

    # Должен вернуть один из них
    result = pick_background_video(assets_root, "minecraft")
    assert result in [video1, video2]
    assert result.suffix == ".mp4"


def test_pick_background_video_defaults_to_minecraft(tmp_path):
    """Если background не указан или неизвестен → используем minecraft"""
    assets_root = tmp_path / "assets"
    minecraft_dir = assets_root / "minecraft"
    minecraft_dir.mkdir(parents=True)

    video = minecraft_dir / "default.mp4"
    video.touch()

    # None → minecraft
    result1 = pick_background_video(assets_root, None)
    assert result1 == video

    # Пустая строка → minecraft
    result2 = pick_background_video(assets_root, "")
    assert result2 == video

    # Неизвестный тип → minecraft
    result3 = pick_background_video(assets_root, "unknown_game")
    assert result3 == video


def test_pick_background_video_case_insensitive(tmp_path):
    """Должен игнорировать регистр в названии фона"""
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
    """Папка с фоном отсутствует → FileNotFoundError"""
    assets_root = tmp_path / "assets"

    with pytest.raises(FileNotFoundError, match="Background folder not found"):
        pick_background_video(assets_root, "minecraft")


def test_pick_background_video_raises_if_no_mp4_files(tmp_path):
    """Папка есть, но .mp4 файлов нет → FileNotFoundError"""
    assets_root = tmp_path / "assets"
    minecraft_dir = assets_root / "minecraft"
    minecraft_dir.mkdir(parents=True)

    # Создаем .txt файл, не .mp4
    (minecraft_dir / "not_video.txt").touch()

    with pytest.raises(FileNotFoundError, match="No .mp4 files in"):
        pick_background_video(assets_root, "minecraft")


def test_pick_background_video_handles_subway(tmp_path):
    """Проверяем выбор фона subway"""
    assets_root = tmp_path / "assets"
    subway_dir = assets_root / "subway"
    subway_dir.mkdir(parents=True)

    video = subway_dir / "gameplay.mp4"
    video.touch()

    result = pick_background_video(assets_root, "subway")
    assert result == video


def test_assets_root_from_env(monkeypatch):
    """Читаем ASSETS_ROOT из окружения"""
    monkeypatch.setenv("ASSETS_ROOT", "/custom/assets")
    assert assets_root_from_env() == Path("/custom/assets")


def test_assets_root_from_env_default(monkeypatch):
    """Если переменной нет → дефолтное значение"""
    monkeypatch.delenv("ASSETS_ROOT", raising=False)
    assert assets_root_from_env() == Path("/app/assets")