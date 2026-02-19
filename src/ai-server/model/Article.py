from sqlalchemy import Column, Integer, BigInteger, String, Text, TIMESTAMP
from database.database_connection import db


class Article(db.Base):
    __tablename__ = "articles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    article_id = Column(Integer)
    headline = Column(String(500), nullable=False)
    summary = Column(Text)
    original_url = Column(String(1000), nullable=False, unique=True)
    reporter_name = Column(String(100))
    publisher_name = Column(String(100))
    publisher_type = Column(Integer, nullable=False)
    published_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)

    def __repr__(self):
        return f"<Article(id={self.id}, headline={self.headline[:50]}...)>"
