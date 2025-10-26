import os
import pandas as pd
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'datasets'))

# Input preference order
CANDIDATES = [
    os.path.join(DATASETS_DIR, 'combined_legal_dataset.csv'),
    os.path.join(DATASETS_DIR, 'train_dataset.csv'),
]

# Output file (overwrite combined so training picks it up automatically)
OUTPUT = os.path.join(DATASETS_DIR, 'combined_legal_dataset.csv')
BACKUP = os.path.join(DATASETS_DIR, 'combined_legal_dataset.raw.backup.csv')

CATEGORY_ALIASES = {
    'ipc': {'ipc', 'indian penal code', 'offense', 'crime', 'section 3', 'section 4', 'section '},
    'consumer': {'consumer', 'defective', 'refund', 'warranty', 'service deficiency'},
    'crpc': {'crpc', 'criminal procedure', 'arrest', 'bail', 'fir', 'chargesheet'},
    'family': {'family', 'divorce', 'custody', 'maintenance', 'alimony', 'marriage'},
    'property': {'property', 'land', 'title', 'ownership', 'registration', 'stamp duty'},
    'it_act': {'it act', 'cyber', 'information technology', 'online', 'digital', 'internet', 'data'},
}

# Compile keyword regex for speed
CATEGORY_REGEX = {
    cat: re.compile('|'.join([re.escape(k) for k in keys]), re.IGNORECASE)
    for cat, keys in CATEGORY_ALIASES.items()
}


def load_first_existing(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    raise FileNotFoundError('No dataset file found among: ' + ', '.join(paths))


def normalize_category(text):
    if not isinstance(text, str):
        text = ''
    t = text.strip().lower()
    if t in {'ipc', 'consumer', 'crpc', 'family', 'property', 'it_act'}:
        return t
    # Heuristic based on content keywords
    for cat, rx in CATEGORY_REGEX.items():
        if rx.search(t):
            return cat
    return ''


def infer_category_from_row(row):
    # 1) use existing category if usable
    cat = normalize_category(row.get('category', ''))
    if cat:
        return cat
    # 2) infer from input and output text
    inp = str(row.get('input', '')).lower()
    out = str(row.get('output', '')).lower()
    text = inp + ' ' + out
    for cat, rx in CATEGORY_REGEX.items():
        if rx.search(text):
            return cat
    # Default bucket; keep uncategorized as 'ipc' minimally to avoid empty buckets
    return 'ipc'


def main():
    src_path = load_first_existing(CANDIDATES)
    df = pd.read_csv(src_path, encoding='utf-8')
    # Backup original combined if we're overwriting it
    if os.path.exists(OUTPUT) and not os.path.exists(BACKUP):
        try:
            pd.read_csv(OUTPUT, encoding='utf-8').to_csv(BACKUP, index=False)
        except Exception:
            pass

    # Ensure required columns
    for col in ['input', 'output']:
        if col not in df.columns:
            raise ValueError(f"Dataset missing required column: {col}")

    # Map categories
    new_categories = []
    for _, row in df.iterrows():
        new_categories.append(infer_category_from_row(row))
    df['category'] = new_categories

    # Minimal cleaning
    df = df.dropna(subset=['input', 'output'])
    df = df[df['input'].astype(str).str.strip() != '']
    df = df[df['output'].astype(str).str.strip() != '']
    if 'source' not in df.columns:
        df['source'] = 'mapped'

    # Save back to combined so training script picks it up
    df.to_csv(OUTPUT, index=False, encoding='utf-8')
    print(f"✅ Wrote categorized dataset to {OUTPUT}")
    print(df['category'].value_counts())


if __name__ == '__main__':
    main()
