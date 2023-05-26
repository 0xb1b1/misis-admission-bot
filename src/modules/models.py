#!/usr/bin/env python3


"""Models for SQLAlchemy."""
import enum
from datetime import datetime
# from sqlalchemy import ForeignKey
from sqlalchemy import Column, Integer, BigInteger, Boolean, Text, Date, DateTime, JSON, TypeDecorator
from sqlalchemy.orm import declarative_base  # , relationship

Base = declarative_base()


# region Custom column types
class IntEnum(TypeDecorator):
    """
    Enables passing in a Python enum and storing the enum's *value* in the db.

    The default would have stored the enum's *name* (ie the string).
    """
    impl = Integer
    cache_ok: bool = True

    def __init__(self, enumtype, *args, **kwargs):
        super(IntEnum, self).__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, dialect):
        if isinstance(value, int):
            return value

        return value.value

    def process_result_value(self, value, dialect):
        return self._enumtype(value)
# endregion


# region Enums
class Platform(enum.Enum):
    """Platform enum."""
    UNKNOWN = 0
    TELEGRAM = 1
    VK = 2
# endregion


class TelemetryEntry(Base):
    """Telemetry entry model."""
    __tablename__ = 'telemetry'
    id = Column(Integer, primary_key=True, autoincrement=True)
    button_id = Column(Text, nullable=False)
    platform = Column(IntEnum(Platform), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
