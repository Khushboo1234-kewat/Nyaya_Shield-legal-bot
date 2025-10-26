import os
import sys
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import f1_score

# Enable importing preprocess when run both as module and script
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


def _load_dataset() -> pd.DataFrame:
    base_dir = os.path.dirname(os.path.dirname(__file__))  # .../backend
    project_root = os.path.dirname(base_dir)               # project root
    # Build candidate paths similar to train_model.py
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../../datasets/combined_legal_dataset.csv')),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../../datasets/train_dataset.csv')),
        os.path.join(base_dir, 'datasets', 'combined_legal_dataset.csv'),
        os.path.join(base_dir, 'datasets', 'train_dataset.csv'),
        os.path.join(project_root, 'datasets', 'combined_legal_dataset.csv'),
        os.path.join(project_root, 'datasets', 'train_dataset.csv'),
    ]
    for p in candidates:
        if os.path.exists(p):
            df = pd.read_csv(p, encoding='utf-8')
            df = df.dropna(subset=['input', 'output'])
            df = df[df['input'].astype(str).str.strip() != '']
            if 'category' not in df.columns:
                df['category'] = 'general'
            return df
    raise FileNotFoundError('Dataset not found in expected datasets/ locations.')


def _prep_texts(texts):
    out = []
    for t in texts:
        try:
            out.append(preprocess_legal_text(str(t)))
        except Exception:
            out.append(str(t).lower().strip())
    return out


def train_category_classifier(random_state: int = 42) -> Dict[str, Any]:
    df = _load_dataset()
    X = _prep_texts(df['input'].tolist())
    y = df['category'].astype(str).fillna('general').tolist()

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=random_state, stratify=y if len(set(y)) > 1 else None
    )

    models = []

    models.append(('tfidf_nb', Pipeline([
        ('vec', TfidfVectorizer(max_features=20000, ngram_range=(1, 2), stop_words='english', min_df=1, max_df=0.95)),
        ('clf', MultinomialNB())
    ])))

    models.append(('tfidf_svm', Pipeline([
        ('vec', TfidfVectorizer(max_features=20000, ngram_range=(1, 2), stop_words='english', min_df=1, max_df=0.95)),
        ('clf', LinearSVC())
    ])))

    models.append(('count_nb', Pipeline([
        ('vec', CountVectorizer(max_features=30000, ngram_range=(1, 2), stop_words='english', min_df=1)),
        ('clf', MultinomialNB())
    ])))

    models.append(('count_rf', Pipeline([
        ('vec', CountVectorizer(max_features=30000, ngram_range=(1, 2), stop_words='english', min_df=2)),
        ('clf', RandomForestClassifier(n_estimators=200, random_state=random_state, n_jobs=-1))
    ])))

    scores = []
    for name, pipe in models:
        try:
            pipe.fit(X_train, y_train)
            preds = pipe.predict(X_val)
            score = f1_score(y_val, preds, average='macro')
            scores.append((score, name, pipe))
        except Exception as e:
            continue

    if not scores:
        raise RuntimeError('No classifier could be trained successfully.')

    scores.sort(reverse=True, key=lambda x: x[0])
    best_score, best_name, best_pipe = scores[0]

    bundle = {
        'model_name': best_name,
        'f1_macro': float(best_score),
        'pipeline': best_pipe,
        'labels': sorted(list(set(y)))
    }

    save_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(save_dir, 'classifier_category.joblib')
    joblib.dump(bundle, out_path)

    return {'path': out_path, 'model_name': best_name, 'f1_macro': float(best_score)}


if __name__ == '__main__':
    try:
        res = train_category_classifier()
        print(f"✅ Saved category classifier to {res['path']} ({res['model_name']}, F1={res['f1_macro']:.3f})")
    except Exception as e:
        print(f"❌ Training classifier failed: {e}")
