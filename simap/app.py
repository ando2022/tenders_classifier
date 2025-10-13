"""
Streamlit app to display SIMAP tender data
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Page config
st.set_page_config(
    page_title="SIMAP Tender Monitor",
    page_icon="📋",
    layout="wide"
)

# Title
st.title("📋 SIMAP Tender Monitor")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Controls")
    
    # Data source selection
    data_source = st.radio(
        "Select data source:",
        ["Daily (Today)", "Weekly (Last 7 days)"]
    )
    
    # File paths based on selection
    if data_source == "Daily (Today)":
        essential_file = "unlabeled/simap_essential.csv"
        flat_file = "unlabeled/simap_flat.csv"
        raw_file = "unlabeled/simap.csv"
    else:
        essential_file = "unlabeled/simap_weekly_essential.csv"
        flat_file = "unlabeled/simap_weekly_flat.csv"
        raw_file = "unlabeled/simap_weekly.csv"
    
    # Check if files exist
    files_exist = os.path.exists(essential_file)
    
    if files_exist:
        st.success(f"✅ {data_source} data loaded")
    else:
        st.error(f"❌ No {data_source.lower()} data found")
        st.info("Run the pipeline first:\n\n`python 01a_run_daily_pipeline.py`\n\nor\n\n`python 01b_run_weekly_pipeline.py`")
    
    st.markdown("---")
    
    # Filters
    st.header("🔍 Filters")
    show_all_columns = st.checkbox("Show all columns", value=False)

# Main content
if files_exist:
    # Load data
    df_essential = pd.read_csv(essential_file)
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Tenders", len(df_essential))
    with col2:
        unique_cpv = df_essential['CPV Code'].nunique()
        st.metric("Unique CPV Codes", unique_cpv)
    with col3:
        # Count tenders with eligibility criteria
        with_eligibility = df_essential['Eligibility'].notna().sum()
        st.metric("With Eligibility Criteria", with_eligibility)
    
    st.markdown("---")
    
    # Search/Filter
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("🔍 Search in titles", "")
    with col2:
        cpv_filter = st.multiselect(
            "Filter by CPV Code",
            options=sorted(df_essential['CPV Code'].dropna().unique())
        )
    
    # Apply filters
    filtered_df = df_essential.copy()
    
    if search_term:
        filtered_df = filtered_df[
            filtered_df['Title'].str.contains(search_term, case=False, na=False)
        ]
    
    if cpv_filter:
        filtered_df = filtered_df[filtered_df['CPV Code'].isin(cpv_filter)]
    
    # Display filtered count
    if len(filtered_df) != len(df_essential):
        st.info(f"Showing {len(filtered_df)} of {len(df_essential)} tenders")
    
    # Display data
    st.subheader("📊 Tender Data")
    
    # Show all columns or just essential
    if show_all_columns and os.path.exists(flat_file):
        df_display = pd.read_csv(flat_file)
        st.dataframe(df_display, use_container_width=True, height=400)
    else:
        st.dataframe(filtered_df, use_container_width=True, height=400)
    
    # Detailed view
    st.markdown("---")
    st.subheader("📋 Detailed View")
    
    if len(filtered_df) > 0:
        # Tender selector
        tender_titles = filtered_df['Title'].tolist()
        selected_title = st.selectbox("Select a tender to view details:", tender_titles)
        
        if selected_title:
            tender = filtered_df[filtered_df['Title'] == selected_title].iloc[0]
            
            # Display tender details
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📌 Basic Information**")
                st.write(f"**ID:** {tender.get('ID', 'N/A')}")
                st.write(f"**Title:** {tender.get('Title', 'N/A')}")
                st.write(f"**CPV Code:** {tender.get('CPV Code', 'N/A')}")
                st.write(f"**CPV Label (DE):** {tender.get('CPV Label DE', 'N/A')}")
                st.write(f"**Additional CPV:** {tender.get('Additional CPV', 'N/A')}")
            
            with col2:
                st.markdown("**📅 Important Dates**")
                st.write(f"**Publication Date:** {tender.get('Publication Date', 'N/A')}")
                st.write(f"**Submission Deadline:** {tender.get('Submission Deadline', 'N/A')}")
                st.markdown("**🏢 Organizations**")
                st.write(f"**Procurement Office:** {tender.get('Procurement Office', 'N/A')}")
                st.write(f"**Requesting Unit:** {tender.get('Requesting Unit', 'N/A')}")
            
            # Eligibility and participation
            st.markdown("**📋 Requirements**")
            st.write(f"**Eligibility Criteria:** {tender.get('Eligibility', 'N/A')}")
            st.write(f"**Language of Procedure:** {tender.get('Language of Procedure', 'N/A')}")
    else:
        st.info("No tenders match your filters")
    
    # Download button
    st.markdown("---")
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Download filtered data as CSV",
        data=csv,
        file_name=f"simap_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

else:
    st.warning("⚠️ No data available. Please run the pipeline first.")
    
    st.markdown("""
    ### 🚀 How to get data:
    
    #### Daily data (today):
    ```bash
    python 01a_run_daily_pipeline.py
    ```
    
    #### Weekly data (last 7 days):
    ```bash
    python 01b_run_weekly_pipeline.py
    ```
    """)

# Footer
st.markdown("---")
st.caption("SIMAP Tender Monitor | BAK Economics | Data source: prod.simap.ch")

