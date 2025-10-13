"""
Export module for client-ready tender reports.
Generates formatted Excel/CSV with German translations and summaries.
"""
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
from sqlalchemy import desc

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database.models import get_session, Tender
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClientReportExporter:
    """Export tender data in client-ready format"""
    
    def __init__(self):
        self.session = get_session()
    
    def export_relevant_tenders(
        self, 
        output_file: str = None,
        min_confidence: float = 50,
        format: str = 'excel',
        include_full_text: bool = True
    ):
        """
        Export relevant tenders for client review.
        
        Args:
            output_file: Output filename (default: auto-generated with timestamp)
            min_confidence: Minimum confidence score (0-100)
            format: 'excel' or 'csv'
            include_full_text: Whether to include full tender text
        """
        # Query relevant tenders
        tenders = self.session.query(Tender).filter(
            Tender.is_relevant == True,
            Tender.confidence_score >= min_confidence
        ).order_by(desc(Tender.confidence_score)).all()
        
        if not tenders:
            logger.warning(f"No relevant tenders found with confidence >= {min_confidence}%")
            return None
        
        logger.info(f"📊 Exporting {len(tenders)} relevant tenders...")
        
        # Build export data
        export_data = []
        for tender in tenders:
            row = {
                # Core fields for client
                'Titel (Deutsch)': tender.title_de or tender.title,
                'Zusammenfassung': tender.summary or 'Keine Zusammenfassung verfügbar',
                'Veröffentlichungsdatum': tender.publication_date.strftime('%d.%m.%Y') if tender.publication_date else 'N/A',
                'Einreichungsfrist': tender.deadline.strftime('%d.%m.%Y') if tender.deadline else 'N/A',
                
                # Classification info
                'Relevanz (%)': f"{tender.confidence_score:.0f}%" if tender.confidence_score else 'N/A',
                'Begründung': tender.reasoning or '',
                
                # Source info
                'Quelle': tender.source.upper(),
                'Auftraggeber': tender.contracting_authority or 'N/A',
                
                # Original title (if different)
                'Originaltitel': tender.title if tender.title != tender.title_de else '',
            }
            
            # Add full text if requested
            if include_full_text:
                row['Volltext'] = tender.description or 'Nicht verfügbar'
            
            export_data.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(export_data)
        
        # Generate filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ext = 'xlsx' if format == 'excel' else 'csv'
            output_file = f"relevant_tenders_{timestamp}.{ext}"
        
        # Export
        if format == 'excel':
            # Create Excel with formatting
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Relevante Ausschreibungen', index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets['Relevante Ausschreibungen']
                for idx, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).apply(len).max(),
                        len(col)
                    )
                    # Cap at 50 for readability, except full text
                    if col == 'Volltext':
                        max_length = min(max_length, 100)
                    else:
                        max_length = min(max_length, 50)
                    worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2
            
            logger.info(f"✅ Excel exported to: {output_file}")
        else:
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            logger.info(f"✅ CSV exported to: {output_file}")
        
        # Print summary
        logger.info(f"\n📋 Export Summary:")
        logger.info(f"   Total tenders: {len(tenders)}")
        logger.info(f"   Min confidence: {min_confidence}%")
        logger.info(f"   Format: {format.upper()}")
        logger.info(f"   File: {output_file}\n")
        
        return output_file
    
    def export_all_tenders(
        self,
        output_file: str = None,
        days_back: int = None,
        format: str = 'excel'
    ):
        """
        Export all tenders (classified and unclassified).
        
        Args:
            output_file: Output filename
            days_back: Only include tenders from last N days
            format: 'excel' or 'csv'
        """
        query = self.session.query(Tender)
        
        if days_back:
            cutoff_date = datetime.now() - pd.Timedelta(days=days_back)
            query = query.filter(Tender.created_at >= cutoff_date)
        
        tenders = query.order_by(desc(Tender.created_at)).all()
        
        if not tenders:
            logger.warning("No tenders found")
            return None
        
        logger.info(f"📊 Exporting {len(tenders)} tenders...")
        
        export_data = []
        for tender in tenders:
            row = {
                'Titel (Deutsch)': tender.title_de or tender.title,
                'Originaltitel': tender.title,
                'Zusammenfassung': tender.summary or 'N/A',
                'Veröffentlichungsdatum': tender.publication_date.strftime('%d.%m.%Y') if tender.publication_date else 'N/A',
                'Einreichungsfrist': tender.deadline.strftime('%d.%m.%Y') if tender.deadline else 'N/A',
                'Relevant': 'Ja' if tender.is_relevant else 'Nein' if tender.is_relevant is False else 'Nicht klassifiziert',
                'Relevanz (%)': f"{tender.confidence_score:.0f}%" if tender.confidence_score else 'N/A',
                'Begründung': tender.reasoning or '',
                'Quelle': tender.source.upper(),
                'Auftraggeber': tender.contracting_authority or 'N/A',
                'Volltext': tender.description or 'N/A'
            }
            export_data.append(row)
        
        df = pd.DataFrame(export_data)
        
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ext = 'xlsx' if format == 'excel' else 'csv'
            output_file = f"all_tenders_{timestamp}.{ext}"
        
        if format == 'excel':
            df.to_excel(output_file, index=False, engine='openpyxl')
        else:
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        logger.info(f"✅ Exported to: {output_file}")
        return output_file
    
    def get_summary_stats(self):
        """Print summary statistics"""
        total = self.session.query(Tender).count()
        relevant = self.session.query(Tender).filter_by(is_relevant=True).count()
        classified = self.session.query(Tender).filter(Tender.is_relevant.isnot(None)).count()
        with_german = self.session.query(Tender).filter(Tender.title_de.isnot(None)).count()
        with_summary = self.session.query(Tender).filter(Tender.summary.isnot(None)).count()
        
        print(f"\n📊 Database Statistics:")
        print(f"   Total tenders: {total}")
        print(f"   Classified: {classified}")
        print(f"   Relevant: {relevant}")
        print(f"   With German translation: {with_german}")
        print(f"   With summary: {with_summary}\n")


def main():
    """CLI for client report export"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Export Client-Ready Tender Reports')
    parser.add_argument('--relevant', action='store_true', help='Export only relevant tenders')
    parser.add_argument('--all', action='store_true', help='Export all tenders')
    parser.add_argument('--min-confidence', type=float, default=50, 
                       help='Minimum confidence score (default: 50)')
    parser.add_argument('--format', choices=['excel', 'csv'], default='excel',
                       help='Output format (default: excel)')
    parser.add_argument('--output', type=str, help='Output filename')
    parser.add_argument('--no-fulltext', action='store_true', 
                       help='Exclude full text (for compact export)')
    parser.add_argument('--days-back', type=int, help='Only include tenders from last N days')
    parser.add_argument('--stats', action='store_true', help='Show statistics only')
    
    args = parser.parse_args()
    
    exporter = ClientReportExporter()
    
    if args.stats:
        exporter.get_summary_stats()
        return
    
    if args.relevant:
        exporter.export_relevant_tenders(
            output_file=args.output,
            min_confidence=args.min_confidence,
            format=args.format,
            include_full_text=not args.no_fulltext
        )
    elif args.all:
        exporter.export_all_tenders(
            output_file=args.output,
            days_back=args.days_back,
            format=args.format
        )
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

