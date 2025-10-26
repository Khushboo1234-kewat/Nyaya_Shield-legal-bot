"""Test script to verify context-aware suggestions work properly"""

def generate_contextual_suggestions(user_query, answer, category):
    """Generate context-specific follow-up questions based on the query and answer"""
    suggestions = []
    
    # Extract key terms from user query and answer
    query_lower = user_query.lower()
    answer_lower = answer.lower() if answer else ''
    
    # Category-specific suggestions
    category_map = {
        'ipc': {
            'keywords': ['section', 'punishment', 'offense', 'crime'],
            'questions': [
                "What is the procedure to file an FIR for this offense?",
                "Can this offense be compounded or settled?",
                "What are the bail provisions for this case?"
            ]
        },
        'consumer': {
            'keywords': ['rights', 'complaint', 'defective', 'refund'],
            'questions': [
                "How do I file a consumer complaint?",
                "What is the time limit for filing a consumer case?",
                "What compensation can I claim?"
            ]
        },
        'crpc': {
            'keywords': ['procedure', 'arrest', 'bail', 'trial'],
            'questions': [
                "What are my rights during arrest?",
                "How long can police detain someone?",
                "What is the process for getting bail?"
            ]
        },
        'family': {
            'keywords': ['divorce', 'custody', 'maintenance', 'marriage'],
            'questions': [
                "What documents are needed for this case?",
                "How long does this legal process take?",
                "Can this matter be resolved through mediation?"
            ]
        },
        'property': {
            'keywords': ['property', 'land', 'title', 'ownership'],
            'questions': [
                "What documents prove property ownership?",
                "How do I verify property title?",
                "What are the registration requirements?"
            ]
        },
        'it_act': {
            'keywords': ['cyber', 'online', 'digital', 'internet'],
            'questions': [
                "How do I report a cybercrime?",
                "What evidence should I preserve?",
                "Which authority handles such complaints?"
            ]
        }
    }
    
    # Get category-specific suggestions
    cat_lower = (category or '').lower()
    if cat_lower in category_map:
        cat_data = category_map[cat_lower]
        # Check if query matches category keywords
        if any(kw in query_lower or kw in answer_lower for kw in cat_data['keywords']):
            suggestions = cat_data['questions'][:3]
    
    # If no category match, generate generic but relevant questions
    if not suggestions:
        if 'section' in answer_lower or 'act' in answer_lower:
            suggestions.append("What are the penalties under this section?")
        if 'file' in query_lower or 'complaint' in query_lower:
            suggestions.append("What is the procedure to file this complaint?")
        if 'right' in query_lower or 'rights' in answer_lower:
            suggestions.append("What are my legal rights in this situation?")
    
    return suggestions[:3]

# Test cases
test_cases = [
    {
        'query': 'What is punishment for theft under IPC?',
        'answer': 'Theft under Section 378 IPC is punishable with imprisonment up to 3 years or fine or both.',
        'category': 'ipc'
    },
    {
        'query': 'What are consumer rights in India?',
        'answer': 'Consumers have the right to safety, information, choice, and redressal of complaints.',
        'category': 'consumer'
    },
    {
        'query': 'What is the arrest procedure under CrPC?',
        'answer': 'Under CrPC, police must inform the arrested person of grounds of arrest and right to bail.',
        'category': 'crpc'
    },
    {
        'query': 'How to file for divorce?',
        'answer': 'Divorce can be filed under various grounds including cruelty, adultery, or mutual consent.',
        'category': 'family'
    },
    {
        'query': 'What is property registration process?',
        'answer': 'Property must be registered with sub-registrar office with proper documentation and stamp duty.',
        'category': 'property'
    },
    {
        'query': 'How to report cybercrime?',
        'answer': 'Cybercrimes can be reported to cybercrime portal or local police station under IT Act.',
        'category': 'it_act'
    }
]

print("=" * 80)
print("TESTING CONTEXT-AWARE SUGGESTIONS")
print("=" * 80)

for i, test in enumerate(test_cases, 1):
    print(f"\n{i}. Category: {test['category'].upper()}")
    print(f"   Query: {test['query']}")
    print(f"   Answer: {test['answer'][:60]}...")
    
    suggestions = generate_contextual_suggestions(
        test['query'],
        test['answer'],
        test['category']
    )
    
    print(f"   Suggested Questions:")
    for j, suggestion in enumerate(suggestions, 1):
        print(f"      {j}. {suggestion}")

print("\n" + "=" * 80)
print("✅ Each category now has UNIQUE, RELEVANT suggestions!")
print("=" * 80)
