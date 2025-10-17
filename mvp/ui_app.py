#!/usr/bin/env python3
"""
Single-Page Tender Management UI
Optimized for efficiency with all features in one view
"""
import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime
import subprocess

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mvp.fetch_tracker import get_fetch_date_range, update_last_fetch_date, update_fetch_stats
from tender_system.classifier.similarity_classifier import SimilarityClassifier

# Page config
st.set_page_config(
    page_title="Tender Management System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'tenders_df' not in st.session_state:
    st.session_state.tenders_df = None
if 'selected_tenders' not in st.session_state:
    st.session_state.selected_tenders = []
if 'emergency_classifier' not in st.session_state:
    # Load emergency classifier
    st.session_state.emergency_classifier = SimilarityClassifier()
    st.session_state.emergency_classifier.load_model()

# Header
st.title("🎯 Tender Management System")
st.markdown("**Single-page interface for fetching, analyzing, and managing tenders**")

# ============================================================================
# SECTION 1: FETCH NEW DATA
# ============================================================================
st.header("📥 1. Fetch New Data")

col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    date_range = get_fetch_date_range()
    st.info(f"""
    **Last Fetch:** {date_range['start_date']}  
    **Today:** {date_range['end_date']}  
    **Days Since Last Fetch:** {date_range['days_since_last']}
    """)

with col2:
    # Manual date override
    use_custom_dates = st.checkbox("Use custom date range")
    if use_custom_dates:
        start_date = st.date_input("Start date", value=date_range['last_fetch'])
        end_date = st.date_input("End date", value=date_range['today'])
    else:
        start_date = date_range['last_fetch']
        end_date = date_range['today']

with col3:
    if st.button("🚀 Fetch Tenders", type="primary", use_container_width=True):
        with st.spinner("Fetching new tenders..."):
            try:
                # Run scrapers
                result = subprocess.run(
                    ["python", "scraper/01_calls_scrapers.py"],
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                
                if result.returncode == 0:
                    # Run consolidation
                    result2 = subprocess.run(
                        ["python", "mvp/01_consolidate_scraped_data.py"],
                        capture_output=True,
                        text=True,
                        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    )
                    
                    if result2.returncode == 0:
                        # Load consolidated data
                        data_dir = 'mvp/data'
                        csv_files = [f for f in os.listdir(data_dir) if f.startswith('consolidated_tenders_')]
                        if csv_files:
                            latest_file = sorted(csv_files)[-1]
                            st.session_state.tenders_df = pd.read_csv(f'{data_dir}/{latest_file}')
                            
                            # Update fetch tracker
                            update_last_fetch_date(end_date)
                            update_fetch_stats(len(st.session_state.tenders_df))
                            
                            st.success(f"✅ Fetched {len(st.session_state.tenders_df)} tenders!")
                            st.rerun()
                    else:
                        st.error(f"Consolidation failed: {result2.stderr}")
                else:
                    st.error(f"Scraping failed: {result.stderr}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Load existing data if available
if st.session_state.tenders_df is None:
    data_dir = 'mvp/data'
    if os.path.exists(data_dir):
        csv_files = [f for f in os.listdir(data_dir) if f.startswith('consolidated_tenders_')]
        if csv_files:
            latest_file = sorted(csv_files)[-1]
            st.session_state.tenders_df = pd.read_csv(f'{data_dir}/{latest_file}')

# ============================================================================
# SECTION 2: CLASSIFY & ANALYZE TENDERS
# ============================================================================
if st.session_state.tenders_df is not None:
    st.header("🤖 2. Classify Tenders")
    
    df = st.session_state.tenders_df
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.metric("Total Tenders", len(df))
    with col2:
        if st.button("🔍 Classify All", type="primary", use_container_width=True):
            with st.spinner("Classifying tenders..."):
                results = []
                progress_bar = st.progress(0)
                
                for idx, row in df.iterrows():
                    # Classify with emergency classifier
                    tender_text = f"{row['title_original']}\n\n{row.get('description_original', '')}"
                    result = st.session_state.emergency_classifier.classify_tender(
                        title=row['title_original'],
                        description=row.get('description_original', '')
                    )
                    
                    results.append({
                        'tender_id': row['tender_id'],
                        'prediction': result['is_relevant'],
                        'confidence': result['confidence_score'],
                        'similarity': result.get('max_similarity', 0),
                        'best_match': result.get('best_match_title', 'N/A'),
                        'reasoning': result.get('reasoning', '')
                    })
                    
                    progress_bar.progress((idx + 1) / len(df))
                
                # Store results
                results_df = pd.DataFrame(results)
                st.session_state.classification_results = results_df
                st.session_state.selected_tenders = results_df[results_df['prediction'] == True]['tender_id'].tolist()
                
                st.success(f"✅ Classified {len(df)} tenders. Found {len(st.session_state.selected_tenders)} relevant!")
                st.rerun()

# ============================================================================
# SECTION 3: SELECTED TENDERS
# ============================================================================
if st.session_state.tenders_df is not None and len(st.session_state.selected_tenders) > 0:
    st.header("✅ 3. Selected Tenders")
    
    df = st.session_state.tenders_df
    selected_df = df[df['tender_id'].isin(st.session_state.selected_tenders)]
    
    if 'classification_results' in st.session_state:
        # Merge with classification results
        selected_df = selected_df.merge(
            st.session_state.classification_results,
            on='tender_id',
            how='left'
        )
    
    st.metric("Relevant Tenders", len(selected_df))
    
    # Display each tender
    for idx, tender in selected_df.iterrows():
        with st.expander(f"📋 {tender['title_original'][:100]}...", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🇩🇪 Original")
                st.markdown(f"**Title:** {tender['title_original']}")
                
                if pd.notna(tender.get('description_original')):
                    desc = tender['description_original']
                    if len(desc) > 500:
                        desc = desc[:500] + "..."
                    st.markdown(f"**Description:** {desc}")
                
                st.markdown(f"**Source:** {tender['source']}")
                st.markdown(f"**Authority:** {tender.get('contracting_authority', 'N/A')}")
                st.markdown(f"**Deadline:** {tender.get('deadline', 'N/A')}")
            
            with col2:
                st.markdown("### 🇬🇧 English Translation")
                
                # Auto-translate button
                if st.button(f"Translate", key=f"translate_{tender['tender_id']}"):
                    with st.spinner("Translating..."):
                        # TODO: Add translation API call
                        st.info("Translation feature: Integrate with OpenAI or translation API")
                
                st.markdown("**Title (EN):** [Translation will appear here]")
                st.markdown("**Description (EN):** [Translation will appear here]")
            
            # Classification Details
            st.markdown("---")
            st.markdown("### 🎯 Classification Details")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                conf = tender.get('confidence', 0)
                st.metric("Confidence", f"{conf:.1f}%")
            with col2:
                sim = tender.get('similarity', 0)
                st.metric("Similarity Score", f"{sim:.3f}")
            with col3:
                best_match = tender.get('best_match', 'N/A')
                if len(best_match) > 30:
                    best_match = best_match[:30] + "..."
                st.metric("Best Match", best_match)
            
            st.markdown(f"**Reasoning:** {tender.get('reasoning', 'N/A')}")
            
            # Feedback Section
            st.markdown("---")
            st.markdown("### 📝 Feedback")
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                feedback = st.radio(
                    "Is this tender relevant?",
                    ["✅ Yes, relevant", "❌ No, not relevant"],
                    key=f"feedback_{tender['tender_id']}"
                )
            
            with col2:
                if st.button("Submit Feedback", key=f"submit_{tender['tender_id']}"):
                    is_relevant = "Yes" in feedback
                    
                    # TODO: Store feedback in database
                    st.success(f"Feedback recorded: {'Relevant' if is_relevant else 'Not Relevant'}")
                    
                    # If marked as positive, add to emergency classifier
                    if is_relevant:
                        st.session_state.emergency_classifier.add_positive_case(
                            title=tender['title_original'],
                            description=tender.get('description_original', ''),
                            confidence=100,
                            source='user_feedback'
                        )
                        st.info("✅ Added to positive cases for emergency classifier")
            
            with col3:
                notes = st.text_input("Notes (optional)", key=f"notes_{tender['tender_id']}")

# ============================================================================
# SECTION 4: STATISTICS & EXPORT
# ============================================================================
if st.session_state.tenders_df is not None:
    st.header("📊 4. Statistics & Export")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total = len(st.session_state.tenders_df)
        st.metric("Total Tenders", total)
    
    with col2:
        selected = len(st.session_state.selected_tenders)
        st.metric("Selected", selected)
    
    with col3:
        if selected > 0:
            percentage = (selected / total) * 100
            st.metric("Selection Rate", f"{percentage:.1f}%")
        else:
            st.metric("Selection Rate", "0%")
    
    with col4:
        if st.button("📥 Export Selected", type="primary", use_container_width=True):
            if len(st.session_state.selected_tenders) > 0:
                selected_df = st.session_state.tenders_df[
                    st.session_state.tenders_df['tender_id'].isin(st.session_state.selected_tenders)
                ]
                
                # Export to CSV
                export_file = f'mvp/data/selected_tenders_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                selected_df.to_csv(export_file, index=False)
                
                st.success(f"✅ Exported {len(selected_df)} tenders to {export_file}")
                
                # Provide download
                with open(export_file, 'rb') as f:
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=f,
                        file_name=os.path.basename(export_file),
                        mime="text/csv"
                    )
            else:
                st.warning("No tenders selected to export")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.caption("🎯 Tender Management System | Optimized Single-Page UI")

