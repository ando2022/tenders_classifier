"""
Database migration script to add new columns for German translations and summaries.
Run this if you have an existing database that needs to be updated.
"""
import sqlite3
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from database.models import DB_PATH
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_database():
    """Add title_de and summary columns to existing database"""
    
    db_path = DB_PATH
    logger.info(f"🔧 Migrating database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(tenders)")
        columns = [col[1] for col in cursor.fetchall()]
        
        migrations_run = []
        
        # Add title_de column if it doesn't exist
        if 'title_de' not in columns:
            logger.info("➕ Adding 'title_de' column...")
            cursor.execute("ALTER TABLE tenders ADD COLUMN title_de VARCHAR(500)")
            migrations_run.append("title_de")
        else:
            logger.info("✓ 'title_de' column already exists")
        
        # Add summary column if it doesn't exist
        if 'summary' not in columns:
            logger.info("➕ Adding 'summary' column...")
            cursor.execute("ALTER TABLE tenders ADD COLUMN summary TEXT")
            migrations_run.append("summary")
        else:
            logger.info("✓ 'summary' column already exists")
        
        conn.commit()
        conn.close()
        
        if migrations_run:
            logger.info(f"✅ Migration complete! Added columns: {', '.join(migrations_run)}")
        else:
            logger.info("✅ Database already up to date!")
        
        logger.info("\n📝 Next steps:")
        logger.info("   1. Run scraper with classification to populate new fields")
        logger.info("   2. Or re-classify existing tenders:")
        logger.info("      python -c \"from database.models import *; from classifier.llm_classifier import *; ...\"")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise


if __name__ == '__main__':
    migrate_database()

