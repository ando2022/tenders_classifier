"""
Simple Streamlit App - No Database Required
This is a workaround to get the app running immediately.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# Page config
st.set_page_config(
    page_title="BAK Economics - Tender Management",
    page_icon="📋",
    layout="wide"
)

# Title
st.title("🎯 BAK Economics - Tender Management System")
st.markdown("---")

# Sidebar
st.sidebar.title("🎯 Tender Management")
st.sidebar.markdown("---")

# Navigation
page = st.sidebar.selectbox(
    "Choose a page:",
    ["📊 Dashboard", "📋 All Tenders", "✅ Relevant Tenders", "🔍 Search", "🚀 Run Scraper", "📈 Analytics"]
)

# Sample data for demonstration
sample_tenders = [
    {
        "id": 1,
        "title": "Economic Analysis of Regional Development",
        "title_de": "Wirtschaftsanalyse der Regionalentwicklung",
        "summary": "Comprehensive economic analysis of regional development patterns and growth opportunities in the target region.",
        "source": "SIMAP",
        "publication_date": "2025-01-10",
        "deadline": "2025-02-15",
        "confidence_score": 85,
        "is_relevant": True,
        "reasoning": "Directly related to economic analysis and regional development - core expertise area.",
        "contracting_authority": "Federal Office for Economic Development"
    },
    {
        "id": 2,
        "title": "Statistical Survey on Employment Trends",
        "title_de": "Statistische Erhebung zu Beschäftigungstrends",
        "summary": "Large-scale statistical survey to analyze employment trends and labor market dynamics.",
        "source": "EVERGABE",
        "publication_date": "2025-01-08",
        "deadline": "2025-02-20",
        "confidence_score": 92,
        "is_relevant": True,
        "reasoning": "Statistical analysis and employment research - perfect match for economic research capabilities.",
        "contracting_authority": "Ministry of Labor"
    },
    {
        "id": 3,
        "title": "IT Infrastructure Maintenance",
        "title_de": "IT-Infrastruktur-Wartung",
        "summary": "Technical maintenance and support for existing IT infrastructure systems.",
        "source": "SIMAP",
        "publication_date": "2025-01-05",
        "deadline": "2025-01-25",
        "confidence_score": 15,
        "is_relevant": False,
        "reasoning": "Pure IT services without economic research component - not relevant.",
        "contracting_authority": "IT Department"
    }
]

if page == "📊 Dashboard":
    st.header("📊 Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tenders", len(sample_tenders))
    
    with col2:
        relevant_count = sum(1 for t in sample_tenders if t["is_relevant"])
        st.metric("Relevant Tenders", relevant_count)
    
    with col3:
        avg_confidence = sum(t["confidence_score"] for t in sample_tenders if t["is_relevant"]) / relevant_count if relevant_count > 0 else 0
        st.metric("Avg Confidence", f"{avg_confidence:.1f}%")
    
    with col4:
        st.metric("Success Rate", "92%")
    
    st.markdown("---")
    
    st.subheader("📈 Recent Activity")
    st.info("🚀 **Last Scraper Run:** 2025-01-10 14:30")
    st.info("📥 **New Tenders Found:** 3")
    st.info("🤖 **Classified:** 3")
    st.info("✅ **Relevant:** 2")

elif page == "📋 All Tenders":
    st.header("📋 All Tenders")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        source_filter = st.selectbox("Filter by Source", ["All"] + list(set(t["source"] for t in sample_tenders)))
    with col2:
        relevance_filter = st.selectbox("Filter by Relevance", ["All", "Relevant Only", "Not Relevant"])
    
    # Apply filters
    filtered_tenders = sample_tenders
    if source_filter != "All":
        filtered_tenders = [t for t in filtered_tenders if t["source"] == source_filter]
    if relevance_filter == "Relevant Only":
        filtered_tenders = [t for t in filtered_tenders if t["is_relevant"]]
    elif relevance_filter == "Not Relevant":
        filtered_tenders = [t for t in filtered_tenders if not t["is_relevant"]]
    
    st.write(f"Showing {len(filtered_tenders)} tenders")
    
    for tender in filtered_tenders:
        title_display = tender["title_de"] if tender["title_de"] != tender["title"] else tender["title"]
        relevance_icon = "✅" if tender["is_relevant"] else "❌"
        
        with st.expander(f"{relevance_icon} {title_display}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Summary:** {tender['summary']}")
                st.write(f"**Reasoning:** {tender['reasoning']}")
            
            with col2:
                st.write(f"**Source:** {tender['source']}")
                st.write(f"**Published:** {tender['publication_date']}")
                st.write(f"**Deadline:** {tender['deadline']}")
                st.write(f"**Confidence:** {tender['confidence_score']}%")
                st.write(f"**Authority:** {tender['contracting_authority']}")

elif page == "✅ Relevant Tenders":
    st.header("✅ Relevant Tenders")
    
    relevant_tenders = [t for t in sample_tenders if t["is_relevant"]]
    
    col1, col2 = st.columns([3, 1])
    with col1:
        min_confidence = st.slider("Minimum Confidence", 0, 100, 50)
    with col2:
        st.write("")  # Spacer
        if st.button("📥 Export to Excel", type="primary"):
            df = pd.DataFrame(relevant_tenders)
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"relevant_tenders_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    filtered_relevant = [t for t in relevant_tenders if t["confidence_score"] >= min_confidence]
    st.write(f"Found {len(filtered_relevant)} relevant tenders (confidence ≥ {min_confidence}%)")
    
    for tender in filtered_relevant:
        title_display = tender["title_de"]
        with st.expander(f"⭐ {title_display} ({tender['confidence_score']}%)"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**📝 Zusammenfassung:** {tender['summary']}")
                st.markdown("---")
                st.write(f"**🤖 AI-Begründung:** {tender['reasoning']}")
            
            with col2:
                st.write(f"**Quelle:** {tender['source']}")
                st.write(f"**📅 Veröffentlicht:** {tender['publication_date']}")
                st.write(f"**⏰ Frist:** {tender['deadline']}")
                st.write(f"**Relevanz:** {tender['confidence_score']}%")
                st.write(f"**Auftraggeber:** {tender['contracting_authority']}")

elif page == "🔍 Search":
    st.header("🔍 Search Tenders")
    
    search_term = st.text_input("Search term", placeholder="Enter keywords...")
    
    if search_term:
        search_results = []
        for tender in sample_tenders:
            if (search_term.lower() in tender["title"].lower() or 
                search_term.lower() in tender["summary"].lower() or
                search_term.lower() in tender["title_de"].lower()):
                search_results.append(tender)
        
        st.write(f"Found {len(search_results)} results for '{search_term}'")
        
        for tender in search_results:
            title_display = tender["title_de"]
            with st.expander(f"🔍 {title_display}"):
                st.write(f"**Summary:** {tender['summary']}")
                st.write(f"**Source:** {tender['source']}")
                st.write(f"**Confidence:** {tender['confidence_score']}%")
    else:
        st.info("Enter a search term to find tenders")

elif page == "🚀 Run Scraper":
    st.header("🚀 Run Scraper")
    
    st.info("🚧 **Demo Mode:** This is a demonstration of the scraper interface.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Configuration")
        days_back = st.slider("Days to look back", 1, 30, 7)
        sources = st.multiselect("Sources", ["SIMAP", "EVERGABE"], default=["SIMAP"])
        enable_classification = st.checkbox("Enable AI Classification", value=True)
    
    with col2:
        st.subheader("Status")
        if st.button("▶️ Run Scraper", type="primary"):
            with st.spinner("Running scraper..."):
                import time
                time.sleep(2)  # Simulate scraping
                
                st.success("✅ Scraping completed!")
                st.info("📥 Found 3 new tenders")
                st.info("🤖 Classified 3 tenders")
                st.info("✅ 2 marked as relevant")
                st.info("⏱️ Duration: 45 seconds")

elif page == "📈 Analytics":
    st.header("📈 Analytics")
    
    # Sample analytics data
    st.subheader("📊 Classification Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Accuracy", "92%")
        st.metric("Precision", "89%")
        st.metric("Recall", "94%")
    
    with col2:
        st.metric("Total Classified", "156")
        st.metric("Relevant Found", "23")
        st.metric("False Positives", "3")
    
    st.subheader("📈 Trends")
    
    # Sample trend data
    dates = pd.date_range(start='2024-12-01', end='2025-01-10', freq='D')
    trend_data = pd.DataFrame({
        'date': dates,
        'tenders_found': [2, 1, 3, 0, 1, 2, 4, 1, 2, 3, 1, 0, 2, 1, 3, 2, 1, 4, 2, 1, 3, 2, 1, 0, 2, 3, 1, 2, 4, 1, 2, 3, 1, 2, 0, 1, 3, 2, 1, 2, 3],
        'relevant_found': [1, 0, 2, 0, 1, 1, 3, 0, 1, 2, 0, 0, 1, 1, 2, 1, 0, 3, 1, 0, 2, 1, 0, 0, 1, 2, 0, 1, 3, 0, 1, 2, 0, 1, 0, 0, 2, 1, 0, 1, 2]
    })
    
    st.line_chart(trend_data.set_index('date'))

# Footer
st.markdown("---")
st.caption("🎯 BAK Economics - Tender Management System | Demo Version")
