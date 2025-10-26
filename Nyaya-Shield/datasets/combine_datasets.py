import pandas as pd
import json
import os
import glob

all_data = []

# Load IndicLegalQA Dataset
with open("IndicLegalQA Dataset/IndicLegalQA Dataset/IndicLegalQA Dataset_10K.json", 'r', encoding='utf-8') as f:
    indic_qa_data = json.load(f)

for item in indic_qa_data:
    all_data.append({
        'input': item.get('question', ''),
        'output': item.get('answer', ''),
        'source': 'IndicLegalQA',
        'category': 'case_qa'
    })

# Load Indian Laws Dataset
with open("IndicLegalQA Dataset/IndicLegalQA Dataset/indian_laws.json", 'r', encoding='utf-8') as f:
    laws_data = json.load(f)

for item in laws_data['indian_dataset']:
    all_data.append({
        'input': item.get('query', ''),
        'output': item.get('response', ''),
        'source': 'IndianLaws',
        'category': item.get('category', 'law')
    })

# Load Court Cases Training Data
court_df = pd.read_csv("court_cases/data.csv")

for _, row in court_df.iterrows():
    messages = row['messages']
    if '[INST]' in messages and '[/INST]' in messages:
        parts = messages.split('[/INST]')
        if len(parts) >= 2:
            instruction = parts[0].split('[INST]')[-1].strip()
            response = parts[1].split('[INST]')[0].strip()
            all_data.append({
                'input': instruction,
                'output': response,
                'source': 'CourtCases',
                'category': 'legal_consultation'
            })

# Load Constitutional Text Data
text_df = pd.read_csv("court_cases/Text.csv")

for _, row in text_df.iterrows():
    text_content = row['Text']
    all_data.append({
        'input': f"Explain this constitutional provision: {text_content[:200]}...",
        'output': text_content,
        'source': 'Constitution',
        'category': 'constitutional_law'
    })

# Load Indian Legal Consultant Dataset (if available)
try:
    ilc_df = pd.read_csv("Indian_legal_consultant/data.csv")
    for _, row in ilc_df.iterrows():
        messages = str(row.get('messages', ''))
        if '[INST]' in messages and '[/INST]' in messages:
            parts = messages.split('[/INST]')
            if len(parts) >= 2:
                instruction = parts[0].split('[INST]')[-1].strip()
                response = parts[1].split('[INST]')[0].strip()
                if instruction and response:
                    all_data.append({
                        'input': instruction,
                        'output': response,
                        'source': 'IndianLegalConsultant',
                        'category': 'legal_consultation'
                    })
except Exception:
    pass

try:
    ilc_text_df = pd.read_csv("Indian_legal_consultant/Text.csv")
    for _, row in ilc_text_df.iterrows():
        text_content = str(row.get('Text', '')).strip()
        if text_content:
            all_data.append({
                'input': f"Explain this legal text: {text_content[:200]}...",
                'output': text_content,
                'source': 'IndianLegalConsultant',
                'category': 'legal_knowledge'
            })
except Exception:
    pass

try:
    law_dir = os.path.join("Law data set")
    json_files = glob.glob(os.path.join(law_dir, "*.json"))
    for jf in json_files:
        try:
            with open(jf, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            continue
        fname = os.path.basename(jf).lower()
        if "consumer" in fname:
            cat = "consumer"
        elif "crpc" in fname:
            cat = "crpc"
        elif "cyber" in fname or "it" in fname:
            cat = "it_act"
        elif "ipc" in fname or "criminal" in fname:
            cat = "ipc"
        elif "family" in fname:
            cat = "family"
        elif "property" in fname:
            cat = "property"
        else:
            cat = "general"
        if isinstance(data, dict):
            items = data.get('data') or data.get('items') or data.get('records') or []
        else:
            items = data
        for item in items:
            if not isinstance(item, dict):
                continue
            q = item.get('question') or item.get('query') or item.get('Q') or item.get('prompt') or item.get('input') or ""
            a = item.get('answer') or item.get('response') or item.get('A') or item.get('completion') or item.get('output') or ""
            q = str(q).strip()
            a = str(a).strip()
            if q and a:
                all_data.append({
                    'input': q,
                    'output': a,
                    'source': 'LawDataSet',
                    'category': cat
                })
except Exception:
    pass

# Create and clean dataset
combined_df = pd.DataFrame(all_data)
combined_df['input'] = combined_df['input'].astype(str).str.replace('\s+', ' ', regex=True).str.strip()
combined_df['output'] = combined_df['output'].astype(str).str.replace('\s+', ' ', regex=True).str.strip()

# Basic validity filters
combined_df = combined_df.dropna(subset=['input', 'output'])
combined_df = combined_df[(combined_df['input'] != '') & (combined_df['output'] != '')]

# Remove trivial or noisy rows
combined_df = combined_df[combined_df['input'].str.len() >= 5]
combined_df = combined_df[combined_df['output'].str.len() >= 5]
combined_df = combined_df[combined_df['input'] != combined_df['output']]

# Remove common placeholder outputs
bad_outputs = {"n/a", "na", "none", "null", "?", "no answer", "not available"}
combined_df = combined_df[~combined_df['output'].str.lower().isin(bad_outputs)]

# Deduplicate
combined_df = combined_df.drop_duplicates(subset=['input', 'output'])

# Save datasets
combined_df.to_csv("combined_legal_dataset.csv", index=False, encoding='utf-8')

# Training/validation split
train_size = int(0.8 * len(combined_df))
train_df = combined_df[:train_size]
val_df = combined_df[train_size:]

train_df.to_csv("train_dataset.csv", index=False, encoding='utf-8')
val_df.to_csv("validation_dataset.csv", index=False, encoding='utf-8')

print(f"✅ Dataset ready: {len(combined_df):,} total records")
print(f"📊 Training: {len(train_df):,} | Validation: {len(val_df):,}")
print(f"📁 Files: combined_legal_dataset.csv, train_dataset.csv, validation_dataset.csv")