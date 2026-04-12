"""
Pytest bootstrapping lives in ``pyproject.toml`` (``pythonpath``).

``"."`` allows ``from src.…`` imports; ``"src"`` matches runtime layout where
modules use flat imports such as ``from db import …``.
"""
