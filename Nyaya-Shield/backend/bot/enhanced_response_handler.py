"""
Enhanced Response Handler
- Understands user query
- Explains the question
- Provides solution from dataset
"""

import re
from typing import Dict, Tuple

class EnhancedResponseHandler:
    """Handles query understanding and solution-oriented responses"""
    
    def __init__(self):
        self.domain_keywords = {
            'ipc': ['ipc', 'section', 'penal code', 'criminal', 'offense', 'punishment', 'crime', 'murder', 'theft', 'assault'],
            'consumer': ['consumer', 'complaint', 'defective', 'product', 'service', 'refund', 'warranty', 'seller', 'buyer'],
            'crpc': ['crpc', 'arrest', 'bail', 'fir', 'procedure', 'investigation', 'magistrate', 'warrant', 'police'],
            'family': ['marriage', 'divorce', 'custody', 'maintenance', 'alimony', 'matrimonial', 'family', 'spouse', 'child'],
            'property': ['property', 'land', 'deed', 'registration', 'mutation', 'ownership', 'estate', 'title', 'sale'],
            'it_act': ['cyber', 'it act', 'online', 'hacking', 'digital', 'internet', 'data breach', 'phishing', 'fraud']
        }
    
    def understand_query(self, query: str) -> Dict[str, str]:
        """Analyze and understand the user's query"""
        query_lower = query.lower()
        
        # Detect domain
        detected_domain = self._detect_domain(query_lower)
        
        # Detect query type
        query_type = self._detect_query_type(query_lower)
        
        # Extract key entities
        entities = self._extract_entities(query)
        
        # Generate query explanation
        explanation = self._generate_explanation(query, detected_domain, query_type, entities)
        
        return {
            'domain': detected_domain,
            'query_type': query_type,
            'entities': entities,
            'explanation': explanation
        }
    
    def _detect_domain(self, query: str) -> str:
        """Detect legal domain from query"""
        domain_scores = {}
        
        for domain, keywords in self.domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query)
            if score > 0:
                domain_scores[domain] = score
        
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        return 'general'
    
    def _detect_query_type(self, query: str) -> str:
        """Detect type of legal query"""
        if any(word in query for word in ['what is', 'define', 'explain', 'meaning']):
            return 'definition'
        elif any(word in query for word in ['how to', 'procedure', 'process', 'steps']):
            return 'procedure'
        elif any(word in query for word in ['can i', 'am i', 'do i have', 'rights']):
            return 'rights'
        elif any(word in query for word in ['punishment', 'penalty', 'fine', 'jail']):
            return 'penalty'
        elif any(word in query for word in ['file', 'complaint', 'case', 'suit']):
            return 'filing'
        else:
            return 'general'
    
    def _extract_entities(self, query: str) -> Dict[str, list]:
        """Extract legal entities from query"""
        entities = {
            'sections': [],
            'acts': [],
            'terms': []
        }
        
        # Extract section numbers (e.g., Section 420, 302 IPC)
        section_pattern = r'section\s+(\d+[a-z]?)|(\d+[a-z]?)\s+ipc'
        sections = re.findall(section_pattern, query, re.IGNORECASE)
        entities['sections'] = [s[0] or s[1] for s in sections if s[0] or s[1]]
        
        # Extract act names
        act_pattern = r'([\w\s]+)\s+act|ipc|crpc|consumer protection act'
        acts = re.findall(act_pattern, query, re.IGNORECASE)
        entities['acts'] = [act.strip() for act in acts if act.strip()]
        
        # Extract key legal terms
        legal_terms = ['bail', 'arrest', 'fir', 'complaint', 'divorce', 'custody', 'property', 'registration']
        entities['terms'] = [term for term in legal_terms if term in query.lower()]
        
        return entities
    
    def _generate_explanation(self, query: str, domain: str, query_type: str, entities: Dict) -> str:
        """Generate explanation of the query"""
        explanations = []
        
        # Domain explanation
        domain_names = {
            'ipc': 'Indian Penal Code (Criminal Law)',
            'consumer': 'Consumer Protection Law',
            'crpc': 'Criminal Procedure Code',
            'family': 'Family Law',
            'property': 'Property Law',
            'it_act': 'Information Technology Act (Cyber Law)'
        }
        
        if domain in domain_names:
            explanations.append(f"Your question is about **{domain_names[domain]}**.")
        
        # Query type explanation
        type_explanations = {
            'definition': 'You want to understand the legal definition or meaning.',
            'procedure': 'You want to know the legal procedure or steps to follow.',
            'rights': 'You want to know your legal rights in this situation.',
            'penalty': 'You want to know about punishments or penalties.',
            'filing': 'You want to know how to file a legal complaint or case.'
        }
        
        if query_type in type_explanations:
            explanations.append(type_explanations[query_type])
        
        # Entity explanation
        if entities['sections']:
            sections_str = ', '.join(entities['sections'])
            explanations.append(f"This relates to Section(s): {sections_str}.")
        
        if entities['acts']:
            acts_str = ', '.join(set(entities['acts']))
            explanations.append(f"Under: {acts_str}.")
        
        return ' '.join(explanations) if explanations else 'Let me help you with your legal query.'
    
    def format_solution_response(self, query: str, answer: str, confidence: float, category: str) -> str:
        """Format response in user-friendly, conversational way like ChatGPT"""
        
        # Understand the query
        understanding = self.understand_query(query)
        
        # Build conversational response
        response_parts = []
        
        # 1. Friendly greeting based on query type
        greeting = self._get_friendly_greeting(understanding['query_type'], category)
        response_parts.append(greeting)
        response_parts.append("")
        
        # 2. Quick summary/understanding
        response_parts.append(f"**{understanding['explanation']}**")
        response_parts.append("")
        
        # 3. Main answer - formatted for readability
        response_parts.append("### Here's what you need to know:")
        response_parts.append("")
        
        # Format the answer for better readability
        formatted_answer = self._format_answer_paragraphs(answer)
        response_parts.append(formatted_answer)
        response_parts.append("")
        
        # 4. Key takeaways (if answer is long)
        if len(answer) > 300:
            key_points = self._extract_key_points(answer)
            if key_points:
                response_parts.append("### 🔑 Key Takeaways:")
                for point in key_points:
                    response_parts.append(f"✓ {point}")
                response_parts.append("")
        
        # 5. Action steps (for procedure queries)
        if understanding['query_type'] in ['procedure', 'filing']:
            steps = self._extract_steps(answer)
            if steps:
                response_parts.append("### 📋 What You Should Do:")
                for i, step in enumerate(steps, 1):
                    response_parts.append(f"**{i}.** {step}")
                response_parts.append("")
        
        # 6. Important notes (for rights queries)
        if understanding['query_type'] == 'rights':
            response_parts.append("### ⚠️ Important to Remember:")
            response_parts.append("• These are your legal rights - don't hesitate to exercise them")
            response_parts.append("• Consider consulting a lawyer for specific advice on your situation")
            response_parts.append("")
        
        # 7. Related legal references
        if understanding['entities']['sections'] or understanding['entities']['acts']:
            response_parts.append("### 📚 Legal References:")
            if understanding['entities']['sections']:
                response_parts.append(f"**Sections:** {', '.join(understanding['entities']['sections'])}")
            if understanding['entities']['acts']:
                response_parts.append(f"**Acts:** {', '.join(set(understanding['entities']['acts']))}")
            response_parts.append("")
        
        # 8. Helpful closing
        closing = self._get_helpful_closing(understanding['query_type'])
        response_parts.append(closing)
        
        return '\n'.join(response_parts)
    
    def _get_friendly_greeting(self, query_type: str, category: str) -> str:
        """Get friendly greeting based on query type"""
        greetings = {
            'definition': "Let me explain that for you! 📖",
            'procedure': "I'll walk you through the process step by step! 📝",
            'rights': "Here are your legal rights in this situation! ⚖️",
            'penalty': "Let me tell you about the legal consequences! ⚠️",
            'filing': "I'll guide you through the filing process! 📄",
            'general': "I'm here to help! 💡"
        }
        return greetings.get(query_type, "I'm here to help! 💡")
    
    def _format_answer_paragraphs(self, answer: str) -> str:
        """Format answer into readable paragraphs"""
        # Split into sentences
        sentences = answer.split('. ')
        
        # Group into paragraphs (every 3-4 sentences)
        paragraphs = []
        current_para = []
        
        for i, sentence in enumerate(sentences):
            current_para.append(sentence.strip())
            
            # Create paragraph every 3 sentences or at natural breaks
            if (i + 1) % 3 == 0 or i == len(sentences) - 1:
                para_text = '. '.join(current_para)
                if not para_text.endswith('.'):
                    para_text += '.'
                paragraphs.append(para_text)
                current_para = []
        
        return '\n\n'.join(paragraphs)
    
    def _get_helpful_closing(self, query_type: str) -> str:
        """Get helpful closing message"""
        closings = {
            'procedure': "💡 **Need more help?** Feel free to ask follow-up questions about any step!",
            'rights': "💡 **Remember:** If you need specific legal advice for your case, consult with a qualified lawyer.",
            'filing': "💡 **Pro tip:** Keep copies of all documents you file and note down important dates!",
            'penalty': "💡 **Important:** Legal consequences can vary based on specific circumstances. Consult a lawyer for your case.",
            'definition': "💡 **Want to know more?** Ask me about related sections or practical applications!",
            'general': "💡 **Have more questions?** I'm here to help with any legal queries!"
        }
        return closings.get(query_type, "💡 **Have more questions?** I'm here to help with any legal queries!")
    
    def _extract_key_points(self, text: str) -> list:
        """Extract key points from answer"""
        # Split by common delimiters
        sentences = re.split(r'[.;]', text)
        
        # Filter important sentences (containing keywords)
        important_keywords = ['right', 'must', 'shall', 'can', 'cannot', 'punishable', 'required', 'entitled']
        key_points = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in important_keywords) and len(sentence) > 20:
                key_points.append(sentence)
                if len(key_points) >= 3:  # Limit to 3 key points
                    break
        
        return key_points
    
    def _extract_steps(self, text: str) -> list:
        """Extract procedural steps from answer"""
        steps = []
        
        # Look for numbered steps
        step_pattern = r'(?:step\s*)?(\d+)[.):]\s*([^.]+\.)'
        matches = re.findall(step_pattern, text, re.IGNORECASE)
        
        for match in matches:
            steps.append(match[1].strip())
        
        # If no numbered steps, look for sentences with action words
        if not steps:
            action_words = ['file', 'submit', 'apply', 'contact', 'approach', 'obtain', 'register']
            sentences = re.split(r'[.;]', text)
            
            for sentence in sentences:
                sentence = sentence.strip()
                if any(word in sentence.lower() for word in action_words) and len(sentence) > 15:
                    steps.append(sentence)
                    if len(steps) >= 5:  # Limit to 5 steps
                        break
        
        return steps

# Global instance
_handler = None

def get_enhanced_handler():
    """Get singleton instance of enhanced handler"""
    global _handler
    if _handler is None:
        _handler = EnhancedResponseHandler()
    return _handler

def format_enhanced_response(query: str, answer: str, confidence: float, category: str) -> str:
    """Format response with query understanding and solution"""
    handler = get_enhanced_handler()
    return handler.format_solution_response(query, answer, confidence, category)
