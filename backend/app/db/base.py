"""Shared declarative metadata; schema changes require explicit migrations."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
