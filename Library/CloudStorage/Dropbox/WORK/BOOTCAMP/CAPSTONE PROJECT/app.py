"""
Streamlit Tender Management App
Complete single-file implementation with translation and classification
"""

import streamlit as st
import sqlite3
import pandas as pd
import json
import os
import glob
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
import time

# Import scrapers and classifier
try:
    from simap_scraper import simap_main
    from evergabe_scraper import crawl_evergabe
    from classifier import ProductionTenderClassifier
    SCRAPERS_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Could not import scrapers: {e}")
    SCRAPERS_AVAILABLE = False

# Try to import OpenAI for translation
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    st.warning("⚠️ OpenAI not installed. Install with: pip install openai")

# ============================================================================
# DATABASE SETUP
# ============================================================================

DB_PATH = "tenders.db"

def cleanup_temp_files():
    """Delete any leftover CSV files from previous runs"""
    import glob
    patterns = ["simap_export_*.csv", "evergabe_filtered_*.csv"]
    for pattern in patterns:
        for file in glob.glob(pattern):
            try:
                os.remove(file)
                print(f"🗑️  Cleaned up: {file}")
            except:
                pass

def init_database():
    """Initialize SQLite database with schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tenders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            publication_id TEXT,
            title TEXT,
            title_en TEXT,
            description TEXT,
            description_en TEXT,
            organization TEXT,
            url TEXT,
            deadline TEXT,
            publication_date TEXT,
            cpv_codes TEXT,
            languages TEXT,
            classification TEXT,
            confidence REAL,
            reasoning TEXT,
            user_feedback TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            classified_at TIMESTAMP,
            UNIQUE(source, publication_id, title)
        )
    """)
    
    conn.commit()
    conn.close()

def get_last_scrape_date(source: str = None) -> Optional[date]:
    """Get the last scrape date from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if source:
        cursor.execute(
            "SELECT MAX(scraped_at) FROM tenders WHERE source = ?",
            (source,)
        )
    else:
        cursor.execute("SELECT MAX(scraped_at) FROM tenders")
    
    result = cursor.fetchone()[0]
    conn.close()
    
    if result:
        try:
            return datetime.fromisoformat(result).date()
        except:
            return None
    return None

# ============================================================================
# TRANSLATION FUNCTIONS
# ============================================================================

def load_openai_key():
    """Load OpenAI API key from time.config"""
    try:
        if os.path.exists("time.config"):
            with open("time.config", "r", encoding="utf-8") as f:
                config = json.load(f)
                api_key = config.get("openai_api_key")
                if api_key:
                    openai.api_key = api_key
                    return True
    except Exception as e:
        st.error(f"❌ Error loading API key: {e}")
    return False

def translate_batch(texts: List[str], target_lang: str = "en") -> List[str]:
    """
    Translate multiple texts in one API call using ###SEPARATOR###
    Reduces API costs by ~95%
    """
    if not texts:
        return []
    
    # Remove empty texts but remember their positions
    text_indices = [(i, t) for i, t in enumerate(texts) if t and t.strip()]
    if not text_indices:
        return [""] * len(texts)
    
    indices, valid_texts = zip(*text_indices)
    
    # Combine texts with separator
    separator = "\n###SEPARATOR###\n"
    combined = separator.join(valid_texts)
    
    try:
        # Single API call for all texts
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"Translate the following texts to {target_lang}. Keep the ###SEPARATOR### markers exactly as they are."
                },
                {"role": "user", "content": combined}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        translated_combined = response.choices[0].message.content
        translated_parts = translated_combined.split(separator)
        
        # Reconstruct full list with empty strings for skipped items
        result = [""] * len(texts)
        for idx, translation in zip(indices, translated_parts):
            result[idx] = translation.strip()
        
        return result
        
    except Exception as e:
        st.warning(f"⚠️ Batch translation failed: {e}. Falling back to individual translations.")
        # Fallback to individual translation
        result = [""] * len(texts)
        for idx, text in text_indices:
            try:
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": f"Translate to {target_lang}"},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                result[idx] = response.choices[0].message.content.strip()
            except:
                result[idx] = ""
        
        return result

def translate_tender_efficiently(tender_dict: Dict) -> Dict:
    """Translate title + description together (2 texts in 1 call)"""
    title = tender_dict.get("title", "")
    description = tender_dict.get("description", "")
    
    if not title and not description:
        tender_dict["title_en"] = ""
        tender_dict["description_en"] = ""
        return tender_dict
    
    # Batch translate both at once
    translations = translate_batch([title, description])
    
    tender_dict["title_en"] = translations[0]
    tender_dict["description_en"] = translations[1]
    
    return tender_dict

def process_scraped_data_with_translation(df: pd.DataFrame, source: str, progress_callback=None) -> int:
    """
    Process scraped data with efficient batch translation
    1. Detect duplicates
    2. Batch translate new tenders (10 tenders = 20 texts per batch)
    3. Save to database
    4. Return count of NEW tenders added
    """
    if df.empty:
        return 0
    
    # Normalize column names
    df = normalize_columns(df, source)
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check for existing tenders
    new_tenders = []
    for idx, row in df.iterrows():
        cursor.execute(
            "SELECT id FROM tenders WHERE source = ? AND publication_id = ? AND title = ?",
            (source, row.get("publication_id", ""), row.get("title", ""))
        )
        if not cursor.fetchone():
            new_tenders.append(row.to_dict())
    
    if not new_tenders:
        conn.close()
        return 0
    
    st.info(f"🔍 Found {len(new_tenders)} new tenders to translate")
    
    # Batch translate (10 tenders at a time = 20 texts per batch)
    batch_size = 10
    translated_tenders = []
    
    for i in range(0, len(new_tenders), batch_size):
        batch = new_tenders[i:i + batch_size]
        
        # Collect all titles and descriptions
        texts_to_translate = []
        for tender in batch:
            texts_to_translate.append(tender.get("title", ""))
            texts_to_translate.append(tender.get("description", ""))
        
        # Translate in one call
        if progress_callback:
            progress_callback(i / len(new_tenders))
        
        translations = translate_batch(texts_to_translate)
        
        # Assign translations back to tenders
        for j, tender in enumerate(batch):
            tender["title_en"] = translations[j * 2]
            tender["description_en"] = translations[j * 2 + 1]
            translated_tenders.append(tender)
    
    if progress_callback:
        progress_callback(1.0)
    
    # Insert into database
    for tender in translated_tenders:
        cursor.execute("""
            INSERT INTO tenders (
                source, publication_id, title, title_en, description, description_en,
                organization, url, deadline, publication_date, cpv_codes, languages
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            source,
            tender.get("publication_id", ""),
            tender.get("title", ""),
            tender.get("title_en", ""),
            tender.get("description", ""),
            tender.get("description_en", ""),
            tender.get("organization", ""),
            tender.get("url", ""),
            tender.get("deadline", ""),
            tender.get("publication_date", ""),
            tender.get("cpv_codes", ""),
            tender.get("languages", "")
        ))
    
    conn.commit()
    conn.close()
    
    return len(translated_tenders)

def normalize_columns(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Normalize column names from different scrapers"""
    # All scrapers should now output the same columns, but just in case:
    required_columns = [
        "organization", "languages", "submission_language", "deadline",
        "cpv_codes", "CPV_labels", "title", "publication_id",
        "publication_date", "url", "description"
    ]
    
    # Ensure all required columns exist
    for col in required_columns:
        if col not in df.columns:
            df[col] = ""
    
    return df[required_columns]

# ============================================================================
# CLASSIFICATION FUNCTIONS
# ============================================================================

def classify_tender(tender_id: int, classifier: ProductionTenderClassifier, conn: sqlite3.Connection):
    """Classify a single tender and update database"""
    cursor = conn.cursor()
    
    # Get tender
    cursor.execute(
        "SELECT title_en, description_en FROM tenders WHERE id = ?",
        (tender_id,)
    )
    result = cursor.fetchone()
    
    if not result:
        return False
    
    title_en, description_en = result
    
    # Classify
    classification_result = classifier.classify_tender(title_en, description_en)
    
    # Update database
    cursor.execute("""
        UPDATE tenders 
        SET classification = ?,
            confidence = ?,
            reasoning = ?,
            classified_at = ?
        WHERE id = ?
    """, (
        classification_result["prediction"],
        classification_result["confidence"],
        classification_result["reasoning"],
        datetime.now().isoformat(),
        tender_id
    ))
    
    conn.commit()
    return True

def classify_all_unclassified(progress_callback=None):
    """Classify all unclassified tenders"""
    # Load API key
    if not load_openai_key():
        st.error("❌ Could not load OpenAI API key from time.config")
        return 0
    
    # Initialize classifier
    classifier = ProductionTenderClassifier()
    
    # Get unclassified tenders
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id FROM tenders 
        WHERE classification IS NULL OR classification = ''
    """)
    
    tender_ids = [row[0] for row in cursor.fetchall()]
    
    if not tender_ids:
        conn.close()
        return 0
    
    # Classify each tender
    for i, tender_id in enumerate(tender_ids):
        classify_tender(tender_id, classifier, conn)
        if progress_callback:
            progress_callback((i + 1) / len(tender_ids))
        time.sleep(0.1)  # Rate limiting
    
    conn.close()
    return len(tender_ids)

# ============================================================================
# STREAMLIT UI
# ============================================================================

def update_time_config(start_date: date, end_date: date):
    """Update time.config with new date range"""
    config = {}
    if os.path.exists("time.config"):
        try:
            with open("time.config", "r", encoding="utf-8") as f:
                config = json.load(f)
        except:
            pass
    
    config["mode"] = "absolute"
    config["from"] = start_date.strftime("%Y-%m-%d")
    config["to"] = end_date.strftime("%Y-%m-%d")
    
    with open("time.config", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

def page_scrape_tenders():
    """Page 1: Scrape Tenders"""
    st.title("🔍 Scrape Tenders")
    
    # Check if operation in progress
    if st.session_state.get('operation_in_progress', False):
        st.error("⚠️ **WARNING: An operation is in progress on another page!**")
        st.warning("Please return to the other page to complete the operation.")
        return
    
    if not SCRAPERS_AVAILABLE:
        st.error("❌ Scrapers not available. Check imports.")
        return
    
    if not OPENAI_AVAILABLE:
        st.error("❌ OpenAI not installed. Translation will not work.")
        return
    
    # Check last scrape date
    last_scrape = get_last_scrape_date()
    if last_scrape:
        st.info(f"📅 Last scrape: {last_scrape.strftime('%Y-%m-%d')}")
        suggested_start = last_scrape + timedelta(days=1)
    else:
        st.info("📅 No previous scrapes found")
        suggested_start = date.today() - timedelta(days=7)
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=suggested_start,
            max_value=date.today()
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=date.today(),
            max_value=date.today()
        )
    
    # Source selector
    st.subheader("Select Sources")
    col1, col2 = st.columns(2)
    with col1:
        scrape_simap = st.checkbox("SIMAP (Swiss)", value=True)
    with col2:
        scrape_evergabe = st.checkbox("Evergabe (German)", value=True)
    
    if not scrape_simap and not scrape_evergabe:
        st.warning("⚠️ Please select at least one source")
        return
    
    # Start scraping button
    if st.button("🚀 Start Scraping", type="primary"):
        # Set operation flag
        st.session_state.operation_in_progress = True
        
        # Warning message
        st.error("⚠️ **SCRAPING IN PROGRESS - DO NOT SWITCH PAGES OR CLOSE WINDOW!**")
        st.info("ℹ️ This may take 1-5 minutes depending on the number of tenders found.")
        
        # Update time.config
        update_time_config(start_date, end_date)
        
        # Load OpenAI key
        if not load_openai_key():
            st.error("❌ Could not load OpenAI API key from time.config")
            st.session_state.operation_in_progress = False
            return
        
        results = {}
        
        # SIMAP
        if scrape_simap:
            st.subheader("📊 SIMAP")
            with st.spinner("Scraping SIMAP..."):
                try:
                    csv_path = simap_main(start_date, end_date)
                    
                    # Load CSV
                    df = pd.read_csv(csv_path, encoding="utf-8-sig")
                    
                    # Translate with progress
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    def update_progress(pct):
                        progress_bar.progress(pct)
                        status_text.text(f"Translating... {int(pct * 100)}%")
                    
                    new_count = process_scraped_data_with_translation(
                        df, "SIMAP", update_progress
                    )
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Delete CSV file after successful processing
                    try:
                        os.remove(csv_path)
                        print(f"🗑️  Deleted temporary file: {os.path.basename(csv_path)}")
                    except Exception as e:
                        print(f"⚠️  Could not delete {os.path.basename(csv_path)}: {e}")
                    
                    results["SIMAP"] = new_count
                    st.success(f"✅ SIMAP: {new_count} new tenders added (with translations)")
                    
                except Exception as e:
                    st.error(f"❌ SIMAP failed: {e}")
                    results["SIMAP"] = 0
        
        # Evergabe
        if scrape_evergabe:
            st.subheader("📊 Evergabe")
            with st.spinner("Scraping Evergabe..."):
                try:
                    csv_path = crawl_evergabe(start_date, end_date, headless=True)
                    
                    # Load CSV
                    df = pd.read_csv(csv_path, encoding="utf-8-sig")
                    
                    # Translate with progress
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    def update_progress(pct):
                        progress_bar.progress(pct)
                        status_text.text(f"Translating... {int(pct * 100)}%")
                    
                    new_count = process_scraped_data_with_translation(
                        df, "Evergabe", update_progress
                    )
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Delete CSV file after successful processing
                    try:
                        os.remove(csv_path)
                        print(f"🗑️  Deleted temporary file: {os.path.basename(csv_path)}")
                    except Exception as e:
                        print(f"⚠️  Could not delete {os.path.basename(csv_path)}: {e}")
                    
                    results["Evergabe"] = new_count
                    st.success(f"✅ Evergabe: {new_count} new tenders added (with translations)")
                    
                except Exception as e:
                    st.error(f"❌ Evergabe failed: {e}")
                    results["Evergabe"] = 0
        
        # Summary
        st.subheader("📈 Summary")
        total = sum(results.values())
        st.metric("Total New Tenders", total)
        for source, count in results.items():
            st.write(f"- {source}: {count} tenders")
        
        # Clear operation flag
        st.session_state.operation_in_progress = False
        st.success("✅ **Scraping complete! You can now navigate freely.**")

def page_view_classify():
    """Page 2: View & Classify"""
    st.title("📋 View & Classify Tenders")
    
    # Check if operation in progress  
    if st.session_state.get('operation_in_progress', False):
        st.error("⚠️ **WARNING: An operation is in progress on another page!**")
        st.warning("Please return to the other page to complete the operation.")
        return
    
    # Filters
    st.subheader("🔍 Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        classification_filter = st.selectbox(
            "Classification",
            ["All", "Yes", "No", "Unclassified"]
        )
    
    with col2:
        source_filter = st.selectbox(
            "Source",
            ["All", "SIMAP", "Evergabe"]
        )
    
    with col3:
        view_mode = st.radio(
            "View Mode",
            ["📋 Compact", "📖 Detailed"],
            horizontal=True
        )
    
    # Bulk actions
    st.subheader("⚡ Bulk Actions")
    if st.button("🤖 Classify All Unclassified", type="primary"):
        # Set operation flag
        st.session_state.operation_in_progress = True
        
        st.error("⚠️ **CLASSIFICATION IN PROGRESS - DO NOT SWITCH PAGES OR CLOSE WINDOW!**")
        
        with st.spinner("Classifying tenders..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(pct):
                progress_bar.progress(pct)
                status_text.text(f"Classifying... {int(pct * 100)}%")
            
            count = classify_all_unclassified(update_progress)
            
            progress_bar.empty()
            status_text.empty()
            
            # Clear operation flag
            st.session_state.operation_in_progress = False
            
            if count > 0:
                st.success(f"✅ Classified {count} tenders - You can now navigate freely!")
                st.rerun()
            else:
                st.info("ℹ️ No unclassified tenders found")
    
    # Build query
    query = "SELECT * FROM tenders WHERE 1=1"
    params = []
    
    if classification_filter == "Yes":
        query += " AND classification = 'Yes'"
    elif classification_filter == "No":
        query += " AND classification = 'No'"
    elif classification_filter == "Unclassified":
        query += " AND (classification IS NULL OR classification = '')"
    
    if source_filter != "All":
        query += " AND source = ?"
        params.append(source_filter)
    
    query += " ORDER BY scraped_at DESC"
    
    # Load tenders
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    if df.empty:
        st.info("ℹ️ No tenders found")
        return
    
    st.write(f"**Found {len(df)} tenders**")
    
    # Display tenders based on view mode
    is_compact = view_mode == "📋 Compact"
    
    for idx, row in df.iterrows():
        # Icon based on classification
        if row["classification"] == "Yes":
            icon = "✅"
        elif row["classification"] == "No":
            icon = "❌"
        else:
            icon = "⚪"
        
        if is_compact:
            # Compact view - expandable cards
            with st.expander(f"{icon} {row['title_en'][:100]}..."):
                render_tender_details(row)
        else:
            # Detailed view - always expanded
            st.markdown(f"### {icon} {row['title_en']}")
            render_tender_details(row)
            st.divider()

def render_tender_details(row):
    """Render tender details (used by both compact and detailed views)"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.write(f"**Title:** {row['title_en']}")
        st.write(f"**Description:** {row['description_en'][:500]}...")
        st.write(f"**Organization:** {row['organization']}")
        st.write(f"**Source:** {row['source']}")
        st.write(f"**Publication Date:** {row['publication_date']}")
        st.write(f"**Deadline:** {row['deadline']}")
        st.write(f"**URL:** {row['url']}")
    
    with col2:
        if row["classification"]:
            st.write(f"**Classification:** {row['classification']}")
            st.write(f"**Confidence:** {row['confidence']:.1f}%")
            st.write(f"**Reasoning:** {row['reasoning']}")
        else:
            st.write("**Status:** Unclassified")
    
    # Feedback
    st.write("---")
    feedback = st.radio(
        "Feedback",
        ["None", "Correct", "Incorrect"],
        key=f"feedback_{row['id']}",
        index=0 if not row["user_feedback"] else 
              (1 if row["user_feedback"] == "Correct" else 2)
    )
    
    if feedback != "None":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tenders SET user_feedback = ? WHERE id = ?",
            (feedback, row["id"])
        )
        conn.commit()
        conn.close()
        st.success(f"✅ Feedback saved: {feedback}")

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    st.set_page_config(
        page_title="Tender Management System",
        page_icon="📋",
        layout="wide"
    )
    
    # Initialize session state for tracking operations
    if 'operation_in_progress' not in st.session_state:
        st.session_state.operation_in_progress = False
    
    # Initialize database
    init_database()
    
    # Clean up any leftover CSV files
    cleanup_temp_files()
    
    # Sidebar navigation
    st.sidebar.title("📋 Tender Management")
    
    # Show warning in sidebar if operation in progress
    if st.session_state.operation_in_progress:
        st.sidebar.error("⚠️ **OPERATION IN PROGRESS**")
        st.sidebar.warning("Do not switch pages!")
    
    page = st.sidebar.radio(
        "Navigation",
        ["🔍 Scrape Tenders", "📋 View & Classify"],
        disabled=st.session_state.operation_in_progress
    )
    
    # Show database stats
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tenders")
    total_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tenders WHERE classification IS NOT NULL")
    classified_count = cursor.fetchone()[0]
    conn.close()
    
    st.sidebar.write("---")
    st.sidebar.metric("Total Tenders", total_count)
    st.sidebar.metric("Classified", classified_count)
    
    # Route to page
    if page == "🔍 Scrape Tenders":
        page_scrape_tenders()
    else:
        page_view_classify()

if __name__ == "__main__":
    main()