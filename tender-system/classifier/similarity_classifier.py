"""
Emergency fallback classifier using cosine similarity.
Matches new tenders against known positive cases when OpenAI is unavailable.
"""
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import LabelEncoder
import pickle
import os
from typing import List, Dict, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SimilarityClassifier:
    """
    Fallback classifier using cosine similarity against known positive cases.
    """
    
    def __init__(self, model_path: str = "classifier/similarity_model.pkl"):
        self.model_path = model_path
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95
        )
        self.positive_cases = []
        self.vectorizer_fitted = False
        self.similarity_threshold = 0.3  # Adjustable threshold
        
        # Load existing model if available
        self.load_model()

        # Auto-load positive cases from DB on first init if none loaded
        # This ensures the emergency classifier immediately leverages
        # previously confirmed positive tenders (titles + full texts)
        try:
            if not self.positive_cases:
                from database.models import get_session  # lazy import to avoid cycles
                session = get_session()
                # Load high-confidence positives as exemplars
                self.add_positive_cases_from_database(session, min_confidence=80.0)
                if self.positive_cases and not getattr(self, 'tfidf_matrix', None):
                    self.build_model()
                    self.save_model()
        except Exception as autoload_exc:
            logger.warning(f"Emergency classifier DB autoload skipped: {autoload_exc}")
    
    def add_positive_case(self, title: str, description: str = None, 
                         confidence: float = 1.0, source: str = "manual"):
        """
        Add a positive case to the training set.
        
        Args:
            title: Tender title
            description: Tender description
            confidence: Confidence score (0-1)
            source: Source of the positive case
        """
        case = {
            'title': title,
            'description': description or '',
            'confidence': confidence,
            'source': source,
            'added_at': datetime.now()
        }
        self.positive_cases.append(case)
        logger.info(f"Added positive case: {title[:50]}...")
    
    def build_model(self):
        """
        Build the similarity model from positive cases.
        """
        if not self.positive_cases:
            logger.warning("No positive cases available. Please add some positive cases first.")
            return False
        
        # Prepare text data
        texts = []
        for case in self.positive_cases:
            # Combine title and description
            text = f"{case['title']} {case['description']}"
            texts.append(text)
        
        # Fit TF-IDF vectorizer
        try:
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
            self.vectorizer_fitted = True
            logger.info(f"Built similarity model with {len(texts)} positive cases")
            return True
        except Exception as e:
            logger.error(f"Error building similarity model: {e}")
            return False
    
    def classify_tender(self, title: str, description: str = None) -> Dict:
        """
        Classify a tender using cosine similarity.
        
        Args:
            title: Tender title
            description: Tender description
            
        Returns:
            Dictionary with classification results
        """
        if not self.vectorizer_fitted:
            logger.warning("Model not fitted. Building model from positive cases...")
            if not self.build_model():
                return self._default_response(title, "Model not available")
        
        # Prepare input text
        input_text = f"{title} {description or ''}"
        
        try:
            # Vectorize input text
            input_vector = self.vectorizer.transform([input_text])
            
            # Calculate cosine similarities
            similarities = cosine_similarity(input_vector, self.tfidf_matrix)[0]
            
            # Find best match
            max_similarity = np.max(similarities)
            best_match_idx = np.argmax(similarities)
            best_match = self.positive_cases[best_match_idx]
            
            # Determine classification
            is_relevant = max_similarity >= self.similarity_threshold
            
            # Calculate confidence score (0-100)
            confidence_score = min(max_similarity * 100, 100)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                max_similarity, best_match, is_relevant
            )
            
            # Generate German title (simple fallback)
            title_de = self._generate_german_title(title)
            
            # Generate summary
            summary = self._generate_summary(title, description, best_match)
            
            logger.debug(f"Classified: {title[:50]}... -> {is_relevant} ({confidence_score:.1f}%)")
            
            return {
                'is_relevant': is_relevant,
                'confidence_score': confidence_score,
                'reasoning': reasoning,
                'title_de': title_de,
                'summary': summary,
                'similarity_score': max_similarity,
                'best_match': best_match['title'],
                'classification_method': 'cosine_similarity'
            }
            
        except Exception as e:
            logger.error(f"Error classifying tender: {e}")
            return self._default_response(title, f"Classification error: {str(e)}")
    
    def classify_batch(self, tenders: List[Dict]) -> List[Dict]:
        """
        Classify multiple tenders using similarity matching.
        
        Args:
            tenders: List of tender dictionaries with 'title' and 'description'
            
        Returns:
            List of classification results
        """
        results = []
        
        logger.info(f"🔍 Classifying {len(tenders)} tenders using similarity matching...")
        
        for i, tender in enumerate(tenders, 1):
            title = tender.get('title', '')
            description = tender.get('description', '')
            
            result = self.classify_tender(title, description)
            result['tender_id'] = tender.get('tender_id')
            results.append(result)
            
            if i % 10 == 0:
                logger.info(f"  Progress: {i}/{len(tenders)} classified")
        
        relevant_count = sum(1 for r in results if r['is_relevant'])
        logger.info(f"✅ Similarity classification complete: {relevant_count}/{len(tenders)} marked as relevant")
        
        return results
    
    def _generate_reasoning(self, similarity: float, best_match: Dict, is_relevant: bool) -> str:
        """Generate reasoning for the classification."""
        if is_relevant:
            return f"High similarity ({similarity:.2f}) to known relevant tender: '{best_match['title'][:50]}...'. This tender matches patterns from previous successful cases."
        else:
            return f"Low similarity ({similarity:.2f}) to known relevant tenders. Best match: '{best_match['title'][:50]}...' but below threshold ({self.similarity_threshold})."
    
    def _generate_german_title(self, title: str) -> str:
        """Simple fallback for German title generation."""
        # This is a basic fallback - in production, you might use a translation service
        # For now, return the original title
        return title
    
    def _generate_summary(self, title: str, description: str, best_match: Dict) -> str:
        """Generate a summary based on the best match."""
        if description:
            # Truncate description if too long
            desc_short = description[:200] + "..." if len(description) > 200 else description
            return f"Similar to '{best_match['title'][:30]}...'. {desc_short}"
        else:
            return f"Similar to known relevant tender: '{best_match['title'][:50]}...'"
    
    def _default_response(self, title: str, reason: str) -> Dict:
        """Return default response when classification fails."""
        return {
            'is_relevant': False,
            'confidence_score': 0.0,
            'reasoning': reason,
            'title_de': title,
            'summary': 'Classification not available',
            'similarity_score': 0.0,
            'best_match': None,
            'classification_method': 'fallback'
        }
    
    def save_model(self):
        """Save the model to disk."""
        try:
            model_data = {
                'positive_cases': self.positive_cases,
                'vectorizer': self.vectorizer if self.vectorizer_fitted else None,
                'tfidf_matrix': self.tfidf_matrix if self.vectorizer_fitted else None,
                'similarity_threshold': self.similarity_threshold,
                'vectorizer_fitted': self.vectorizer_fitted
            }
            
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"Saved similarity model to {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False
    
    def load_model(self):
        """Load the model from disk."""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                self.positive_cases = model_data.get('positive_cases', [])
                self.vectorizer = model_data.get('vectorizer', self.vectorizer)
                self.tfidf_matrix = model_data.get('tfidf_matrix', None)
                self.similarity_threshold = model_data.get('similarity_threshold', 0.3)
                self.vectorizer_fitted = model_data.get('vectorizer_fitted', False)
                
                logger.info(f"Loaded similarity model with {len(self.positive_cases)} positive cases")
                return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
        
        return False
    
    def add_positive_cases_from_database(self, session, min_confidence: float = 80.0):
        """
        Load positive cases from existing database.
        
        Args:
            session: Database session
            min_confidence: Minimum confidence score for positive cases
        """
        from database.models import Tender
        
        try:
            # Query high-confidence relevant tenders
            tenders = session.query(Tender).filter(
                Tender.is_relevant == True,
                Tender.confidence_score >= min_confidence
            ).all()
            
            for tender in tenders:
                self.add_positive_case(
                    title=tender.title,
                    description=tender.description,
                    confidence=tender.confidence_score / 100.0,
                    source="database"
                )
            
            logger.info(f"Loaded {len(tenders)} positive cases from database")
            
            # Rebuild model with new cases
            if self.positive_cases:
                self.build_model()
                self.save_model()
            
            return True
        except Exception as e:
            logger.error(f"Error loading positive cases from database: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get statistics about the similarity model."""
        return {
            'positive_cases_count': len(self.positive_cases),
            'model_fitted': self.vectorizer_fitted,
            'similarity_threshold': self.similarity_threshold,
            'sources': list(set(case['source'] for case in self.positive_cases)),
            'latest_case': max(self.positive_cases, key=lambda x: x['added_at'])['added_at'] if self.positive_cases else None
        }


def create_emergency_classifier():
    """Create and initialize emergency classifier with sample positive cases."""
    classifier = SimilarityClassifier()
    
    # Add sample positive cases (these would typically come from your database)
    sample_cases = [
        {
            'title': 'Economic Analysis of Regional Development',
            'description': 'Comprehensive economic analysis of regional development patterns and growth opportunities',
            'confidence': 0.92
        },
        {
            'title': 'Statistical Survey on Employment Trends',
            'description': 'Large-scale statistical survey to analyze employment trends and labor market dynamics',
            'confidence': 0.88
        },
        {
            'title': 'Cost-Benefit Analysis for Infrastructure Projects',
            'description': 'Economic evaluation and cost-benefit analysis for major infrastructure development',
            'confidence': 0.85
        },
        {
            'title': 'Labor Market Research and Analysis',
            'description': 'Research project focusing on labor market conditions and employment statistics',
            'confidence': 0.90
        },
        {
            'title': 'Economic Impact Assessment Study',
            'description': 'Study to assess economic impacts of policy changes and market interventions',
            'confidence': 0.87
        }
    ]
    
    for case in sample_cases:
        classifier.add_positive_case(
            title=case['title'],
            description=case['description'],
            confidence=case['confidence'],
            source='sample'
        )
    
    # Build and save the model
    classifier.build_model()
    classifier.save_model()
    
    return classifier


if __name__ == "__main__":
    # Test the emergency classifier
    classifier = create_emergency_classifier()
    
    # Test cases
    test_tenders = [
        {
            'title': 'Regional Economic Development Analysis',
            'description': 'Analysis of economic development patterns in target regions'
        },
        {
            'title': 'IT Infrastructure Maintenance',
            'description': 'Technical maintenance and support for IT systems'
        },
        {
            'title': 'Statistical Research on Employment Data',
            'description': 'Research project analyzing employment statistics and trends'
        }
    ]
    
    print("🧪 Testing Emergency Classifier:")
    print("=" * 50)
    
    for tender in test_tenders:
        result = classifier.classify_tender(tender['title'], tender['description'])
        print(f"\nTitle: {tender['title']}")
        print(f"Relevant: {result['is_relevant']}")
        print(f"Confidence: {result['confidence_score']:.1f}%")
        print(f"Reasoning: {result['reasoning']}")
        print(f"Best Match: {result['best_match']}")
    
    print(f"\n📊 Model Stats: {classifier.get_stats()}")
