"""
Diagnostic script to check bot functionality
"""

import os
import sys

print("=" * 80)
print("NYAYA-SHIELD BOT DIAGNOSTIC")
print("=" * 80)

# Check 1: Python version
print(f"\n1. Python Version: {sys.version}")

# Check 2: Check if model files exist
print("\n2. Checking Model Files:")
bot_dir = os.path.join(os.path.dirname(__file__), 'bot')
model_files = [
    'chatbot_model.pkl',
    'chatbot_model_ipc.pkl',
    'chatbot_model_consumer.pkl',
    'chatbot_model_crpc.pkl',
    'chatbot_model_family.pkl',
    'chatbot_model_property.pkl',
    'chatbot_model_it_act.pkl',
    'vectorizer.pkl'
]

for model_file in model_files:
    path = os.path.join(bot_dir, model_file)
    exists = os.path.exists(path)
    size = os.path.getsize(path) if exists else 0
    status = "✓" if exists else "✗"
    print(f"   {status} {model_file:30s} {size:>12,} bytes" if exists else f"   {status} {model_file:30s} MISSING")

# Check 3: Try loading models
print("\n3. Testing Model Loading:")
try:
    import joblib
    print("   ✓ joblib imported")
    
    global_model_path = os.path.join(bot_dir, 'chatbot_model.pkl')
    if os.path.exists(global_model_path):
        model_data = joblib.load(global_model_path)
        qa_count = len(model_data.get('qa_pairs', []))
        print(f"   ✓ Global model loaded: {qa_count} Q&A pairs")
        
        # Test a simple query
        from bot.train_model import get_legal_answer
        test_query = "What is Section 420 IPC?"
        answer, score, category = get_legal_answer(test_query, model_data, top_k=1)
        print(f"   ✓ Test query successful")
        print(f"     Query: {test_query}")
        print(f"     Answer: {answer[:100]}...")
        print(f"     Confidence: {score:.3f}")
        print(f"     Category: {category}")
    else:
        print("   ✗ Global model file not found")
except Exception as e:
    print(f"   ✗ Error loading models: {e}")
    import traceback
    traceback.print_exc()

# Check 4: Test imports
print("\n4. Testing Bot Imports:")
try:
    from bot.nlp_service import initialize_service
    print("   ✓ nlp_service imported")
except Exception as e:
    print(f"   ✗ nlp_service import failed: {e}")

try:
    from bot.bot_controller import LegalBotController
    print("   ✓ bot_controller imported")
except Exception as e:
    print(f"   ✗ bot_controller import failed: {e}")

try:
    from bot.train_model import get_legal_answer
    print("   ✓ train_model imported")
except Exception as e:
    print(f"   ✗ train_model import failed: {e}")

try:
    from bot.multi_dataset_search import search_legal_answer
    print("   ✓ multi_dataset_search imported")
except Exception as e:
    print(f"   ✗ multi_dataset_search import failed: {e}")

# Check 5: Test multi-dataset search
print("\n5. Testing Multi-Dataset Search:")
try:
    from bot.multi_dataset_search import search_legal_answer, get_search_engine
    
    engine = get_search_engine()
    print(f"   ✓ Search engine initialized with {len(engine.models)} models")
    
    test_queries = [
        ("What is Section 420 IPC?", "ipc"),
        ("How to file consumer complaint?", "consumer"),
        ("What are my rights during arrest?", "crpc")
    ]
    
    for query, expected_domain in test_queries:
        result = search_legal_answer(query, domain=expected_domain, threshold=0.3)
        print(f"\n   Query: {query}")
        print(f"   Confidence: {result['confidence']:.3f}")
        print(f"   Category: {result['category']}")
        print(f"   Answer: {result['answer'][:80]}...")
        
except Exception as e:
    print(f"   ✗ Multi-dataset search test failed: {e}")
    import traceback
    traceback.print_exc()

# Check 6: Dataset files
print("\n6. Checking Dataset Files:")
dataset_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'datasets')
dataset_files = [
    'combined_legal_dataset.csv',
    'train_dataset.csv',
    'validation_dataset.csv'
]

for dataset_file in dataset_files:
    path = os.path.join(dataset_dir, dataset_file)
    exists = os.path.exists(path)
    size = os.path.getsize(path) if exists else 0
    status = "✓" if exists else "✗"
    print(f"   {status} {dataset_file:30s} {size:>12,} bytes" if exists else f"   {status} {dataset_file:30s} MISSING")

# Summary
print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
print("\nIf all checks passed, your bot should be working correctly.")
print("If any checks failed, review the errors above and fix the issues.")
print("\nTo start the bot, run: python app.py")
