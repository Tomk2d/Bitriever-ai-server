from sqlalchemy import Column, Integer, Date, TIMESTAMP, func
from database.database_connection import db


class FearGreedIndex(db.Base):
    __tablename__ = "fear_greed_indices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, unique=True)
    value = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)

    def __repr__(self):
        return f"<FearGreedIndex(id={self.id}, date={self.date}, value={self.value})>"
