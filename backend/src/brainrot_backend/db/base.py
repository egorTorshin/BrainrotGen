"""Declarative base class for ORM models"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class inherited by all SQLAlchemy ORM models"""
