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
import openai
import os
from typing import Tuple
import warnings
import time
from tqdm import tqdm
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
        
        # Create progress bar for data loading
        with tqdm(total=4, desc="Loading data", unit="file", ncols=100) as pbar:
            # Load tenders data and filter for winning tenders (N2=TRUE)
            pbar.set_description("Loading tenders data")
            tenders_df = pd.read_excel(tenders_file)
            pbar.update(1)
            
            # Filter for winning tenders (N2=1)
            pbar.set_description("Filtering winning tenders")
            winning_tenders = tenders_df[tenders_df['N2'] == 1].copy()
            pbar.update(1)
            
            # Load prompt data sheets
            pbar.set_description("Loading simap data")
            simap_data = pd.read_excel(prompt_data_file, sheet_name='simap')
            pbar.update(1)
            
            pbar.set_description("Loading keywords and services")
            keywords_data = pd.read_excel(prompt_data_file, sheet_name='keywords')
            services_data = pd.read_excel(prompt_data_file, sheet_name='services')
            pbar.update(1)
        
        print(f"SUCCESS: Loaded {len(tenders_df)} total tenders")
        print(f"SUCCESS: Found {len(winning_tenders)} winning tenders (N2=1)")
        print(f"SUCCESS: Loaded {len(simap_data)} new tenders to classify")
        print(f"SUCCESS: Loaded {len(keywords_data)} keywords")
        print(f"SUCCESS: Loaded {len(services_data)} services")
        
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
        
        # Create progress bar for DNA creation
        with tqdm(total=3, desc="Building winning DNA", unit="step", ncols=100) as pbar:
            # Extract and combine text from winning tenders
            pbar.set_description("Processing winning tenders")
            winning_texts = []
            for _, row in winning_tenders.iterrows():
                title = str(row.get('title', '')) if pd.notna(row.get('title')) else ''
                full_body = str(row.get('full-body text', '')) if pd.notna(row.get('full-body text')) else ''
                
                combined_text = f"{title} {full_body}".strip()
                if combined_text and len(combined_text) > 10:  # Filter out very short texts
                    winning_texts.append(combined_text)
            pbar.update(1)
            
            # Extract keywords
            pbar.set_description("Extracting keywords")
            self.keywords = []
            if not keywords_data.empty:
                for _, row in keywords_data.iterrows():
                    keyword = str(row['Studie']) if pd.notna(row['Studie']) else ''
                    if keyword and keyword.strip():
                        self.keywords.append(keyword.strip())
            pbar.update(1)
            
            # Extract services
            pbar.set_description("Extracting services")
            self.services = []
            if not services_data.empty:
                for _, row in services_data.iterrows():
                    service_name = str(row['service name']) if pd.notna(row['service name']) else ''
                    service_desc = str(row['description']) if pd.notna(row['description']) else ''
                    service = f"{service_name} {service_desc}".strip()
                    if service and service.strip():
                        self.services.append(service.strip())
            pbar.update(1)
        
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
        
        print(f"SUCCESS: Created winning DNA profile with {len(winning_texts)} examples")
        print(f"SUCCESS: Added {len(self.keywords)} keywords and {len(self.services)} services")
        
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
                model="gpt-4o-mini",
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
        
        # Create progress bar
        total_tenders = len(result_df)
        progress_bar = tqdm(total=total_tenders, desc="Classifying tenders", 
                          unit="tender", ncols=100, 
                          bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]')
        
        # Process each tender
        for idx, row in result_df.iterrows():
            # Use 'Topic' column for classification
            tender_text = row.get('Topic', '')
            
            # Update progress bar description with current tender info
            progress_bar.set_description(f"Processing tender {idx + 1}/{total_tenders}")
            
            prediction, confidence, justification = self.classify_tender_with_openai(tender_text)
            
            predictions.append(prediction)
            confidence_scores.append(round(confidence, 1))
            justifications.append(justification)
            
            # Update progress bar
            progress_bar.update(1)
            
            # Add small delay to avoid rate limiting
            time.sleep(0.5)
        
        # Close progress bar
        progress_bar.close()
        
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
        
        # Create progress bar for saving
        with tqdm(total=3, desc="Saving results", unit="sheet", ncols=100) as pbar:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Save updated simap data with predictions
                pbar.set_description("Saving simap data")
                simap_data.to_excel(writer, sheet_name='simap', index=False)
                pbar.update(1)
                
                # Save original keywords data
                pbar.set_description("Saving keywords data")
                keywords_data.to_excel(writer, sheet_name='keywords', index=False)
                pbar.update(1)
                
                # Save original services data
                pbar.set_description("Saving services data")
                services_data.to_excel(writer, sheet_name='services', index=False)
                pbar.update(1)
        
        print(f"SUCCESS: Results saved successfully to {output_file}")

def main():
    """Main function to run the tender classification process."""
    print("=" * 60)
    print("OpenAI Tender Classification Script")
    print("=" * 60)
    
    # OpenAI API key
    api_key = "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"
    
    # File paths
    tenders_file = "../data/raw/tenders.xlsx"
    prompt_data_file = "../data/raw/Prompt_data.xlsx"
    output_file = "prompt_data_with_predictions_openai.xlsx"
    
    # Check if input files exist
    print("Checking input files...")
    if not os.path.exists(tenders_file):
        print(f"ERROR: {tenders_file} not found!")
        return
    
    if not os.path.exists(prompt_data_file):
        print(f"ERROR: {prompt_data_file} not found!")
        return
    
    print("SUCCESS: All input files found!")
    print()
    
    try:
        # Initialize classifier
        print("Initializing OpenAI classifier...")
        classifier = OpenAITenderClassifier(api_key)
        print("SUCCESS: Classifier initialized!")
        print()
        
        # Load data
        winning_tenders, simap_data, keywords_data, services_data = classifier.load_data(
            tenders_file, prompt_data_file
        )
        print()
        
        # Create winning DNA
        classifier.create_winning_dna(winning_tenders, keywords_data, services_data)
        print()
        
        # Classify new tenders
        classified_data = classifier.classify_tenders(simap_data)
        print()
        
        # Save results
        classifier.save_results(classified_data, keywords_data, services_data, output_file)
        print()
        
        # Final summary
        print("=" * 60)
        print("CLASSIFICATION SUMMARY")
        print("=" * 60)
        print(f"Total tenders classified: {len(classified_data)}")
        print(f"Predicted wins: {sum(classified_data['Prediction'])}")
        print(f"Predicted losses: {sum(~classified_data['Prediction'])}")
        print(f"Average confidence: {classified_data['Confidence_Score'].mean():.1f}%")
        print(f"Results saved to: {output_file}")
        print("=" * 60)
        print("Classification complete!")
        
    except Exception as e:
        print(f"ERROR during classification: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
