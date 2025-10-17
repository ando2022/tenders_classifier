"""
Translation service for tender titles and descriptions
Supports OpenAI translation or fallback to basic translation
"""
import os
from openai import OpenAI

class TenderTranslator:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            self.has_api = True
        else:
            self.has_api = False
    
    def translate_to_english(self, text, source_language='auto'):
        """
        Translate text to English
        
        Args:
            text: Text to translate
            source_language: Source language (auto-detect if 'auto')
        
        Returns:
            Translated text or original if translation fails
        """
        if not text or len(text.strip()) == 0:
            return ""
        
        if not self.has_api:
            return f"[Translation unavailable - no API key. Original: {text[:100]}...]"
        
        try:
            prompt = f"""
            Translate the following text to English. 
            If it's already in English, return it as is.
            Only return the translation, no explanations.
            
            Text to translate:
            {text}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000
            )
            
            translation = response.choices[0].message.content.strip()
            return translation
        
        except Exception as e:
            print(f"Translation error: {e}")
            return text  # Return original on error
    
    def translate_tender(self, title, description=None):
        """
        Translate both title and description of a tender
        
        Returns:
            dict with title_en and description_en
        """
        result = {
            'title_en': self.translate_to_english(title),
            'description_en': None
        }
        
        if description and len(description.strip()) > 0:
            # Limit description length for API
            desc_to_translate = description[:2000]
            if len(description) > 2000:
                desc_to_translate += "..."
            
            result['description_en'] = self.translate_to_english(desc_to_translate)
        
        return result
    
    def batch_translate_tenders(self, tenders_df, title_col='title_original', desc_col='description_original'):
        """
        Translate a batch of tenders
        
        Args:
            tenders_df: DataFrame with tenders
            title_col: Column name for title
            desc_col: Column name for description
        
        Returns:
            DataFrame with added title_en and description_en columns
        """
        import pandas as pd
        
        translations = []
        for idx, row in tenders_df.iterrows():
            trans = self.translate_tender(
                title=row[title_col],
                description=row.get(desc_col, '')
            )
            translations.append(trans)
        
        # Add translations to dataframe
        tenders_df['title_en'] = [t['title_en'] for t in translations]
        tenders_df['description_en'] = [t['description_en'] for t in translations]
        
        return tenders_df

# Simple fallback translator without API
class SimpleTranslator:
    """Basic translator that just marks text as needing translation"""
    
    def translate_to_english(self, text, source_language='auto'):
        if not text:
            return ""
        # Return a marker indicating manual translation needed
        return f"[TO TRANSLATE: {text[:100]}{'...' if len(text) > 100 else ''}]"
    
    def translate_tender(self, title, description=None):
        return {
            'title_en': self.translate_to_english(title),
            'description_en': self.translate_to_english(description) if description else None
        }

if __name__ == "__main__":
    # Test translator
    translator = TenderTranslator()
    
    test_title = "Regulierungsfolgenabschätzungen (RFA)"
    test_desc = "Die volkswirtschaftlichen Auswirkungen von Vorlagen des Bundes werden untersucht."
    
    result = translator.translate_tender(test_title, test_desc)
    print("Translation Test:")
    print(f"Original title: {test_title}")
    print(f"Translated title: {result['title_en']}")
    print(f"\nOriginal desc: {test_desc}")
    print(f"Translated desc: {result['description_en']}")

