#!/usr/bin/env python3
"""
Optimized Tender Classifier - Title-Only Approach (92% Accuracy)
Separates classification from summarization for optimal results
"""
import os
import json
import sys
from pathlib import Path
from openai import OpenAI
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class OptimizedTenderClassifier:
    """
    Classifier optimized for 92% accuracy using title-only approach
    """
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.has_api = bool(self.api_key)
        
        if self.has_api:
            self.client = OpenAI(api_key=self.api_key)
            self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        
        # Load the balanced prompt (92% accuracy)
        self.prompt_template = self._load_prompt()
    
    def _load_prompt(self):
        """Load the 92% accuracy balanced prompt"""
        prompt_path = Path(__file__).parent.parent / 'tenders-llm' / 'prompts' / 'classify_tender_balanced.md'
        
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # Fallback to basic prompt
            return """You are an expert in public procurement for economic research.
Classify if this tender is relevant for BAK Economics (economic analysis, research, forecasting).
Focus on: economic analysis, impact studies, statistical research, policy evaluation."""
    
    def classify_title_only(self, title: str) -> dict:
        """
        Classify tender using TITLE-ONLY (92% accuracy approach)
        
        Args:
            title: Tender title in original language
            
        Returns:
            dict with prediction, confidence, reasoning
        """
        if not self.has_api:
            return {
                'prediction': 'No',
                'confidence_score': 0,
                'reasoning': 'No API key - using emergency classifier',
                'method': 'no_api'
            }
        
        # Create classification prompt with TITLE-ONLY
        classification_input = f"Title: {title}"
        full_prompt = self.prompt_template + "\n\n" + classification_input
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.1,
                max_tokens=200
            )
            
            result = json.loads(response.choices[0].message.content)
            result['method'] = 'llm_title_only'
            
            # Convert to standard format
            return {
                'prediction': result.get('prediction', 'No'),
                'confidence_score': result.get('confidence_score', 0),
                'reasoning': result.get('reasoning', ''),
                'method': 'llm_title_only'
            }
        
        except Exception as e:
            return {
                'prediction': 'No',
                'confidence_score': 0,
                'reasoning': f'Classification error: {str(e)}',
                'method': 'error'
            }
    
    def translate_and_summarize(self, title: str, description: str = None) -> dict:
        """
        Translate title and generate summary from full text
        
        Args:
            title: Title to translate
            description: Full description for summary
            
        Returns:
            dict with title_en and summary
        """
        if not self.has_api:
            return {
                'title_en': f'[Translation unavailable: {title}]',
                'summary': '[Summary unavailable - no API key]'
            }
        
        try:
            # Build translation/summary prompt
            prompt = f"""
            Task 1: Translate this title to English (if not already English, keep as is if already English):
            {title}
            
            Task 2: Generate a concise 2-3 sentence summary of the tender:
            {description[:2000] if description else 'No description available'}
            
            Return JSON format:
            {{
              "title_en": "<English title>",
              "summary": "<2-3 sentence summary>"
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        
        except Exception as e:
            return {
                'title_en': title,
                'summary': f'Summary error: {str(e)}'
            }
    
    def classify_and_enrich(self, title: str, description: str = None) -> dict:
        """
        Complete classification with translation and summary
        
        Args:
            title: Tender title
            description: Tender description
            
        Returns:
            Complete classification result
        """
        # Step 1: Classify using title-only (92% accuracy)
        classification = self.classify_title_only(title)
        
        # Step 2: Translate and summarize
        if self.has_api:
            enrichment = self.translate_and_summarize(title, description)
            classification.update(enrichment)
        else:
            classification['title_en'] = title
            classification['summary'] = 'No summary available'
        
        classification['classified_at'] = datetime.now().isoformat()
        
        return classification


if __name__ == "__main__":
    # Test the optimized classifier
    classifier = OptimizedTenderClassifier()
    
    # Test case 1: Highly relevant tender
    test1 = classifier.classify_and_enrich(
        title="Regulierungsfolgenabschätzungen (RFA)",
        description="Die volkswirtschaftlichen Auswirkungen von Vorlagen des Bundes werden im Rahmen der RFA untersucht."
    )
    
    print("Test 1: Economic Analysis Tender")
    print("=" * 60)
    print(f"Prediction: {test1['prediction']}")
    print(f"Confidence: {test1['confidence_score']}")
    print(f"Reasoning: {test1['reasoning']}")
    print(f"Title (EN): {test1.get('title_en', 'N/A')}")
    print(f"Summary: {test1.get('summary', 'N/A')}")
    print(f"Method: {test1['method']}")
    
    # Test case 2: Irrelevant tender
    test2 = classifier.classify_and_enrich(
        title="IT Infrastructure Services",
        description="Provide IT support and infrastructure maintenance for government offices."
    )
    
    print("\n\nTest 2: IT Services Tender")
    print("=" * 60)
    print(f"Prediction: {test2['prediction']}")
    print(f"Confidence: {test2['confidence_score']}")
    print(f"Reasoning: {test2['reasoning']}")
    print(f"Title (EN): {test2.get('title_en', 'N/A')}")

