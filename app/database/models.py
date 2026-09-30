from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.database.db import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    phone = Column(String, nullable=False)

    source = Column(String, nullable=True)

    status = Column(String, default="new")

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    call_at = Column(
        DateTime,
        nullable=True
    )