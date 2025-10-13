import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="BAK Economics - Tender Management", page_icon="📋", layout="wide")

st.title("🎯 BAK Economics - Tender Management System")
st.markdown("---")

# Sample data
tenders = [
    {"title": "Economic Analysis of Regional Development", "title_de": "Wirtschaftsanalyse der Regionalentwicklung", "summary": "Comprehensive economic analysis", "confidence": 85, "relevant": True},
    {"title": "Statistical Survey on Employment", "title_de": "Statistische Erhebung zu Beschäftigung", "summary": "Large-scale statistical survey", "confidence": 92, "relevant": True},
    {"title": "IT Infrastructure Maintenance", "title_de": "IT-Infrastruktur-Wartung", "summary": "Technical maintenance", "confidence": 15, "relevant": False}
]

page = st.sidebar.selectbox("Choose page:", ["📊 Dashboard", "📋 All Tenders", "✅ Relevant Tenders"])

if page == "📊 Dashboard":
    st.header("📊 Dashboard")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Tenders", len(tenders))
    with col2:
        relevant = sum(1 for t in tenders if t["relevant"])
        st.metric("Relevant", relevant)
    with col3:
        st.metric("Success Rate", "92%")

elif page == "📋 All Tenders":
    st.header("📋 All Tenders")
    for tender in tenders:
        icon = "✅" if tender["relevant"] else "❌"
        with st.expander(f"{icon} {tender['title_de']}"):
            st.write(f"**Summary:** {tender['summary']}")
            st.write(f"**Confidence:** {tender['confidence']}%")

elif page == "✅ Relevant Tenders":
    st.header("✅ Relevant Tenders")
    relevant_tenders = [t for t in tenders if t["relevant"]]
    for tender in relevant_tenders:
        with st.expander(f"⭐ {tender['title_de']} ({tender['confidence']}%)"):
            st.write(f"**Summary:** {tender['summary']}")
            st.write(f"**Confidence:** {tender['confidence']}%")

st.markdown("---")
st.caption("🎯 BAK Economics - Tender Management System | Demo Version")
