"""
Test script for Multi-Dataset Search Engine
"""

import sys
import os

# Add bot directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_multi_dataset_search():
    """Test the multi-dataset search functionality"""
    
    print("=" * 80)
    print("TESTING MULTI-DATASET SEARCH ENGINE")
    print("=" * 80)
    
    try:
        from bot.multi_dataset_search import search_legal_answer, get_search_engine
        
        # Initialize search engine
        print("\n1. Initializing search engine...")
        engine = get_search_engine()
        print(f"   ✓ Loaded {len(engine.models)} models")
        for model_name, model_data in engine.models.items():
            qa_count = len(model_data.get('qa_pairs', []))
            print(f"     - {model_name}: {qa_count} Q&A pairs")
        
        # Test queries
        test_cases = [
            {
                'query': 'What is Section 420 IPC?',
                'domain': None,
                'expected_category': 'ipc'
            },
            {
                'query': 'How to file a consumer complaint?',
                'domain': 'consumer',
                'expected_category': 'consumer'
            },
            {
                'query': 'What are my rights during arrest?',
                'domain': None,
                'expected_category': 'crpc'
            },
            {
                'query': 'Divorce procedure in India',
                'domain': None,
                'expected_category': 'family'
            },
            {
                'query': 'How to report cybercrime?',
                'domain': None,
                'expected_category': 'it_act'
            },
            {
                'query': 'Property registration process',
                'domain': 'property',
                'expected_category': 'property'
            }
        ]
        
        print("\n2. Running test queries...")
        print("=" * 80)
        
        passed = 0
        failed = 0
        
        for i, test in enumerate(test_cases, 1):
            print(f"\nTest {i}/{len(test_cases)}")
            print("-" * 80)
            print(f"Query: {test['query']}")
            if test['domain']:
                print(f"Domain Hint: {test['domain']}")
            
            try:
                result = search_legal_answer(
                    query=test['query'],
                    domain=test['domain'],
                    threshold=0.3
                )
                
                print(f"\n✓ Search completed successfully")
                print(f"  Confidence: {result['confidence']:.3f}")
                print(f"  Category: {result['category']}")
                print(f"  Search Path: {' → '.join(result.get('search_path', []))}")
                print(f"  Found Matches: {result.get('found_matches', 0)}")
                print(f"  Sources: {', '.join(result.get('sources', []))}")
                
                # Show answer preview
                answer = result.get('answer', '')
                preview = answer[:200] + "..." if len(answer) > 200 else answer
                print(f"\n  Answer Preview:\n  {preview}")
                
                # Verify category if expected
                if test['expected_category']:
                    actual_cat = result['category'].lower()
                    expected_cat = test['expected_category'].lower()
                    if actual_cat == expected_cat or expected_cat in actual_cat:
                        print(f"\n  ✓ Category matches expected: {expected_cat}")
                        passed += 1
                    else:
                        print(f"\n  ✗ Category mismatch: expected {expected_cat}, got {actual_cat}")
                        failed += 1
                else:
                    passed += 1
                
            except Exception as e:
                print(f"\n✗ Test failed with error: {e}")
                failed += 1
        
        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {len(test_cases)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(test_cases)*100):.1f}%")
        
        if failed == 0:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print(f"\n⚠️  {failed} test(s) failed")
            return 1
            
    except ImportError as e:
        print(f"\n✗ Failed to import multi_dataset_search module: {e}")
        print("\nMake sure the bot/multi_dataset_search.py file exists and models are loaded.")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(test_multi_dataset_search())
