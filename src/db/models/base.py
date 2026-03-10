"""Shared declarative base for all ORM models.

Every model module must import ``Base`` from here so that all tables
are registered on the same ``MetaData`` instance.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
