from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    code = Column(String(3), unique=True, nullable=False)
    group_name = Column(String(1), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    players = relationship("Player", back_populates="team", cascade="all, delete-orphan")