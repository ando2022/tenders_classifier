#!/usr/bin/env python3
"""
Tender Classification Script

This script automates the classification of new business tenders by:
1. Loading historical tender data and filtering for winning tenders (N2=TRUE)
2. Building a classification model based on "winning DNA" from text content
3. Predicting whether new tenders are likely wins (True/False)
4. Outputting results to a new Excel file with predictions and justifications
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import os
from typing import Tuple, List, Dict
import warnings
warnings.filterwarnings('ignore')

class TenderClassifier:
    """Main class for tender classification using TF-IDF similarity scoring."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2
        )
        self.winning_corpus = None
        self.keywords = []
        self.services = []
        self.tfidf_matrix = None
        
    def load_data(self, tenders_file: str, prompt_data_file: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Load data from Excel files.
        
        Args:
            tenders_file: Path to tenders.xlsx
            prompt_data_file: Path to Prompt_data.xlsx
            
        Returns:
            Tuple of (winning_tenders, simap_data, keywords_data, services_data)
        """
        print("Loading data from Excel files...")
        
        # Load tenders data and filter for winning tenders (N2=TRUE)
        tenders_df = pd.read_excel(tenders_file)
        print(f"Loaded {len(tenders_df)} total tenders")
        
        # Filter for winning tenders (N2=TRUE)
        winning_tenders = tenders_df[tenders_df['N2'] == True].copy()
        print(f"Found {len(winning_tenders)} winning tenders (N2=TRUE)")
        
        # Load prompt data sheets
        simap_data = pd.read_excel(prompt_data_file, sheet_name='simap')
        keywords_data = pd.read_excel(prompt_data_file, sheet_name='keywords')
        services_data = pd.read_excel(prompt_data_file, sheet_name='services')
        
        print(f"Loaded {len(simap_data)} new tenders to classify")
        print(f"Loaded {len(keywords_data)} keywords")
        print(f"Loaded {len(services_data)} services")
        
        return winning_tenders, simap_data, keywords_data, services_data
    
    def create_winning_corpus(self, winning_tenders: pd.DataFrame, keywords_data: pd.DataFrame, services_data: pd.DataFrame) -> List[str]:
        """
        Create training corpus from winning tenders and augment with keywords/services.
        
        Args:
            winning_tenders: DataFrame of winning tenders
            keywords_data: DataFrame of keywords
            services_data: DataFrame of services
            
        Returns:
            List of text documents for the winning corpus
        """
        print("Creating winning DNA corpus...")
        
        corpus_docs = []
        
        # Combine title and full-body text from winning tenders
        for _, row in winning_tenders.iterrows():
            # Handle potential missing values
            title = str(row.get('title', '')) if pd.notna(row.get('title')) else ''
            full_body = str(row.get('full-body text', '')) if pd.notna(row.get('full-body text')) else ''
            
            # Combine title and body text
            combined_text = f"{title} {full_body}".strip()
            if combined_text:
                corpus_docs.append(combined_text)
        
        # Augment with keywords (repeat each keyword multiple times for emphasis)
        self.keywords = []
        if not keywords_data.empty:
            for _, row in keywords_data.iterrows():
                keyword = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ''
                if keyword and keyword.strip():
                    self.keywords.append(keyword.strip())
                    # Add keyword multiple times to increase its weight
                    for _ in range(5):
                        corpus_docs.append(keyword.strip())
        
        # Augment with services (repeat each service multiple times for emphasis)
        self.services = []
        if not services_data.empty:
            for _, row in services_data.iterrows():
                service = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ''
                if service and service.strip():
                    self.services.append(service.strip())
                    # Add service multiple times to increase its weight
                    for _ in range(5):
                        corpus_docs.append(service.strip())
        
        print(f"Created corpus with {len(corpus_docs)} documents")
        print(f"Added {len(self.keywords)} keywords and {len(self.services)} services")
        
        return corpus_docs
    
    def build_model(self, corpus_docs: List[str]):
        """
        Build TF-IDF model from the winning corpus.
        
        Args:
            corpus_docs: List of text documents for training
        """
        print("Building TF-IDF model...")
        
        # Fit TF-IDF vectorizer on the winning corpus
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus_docs)
        self.winning_corpus = corpus_docs
        
        print(f"TF-IDF matrix shape: {self.tfidf_matrix.shape}")
        print(f"Vocabulary size: {len(self.vectorizer.vocabulary_)}")
    
    def predict_tender(self, tender_text: str) -> Tuple[bool, float, str]:
        """
        Predict whether a tender is likely to win.
        
        Args:
            tender_text: Text content of the tender to classify
            
        Returns:
            Tuple of (prediction, confidence_score, justification)
        """
        if not tender_text or pd.isna(tender_text):
            return False, 0.0, "No text content available"
        
        # Clean and prepare text
        clean_text = str(tender_text).strip()
        if not clean_text:
            return False, 0.0, "Empty text content"
        
        # Transform tender text to TF-IDF vector
        tender_vector = self.vectorizer.transform([clean_text])
        
        # Calculate cosine similarity with winning corpus
        similarities = cosine_similarity(tender_vector, self.tfidf_matrix)
        max_similarity = np.max(similarities)
        avg_similarity = np.mean(similarities)
        
        # Use a combination of max and average similarity for scoring
        combined_score = (max_similarity * 0.7) + (avg_similarity * 0.3)
        
        # Convert to percentage confidence
        confidence_score = min(100.0, max(0.0, combined_score * 100))
        
        # Determine prediction based on threshold
        prediction_threshold = 0.15  # Adjust this threshold as needed
        prediction = combined_score >= prediction_threshold
        
        # Generate justification
        justification_parts = []
        
        # Check for keyword matches
        matched_keywords = []
        for keyword in self.keywords:
            if keyword.lower() in clean_text.lower():
                matched_keywords.append(keyword)
        
        if matched_keywords:
            justification_parts.append(f"Matches keywords: {matched_keywords[:3]}")  # Limit to first 3
        
        # Check for service matches
        matched_services = []
        for service in self.services:
            if service.lower() in clean_text.lower():
                matched_services.append(service)
        
        if matched_services:
            justification_parts.append(f"Matches services: {matched_services[:3]}")  # Limit to first 3
        
        # Add similarity information
        if max_similarity > 0.1:
            justification_parts.append(f"High similarity to past winning projects ({max_similarity:.2f})")
        elif avg_similarity > 0.05:
            justification_parts.append(f"Moderate similarity to past winning projects ({avg_similarity:.2f})")
        else:
            justification_parts.append("Low similarity to past winning projects")
        
        justification = "; ".join(justification_parts) if justification_parts else "No clear indicators found"
        
        return prediction, confidence_score, justification
    
    def classify_tenders(self, simap_data: pd.DataFrame) -> pd.DataFrame:
        """
        Classify all tenders in the simap data.
        
        Args:
            simap_data: DataFrame containing new tenders to classify
            
        Returns:
            DataFrame with added prediction columns
        """
        print("Classifying new tenders...")
        
        # Create a copy to avoid modifying original
        result_df = simap_data.copy()
        
        # Initialize prediction columns
        predictions = []
        confidence_scores = []
        justifications = []
        
        # Process each tender
        for idx, row in result_df.iterrows():
            # Use 'topic' column for classification
            tender_text = row.get('topic', '')
            
            prediction, confidence, justification = self.predict_tender(tender_text)
            
            predictions.append(prediction)
            confidence_scores.append(round(confidence, 1))
            justifications.append(justification)
            
            if (idx + 1) % 10 == 0:
                print(f"Processed {idx + 1}/{len(result_df)} tenders")
        
        # Add prediction columns
        result_df['Prediction'] = predictions
        result_df['Confidence_Score'] = confidence_scores
        result_df['Justification'] = justifications
        
        print(f"Classification complete. {sum(predictions)}/{len(predictions)} tenders predicted as wins")
        
        return result_df
    
    def save_results(self, simap_data: pd.DataFrame, keywords_data: pd.DataFrame, 
                    services_data: pd.DataFrame, output_file: str):
        """
        Save results to Excel file with multiple sheets.
        
        Args:
            simap_data: Updated simap data with predictions
            keywords_data: Original keywords data
            services_data: Original services data
            output_file: Path for output Excel file
        """
        print(f"Saving results to {output_file}...")
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Save updated simap data with predictions
            simap_data.to_excel(writer, sheet_name='simap', index=False)
            
            # Save original keywords data
            keywords_data.to_excel(writer, sheet_name='keywords', index=False)
            
            # Save original services data
            services_data.to_excel(writer, sheet_name='services', index=False)
        
        print(f"Results saved successfully to {output_file}")

def main():
    """Main function to run the tender classification process."""
    print("=== Tender Classification Script ===")
    
    # File paths
    tenders_file = "data/raw/tenders.xlsx"
    prompt_data_file = "data/raw/Prompt_data.xlsx"
    output_file = "prompt_data_with_predictions.xlsx"
    
    # Check if input files exist
    if not os.path.exists(tenders_file):
        print(f"Error: {tenders_file} not found!")
        return
    
    if not os.path.exists(prompt_data_file):
        print(f"Error: {prompt_data_file} not found!")
        return
    
    try:
        # Initialize classifier
        classifier = TenderClassifier()
        
        # Load data
        winning_tenders, simap_data, keywords_data, services_data = classifier.load_data(
            tenders_file, prompt_data_file
        )
        
        # Create winning corpus
        corpus_docs = classifier.create_winning_corpus(
            winning_tenders, keywords_data, services_data
        )
        
        # Build classification model
        classifier.build_model(corpus_docs)
        
        # Classify new tenders
        classified_data = classifier.classify_tenders(simap_data)
        
        # Save results
        classifier.save_results(classified_data, keywords_data, services_data, output_file)
        
        print("\n=== Classification Summary ===")
        print(f"Total tenders classified: {len(classified_data)}")
        print(f"Predicted wins: {sum(classified_data['Prediction'])}")
        print(f"Predicted losses: {sum(~classified_data['Prediction'])}")
        print(f"Average confidence: {classified_data['Confidence_Score'].mean():.1f}%")
        
        print(f"\nResults saved to: {output_file}")
        
    except Exception as e:
        print(f"Error during classification: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
