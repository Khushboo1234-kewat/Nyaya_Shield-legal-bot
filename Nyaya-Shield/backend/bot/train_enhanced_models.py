"""
Enhanced Model Training with Indian Legal Consultant Integration
Trains domain-specific models with better accuracy and solution-oriented responses
"""

import os
import sys
import json
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
datasets_dir = os.path.join(os.path.dirname(parent_dir), 'datasets')

print("=" * 80)
print("ENHANCED MODEL TRAINING - Domain-Specific with Legal Consultant Integration")
print("=" * 80)

def load_law_dataset_by_domain(domain):
    """Load specific law dataset JSON files for a domain"""
    law_dir = os.path.join(datasets_dir, "Law data set")
    qa_pairs = []
    
    # Domain-specific file mapping
    domain_files = {
        'ipc': ['indian_criminal_law_ipc_qa_1000_pairs_set2.json', 'ipc_*.json'],
        'consumer': ['consumer_law_india_qa_1000.json', 'consumer_*.json'],
        'crpc': ['crpc_india_qa_1000.json', 'crpc_*.json'],
        'family': ['indian_family_law_qa_1000_pairs.json', 'family_*.json'],
        'property': ['indian_property_law_qa_1000_pairs_set2.json', 'property_*.json'],
        'it_act': ['cyber_law_india_qa_1000.json', 'cyber_*.json', 'it_*.json']
    }
    
    files_to_check = domain_files.get(domain, [])
    
    for filename in files_to_check:
        if '*' in filename:
            # Pattern matching
            import glob
            pattern = os.path.join(law_dir, filename)
            matching_files = glob.glob(pattern)
            for filepath in matching_files:
                qa_pairs.extend(load_json_qa_file(filepath, domain))
        else:
            filepath = os.path.join(law_dir, filename)
            if os.path.exists(filepath):
                qa_pairs.extend(load_json_qa_file(filepath, domain))
    
    print(f"   Loaded {len(qa_pairs)} Q&A pairs from Law data set for {domain}")
    return qa_pairs

def load_json_qa_file(filepath, category):
    """Load Q&A pairs from JSON file"""
    qa_pairs = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, dict):
            items = data.get('qa_pairs') or data.get('data') or data.get('items') or []
        else:
            items = data
        
        for item in items:
            if not isinstance(item, dict):
                continue
            
            question = item.get('question') or item.get('query') or item.get('Q') or ''
            answer = item.get('answer') or item.get('response') or item.get('A') or ''
            
            if question and answer:
                qa_pairs.append({
                    'question': str(question).strip(),
                    'answer': str(answer).strip(),
                    'category': category
                })
    except Exception as e:
        print(f"   Warning: Could not load {os.path.basename(filepath)}: {e}")
    
    return qa_pairs

def load_indian_legal_consultant_data(domain=None):
    """Load Indian Legal Consultant dataset for solution-oriented responses"""
    ilc_dir = os.path.join(datasets_dir, "Indian_legal_consultant")
    qa_pairs = []
    
    print(f"\n   Loading Indian Legal Consultant data for {domain or 'all domains'}...")
    
    # Load main consultation data
    try:
        data_csv = os.path.join(ilc_dir, "data.csv")
        if os.path.exists(data_csv):
            df = pd.read_csv(data_csv, nrows=5000)  # Limit for performance
            
            for _, row in df.iterrows():
                messages = str(row.get('messages', ''))
                if '[INST]' in messages and '[/INST]' in messages:
                    parts = messages.split('[/INST]')
                    if len(parts) >= 2:
                        question = parts[0].split('[INST]')[-1].strip()
                        answer = parts[1].split('[INST]')[0].strip()
                        
                        if question and answer and len(question) > 10 and len(answer) > 20:
                            # Categorize based on keywords if domain specified
                            if domain:
                                if should_include_for_domain(question, answer, domain):
                                    qa_pairs.append({
                                        'question': question,
                                        'answer': answer,
                                        'category': domain,
                                        'source': 'IndianLegalConsultant'
                                    })
                            else:
                                qa_pairs.append({
                                    'question': question,
                                    'answer': answer,
                                    'category': 'legal_consultation',
                                    'source': 'IndianLegalConsultant'
                                })
            
            print(f"   ✓ Loaded {len(qa_pairs)} consultation Q&A pairs")
    except Exception as e:
        print(f"   Warning: Could not load Indian Legal Consultant data: {e}")
    
    return qa_pairs

def should_include_for_domain(question, answer, domain):
    """Check if Q&A pair is relevant to domain"""
    text = (question + " " + answer).lower()
    
    domain_keywords = {
        'ipc': ['ipc', 'section', 'penal code', 'criminal', 'offense', 'punishment', 'crime'],
        'consumer': ['consumer', 'complaint', 'defective', 'product', 'service', 'refund', 'warranty'],
        'crpc': ['crpc', 'arrest', 'bail', 'fir', 'procedure', 'investigation', 'magistrate'],
        'family': ['marriage', 'divorce', 'custody', 'maintenance', 'alimony', 'matrimonial', 'family'],
        'property': ['property', 'land', 'deed', 'registration', 'mutation', 'ownership', 'estate'],
        'it_act': ['cyber', 'it act', 'online', 'hacking', 'digital', 'internet', 'data breach']
    }
    
    keywords = domain_keywords.get(domain, [])
    return any(keyword in text for keyword in keywords)

def train_domain_model(domain):
    """Train enhanced model for specific domain"""
    print(f"\n{'='*80}")
    print(f"Training Enhanced Model: {domain.upper()}")
    print(f"{'='*80}")
    
    # Load domain-specific law dataset
    qa_pairs = load_law_dataset_by_domain(domain)
    
    # Load relevant Indian Legal Consultant data
    ilc_pairs = load_indian_legal_consultant_data(domain)
    
    # Combine datasets
    all_pairs = qa_pairs + ilc_pairs
    
    if not all_pairs:
        print(f"   ✗ No data found for {domain}")
        return None
    
    print(f"   Total Q&A pairs: {len(all_pairs)}")
    print(f"   - Law dataset: {len(qa_pairs)}")
    print(f"   - Legal Consultant: {len(ilc_pairs)}")
    
    # Extract questions and answers
    questions = [pair['question'] for pair in all_pairs]
    answers = [pair['answer'] for pair in all_pairs]
    
    # Train TF-IDF vectorizer
    print(f"   Training TF-IDF vectorizer...")
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 3),
        min_df=1,
        max_df=0.95,
        stop_words='english'
    )
    
    question_vectors = vectorizer.fit_transform(questions)
    
    # Create model
    model = {
        'vectorizer': vectorizer,
        'question_vectors': question_vectors,
        'qa_pairs': all_pairs,
        'domain': domain,
        'version': '2.0_enhanced'
    }
    
    # Save model
    model_path = os.path.join(current_dir, f'chatbot_model_{domain}.pkl')
    joblib.dump(model, model_path)
    
    print(f"   ✓ Model saved: {model_path}")
    print(f"   ✓ Model size: {os.path.getsize(model_path):,} bytes")
    
    return model

def train_all_enhanced_models():
    """Train all domain-specific enhanced models"""
    domains = ['ipc', 'consumer', 'crpc', 'family', 'property', 'it_act']
    
    results = {}
    for domain in domains:
        try:
            model = train_domain_model(domain)
            if model:
                results[domain] = {
                    'status': 'success',
                    'qa_count': len(model['qa_pairs'])
                }
            else:
                results[domain] = {
                    'status': 'failed',
                    'qa_count': 0
                }
        except Exception as e:
            print(f"   ✗ Error training {domain}: {e}")
            results[domain] = {
                'status': 'error',
                'error': str(e)
            }
    
    # Summary
    print(f"\n{'='*80}")
    print("TRAINING SUMMARY")
    print(f"{'='*80}")
    
    for domain, result in results.items():
        status = result['status']
        if status == 'success':
            print(f"✓ {domain.upper():12s} - {result['qa_count']:,} Q&A pairs")
        else:
            print(f"✗ {domain.upper():12s} - {status}")
    
    print(f"\n{'='*80}")
    print("Enhanced models trained successfully!")
    print("Models include Law dataset + Indian Legal Consultant data")
    print(f"{'='*80}")
    
    return results

if __name__ == "__main__":
    print("\nStarting enhanced model training...")
    print("This will train domain-specific models with:")
    print("1. Law dataset (domain-specific JSON files)")
    print("2. Indian Legal Consultant dataset (solution-oriented)")
    print()
    
    results = train_all_enhanced_models()
    
    print("\n✅ Training complete!")
    print("Restart your server to use the enhanced models.")
