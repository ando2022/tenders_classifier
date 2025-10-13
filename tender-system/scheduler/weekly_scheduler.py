"""
Weekly scheduler for automated tender scraping.
"""
import sys
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import TenderOrchestrator
from database.models import init_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def weekly_scrape_job():
    """Job to run weekly scraping and classification"""
    logger.info(f"\n{'='*60}")
    logger.info(f"⏰ SCHEDULED JOB TRIGGERED")
    logger.info(f"   Time: {datetime.now()}")
    logger.info(f"{'='*60}\n")
    
    try:
        orchestrator = TenderOrchestrator()
        
        # Scrape SIMAP (7 days back to avoid duplicates)
        orchestrator.run_scraper(source='simap', days_back=7, classify=True)
        
        # Show stats
        orchestrator.get_stats()
        
        logger.info("✅ Scheduled job completed successfully\n")
        
    except Exception as e:
        logger.error(f"❌ Scheduled job failed: {e}", exc_info=True)


def start_scheduler(day_of_week='mon', hour=9, minute=0):
    """
    Start the weekly scheduler.
    
    Args:
        day_of_week: Day to run (mon, tue, wed, thu, fri, sat, sun)
        hour: Hour to run (0-23)
        minute: Minute to run (0-59)
    """
    # Initialize database if needed
    init_db()
    
    scheduler = BlockingScheduler()
    
    # Schedule weekly job
    trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
    scheduler.add_job(
        weekly_scrape_job,
        trigger=trigger,
        id='weekly_tender_scrape',
        name='Weekly Tender Scraping & Classification',
        replace_existing=True
    )
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🕐 SCHEDULER STARTED")
    logger.info(f"   Schedule: Every {day_of_week.upper()} at {hour:02d}:{minute:02d}")
    logger.info(f"   Next run: {scheduler.get_jobs()[0].next_run_time}")
    logger.info(f"{'='*60}\n")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("\n🛑 Scheduler stopped by user")
        scheduler.shutdown()


def run_once_now():
    """Run the job immediately (for testing)"""
    logger.info("🚀 Running job immediately (test mode)")
    weekly_scrape_job()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Tender Scraping Scheduler')
    parser.add_argument('--now', action='store_true', help='Run job immediately (for testing)')
    parser.add_argument('--day', type=str, default='mon', 
                       choices=['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
                       help='Day of week to run (default: mon)')
    parser.add_argument('--hour', type=int, default=9, help='Hour to run (0-23, default: 9)')
    parser.add_argument('--minute', type=int, default=0, help='Minute to run (0-59, default: 0)')
    
    args = parser.parse_args()
    
    if args.now:
        run_once_now()
    else:
        start_scheduler(day_of_week=args.day, hour=args.hour, minute=args.minute)

