"""
Multi-Dataset Search Engine for Nyaya-Shield Legal Bot
========================================================

This module implements intelligent multi-dataset search:
1. Analyzes query to determine legal domain
2. Searches specific domain dataset first
3. Falls back to all datasets if needed
4. Frames accurate combined responses
"""

import os
import sys
import joblib
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple, Optional

# Import preprocessing
try:
    if __package__:
        from .preprocess import preprocess_legal_text
    else:
        raise ImportError
except Exception:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from bot.preprocess import preprocess_legal_text


class MultiDatasetSearchEngine:
    """
    Intelligent search engine that searches across multiple legal domain datasets
    """
    
    def __init__(self):
        """Initialize the search engine with all available models"""
        self.models = {}
        self.domain_keywords = {
            'ipc': ['ipc', 'criminal', 'murder', 'theft', 'assault', 'section', 'punishment', 'crime', 'offense', 'penal code'],
            'consumer': ['consumer', 'defective', 'product', 'service', 'complaint', 'refund', 'warranty', 'forum', 'seller'],
            'crpc': ['crpc', 'procedure', 'arrest', 'bail', 'fir', 'investigation', 'trial', 'magistrate', 'warrant'],
            'family': ['family', 'marriage', 'divorce', 'custody', 'maintenance', 'alimony', 'adoption', 'matrimonial'],
            'property': ['property', 'land', 'title', 'deed', 'registration', 'mutation', 'ownership', 'inheritance', 'estate'],
            'it_act': ['cyber', 'it act', 'online', 'internet', 'hacking', 'digital', 'data', 'privacy', 'phishing', 'fraud']
        }
        self.load_all_models()
    
    def load_all_models(self):
        """Load all available trained models"""
        bot_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Load global model
        global_model_path = os.path.join(bot_dir, 'chatbot_model.pkl')
        if os.path.exists(global_model_path):
            try:
                self.models['global'] = joblib.load(global_model_path)
                print(f"✓ Loaded global model: {len(self.models['global']['qa_pairs'])} Q&A pairs")
            except Exception as e:
                print(f"✗ Failed to load global model: {e}")
        
        # Load domain-specific models
        domains = ['ipc', 'consumer', 'crpc', 'family', 'property', 'it_act']
        for domain in domains:
            model_path = os.path.join(bot_dir, f'chatbot_model_{domain}.pkl')
            if os.path.exists(model_path):
                try:
                    self.models[domain] = joblib.load(model_path)
                    print(f"✓ Loaded {domain} model: {len(self.models[domain]['qa_pairs'])} Q&A pairs")
                except Exception as e:
                    print(f"✗ Failed to load {domain} model: {e}")
    
    def analyze_query_domain(self, query: str) -> List[Tuple[str, float]]:
        """
        Analyze query to determine which legal domain(s) it belongs to
        Returns list of (domain, confidence) tuples sorted by confidence
        """
        query_lower = query.lower()
        domain_scores = {}
        
        for domain, keywords in self.domain_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in query_lower:
                    # Weight longer keywords more heavily
                    score += len(keyword.split())
            
            if score > 0:
                # Normalize by number of keywords
                domain_scores[domain] = score / len(keywords)
        
        # Sort by score descending
        sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_domains
    
    def search_in_model(self, query: str, model_data: Dict, top_k: int = 5) -> List[Dict]:
        """
        Search for answers in a specific model using improved keyword-boosted search
        Returns list of {answer, score, category, source} dicts
        """
        if not model_data:
            return []
        
        try:
            # Try using improved search with keyword boosting
            try:
                from bot.improved_search import improved_search
                results_tuples = improved_search(query, model_data, top_k=top_k, keyword_boost_weight=0.4)
                
                results = []
                for idx, score, qa_data in results_tuples:
                    if score > 0:  # Only include non-zero matches
                        results.append({
                            'answer': qa_data['answer'],
                            'question': qa_data['question'],
                            'score': float(score),
                            'category': qa_data.get('category', 'general'),
                            'source': qa_data.get('source', 'unknown'),
                            'tfidf_score': qa_data.get('tfidf_score', 0),
                            'keyword_score': qa_data.get('keyword_score', 0)
                        })
                return results
                
            except Exception as improve_err:
                # Fallback to basic search
                print(f"Improved search failed in multi-dataset, using basic: {improve_err}")
                pass
            
            # Basic search fallback
            vectorizer = model_data['vectorizer']
            qa_pairs = model_data['qa_pairs']
            question_vectors = model_data['question_vectors']
            
            # Process query
            processed_query = preprocess_legal_text(query)
            query_vector = vectorizer.transform([processed_query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, question_vectors)[0]
            
            # Get top K matches
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0:  # Only include non-zero matches
                    results.append({
                        'answer': qa_pairs[idx]['answer'],
                        'question': qa_pairs[idx]['question'],
                        'score': float(similarities[idx]),
                        'category': qa_pairs[idx].get('category', 'general'),
                        'source': qa_pairs[idx].get('source', 'unknown')
                    })
            
            return results
        
        except Exception as e:
            print(f"Error searching model: {e}")
            return []
    
    def search_all_datasets(self, query: str, threshold: float = 0.3) -> Dict:
        """
        Comprehensive search across all datasets
        
        Strategy:
        1. Analyze query to determine domain
        2. Search specific domain dataset first
        3. If no good match (< threshold), search all other datasets
        4. Combine and rank results
        5. Frame accurate response
        
        Returns: {
            'answer': str,
            'confidence': float,
            'category': str,
            'sources': list,
            'search_path': list (domains searched in order)
        }
        """
        
        # Step 1: Analyze query domain
        detected_domains = self.analyze_query_domain(query)
        search_path = []
        all_results = []
        
        # Step 2: Search primary domain(s) first
        if detected_domains:
            for domain, domain_confidence in detected_domains[:2]:  # Top 2 detected domains
                if domain in self.models:
                    search_path.append(f"{domain} (detected: {domain_confidence:.2f})")
                    results = self.search_in_model(query, self.models[domain], top_k=5)
                    all_results.extend(results)
        
        # Step 3: Check if we have a good match
        best_score = max([r['score'] for r in all_results], default=0)
        
        # Step 4: If no good match, search all other datasets
        if best_score < threshold:
            search_path.append("all_datasets (fallback)")
            
            # Search remaining domain models
            searched_domains = set([d for d, _ in detected_domains[:2]])
            for domain in ['ipc', 'consumer', 'crpc', 'family', 'property', 'it_act']:
                if domain not in searched_domains and domain in self.models:
                    results = self.search_in_model(query, self.models[domain], top_k=3)
                    all_results.extend(results)
            
            # Search global model
            if 'global' in self.models:
                search_path.append("global_model")
                results = self.search_in_model(query, self.models['global'], top_k=5)
                all_results.extend(results)
        
        # Step 5: Rank all results
        if not all_results:
            return {
                'answer': "I couldn't find a relevant answer in any of the legal datasets. Please rephrase your question with more specific details about the legal issue, relevant sections, or acts.",
                'confidence': 0.0,
                'category': 'unknown',
                'sources': [],
                'search_path': search_path,
                'found_matches': 0
            }
        
        # Sort by score
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Step 6: Frame the answer
        best_match = all_results[0]
        confidence = best_match['score']
        
        # If we have multiple good matches, combine them
        if len(all_results) > 1 and all_results[1]['score'] > threshold * 0.8:
            framed_answer = self.frame_combined_answer(query, all_results[:3])
        else:
            framed_answer = best_match['answer']
        
        # Collect unique sources
        sources = list(set([r['source'] for r in all_results[:5]]))
        
        return {
            'answer': framed_answer,
            'confidence': confidence,
            'category': best_match['category'],
            'sources': sources,
            'search_path': search_path,
            'found_matches': len(all_results),
            'top_matches': all_results[:3]  # Include top 3 for reference
        }
    
    def frame_combined_answer(self, query: str, top_matches: List[Dict]) -> str:
        """
        Frame a comprehensive answer by combining multiple relevant matches
        """
        if not top_matches:
            return "No relevant information found."
        
        # Start with the best match
        primary_answer = top_matches[0]['answer']
        
        # If we have additional relevant matches, add them as supplementary info
        if len(top_matches) > 1:
            supplementary = []
            for match in top_matches[1:]:
                if match['score'] > 0.4:  # Only include reasonably relevant matches
                    # Avoid duplicating the same answer
                    if match['answer'][:100] != primary_answer[:100]:
                        supplementary.append(match['answer'])
            
            if supplementary:
                # Combine answers intelligently
                combined = f"{primary_answer}\n\n**Additional Information:**\n"
                for i, supp in enumerate(supplementary[:2], 1):  # Max 2 supplementary
                    combined += f"\n{i}. {supp}\n"
                return combined
        
        return primary_answer
    
    def get_answer(self, query: str, domain_hint: Optional[str] = None, threshold: float = 0.3) -> Dict:
        """
        Main method to get answer for a query
        
        Args:
            query: User's legal question
            domain_hint: Optional domain hint from UI (ipc, consumer, etc.)
            threshold: Minimum similarity threshold
        
        Returns:
            Dictionary with answer, confidence, category, sources, etc.
        """
        
        # If domain hint provided, prioritize that domain
        if domain_hint and domain_hint in self.models:
            # Search hinted domain first
            results = self.search_in_model(query, self.models[domain_hint], top_k=5)
            
            if results and results[0]['score'] >= threshold:
                # Good match in hinted domain
                return {
                    'answer': results[0]['answer'],
                    'confidence': results[0]['score'],
                    'category': domain_hint,
                    'sources': [results[0]['source']],
                    'search_path': [f"{domain_hint} (hinted)"],
                    'found_matches': len(results)
                }
        
        # Otherwise, do comprehensive search
        return self.search_all_datasets(query, threshold)


# Global instance
_search_engine = None

def get_search_engine() -> MultiDatasetSearchEngine:
    """Get or create global search engine instance"""
    global _search_engine
    if _search_engine is None:
        _search_engine = MultiDatasetSearchEngine()
    return _search_engine


def search_legal_answer(query: str, domain: Optional[str] = None, threshold: float = 0.3) -> Dict:
    """
    Convenience function to search for legal answers
    
    Args:
        query: User's legal question
        domain: Optional domain hint (ipc, consumer, crpc, family, property, it_act)
        threshold: Minimum similarity threshold (default: 0.3)
    
    Returns:
        Dictionary with answer, confidence, category, sources, and search metadata
    """
    engine = get_search_engine()
    return engine.get_answer(query, domain, threshold)


if __name__ == "__main__":
    # Test the search engine
    print("=" * 70)
    print("MULTI-DATASET SEARCH ENGINE TEST")
    print("=" * 70)
    
    engine = MultiDatasetSearchEngine()
    
    test_queries = [
        ("What is Section 420 IPC?", None),
        ("How to file a consumer complaint?", "consumer"),
        ("What are my rights during arrest?", None),
        ("Divorce procedure in India", "family"),
        ("How to report cybercrime?", None),
    ]
    
    for query, domain_hint in test_queries:
        print(f"\n{'='*70}")
        print(f"Query: {query}")
        if domain_hint:
            print(f"Domain Hint: {domain_hint}")
        print("-" * 70)
        
        result = engine.get_answer(query, domain_hint)
        
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"Category: {result['category']}")
        print(f"Search Path: {' → '.join(result['search_path'])}")
        print(f"Found Matches: {result['found_matches']}")
        print(f"Sources: {', '.join(result['sources'])}")
        print(f"\nAnswer:\n{result['answer'][:300]}...")
