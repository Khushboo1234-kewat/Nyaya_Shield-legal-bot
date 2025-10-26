"""Quick test to verify bot is working with datasets"""
import sys
import os

print("=" * 80)
print("QUICK BOT TEST")
print("=" * 80)

# Test 1: Check if models exist
print("\n1. Checking models...")
bot_dir = os.path.join(os.path.dirname(__file__), 'bot')
models = ['chatbot_model.pkl', 'chatbot_model_consumer.pkl', 'chatbot_model_ipc.pkl']
for model in models:
    path = os.path.join(bot_dir, model)
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"   ✓ {model}: {size:,} bytes")
    else:
        print(f"   ✗ {model}: MISSING")

# Test 2: Load and test model
print("\n2. Testing model loading...")
try:
    import joblib
    from bot.train_model import get_legal_answer
    
    model_path = os.path.join(bot_dir, 'chatbot_model_consumer.pkl')
    model_data = joblib.load(model_path)
    qa_count = len(model_data.get('qa_pairs', []))
    print(f"   ✓ Consumer model loaded: {qa_count} Q&A pairs")
    
    # Test query
    test_query = "What are consumer rights under Consumer Protection Act?"
    answer, score, category = get_legal_answer(test_query, model_data, top_k=1)
    
    print(f"\n3. Test Query Results:")
    print(f"   Query: {test_query}")
    print(f"   Confidence: {score:.3f}")
    print(f"   Category: {category}")
    print(f"   Answer: {answer[:150]}...")
    
    if score > 0.5:
        print(f"\n   ✓ SUCCESS! Bot is working properly")
    else:
        print(f"\n   ⚠ Low confidence. May need threshold adjustment.")
        
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Multi-dataset search
print("\n4. Testing multi-dataset search...")
try:
    from bot.multi_dataset_search import search_legal_answer
    
    test_queries = [
        ("What is Section 420 IPC?", "ipc"),
        ("How to file consumer complaint?", "consumer"),
        ("What are my rights during arrest?", "crpc")
    ]
    
    for query, domain in test_queries:
        result = search_legal_answer(query, domain=domain, threshold=0.3)
        print(f"\n   Query: {query}")
        print(f"   Confidence: {result['confidence']:.3f}")
        print(f"   Category: {result['category']}")
        print(f"   Answer: {result['answer'][:100]}...")
        
    print(f"\n   ✓ Multi-dataset search working!")
    
except Exception as e:
    print(f"   ✗ Multi-dataset search error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print("\nIf all tests passed, your bot is ready to use!")
print("Start server with: python app.py")
