"""
Verification module to ensure bot understands query and answers from dataset
"""

import os
import sys
import joblib
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def verify_query_understanding(query, domain=None):
    """
    Verify that bot understands the query and will answer from dataset
    Returns: understanding details and dataset match info
    """
    
    # Load appropriate model
    bot_dir = os.path.dirname(os.path.abspath(__file__))
    
    if domain:
        model_path = os.path.join(bot_dir, f'chatbot_model_{domain}.pkl')
    else:
        model_path = os.path.join(bot_dir, 'chatbot_model.pkl')
    
    if not os.path.exists(model_path):
        return {
            'status': 'error',
            'message': f'Model not found: {model_path}',
            'will_answer_from_dataset': False
        }
    
    try:
        # Load model
        model = joblib.load(model_path)
        vectorizer = model.get('vectorizer')
        question_vectors = model.get('question_vectors')
        qa_pairs = model.get('qa_pairs', [])
        
        if not vectorizer or question_vectors is None or not qa_pairs:
            return {
                'status': 'error',
                'message': 'Model data incomplete',
                'will_answer_from_dataset': False
            }
        
        # Vectorize query
        query_vector = vectorizer.transform([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_vector, question_vectors)[0]
        
        # Get top 3 matches
        top_indices = np.argsort(similarities)[-3:][::-1]
        top_matches = []
        
        for idx in top_indices:
            if idx < len(qa_pairs):
                match = qa_pairs[idx]
                top_matches.append({
                    'question': match.get('question', ''),
                    'answer_preview': match.get('answer', '')[:100] + '...',
                    'similarity': float(similarities[idx]),
                    'category': match.get('category', 'unknown')
                })
        
        # Determine if will answer from dataset
        best_similarity = float(similarities[top_indices[0]]) if len(top_indices) > 0 else 0.0
        will_answer = best_similarity >= 0.3  # Threshold
        
        return {
            'status': 'success',
            'query': query,
            'domain': domain or 'global',
            'model_qa_count': len(qa_pairs),
            'best_match_similarity': best_similarity,
            'will_answer_from_dataset': will_answer,
            'top_matches': top_matches,
            'threshold': 0.3,
            'recommendation': 'WILL ANSWER FROM DATASET' if will_answer else 'MAY NOT FIND GOOD MATCH - Try rephrasing or use domain-specific chat'
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'will_answer_from_dataset': False
        }

def test_query_verification():
    """Test query verification for all domains"""
    
    print("=" * 80)
    print("QUERY UNDERSTANDING & DATASET RESPONSE VERIFICATION")
    print("=" * 80)
    
    test_cases = {
        'ipc': [
            "What is Section 420 IPC?",
            "What is the punishment for murder?",
            "Explain Section 302 IPC"
        ],
        'consumer': [
            "What are consumer rights under Consumer Protection Act?",
            "How to file consumer complaint?",
            "What is deficiency in service?"
        ],
        'crpc': [
            "What are my rights during arrest?",
            "How to file an FIR?",
            "What is anticipatory bail?"
        ],
        'family': [
            "What is the procedure for divorce in India?",
            "What are the rights of wife in divorce?",
            "How to file for child custody?"
        ],
        'property': [
            "How to verify property documents?",
            "What is mutation of property?",
            "What documents are required for property registration?"
        ],
        'it_act': [
            "How to report cybercrime in India?",
            "What to do if someone hacks my social media?",
            "Is online defamation a crime?"
        ]
    }
    
    total_tests = 0
    passed_tests = 0
    
    for domain, queries in test_cases.items():
        print(f"\n{'='*80}")
        print(f"Testing Domain: {domain.upper()}")
        print(f"{'='*80}")
        
        for query in queries:
            total_tests += 1
            result = verify_query_understanding(query, domain)
            
            print(f"\nQuery: {query}")
            print(f"Status: {result['status']}")
            
            if result['status'] == 'success':
                print(f"Model Q&A Count: {result['model_qa_count']}")
                print(f"Best Match Similarity: {result['best_match_similarity']:.3f}")
                print(f"Will Answer from Dataset: {'✓ YES' if result['will_answer_from_dataset'] else '✗ NO'}")
                print(f"Recommendation: {result['recommendation']}")
                
                if result['will_answer_from_dataset']:
                    passed_tests += 1
                    print("\nTop Match:")
                    if result['top_matches']:
                        top = result['top_matches'][0]
                        print(f"  Similar Question: {top['question'][:80]}...")
                        print(f"  Answer Preview: {top['answer_preview']}")
                        print(f"  Similarity: {top['similarity']:.3f}")
            else:
                print(f"Error: {result.get('message', 'Unknown error')}")
    
    # Summary
    print(f"\n{'='*80}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*80}")
    print(f"Total Tests: {total_tests}")
    print(f"Will Answer from Dataset: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"May Not Find Match: {total_tests - passed_tests} ({(total_tests-passed_tests)/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("\n✓✓✓ ALL QUERIES WILL BE ANSWERED FROM DATASET ✓✓✓")
    elif passed_tests >= total_tests * 0.8:
        print(f"\n✓ GOOD: {passed_tests/total_tests*100:.0f}% queries will be answered from dataset")
    else:
        print(f"\n⚠ WARNING: Only {passed_tests/total_tests*100:.0f}% queries will be answered from dataset")
        print("Consider retraining models with enhanced training script")
    
    print(f"\n{'='*80}")

if __name__ == "__main__":
    test_query_verification()
