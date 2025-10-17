"""
Consolidated schema for tender data from multiple sources.
Supports both PostgreSQL and CSV storage.
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import pandas as pd

Base = declarative_base()

class ConsolidatedTender(Base):
    """Unified tender schema for all sources"""
    __tablename__ = 'consolidated_tenders'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Source identification
    tender_id = Column(String(200), unique=True, nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)  # 'simap', 'eu-tender', 'evergabe'
    source_url = Column(String(500))
    
    # Basic tender info (original language)
    title_original = Column(Text, nullable=False)
    description_original = Column(Text)  # Full text
    original_language = Column(String(10))  # DE, FR, IT, EN
    
    # English translations (for unified analysis)
    title_en = Column(Text)  # English translation of title
    description_en = Column(Text)  # English translation of full text (optional)
    
    # Dates
    publication_date = Column(DateTime, index=True)
    deadline = Column(DateTime, index=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    contracting_authority = Column(String(500))
    buyer_country = Column(String(10))
    cpv_codes = Column(JSON)  # List of CPV codes
    procedure_type = Column(String(100))
    contract_nature = Column(String(100))
    estimated_value = Column(Float)
    
    # LLM Classification (OpenAI)
    llm_prediction = Column(Boolean)  # True=Relevant, False=Not Relevant
    llm_confidence = Column(Float)  # 0-100
    llm_reasoning = Column(Text)
    llm_classified_at = Column(DateTime)
    
    # Emergency Classification (Cosine Similarity)
    emergency_prediction = Column(Boolean)
    emergency_confidence = Column(Float)  # 0-100
    emergency_similarity_score = Column(Float)  # 0-1
    emergency_best_match = Column(Text)
    emergency_classified_at = Column(DateTime)
    
    # User Feedback (Platform user confirms/rejects)
    user_feedback = Column(Boolean)  # True=Confirmed, False=Rejected, None=Not reviewed
    user_feedback_at = Column(DateTime)
    user_feedback_by = Column(String(100))  # Username
    user_feedback_notes = Column(Text)
    
    # Sales Department Feedback (Final outcome)
    sales_feedback = Column(Boolean)  # True=Selected for proposal, False=Not selected
    sales_feedback_at = Column(DateTime)
    sales_feedback_by = Column(String(100))
    sales_feedback_notes = Column(Text)
    proposal_submitted = Column(Boolean)
    proposal_won = Column(Boolean)
    
    # Raw data (for reference)
    raw_data = Column(JSON)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Tender({self.tender_id}, {self.source}, {self.title_original[:50]}...)>"


# Database configuration
USE_POSTGRES = os.getenv('USE_POSTGRES', 'false').lower() == 'true'
POSTGRES_URL = os.getenv('POSTGRES_URL', 'postgresql://user:pass@localhost/tenders')
SQLITE_PATH = os.getenv('SQLITE_PATH', 'mvp/database/tenders.db')

if USE_POSTGRES:
    engine = create_engine(POSTGRES_URL, echo=False)
    logger_msg = f"Using PostgreSQL: {POSTGRES_URL}"
else:
    # Use SQLite as fallback
    db_dir = os.path.dirname(SQLITE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    engine = create_engine(f'sqlite:///{SQLITE_PATH}', echo=False)
    logger_msg = f"Using SQLite: {SQLITE_PATH}"

SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(engine)
    print(f"✅ Database initialized")
    print(f"   {logger_msg}")

def get_session():
    """Get database session"""
    return SessionLocal()


# CSV Export/Import functions
def export_to_csv(output_file='mvp/data/consolidated_tenders.csv'):
    """Export all tenders to CSV"""
    session = get_session()
    tenders = session.query(ConsolidatedTender).all()
    
    data = []
    for t in tenders:
        data.append({
            'tender_id': t.tender_id,
            'source': t.source,
            'title_original': t.title_original,
            'title_en': t.title_en,
            'description_original': t.description_original[:500] if t.description_original else '',
            'description_en': t.description_en[:500] if t.description_en else '',
            'publication_date': t.publication_date,
            'deadline': t.deadline,
            'contracting_authority': t.contracting_authority,
            'buyer_country': t.buyer_country,
            'llm_prediction': t.llm_prediction,
            'llm_confidence': t.llm_confidence,
            'llm_reasoning': t.llm_reasoning,
            'emergency_prediction': t.emergency_prediction,
            'emergency_confidence': t.emergency_confidence,
            'user_feedback': t.user_feedback,
            'sales_feedback': t.sales_feedback,
        })
    
    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✅ Exported {len(data)} tenders to {output_file}")
    return output_file


def import_from_csv(input_file):
    """Import tenders from CSV"""
    df = pd.read_csv(input_file)
    session = get_session()
    
    for _, row in df.iterrows():
        tender = ConsolidatedTender(
            tender_id=row['tender_id'],
            source=row['source'],
            title_original=row['title_original'],
            title_en=row.get('title_en'),
            description_original=row.get('description_original'),
            publication_date=pd.to_datetime(row['publication_date']) if pd.notna(row.get('publication_date')) else None,
            deadline=pd.to_datetime(row['deadline']) if pd.notna(row.get('deadline')) else None,
        )
        session.add(tender)
    
    session.commit()
    print(f"✅ Imported {len(df)} tenders from {input_file}")


if __name__ == "__main__":
    # Initialize database
    init_db()
    
    # Show schema
    print("\n📋 Consolidated Tender Schema:")
    print("=" * 60)
    for column in ConsolidatedTender.__table__.columns:
        print(f"  {column.name:30s} {column.type}")

