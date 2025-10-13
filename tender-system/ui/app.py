"""
Streamlit UI for Tender Management System.
"""
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import desc

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.models import init_db, get_session, Tender, ScraperLog
from main import TenderOrchestrator

# Page config
st.set_page_config(
    page_title="BAK Economics - Tender Management",
    page_icon="📋",
    layout="wide"
)

# Initialize
init_db()
session = get_session()

# Sidebar
st.sidebar.title("🎯 Tender Management")
st.sidebar.markdown("---")

# Navigation
page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "📋 All Tenders", "✅ Relevant Tenders", "🔍 Search", "🚀 Run Scraper", "📈 Analytics"]
)

st.sidebar.markdown("---")

# Quick stats in sidebar
total_tenders = session.query(Tender).count()
relevant_tenders = session.query(Tender).filter_by(is_relevant=True).count()
recent_tenders = session.query(Tender).filter(
    Tender.created_at >= datetime.now() - timedelta(days=7)
).count()

st.sidebar.metric("Total Tenders", total_tenders)
st.sidebar.metric("Relevant", relevant_tenders)
st.sidebar.metric("New (7 days)", recent_tenders)


# Main content
if page == "📊 Dashboard":
    st.title("📊 Tender Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tenders", total_tenders)
    with col2:
        st.metric("Relevant", relevant_tenders)
    with col3:
        classified = session.query(Tender).filter(Tender.is_relevant.isnot(None)).count()
        st.metric("Classified", classified)
    with col4:
        avg_confidence = session.query(Tender).filter(Tender.is_relevant == True).with_entities(
            Tender.confidence_score
        ).all()
        if avg_confidence:
            avg = sum([c[0] for c in avg_confidence if c[0]]) / len([c for c in avg_confidence if c[0]])
            st.metric("Avg Confidence", f"{avg:.1f}%")
        else:
            st.metric("Avg Confidence", "N/A")
    
    st.markdown("---")
    
    # Recent tenders
    st.subheader("📥 Recent Tenders (Last 10)")
    recent = session.query(Tender).order_by(desc(Tender.created_at)).limit(10).all()
    
    if recent:
        df = pd.DataFrame([{
            'Datum': t.publication_date.strftime('%d.%m.%Y') if t.publication_date else 'N/A',
            'Titel (DE)': (t.title_de or t.title)[:80] + '...' if len(t.title_de or t.title) > 80 else (t.title_de or t.title),
            'Quelle': t.source.upper(),
            'Relevant': '✅' if t.is_relevant else '❌' if t.is_relevant is False else '❓',
            'Relevanz': f"{t.confidence_score:.0f}%" if t.confidence_score else 'N/A'
        } for t in recent])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No tenders yet. Run a scraper to collect data!")
    
    # Scraper logs
    st.markdown("---")
    st.subheader("📝 Recent Scraper Runs")
    logs = session.query(ScraperLog).order_by(desc(ScraperLog.run_date)).limit(5).all()
    
    if logs:
        df_logs = pd.DataFrame([{
            'Date': log.run_date.strftime('%Y-%m-%d %H:%M'),
            'Source': log.source.upper(),
            'Found': log.tenders_found,
            'New': log.tenders_new,
            'Updated': log.tenders_updated,
            'Status': '✅' if log.success else '❌',
            'Duration': f"{log.duration_seconds:.1f}s" if log.duration_seconds else 'N/A'
        } for log in logs])
        st.dataframe(df_logs, use_container_width=True)
    else:
        st.info("No scraper runs yet")


elif page == "📋 All Tenders":
    st.title("📋 All Tenders")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        source_filter = st.selectbox("Source", ["All"] + ["SIMAP", "Other"])
    with col2:
        classification_filter = st.selectbox("Classification", ["All", "Relevant", "Not Relevant", "Unclassified"])
    with col3:
        sort_by = st.selectbox("Sort by", ["Newest", "Oldest", "Confidence"])
    
    # Build query
    query = session.query(Tender)
    
    if source_filter != "All":
        query = query.filter_by(source=source_filter.lower())
    
    if classification_filter == "Relevant":
        query = query.filter_by(is_relevant=True)
    elif classification_filter == "Not Relevant":
        query = query.filter_by(is_relevant=False)
    elif classification_filter == "Unclassified":
        query = query.filter(Tender.is_relevant.is_(None))
    
    if sort_by == "Newest":
        query = query.order_by(desc(Tender.created_at))
    elif sort_by == "Oldest":
        query = query.order_by(Tender.created_at)
    else:
        query = query.order_by(desc(Tender.confidence_score))
    
    tenders = query.limit(100).all()
    
    st.write(f"Showing {len(tenders)} tenders")
    
    for tender in tenders:
        title_display = tender.title_de or tender.title
        with st.expander(f"{'✅' if tender.is_relevant else '❌' if tender.is_relevant is False else '❓'} {title_display}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Show summary first if available
                if tender.summary:
                    st.write(f"**📝 Zusammenfassung:** {tender.summary}")
                    st.markdown("---")
                
                # Show full description
                st.write(f"**Volltext:** {tender.description[:500]}..." if tender.description and len(tender.description) > 500 else tender.description or "Nicht verfügbar")
                
                if tender.reasoning:
                    st.markdown("---")
                    st.write(f"**🤖 AI-Begründung:** {tender.reasoning}")
            
            with col2:
                st.write(f"**Quelle:** {tender.source.upper()}")
                st.write(f"**Veröffentlicht:** {tender.publication_date.strftime('%d.%m.%Y') if tender.publication_date else 'N/A'}")
                if tender.deadline:
                    st.write(f"**⏰ Frist:** {tender.deadline.strftime('%d.%m.%Y')}")
                if tender.confidence_score:
                    st.write(f"**Relevanz:** {tender.confidence_score:.0f}%")
                if tender.title_de and tender.title != tender.title_de:
                    st.markdown("---")
                    st.caption(f"Original: {tender.title}")


elif page == "✅ Relevant Tenders":
    st.title("✅ Relevant Tenders")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        # Min confidence filter
        min_confidence = st.slider("Minimum Confidence", 0, 100, 50)
    with col2:
        st.write("")  # Spacer
        if st.button("📥 Export to Excel", type="primary"):
            from export_client_report import ClientReportExporter
            exporter = ClientReportExporter()
            file = exporter.export_relevant_tenders(min_confidence=min_confidence, format='excel')
            if file:
                st.success(f"✅ Exported to {file}")
    
    relevant = session.query(Tender).filter(
        Tender.is_relevant == True,
        Tender.confidence_score >= min_confidence
    ).order_by(desc(Tender.confidence_score)).all()
    
    st.write(f"Found {len(relevant)} relevant tenders (confidence ≥ {min_confidence}%)")
    
    for tender in relevant:
        title_display = tender.title_de or tender.title
        with st.expander(f"⭐ {title_display} ({tender.confidence_score:.0f}%)"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Show summary
                if tender.summary:
                    st.write(f"**📝 Zusammenfassung:** {tender.summary}")
                    st.markdown("---")
                
                # Show full description
                st.write(f"**Volltext:** {tender.description[:500]}..." if tender.description and len(tender.description) > 500 else tender.description or "Nicht verfügbar")
                st.markdown("---")
                st.write(f"**🤖 AI-Begründung:** {tender.reasoning}")
            
            with col2:
                st.write(f"**Quelle:** {tender.source.upper()}")
                st.write(f"**📅 Veröffentlicht:** {tender.publication_date.strftime('%d.%m.%Y') if tender.publication_date else 'N/A'}")
                if tender.deadline:
                    st.write(f"**⏰ Frist:** {tender.deadline.strftime('%d.%m.%Y')}")
                st.write(f"**Relevanz:** {tender.confidence_score:.0f}%")
                
                if tender.title_de and tender.title != tender.title_de:
                    st.markdown("---")
                    st.caption(f"Original: {tender.title}")


elif page == "🔍 Search":
    st.title("🔍 Search Tenders")
    
    search_term = st.text_input("Search in title or description")
    
    if search_term:
        results = session.query(Tender).filter(
            (Tender.title.contains(search_term)) | 
            (Tender.description.contains(search_term))
        ).all()
        
        st.write(f"Found {len(results)} results for '{search_term}'")
        
        for tender in results:
            with st.expander(f"{tender.title}"):
                st.write(f"**Description:** {tender.description}")
                st.write(f"**Source:** {tender.source.upper()}")
                st.write(f"**Relevant:** {'Yes' if tender.is_relevant else 'No' if tender.is_relevant is False else 'Not classified'}")


elif page == "🚀 Run Scraper":
    st.title("🚀 Run Scraper")
    
    col1, col2 = st.columns(2)
    
    with col1:
        source = st.selectbox("Source", ["simap"])
        days_back = st.number_input("Days to look back", 1, 30, 7)
        classify = st.checkbox("Classify with LLM", value=True)
    
    if st.button("▶️ Run Scraper", type="primary"):
        with st.spinner(f"Running {source.upper()} scraper..."):
            orchestrator = TenderOrchestrator()
            orchestrator.run_scraper(source=source, days_back=days_back, classify=classify)
            st.success("✅ Scraper completed!")
            st.rerun()


elif page == "📈 Analytics":
    st.title("📈 Analytics")
    
    # Tenders over time
    st.subheader("Tenders Over Time")
    
    tenders_by_date = session.query(
        Tender.publication_date,
        Tender.is_relevant
    ).filter(Tender.publication_date.isnot(None)).all()
    
    if tenders_by_date:
        df = pd.DataFrame([(t[0].date(), t[1]) for t in tenders_by_date], columns=['Date', 'Relevant'])
        df_grouped = df.groupby(['Date', 'Relevant']).size().unstack(fill_value=0)
        st.line_chart(df_grouped)
    
    # Classification accuracy simulation
    st.subheader("Classification Stats")
    col1, col2 = st.columns(2)
    
    with col1:
        classified_count = session.query(Tender).filter(Tender.is_relevant.isnot(None)).count()
        st.metric("Classified", classified_count)
    
    with col2:
        if relevant_tenders > 0:
            st.metric("Relevance Rate", f"{(relevant_tenders/total_tenders*100):.1f}%")
        else:
            st.metric("Relevance Rate", "N/A")

