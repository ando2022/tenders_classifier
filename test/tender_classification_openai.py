#!/usr/bin/env python3
"""
OpenAI-based Tender Classification Script

This script automates the classification of new business tenders using OpenAI's API by:
1. Loading historical tender data and filtering for winning tenders (N2=TRUE)
2. Building a classification prompt based on "winning DNA" from text content
3. Using OpenAI to predict whether new tenders are likely wins (True/False)
4. Outputting results to a new Excel file with predictions and justifications
"""

import pandas as pd
import numpy as np
import openai
import os
import re
from typing import Tuple, List, Dict
import warnings
import time
warnings.filterwarnings('ignore')

class OpenAITenderClassifier:
    """Main class for tender classification using OpenAI API."""
    
    def __init__(self, api_key: str):
        """
        Initialize the classifier with OpenAI API key.
        
        Args:
            api_key: OpenAI API key
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.winning_tenders = None
        self.keywords = []
        self.services = []
        self.winning_dna = ""
        
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
    
    def create_winning_dna(self, winning_tenders: pd.DataFrame, keywords_data: pd.DataFrame, services_data: pd.DataFrame) -> str:
        """
        Create a comprehensive "winning DNA" description from winning tenders and keywords/services.
        
        Args:
            winning_tenders: DataFrame of winning tenders
            keywords_data: DataFrame of keywords
            services_data: DataFrame of services
            
        Returns:
            String containing the winning DNA description
        """
        print("Creating winning DNA profile...")
        
        # Extract and combine text from winning tenders
        winning_texts = []
        for _, row in winning_tenders.iterrows():
            title = str(row.get('title', '')) if pd.notna(row.get('title')) else ''
            full_body = str(row.get('full-body text', '')) if pd.notna(row.get('full-body text')) else ''
            
            combined_text = f"{title} {full_body}".strip()
            if combined_text and len(combined_text) > 10:  # Filter out very short texts
                winning_texts.append(combined_text)
        
        # Extract keywords
        self.keywords = []
        if not keywords_data.empty:
            for _, row in keywords_data.iterrows():
                keyword = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ''
                if keyword and keyword.strip():
                    self.keywords.append(keyword.strip())
        
        # Extract services
        self.services = []
        if not services_data.empty:
            for _, row in services_data.iterrows():
                service = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ''
                if service and service.strip():
                    self.services.append(service.strip())
        
        # Create winning DNA description
        winning_dna_parts = []
        
        # Add sample winning tender descriptions (limit to avoid token limits)
        if winning_texts:
            sample_texts = winning_texts[:10]  # Take first 10 winning tenders
            winning_dna_parts.append("WINNING TENDER EXAMPLES:")
            for i, text in enumerate(sample_texts, 1):
                # Truncate very long texts
                truncated_text = text[:500] + "..." if len(text) > 500 else text
                winning_dna_parts.append(f"{i}. {truncated_text}")
        
        # Add keywords
        if self.keywords:
            winning_dna_parts.append(f"\nIMPORTANT KEYWORDS: {', '.join(self.keywords)}")
        
        # Add services
        if self.services:
            winning_dna_parts.append(f"\nIMPORTANT SERVICES: {', '.join(self.services)}")
        
        # Add analysis instructions
        winning_dna_parts.append("""
ANALYSIS INSTRUCTIONS:
- Look for matches with the keywords and services listed above
- Consider similarity to the winning tender examples
- Evaluate the overall business potential and alignment with our expertise
- Consider the scope, complexity, and type of work described
""")
        
        self.winning_dna = "\n".join(winning_dna_parts)
        
        print(f"Created winning DNA profile with {len(winning_texts)} examples")
        print(f"Added {len(self.keywords)} keywords and {len(self.services)} services")
        
        return self.winning_dna
    
    def create_classification_prompt(self, tender_text: str) -> str:
        """
        Create a prompt for OpenAI to classify a tender.
        
        Args:
            tender_text: Text content of the tender to classify
            
        Returns:
            Formatted prompt for OpenAI
        """
        prompt = f"""
You are an expert business analyst specializing in tender evaluation. Based on our company's winning track record, analyze the following tender and determine if it's likely to be a successful win for us.

{self.winning_dna}

TENDER TO ANALYZE:
{tender_text}

Please provide your analysis in the following JSON format:
{{
    "prediction": true/false,
    "confidence_score": 0-100,
    "justification": "Brief explanation of your reasoning, including specific keywords/services matched or similarities to winning examples"
}}

Consider:
1. Keyword and service matches
2. Similarity to past winning projects
3. Business potential and alignment with our expertise
4. Project scope and complexity

Respond with ONLY the JSON object, no additional text.
"""
        return prompt
    
    def classify_tender_with_openai(self, tender_text: str) -> Tuple[bool, float, str]:
        """
        Use OpenAI to classify a single tender.
        
        Args:
            tender_text: Text content of the tender to classify
            
        Returns:
            Tuple of (prediction, confidence_score, justification)
        """
        if not tender_text or pd.isna(tender_text):
            return False, 0.0, "No text content available"
        
        clean_text = str(tender_text).strip()
        if not clean_text:
            return False, 0.0, "Empty text content"
        
        try:
            prompt = self.create_classification_prompt(clean_text)
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert business analyst. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            try:
                result = json.loads(response_text)
                prediction = bool(result.get('prediction', False))
                confidence = float(result.get('confidence_score', 0))
                justification = str(result.get('justification', 'No justification provided'))
                
                return prediction, confidence, justification
                
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                print(f"Warning: Could not parse OpenAI response as JSON: {response_text}")
                return False, 0.0, "Error parsing OpenAI response"
                
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            return False, 0.0, f"API error: {str(e)}"
    
    def classify_tenders(self, simap_data: pd.DataFrame) -> pd.DataFrame:
        """
        Classify all tenders in the simap data using OpenAI.
        
        Args:
            simap_data: DataFrame containing new tenders to classify
            
        Returns:
            DataFrame with added prediction columns
        """
        print("Classifying new tenders using OpenAI...")
        
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
            
            print(f"Processing tender {idx + 1}/{len(result_df)}...")
            prediction, confidence, justification = self.classify_tender_with_openai(tender_text)
            
            predictions.append(prediction)
            confidence_scores.append(round(confidence, 1))
            justifications.append(justification)
            
            # Add small delay to avoid rate limiting
            time.sleep(0.5)
        
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
    print("=== OpenAI Tender Classification Script ===")
    
    # OpenAI API key
    api_key = "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"
    
    # File paths
    tenders_file = "../data/raw/tenders.xlsx"
    prompt_data_file = "../data/raw/Prompt_data.xlsx"
    output_file = "prompt_data_with_predictions_openai.xlsx"
    
    # Check if input files exist
    if not os.path.exists(tenders_file):
        print(f"Error: {tenders_file} not found!")
        return
    
    if not os.path.exists(prompt_data_file):
        print(f"Error: {prompt_data_file} not found!")
        return
    
    try:
        # Initialize classifier
        classifier = OpenAITenderClassifier(api_key)
        
        # Load data
        winning_tenders, simap_data, keywords_data, services_data = classifier.load_data(
            tenders_file, prompt_data_file
        )
        
        # Create winning DNA
        classifier.create_winning_dna(winning_tenders, keywords_data, services_data)
        
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
