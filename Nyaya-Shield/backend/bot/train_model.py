import os
import sys
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Support running both as a module (python -m bot.train_model) and as a script (python bot/train_model.py)
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

def load_combined_dataset():
    dataset_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        "../../datasets/combined_legal_dataset.csv"
    ))
    
    if not os.path.exists(dataset_path):
        dataset_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 
            "../../datasets/train_dataset.csv"
        ))
    
    if not os.path.exists(dataset_path):
        raise FileNotFoundError("Dataset not found. Run combine_datasets.py first.")
    
    df = pd.read_csv(dataset_path, encoding='utf-8')
    df = df.dropna(subset=['input', 'output'])
    df = df[df['input'].str.strip() != '']
    df = df[df['output'].str.strip() != '']
    
    print(f"Loaded {len(df):,} records")
    return df

def prepare_training_data(df):
    # Preprocess input texts
    texts = []
    for text in df['input']:
        try:
            texts.append(preprocess_legal_text(str(text)))
        except:
            texts.append(str(text).lower().strip())
    
    # Create question-answer pairs for similarity matching
    qa_pairs = []
    for _, row in df.iterrows():
        qa_pairs.append({
            'question': row['input'],
            'answer': row['output'],
            'category': row['category'],
            'source': row['source']
        })
    
    return texts, qa_pairs

def train_model():
    try:
        df = load_combined_dataset()
        texts, qa_pairs = prepare_training_data(df)
        
        # Create TF-IDF vectorizer for question similarity
        vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 3),
            stop_words='english',
            min_df=2,
            max_df=0.8
        )
        
        # Fit vectorizer on all questions
        X = vectorizer.fit_transform(texts)
        
        # Save the complete model for question-answer matching
        model_data = {
            'vectorizer': vectorizer,
            'qa_pairs': qa_pairs,
            'question_vectors': X,
            'total_samples': len(qa_pairs)
        }
        
        # Ensure models are saved alongside this file (backend/bot/)
        save_dir = os.path.dirname(os.path.abspath(__file__))
        joblib.dump(model_data, os.path.join(save_dir, "chatbot_model.pkl"))
        joblib.dump(vectorizer, os.path.join(save_dir, "vectorizer.pkl"))
        
        print(f"✅ Training complete! Loaded {len(qa_pairs):,} Q&A pairs")
        print(f"📊 Vector dimensions: {X.shape}")
        print(f"📁 Saved: chatbot_model.pkl, vectorizer.pkl")
        
        return True
        
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return False
    except Exception as e:
        print(f"❌ Training failed: {str(e)}")
        return False

def train_models_by_category():
    try:
        df = load_combined_dataset()
        if 'category' not in df.columns:
            raise ValueError("Dataset must contain a 'category' column for per-category training")
        save_dir = os.path.dirname(os.path.abspath(__file__))
        results = {}
        for cat, group in df.groupby(df['category'].astype(str).str.strip().str.lower()):
            if group.empty:
                continue
            texts, qa_pairs = prepare_training_data(group)
            # Adjust vectorizer for small categories
            min_df_val = 1 if len(texts) < 50 else 2
            try:
                vectorizer = TfidfVectorizer(
                    max_features=10000,
                    ngram_range=(1, 3),
                    stop_words='english',
                    min_df=min_df_val,
                    max_df=0.9
                )
                X = vectorizer.fit_transform(texts)
            except ValueError as e:
                # Handle empty vocabulary or similar issues
                print(f"⚠️ Skipping category '{cat}' due to vectorizer error: {e}")
                continue
            model_data = {
                'vectorizer': vectorizer,
                'qa_pairs': qa_pairs,
                'question_vectors': X,
                'total_samples': len(qa_pairs),
                'category': cat
            }
            safe_cat = cat.replace(' ', '_')
            joblib.dump(model_data, os.path.join(save_dir, f"chatbot_model_{safe_cat}.pkl"))
            results[safe_cat] = len(qa_pairs)
        return results
    except Exception as e:
        print(f"❌ Per-category training failed: {str(e)}")
        return {}

def get_legal_answer(query, model_data, top_k=3, category_filter=None):
    """Get the best legal answer for a user query using improved search with keyword boosting.
    If category_filter is provided, prefer answers from that category; fall back to global best if none match.
    """
    try:
        # Try to use improved search with keyword boosting
        from bot.improved_search import get_improved_answer
        return get_improved_answer(query, model_data, top_k=top_k, category_filter=category_filter)
    except Exception as e:
        # Fallback to basic search if improved search fails
        print(f"Improved search failed, using basic search: {e}")
        
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        vectorizer = model_data['vectorizer']
        qa_pairs = model_data['qa_pairs']
        question_vectors = model_data['question_vectors']
        
        # Process user query
        processed_query = preprocess_legal_text(query)
        query_vector = vectorizer.transform([processed_query])
        
        # Calculate similarity with all questions
        similarities = cosine_similarity(query_vector, question_vectors)[0]
        
        # Get ranked indices by similarity (desc)
        ranked_indices = np.argsort(similarities)[::-1]
        
        # Normalize filter for matching
        norm_filter = (category_filter or '').strip().lower()
        
        # Try to find the best match within the filtered category first
        filtered_choice = None
        if norm_filter:
            for idx in ranked_indices:
                cat = str(qa_pairs[idx].get('category', '')).strip().lower()
                # Treat common aliases
                cat_alias = 'it_act' if cat in ['it', 'cyber', 'cyber law', 'it act'] else cat
                filt_alias = 'it_act' if norm_filter in ['it', 'cyber', 'cyber law', 'it_act', 'it act'] else norm_filter
                if cat_alias == filt_alias:
                    filtered_choice = (idx, similarities[idx])
                    break
        
        if filtered_choice is not None:
            chosen_idx, sim = filtered_choice
            best_match = qa_pairs[chosen_idx]
            return best_match['answer'], float(sim), best_match.get('category') or norm_filter
        
        # Otherwise return global best
        top_idx = ranked_indices[0]
        best_match = qa_pairs[top_idx]
        similarity_score = similarities[top_idx]
        return best_match['answer'], float(similarity_score), best_match.get('category')

def test_model():
    try:
        model_data = joblib.load("chatbot_model.pkl")
        
        test_queries = [
            "What is the punishment for murder?",
            "How to file a divorce case?",
            "What are consumer rights in India?",
            "Explain Article 21 of Constitution"
        ]
        
        print("\n🧪 Testing legal Q&A model:")
        for query in test_queries:
            answer, score, category = get_legal_answer(query, model_data)
            print(f"\n❓ Query: {query}")
            print(f"📝 Answer: {answer[:200]}...")
            print(f"🎯 Similarity: {score:.3f} | Category: {category}")
            
    except Exception as e:
        print(f"❌ Testing failed: {str(e)}")

if __name__ == "__main__":
    import sys
    if any(arg in ('--by-category', '-c') for arg in sys.argv):
        res = train_models_by_category()
        if res:
            print("✅ Trained category models:")
            for k, v in res.items():
                print(f"  - {k}: {v} Q&A pairs")
    else:
        success = train_model()
        if success:
            test_model()
