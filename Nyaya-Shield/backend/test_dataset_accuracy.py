"""
Test script to verify bot gives specific replies from dataset for every query
"""
import sys
import os

print("=" * 80)
print("DATASET ACCURACY TEST - Verifying Specific Replies")
print("=" * 80)

# Test queries for each domain
test_cases = {
    'IPC': [
        "What is Section 420 IPC?",
        "What is the punishment for murder under IPC?",
        "Explain Section 302 IPC",
        "What are bailable and non-bailable offenses under IPC?"
    ],
    'Consumer': [
        "What are consumer rights under Consumer Protection Act?",
        "How to file a consumer complaint in India?",
        "What is deficiency in service under consumer law?",
        "Can I file a consumer complaint online?"
    ],
    'CrPC': [
        "What are my rights during arrest?",
        "How to file an FIR?",
        "What is anticipatory bail?",
        "Can police arrest without a warrant?"
    ],
    'Family': [
        "What is the procedure for divorce in India?",
        "What are the grounds for divorce under Hindu Marriage Act?",
        "How to file for child custody?",
        "What is maintenance under family law?"
    ],
    'Property': [
        "How to verify property documents before buying?",
        "What is mutation of property?",
        "What documents are required for property registration?",
        "What is stamp duty on property?"
    ],
    'IT Act': [
        "How to report cybercrime in India?",
        "What is Section 66A of IT Act?",
        "What to do if someone hacks my social media account?",
        "Is online defamation a crime?"
    ]
}

print("\n1. Testing Multi-Dataset Search Engine...")
try:
    from bot.multi_dataset_search import search_legal_answer
    print("   ✓ Multi-dataset search imported successfully")
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for domain, queries in test_cases.items():
        print(f"\n2. Testing {domain} Domain:")
        print("-" * 80)
        
        for query in queries:
            total_tests += 1
            try:
                # Search with domain-specific model
                result = search_legal_answer(
                    query=query,
                    domain=domain.lower().replace(' ', '_'),
                    threshold=0.3
                )
                
                answer = result.get('answer', '')
                confidence = result.get('confidence', 0)
                category = result.get('category', '')
                
                # Check if answer is specific (not generic)
                is_specific = len(answer) > 50 and confidence > 0.3
                
                # Check if category matches expected domain
                expected_cats = {
                    'IPC': 'ipc',
                    'Consumer': 'consumer',
                    'CrPC': 'crpc',
                    'Family': 'family',
                    'Property': 'property',
                    'IT Act': 'it_act'
                }
                category_match = category.lower() == expected_cats.get(domain, '').lower()
                
                if is_specific and category_match:
                    status = "✓ PASS"
                    passed_tests += 1
                else:
                    status = "✗ FAIL"
                    failed_tests.append({
                        'domain': domain,
                        'query': query,
                        'confidence': confidence,
                        'category': category,
                        'answer_length': len(answer)
                    })
                
                print(f"\n   Query: {query}")
                print(f"   Confidence: {confidence:.3f}")
                print(f"   Category: {category} (Expected: {expected_cats.get(domain)})")
                print(f"   Answer Length: {len(answer)} chars")
                print(f"   Answer Preview: {answer[:100]}...")
                print(f"   Status: {status}")
                
            except Exception as e:
                total_tests += 1
                failed_tests.append({
                    'domain': domain,
                    'query': query,
                    'error': str(e)
                })
                print(f"\n   Query: {query}")
                print(f"   Status: ✗ ERROR - {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"Failed: {len(failed_tests)} ({len(failed_tests)/total_tests*100:.1f}%)")
    
    if failed_tests:
        print("\n" + "=" * 80)
        print("FAILED TESTS DETAILS")
        print("=" * 80)
        for i, fail in enumerate(failed_tests, 1):
            print(f"\n{i}. Domain: {fail.get('domain')}")
            print(f"   Query: {fail.get('query')}")
            if 'error' in fail:
                print(f"   Error: {fail['error']}")
            else:
                print(f"   Confidence: {fail.get('confidence', 0):.3f}")
                print(f"   Category: {fail.get('category')} (Wrong)")
                print(f"   Answer Length: {fail.get('answer_length', 0)} chars")
    
    if passed_tests == total_tests:
        print("\n✓✓✓ ALL TESTS PASSED! Bot is giving specific replies from dataset ✓✓✓")
    else:
        print(f"\n⚠ {len(failed_tests)} tests need attention")
        
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
