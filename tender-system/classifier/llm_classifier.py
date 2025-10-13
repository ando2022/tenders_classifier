"""
LLM-based tender classifier using the 92% accuracy balanced prompt.
"""
import os
import json
import logging
from typing import Dict, Tuple
from openai import OpenAI
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TenderClassifier:
    """Classify tenders using OpenAI LLM with balanced prompt"""
    
    def __init__(self, prompt_path: str = None):
        """
        Initialize classifier with API key and prompt.
        
        Args:
            prompt_path: Path to the prompt file (defaults to balanced prompt)
        """
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.temperature = float(os.getenv('TEMPERATURE', '0.1'))
        
        # Load prompt (use balanced v2 by default - 92% accuracy)
        if not prompt_path:
            prompt_path = "tenders-llm/prompts/classify_tender_balanced.md"
        
        self.prompt_template = self._load_prompt(prompt_path)
        logger.info(f"✅ Classifier initialized with model={self.model}, prompt={prompt_path}")
    
    def _load_prompt(self, path: str) -> str:
        """Load prompt from file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Prompt file not found: {path}")
            raise
    
    def classify_tender(self, title: str, description: str = None) -> dict:
        """
        Classify a tender as relevant or not, and generate German translation + summary.
        
        Args:
            title: Tender title
            description: Tender description/full text (optional)
            
        Returns:
            Dictionary with:
            - is_relevant (bool)
            - confidence_score (float)
            - reasoning (str)
            - title_de (str): German translation of title
            - summary (str): Brief summary of tender
        """
        # Build the classification input
        tender_text = f"Title: {title}"
        if description and len(description.strip()) > 0:
            # Truncate description if too long
            max_desc_length = 2000
            desc_truncated = description[:max_desc_length]
            if len(description) > max_desc_length:
                desc_truncated += "..."
            tender_text += f"\n\nDescription: {desc_truncated}"
        
        # Create the full prompt with additional instructions
        additional_instructions = """
        
## Additional Output Requirements:

In addition to the classification, please provide:

1. **title_de**: German translation of the tender title (if not already in German, translate it; if already German, keep it as is)
2. **summary**: A concise 2-3 sentence summary (max 200 words) of what the tender is about, highlighting:
   - Main objective/purpose
   - Key deliverables or services required
   - Any specific requirements or focus areas

Output JSON format (strict):
{
  "prediction": "Yes" or "No",
  "confidence_score": <0..100>,
  "reasoning": "<brief explanation>",
  "title_de": "<German title>",
  "summary": "<2-3 sentence summary>"
}
"""
        
        full_prompt = self.prompt_template + additional_instructions + f"\n\n---\n\n{tender_text}"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert tender classification assistant with multilingual capabilities."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Parse result
            prediction = result.get('prediction', 'No')
            is_relevant = prediction.lower() == 'yes'
            confidence = float(result.get('confidence_score', 0))
            reasoning = result.get('reasoning', 'No reasoning provided')
            title_de = result.get('title_de', title)  # Fallback to original title
            summary = result.get('summary', description[:200] if description else 'No summary available')
            
            logger.debug(f"Classified: {title[:50]}... -> {prediction} ({confidence}%)")
            
            return {
                'is_relevant': is_relevant,
                'confidence_score': confidence,
                'reasoning': reasoning,
                'title_de': title_de,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error classifying tender: {e}")
            # Return conservative default
            return {
                'is_relevant': False,
                'confidence_score': 0.0,
                'reasoning': f"Classification error: {str(e)}",
                'title_de': title,
                'summary': description[:200] if description else 'Error generating summary'
            }
    
    def classify_batch(self, tenders: list) -> list:
        """
        Classify multiple tenders with German translation and summaries.
        
        Args:
            tenders: List of tender dicts with 'title' and 'description'
            
        Returns:
            List of classification results with German titles and summaries
        """
        results = []
        
        logger.info(f"🔬 Classifying {len(tenders)} tenders (with DE translation & summaries)...")
        
        for i, tender in enumerate(tenders, 1):
            title = tender.get('title', '')
            description = tender.get('description', '')
            
            result = self.classify_tender(title, description)
            
            # Add tender_id to result
            result['tender_id'] = tender.get('tender_id')
            results.append(result)
            
            if i % 10 == 0:
                logger.info(f"  Progress: {i}/{len(tenders)} classified")
        
        relevant_count = sum(1 for r in results if r['is_relevant'])
        logger.info(f"✅ Classification complete: {relevant_count}/{len(tenders)} marked as relevant")
        
        return results

