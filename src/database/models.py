"""Database models for the application."""
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class House(Base):
    """House model for storing home information."""
    __tablename__ = "houses"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    
    def __repr__(self) -> str:
        return f"House(id={self.id}, name='{self.name}', description='{self.description}')"
