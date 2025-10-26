"""
Improved Search with Better Query Understanding
==============================================
This module adds keyword boosting and better matching logic
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List, Tuple
import re


# Critical legal keywords that must be preserved and weighted heavily
LEGAL_KEYWORDS = {
    # Crime types
    'theft', 'robbery', 'dacoity', 'murder', 'assault', 'rape', 'kidnapping', 
    'extortion', 'forgery', 'cheating', 'fraud', 'bribery', 'corruption',
    'defamation', 'trespass', 'mischief', 'arson', 'riot',
    
    # Legal concepts
    'bail', 'arrest', 'fir', 'warrant', 'trial', 'appeal', 'petition',
    'complaint', 'cognizable', 'bailable', 'summons', 'investigation',
    'chargesheet', 'custody', 'remand', 'conviction', 'acquittal',
    
    # Laws and sections
    'ipc', 'crpc', 'section', 'act', 'code', 'article', 'clause',
    
    # Family law
    'divorce', 'marriage', 'custody', 'maintenance', 'alimony', 'adoption',
    'matrimonial', 'spouse', 'dowry',
    
    # Property law
    'property', 'land', 'title', 'deed', 'registration', 'mutation',
    'ownership', 'inheritance', 'estate', 'lease',
    
    # Consumer law
    'consumer', 'defective', 'refund', 'warranty', 'compensation',
    
    # Cyber law
    'cyber', 'hacking', 'phishing', 'online', 'digital', 'internet',
    
    # Questions words (preserve for context)
    'what', 'how', 'when', 'where', 'why', 'who', 'which',
    'punishment', 'penalty', 'sentence', 'fine', 'imprisonment',
    'procedure', 'process', 'rights', 'law', 'legal'
}


def extract_keywords(text: str) -> List[str]:
    """Extract important legal keywords from text"""
    text_lower = text.lower()
    found_keywords = []
    
    for keyword in LEGAL_KEYWORDS:
        if keyword in text_lower:
            found_keywords.append(keyword)
    
    # Also extract section numbers
    section_pattern = r'section\s+(\d+[a-z]?)'
    sections = re.findall(section_pattern, text_lower)
    found_keywords.extend([f"section{s}" for s in sections])
    
    # Extract specific numbers that might be important
    number_pattern = r'\b(\d+)\b'
    numbers = re.findall(number_pattern, text_lower)
    found_keywords.extend(numbers)
    
    return found_keywords


def calculate_keyword_match_score(query: str, document_question: str, document_answer: str) -> float:
    """
    Calculate how well the document matches query keywords
    Returns a boost score between 0 and 1
    """
    query_keywords = set(extract_keywords(query))
    doc_question_keywords = set(extract_keywords(document_question))
    doc_answer_keywords = set(extract_keywords(document_answer))
    
    if not query_keywords:
        return 0.0
    
    # Check matches in question (weighted more)
    question_matches = len(query_keywords & doc_question_keywords) / len(query_keywords)
    
    # Check matches in answer
    answer_matches = len(query_keywords & doc_answer_keywords) / len(query_keywords)
    
    # Combined score (question matches weighted 70%, answer 30%)
    total_score = (question_matches * 0.7) + (answer_matches * 0.3)
    
    return min(total_score, 1.0)


def improved_search(query: str, model_data: Dict, top_k: int = 5, 
                    keyword_boost_weight: float = 0.3) -> List[Tuple[int, float, Dict]]:
    """
    Improved search that combines TF-IDF similarity with keyword matching
    
    Args:
        query: User query
        model_data: Model dictionary with vectorizer, qa_pairs, question_vectors
        top_k: Number of results to return
        keyword_boost_weight: Weight for keyword boost (0.0 to 1.0)
    
    Returns:
        List of (index, final_score, qa_pair) tuples
    """
    vectorizer = model_data['vectorizer']
    qa_pairs = model_data['qa_pairs']
    question_vectors = model_data['question_vectors']
    
    # Preprocess query for TF-IDF (but keep original for keyword matching)
    from bot.preprocess import preprocess_legal_text
    processed_query = preprocess_legal_text(query)
    query_vector = vectorizer.transform([processed_query])
    
    # Calculate TF-IDF similarities
    tfidf_similarities = cosine_similarity(query_vector, question_vectors)[0]
    
    # Calculate keyword match scores for each document
    keyword_scores = np.zeros(len(qa_pairs))
    for idx, qa_pair in enumerate(qa_pairs):
        keyword_scores[idx] = calculate_keyword_match_score(
            query,
            qa_pair['question'],
            qa_pair['answer']
        )
    
    # Combine scores: (1-weight)*tfidf + weight*keyword
    final_scores = ((1 - keyword_boost_weight) * tfidf_similarities + 
                   keyword_boost_weight * keyword_scores)
    
    # Get top K
    top_indices = np.argsort(final_scores)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        results.append((
            int(idx),
            float(final_scores[idx]),
            {
                'answer': qa_pairs[idx]['answer'],
                'question': qa_pairs[idx]['question'],
                'category': qa_pairs[idx].get('category', 'general'),
                'source': qa_pairs[idx].get('source', 'unknown'),
                'tfidf_score': float(tfidf_similarities[idx]),
                'keyword_score': float(keyword_scores[idx]),
                'final_score': float(final_scores[idx])
            }
        ))
    
    return results


def get_improved_answer(query: str, model_data: Dict, top_k: int = 3, 
                       category_filter: str = None) -> Tuple[str, float, str]:
    """
    Get answer using improved search with keyword boosting
    
    Args:
        query: User query
        model_data: Model data dictionary
        top_k: Number of candidates to consider
        category_filter: Optional category to filter by
    
    Returns:
        (answer, confidence, category)
    """
    # Get top results with improved search
    results = improved_search(query, model_data, top_k=top_k * 2, keyword_boost_weight=0.4)
    
    # Apply category filter if provided
    if category_filter:
        category_filter_lower = category_filter.lower().strip()
        filtered_results = []
        
        for idx, score, qa_data in results:
            qa_category = str(qa_data.get('category', '')).lower().strip()
            
            # Handle category aliases
            if category_filter_lower in ['it', 'cyber', 'it_act', 'cyber law']:
                category_filter_lower = 'it_act'
                if qa_category in ['it', 'cyber', 'cyber law', 'it act']:
                    qa_category = 'it_act'
            
            if qa_category == category_filter_lower or not filtered_results:
                filtered_results.append((idx, score, qa_data))
                if len(filtered_results) >= top_k:
                    break
        
        if filtered_results:
            results = filtered_results
    
    # Return best match
    if results:
        _, score, best_match = results[0]
        return (
            best_match['answer'],
            score,
            best_match['category']
        )
    
    return ("No relevant answer found.", 0.0, "unknown")


if __name__ == "__main__":
    # Test the improved search
    import joblib
    import os
    
    bot_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load IPC model
    ipc_model_path = os.path.join(bot_dir, 'chatbot_model_ipc.pkl')
    if os.path.exists(ipc_model_path):
        print("Testing Improved Search")
        print("=" * 70)
        
        ipc_model = joblib.load(ipc_model_path)
        
        test_queries = [
            "What is the punishment for theft under IPC?",
            "What is the punishment for murder under IPC?",
            "How to get bail?",
            "What are the rights of arrested person?"
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            print("-" * 70)
            
            # Get answer
            answer, confidence, category = get_improved_answer(
                query, ipc_model, top_k=3, category_filter='ipc'
            )
            
            print(f"Confidence: {confidence:.3f}")
            print(f"Category: {category}")
            print(f"Answer: {answer[:300]}...")
            
            # Show keyword extraction
            keywords = extract_keywords(query)
            print(f"Extracted keywords: {keywords}")
    else:
        print(f"IPC model not found at: {ipc_model_path}")
