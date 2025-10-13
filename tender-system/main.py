"""
Main orchestrator for tender management system.
Coordinates scraping, storing, and classification.
"""
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.models import init_db, get_session, Tender, ScraperLog
from scrapers.simap_scraper import SimapScraper
from classifier.llm_classifier import TenderClassifier
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TenderOrchestrator:
    """Main orchestrator for tender processing pipeline"""
    
    def __init__(self):
        self.session = get_session()
        self.classifier = TenderClassifier()
        
        # Initialize scrapers
        self.scrapers = {
            'simap': SimapScraper()
        }
        
        logger.info("✅ Orchestrator initialized")
    
    def run_scraper(self, source: str = 'simap', days_back: int = 7, classify: bool = True):
        """
        Run scraper for a specific source.
        
        Args:
            source: Source name ('simap', etc.)
            days_back: How many days back to fetch tenders
            classify: Whether to classify tenders with LLM
        """
        if source not in self.scrapers:
            logger.error(f"Unknown source: {source}")
            return
        
        scraper = self.scrapers[source]
        start_time = datetime.now()
        
        # Calculate date range
        date_to = datetime.now()
        date_from = date_to - timedelta(days=days_back)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🚀 Starting tender scraping pipeline")
        logger.info(f"   Source: {source}")
        logger.info(f"   Date range: {date_from.date()} to {date_to.date()}")
        logger.info(f"   Classification: {'Enabled' if classify else 'Disabled'}")
        logger.info(f"{'='*60}\n")
        
        try:
            # 1. Fetch tenders
            tenders = scraper.fetch_tenders(date_from=date_from, date_to=date_to)
            logger.info(f"📥 Fetched {len(tenders)} tenders")
            
            if not tenders:
                logger.info("No new tenders found")
                self._log_scraper_run(source, start_time, 0, 0, 0, True)
                return
            
            # 2. Enrich with details (for SIMAP)
            if hasattr(scraper, 'enrich_with_details'):
                tenders = scraper.enrich_with_details(tenders)
            
            # 3. Classify if enabled
            classifications = {}
            if classify:
                classification_results = self.classifier.classify_batch(tenders)
                classifications = {r['tender_id']: r for r in classification_results}
            
            # 4. Store in database
            new_count, updated_count = self._store_tenders(tenders, classifications)
            
            # 5. Log the run
            duration = (datetime.now() - start_time).total_seconds()
            self._log_scraper_run(
                source, start_time, len(tenders), new_count, updated_count, True, duration=duration
            )
            
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ Pipeline complete!")
            logger.info(f"   Total found: {len(tenders)}")
            logger.info(f"   New: {new_count}")
            logger.info(f"   Updated: {updated_count}")
            logger.info(f"   Duration: {duration:.1f}s")
            logger.info(f"{'='*60}\n")
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}", exc_info=True)
            self._log_scraper_run(source, start_time, 0, 0, 0, False, error=str(e))
    
    def _store_tenders(self, tenders: list, classifications: dict) -> tuple:
        """Store tenders in database"""
        new_count = 0
        updated_count = 0
        
        for tender_data in tenders:
            tender_id = tender_data['tender_id']
            
            # Check if tender exists
            existing = self.session.query(Tender).filter_by(tender_id=tender_id).first()
            
            # Get classification results
            classification = classifications.get(tender_id, {})
            
            if existing:
                # Update existing tender
                existing.title = tender_data.get('title')
                existing.description = tender_data.get('description')
                existing.publication_date = tender_data.get('publication_date')
                existing.deadline = tender_data.get('deadline')
                existing.cpv_codes = tender_data.get('cpv_codes')
                existing.contracting_authority = tender_data.get('contracting_authority')
                existing.raw_data = tender_data.get('raw_data')
                
                if classification:
                    existing.is_relevant = classification.get('is_relevant')
                    existing.confidence_score = classification.get('confidence_score')
                    existing.reasoning = classification.get('reasoning')
                    existing.title_de = classification.get('title_de')
                    existing.summary = classification.get('summary')
                    existing.classified_at = datetime.now()
                
                existing.updated_at = datetime.now()
                updated_count += 1
                
            else:
                # Create new tender
                new_tender = Tender(
                    tender_id=tender_id,
                    source=tender_data['source'],
                    title=tender_data.get('title'),
                    title_de=classification.get('title_de') if classification else None,
                    description=tender_data.get('description'),
                    summary=classification.get('summary') if classification else None,
                    publication_date=tender_data.get('publication_date'),
                    deadline=tender_data.get('deadline'),
                    cpv_codes=tender_data.get('cpv_codes'),
                    contracting_authority=tender_data.get('contracting_authority'),
                    estimated_value=tender_data.get('estimated_value'),
                    raw_data=tender_data.get('raw_data'),
                    is_relevant=classification.get('is_relevant') if classification else None,
                    confidence_score=classification.get('confidence_score') if classification else None,
                    reasoning=classification.get('reasoning') if classification else None,
                    classified_at=datetime.now() if classification else None
                )
                self.session.add(new_tender)
                new_count += 1
        
        self.session.commit()
        return new_count, updated_count
    
    def _log_scraper_run(self, source: str, start_time: datetime, found: int, new: int, 
                        updated: int, success: bool, error: str = None, duration: float = None):
        """Log scraper run"""
        log = ScraperLog(
            source=source,
            run_date=start_time,
            tenders_found=found,
            tenders_new=new,
            tenders_updated=updated,
            success=success,
            error_message=error,
            duration_seconds=duration
        )
        self.session.add(log)
        self.session.commit()
    
    def get_stats(self):
        """Get database statistics"""
        total = self.session.query(Tender).count()
        relevant = self.session.query(Tender).filter_by(is_relevant=True).count()
        classified = self.session.query(Tender).filter(Tender.is_relevant.isnot(None)).count()
        
        stats = {
            'total_tenders': total,
            'relevant_tenders': relevant,
            'classified_tenders': classified,
            'unclassified_tenders': total - classified
        }
        
        logger.info(f"\n📊 Database Statistics:")
        logger.info(f"   Total tenders: {total}")
        logger.info(f"   Relevant: {relevant}")
        logger.info(f"   Classified: {classified}")
        logger.info(f"   Unclassified: {total - classified}\n")
        
        return stats


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Tender Management System')
    parser.add_argument('--init-db', action='store_true', help='Initialize database')
    parser.add_argument('--scrape', type=str, choices=['simap'], help='Run scraper for source')
    parser.add_argument('--days-back', type=int, default=7, help='Days to look back (default: 7)')
    parser.add_argument('--no-classify', action='store_true', help='Skip LLM classification')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    
    args = parser.parse_args()
    
    # Initialize database if requested
    if args.init_db:
        init_db()
        return
    
    # Create orchestrator
    orchestrator = TenderOrchestrator()
    
    # Show stats
    if args.stats:
        orchestrator.get_stats()
        return
    
    # Run scraper
    if args.scrape:
        orchestrator.run_scraper(
            source=args.scrape,
            days_back=args.days_back,
            classify=not args.no_classify
        )
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

