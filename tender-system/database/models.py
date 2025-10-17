"""
Database models for tender management system.
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Tender(Base):
    """Tender data model"""
    __tablename__ = 'tenders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tender_id = Column(String(100), unique=True, nullable=False, index=True)  # External ID from source
    source = Column(String(50), nullable=False, index=True)  # 'simap', 'evergabe', etc.
    
    # Basic tender info
    title = Column(String(500), nullable=False)
    title_de = Column(String(500))  # German translation of title
    description = Column(Text)  # Full text/content
    summary = Column(Text)  # AI-generated summary
    publication_date = Column(DateTime, index=True)
    deadline = Column(DateTime)
    
    # Classification results
    is_relevant = Column(Boolean)  # LLM prediction Yes/No
    confidence_score = Column(Float)  # 0-100
    reasoning = Column(Text)  # LLM reasoning
    
    # Additional metadata
    cpv_codes = Column(JSON)  # List of CPV codes
    contracting_authority = Column(String(300))
    estimated_value = Column(Float)
    raw_data = Column(JSON)  # Store original API response
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    classified_at = Column(DateTime)  # When LLM classification was done
    
    def __repr__(self):
        return f"<Tender(id={self.tender_id}, source={self.source}, title={self.title[:50]}...)>"


class ScraperLog(Base):
    """Log scraper runs for monitoring"""
    __tablename__ = 'scraper_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)
    run_date = Column(DateTime, default=datetime.utcnow)
    tenders_found = Column(Integer, default=0)
    tenders_new = Column(Integer, default=0)
    tenders_updated = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    duration_seconds = Column(Float)
    
    def __repr__(self):
        return f"<ScraperLog(source={self.source}, date={self.run_date}, new={self.tenders_new})>"


# Database setup
# Use relative path from the database module location
DB_DIR = os.path.join(os.path.dirname(__file__), '..', 'db')
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.getenv('DB_PATH', os.path.join(DB_DIR, 'tenders.db'))
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(engine)
    print(f"[SUCCESS] Database initialized at {DB_PATH}")

def get_session():
    """Get database session"""
    return SessionLocal()

