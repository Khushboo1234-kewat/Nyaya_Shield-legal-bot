"""
NLP Service Module for NyayaShield
=================================

This module provides intelligent legal response generation using similarity matching.
It integrates with the trained legal Q&A model and provides enhanced NLP features.

"""

import os
import sys
import json
import joblib
import logging
import numpy as np
import random
from typing import Dict, List, Tuple, Optional, Union
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import warnings

# Import preprocessing functions with fallback for script execution
try:
    if __package__:
        from bot.preprocess import preprocess_legal_text
        from bot.bot_controller import LegalBotController
        try:
            from bot.train_model import get_legal_answer as tm_get_legal_answer
        except Exception:
            tm_get_legal_answer = None
    else:
        raise ImportError
except Exception:
    _current_dir = os.path.dirname(os.path.abspath(__file__))
    _parent_dir = os.path.dirname(_current_dir)
    if _parent_dir not in sys.path:
        sys.path.insert(0, _parent_dir)
    from bot.preprocess import preprocess_legal_text
    from bot.bot_controller import LegalBotController
    try:
        from bot.train_model import get_legal_answer as tm_get_legal_answer
    except Exception:
        tm_get_legal_answer = None

# Try to import LLM helpers; if unavailable, provide safe fallbacks
try:
    from .llm_service import get_response as llm_get_response, is_legal_query, get_casual_response, initialize_llm_service
except Exception as _e:
    logging.getLogger(__name__).warning(f"LLM service unavailable ({_e}). Using fallback responses.")

    def llm_get_response(query: str, legal_response: str = None) -> str:
        return legal_response or "I'm here to help with legal queries. Please provide more details."

    def is_legal_query(query: str) -> bool:
        # Default to treating queries as legal to keep core bot functional
        return True

    def get_casual_response(query: str) -> dict:
        return {
            'answer': "Hello! I'm your legal assistant. Ask a legal question to begin.",
            'confidence': 0.8,
            'type': 'casual',
            'category': 'greeting'
        }

    def initialize_llm_service(device: str = None):
        return None

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LegalNLPService:
    """
    Enhanced NLP service for legal document analysis and response generation.
    Handles both legal queries and casual conversations.
    """
    
    def __init__(self, model_dir: str = None, device: str = None):
        """
        Initialize the NLP service with model loading.
        
        Args:
            model_dir (str): Directory containing trained models (optional)
            device (str): Device to run models on ('cuda' or 'cpu')
        """
        self.model_dir = model_dir or os.path.dirname(__file__)
        self.bot_controller = LegalBotController()
        self.confidence_threshold = 0.3
        self.classifier_bundle = None
        # Initialize LLM service
        self.llm_service = initialize_llm_service(device)
        
        # Legal knowledge base
        self.legal_categories = {
            'criminal': ['murder', 'theft', 'assault', 'fir', 'police', 'arrest', 'bail', 'ipc', 'crpc'],
            'civil': ['contract', 'property', 'tort', 'negligence', 'damages', 'suit', 'injunction'],
            'family': ['marriage', 'divorce', 'custody', 'maintenance', 'alimony', 'adoption'],
            'consumer': ['defective', 'service', 'complaint', 'refund', 'warranty', 'consumer court'],
            'constitutional': ['fundamental rights', 'article', 'constitution', 'writ', 'petition', 'rti', 'right to information', 'information act', 'government information', 'mange'],
            'corporate': ['company', 'director', 'shares', 'corporate law', 'compliance'],
            'labour': ['employment', 'salary', 'wages', 'workplace', 'labour law', 'pf', 'esi', 'labour', 'protection', 'worker']
        }
        
        # Casual conversation responses
        self.casual_responses = {
            'greeting': [
                "Hi there! I'm NyayaShield. How can I assist you with legal matters today?",
                "Hello! I'm here to help with legal questions. What can I help you with?",
                "Hey! How can I assist you with legal information today?"
            ],
            'how_are_you': [
                "I'm just a legal assistant, but I'm functioning well! How can I help you today?",
                "I don't have feelings, but I'm ready to assist with your legal queries!",
                "I'm doing well, thank you! How can I assist you with legal matters today?"
            ],
            'thanks': [
                "You're welcome! Let me know if you have any other legal questions.",
                "Happy to help! Feel free to ask if you have more legal queries.",
                "My pleasure! Is there anything else you'd like to know about?"
            ],
            'goodbye': [
                "Goodbye! Don't hesitate to return if you have more legal questions.",
                "Farewell! Remember, I'm here for your legal queries anytime.",
                "Goodbye! Stay informed and stay legal!"
            ],
            'identity': [
                "I'm NyayaShield, your legal assistant. I can help answer legal questions or point you in the right direction.",
                "I'm your legal AI assistant, here to provide information on legal matters. How can I help?",
                "I'm NyayaShield, designed to assist with legal queries. What would you like to know?"
            ],
            'fallback': [
                "I'm not sure I understand. Could you rephrase that as a legal question?",
                "I'm designed to help with legal questions. Could you clarify what legal information you need?",
                "I might not have the answer to that. Would you like to ask a legal question?"
            ]
        }
        
        # Load model data
        self.model_data = None
        self._load_model_data()
        self._load_classifier()

        # Basic profanity/unsafe phrase list (lightweight safety check)
        self._profanity = {
            'abuse', 'kill', 'suicide', 'self harm', 'hate', 'terror', 'bomb'
        }
        # Simple PII patterns
        self._pii_patterns = {
            'email': '@',
            'phone_digits': ''.join(str(d) for d in range(10))
        }
    
    def _load_model_data(self):
        """Load the trained legal Q&A model data."""
        try:
            # Ensure the controller loads the model into its state
            loaded = self.bot_controller.load_model()
            # bot_controller.load_model returns a boolean; fetch the actual model data from the controller
            self.model_data = getattr(self.bot_controller, 'model_data', None)
            if isinstance(self.model_data, dict) and 'qa_pairs' in self.model_data:
                logger.info(f"Legal model loaded with {len(self.model_data['qa_pairs'])} Q&A pairs")
            else:
                if not loaded:
                    logger.warning("Model could not be loaded by controller")
                else:
                    logger.warning("Model data structure is not as expected")
                self.model_data = None
        except Exception as e:
            logger.warning(f"Could not load model data: {str(e)}")
            self.model_data = None
    
    def _load_classifier(self):
        try:
            path = os.path.join(self.model_dir, 'classifier_category.joblib')
            if os.path.exists(path):
                self.classifier_bundle = joblib.load(path)
        except Exception as e:
            self.classifier_bundle = None
    
    def _predict_category_ml(self, query: str):
        if not self.classifier_bundle:
            return None, 0.0
        pipe = self.classifier_bundle.get('pipeline')
        try:
            x = preprocess_legal_text(query)
        except Exception:
            x = (query or '').lower().strip()
        try:
            if hasattr(pipe, 'predict_proba'):
                proba = pipe.predict_proba([x])[0]
                idx = int(np.argmax(proba))
                label = pipe.classes_[idx]
                conf = float(np.max(proba))
                return str(label), conf
            if hasattr(pipe, 'decision_function'):
                df = pipe.decision_function([x])
                if df.ndim == 1:
                    scores = df
                else:
                    scores = df[0]
                idx = int(np.argmax(scores))
                label = pipe.classes_[idx]
                m = float(np.max(scores))
                M = float(np.max(np.abs(scores))) or 1.0
                conf = max(0.0, min(1.0, 0.5 + 0.5 * (m / M)))
                return str(label), conf
            pred = pipe.predict([x])[0]
            return str(pred), 0.5
        except Exception:
            return None, 0.0
    
    def classify_legal_category(self, query: str) -> Tuple[str, float]:
        ml_label, ml_conf = self._predict_category_ml(query)
        if ml_label and ml_conf >= 0.5:
            return ml_label.strip().lower(), ml_conf
        query_lower = query.lower()
        category_scores = {}
        for category, keywords in self.legal_categories.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                category_scores[category] = score / len(keywords)
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            confidence = category_scores[best_category]
            return best_category, confidence
        return 'general', 0.1

    def detect_intent(self, query: str) -> str:
        """Lightweight intent detection for interactive chat UX."""
        q = (query or '').lower().strip()
        if not q:
            return 'unknown'
        if any(w in q for w in ['hi', 'hello', 'hey', 'good morning', 'good evening']):
            return 'greeting'
        if any(w in q for w in ['bye', 'goodbye', 'see you', 'exit', 'quit']):
            return 'goodbye'
        if any(w in q for w in ['thank', 'thanks', 'thx']):
            return 'thanks'
        if any(w in q for w in ['who are you', 'what are you', 'your name']):
            return 'identity'
        return 'legal_query'

    def safety_screen(self, query: str) -> Dict[str, bool]:
        """Very basic safety/PII screening. Does not block, only flags."""
        q = (query or '').lower()
        flags = {
            'contains_profanity': any(term in q for term in self._profanity),
            'contains_email': '@' in q,
            'contains_phone_like': sum(ch.isdigit() for ch in q) >= 8,
        }
        return flags

    def suggest_followups(self, category: str, legal_terms: List[str]) -> List[str]:
        """Generate follow-up questions to keep the conversation going."""
        base = [
            'Could you share any dates or documents related to this?',
            'Do you want guidance on filing a complaint or drafting a notice?',
        ]
        cat = (category or 'general').lower()
        cat_map = {
            'criminal': [
                'Do you need help understanding FIR or bail process?',
                'Were there any witnesses or medical records?'
            ],
            'family': [
                'Do you want to discuss mediation or custody documentation?',
                'Do you need help with maintenance/alimony process?'
            ],
            'consumer': [
                'Do you need a draft for a consumer complaint?',
                'Do you have receipts, bills, or warranty details?'
            ],
            'property': [
                'Do you want a checklist for property title and registration?',
                'Do you need steps for eviction/tenant dispute?'
            ],
            'constitutional': [
                'Are you considering filing a writ petition?',
                'Do you want to file an RTI for more information?'
            ],
        }
        out = base + cat_map.get(cat, [])
        if legal_terms:
            out.append(f"Do you want more details about {legal_terms[0]}?")
        # Deduplicate preserving order
        seen = set()
        uniq = []
        for s in out:
            if s not in seen:
                seen.add(s)
                uniq.append(s)
        return uniq[:4]
    
    def get_enhanced_response(self, query: str, top_k: int = 3) -> Dict:
        """Get enhanced response with category classification and multiple matches."""
        try:
            # Get basic response from bot controller
            basic_result = self.bot_controller.get_detailed_response(query)
            
            # Classify legal category
            category, category_confidence = self.classify_legal_category(query)
            if self.model_data and category and category_confidence >= 0.6:
                try:
                    if 'vectorizer' in self.model_data and 'qa_pairs' in self.model_data and 'question_vectors' in self.model_data:
                        if 'tm_get_legal_answer' in globals() and tm_get_legal_answer:
                            ans, sim, cat = tm_get_legal_answer(query, self.model_data, top_k=3, category_filter=category)
                            if isinstance(basic_result, dict):
                                if sim > float(basic_result.get('confidence', 0.0)):
                                    basic_result.update({'answer': ans, 'confidence': sim, 'category': cat or category, 'source': 'trained_model'})
                        else:
                            pass
                except Exception:
                    pass
            
            # Get multiple similar answers if model data is available
            similar_answers = []
            if self.model_data:
                similar_answers = self._get_multiple_answers(query, top_k)
            
            # Extract key legal terms
            legal_terms = self._extract_legal_terms(query)
            # Detect intent and safety
            intent = self.detect_intent(query)
            safety = self.safety_screen(query)
            # Follow-up suggestions
            suggestions = self.suggest_followups(category, legal_terms)
            guidance = self._generate_guidance(category)
            
            return {
                'answer': basic_result['answer'],
                'confidence': basic_result['confidence'],
                'category': category,
                'category_confidence': category_confidence,
                'source': basic_result['source'],
                'similar_answers': similar_answers,
                'legal_terms': legal_terms,
                'suggested_questions': suggestions,
                'intent': intent,
                'safety_flags': safety,
                'process': guidance.get('process', []),
                'penalties': guidance.get('penalties', []),
                'defenses': guidance.get('defenses', []),
                'authority_preparation': guidance.get('authority_prep', []),
                'timeline': guidance.get('timeline', []),
                'recommendations': self._get_category_recommendations(category),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced response: {str(e)}")
            return {
                'answer': "I apologize, but I encountered an error processing your query. Please try again.",
                'confidence': 0.0,
                'category': 'error',
                'category_confidence': 0.0,
                'source': 'system',
                'similar_answers': [],
                'legal_terms': [],
                'recommendations': [],
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_multiple_answers(self, query: str, top_k: int = 3) -> List[Dict]:
        """Get multiple similar answers using the trained model."""
        try:
            vectorizer = self.model_data['vectorizer']
            qa_pairs = self.model_data['qa_pairs']
            question_vectors = self.model_data['question_vectors']
            
            # Process query
            try:
                processed_query = preprocess_legal_text(query)
            except:
                processed_query = query.lower().strip()
            
            # Get similarities
            query_vector = vectorizer.transform([processed_query])
            similarities = cosine_similarity(query_vector, question_vectors)[0]
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            similar_answers = []
            for idx in top_indices:
                if similarities[idx] > 0.1:  # Minimum threshold
                    qa_pair = qa_pairs[idx]
                    similar_answers.append({
                        'answer': qa_pair['answer'][:200] + '...' if len(qa_pair['answer']) > 200 else qa_pair['answer'],
                        'similarity': float(similarities[idx]),
                        'category': qa_pair.get('category', 'unknown'),
                        'source': qa_pair.get('source', 'unknown')
                    })
            
            return similar_answers
            
        except Exception as e:
            logger.error(f"Error getting multiple answers: {str(e)}")
            return []
    
    def _extract_legal_terms(self, query: str) -> List[str]:
        """Extract important legal terms from the query."""
        legal_keywords = [
            'section', 'act', 'article', 'clause', 'amendment', 'law', 'rule', 'regulation',
            'court', 'judge', 'lawyer', 'advocate', 'petition', 'appeal', 'case', 'suit',
            'plaintiff', 'defendant', 'accused', 'victim', 'witness', 'evidence', 'proof',
            'bail', 'custody', 'arrest', 'fir', 'complaint', 'charge', 'punishment',
            'contract', 'agreement', 'property', 'ownership', 'transfer', 'registration',
            'marriage', 'divorce', 'maintenance', 'custody', 'adoption', 'inheritance',
            'consumer', 'service', 'defective', 'warranty', 'refund', 'compensation'
        ]
        
        query_lower = query.lower()
        found_terms = [term for term in legal_keywords if term in query_lower]
        return found_terms[:5]  # Return top 5 relevant terms
    
    def _get_category_recommendations(self, category: str) -> List[str]:
        """Get recommendations based on legal category."""
        recommendations = {
            'criminal': [
                "Consult a criminal lawyer immediately",
                "Do not speak to police without legal representation",
                "Gather all relevant documents and evidence"
            ],
            'civil': [
                "Document all communications and agreements",
                "Consult a civil lawyer for legal options",
                "Consider alternative dispute resolution"
            ],
            'family': [
                "Seek family counseling if appropriate",
                "Consult a family law specialist",
                "Gather financial and custody-related documents"
            ],
            'consumer': [
                "File complaint with consumer forum",
                "Keep all receipts and warranty documents",
                "Try to resolve with company first"
            ],
            'constitutional': [
                "Consider filing a writ petition",
                "Consult a constitutional law expert",
                "Research precedent cases"
            ],
            'corporate': [
                "Review company compliance requirements",
                "Consult a corporate law specialist",
                "Check regulatory guidelines"
            ],
            'labour': [
                "Contact labour commissioner",
                "Join or consult trade union",
                "Document workplace violations"
            ]
        }
        
        return recommendations.get(category, [
            "Consult with a qualified legal professional",
            "Gather all relevant documents",
            "Research applicable laws and regulations"
        ])
    
    def find_relevant_sections(self, query: str, legal_area: str) -> List[Dict]:
        """
        Find relevant legal sections based on query and classified area.
        
        Args:
            query (str): User query
            legal_area (str): Classified legal area
            
        Returns:
            List[Dict]: Relevant sections with scores
        """
        relevant_sections = []
        
        try:
            # Use model data if available for finding relevant sections
            if self.model_data and 'qa_pairs' in self.model_data:
                qa_pairs = self.model_data['qa_pairs']
                query_lower = query.lower()
                
                for qa_pair in qa_pairs:
                    if legal_area.lower() in qa_pair.get('category', '').lower():
                        # Simple keyword matching for relevance
                        question = qa_pair.get('question', '').lower()
                        answer = qa_pair.get('answer', '')
                        
                        # Calculate simple similarity
                        query_words = set(query_lower.split())
                        question_words = set(question.split())
                        
                        intersection = query_words.intersection(question_words)
                        if intersection:
                            similarity_score = len(intersection) / max(len(query_words), len(question_words))
                            
                            relevant_sections.append({
                                "section": f"Legal Guidance - {qa_pair.get('category', 'General')}",
                                "content": answer[:200] + '...' if len(answer) > 200 else answer,
                                "score": similarity_score,
                                "area": legal_area
                            })
                
                # Sort by relevance score
                relevant_sections.sort(key=lambda x: x["score"], reverse=True)
                
        except Exception as e:
            logger.error(f"Error finding relevant sections: {str(e)}")
        
        return relevant_sections[:3]  # Return top 3 relevant sections
    
    def find_similar_cases(self, query: str, legal_area: str) -> List[Dict]:
        """
        Find similar legal cases based on query.
        
        Args:
            query (str): User query
            legal_area (str): Legal area
            
        Returns:
            List[Dict]: Similar cases
        """
        similar_cases = []
        
        try:
            # Use model data to find similar cases
            if self.model_data and 'qa_pairs' in self.model_data:
                qa_pairs = self.model_data['qa_pairs']
                query_lower = query.lower()
                
                for qa_pair in qa_pairs:
                    if 'case' in qa_pair.get('source', '').lower() or 'court' in qa_pair.get('source', '').lower():
                        question = qa_pair.get('question', '').lower()
                        
                        # Simple similarity calculation
                        query_words = set(query_lower.split())
                        question_words = set(question.split())
                        
                        intersection = query_words.intersection(question_words)
                        if intersection and len(intersection) > 1:
                            similarity_score = len(intersection) / max(len(query_words), len(question_words))
                            
                            if similarity_score > 0.1:
                                similar_cases.append({
                                    "case": qa_pair.get('source', 'Legal Case'),
                                    "citation": qa_pair.get('category', ''),
                                    "holding": qa_pair.get('answer', '')[:150] + '...',
                                    "score": similarity_score
                                })
                
                # Sort by similarity score
                similar_cases.sort(key=lambda x: x["score"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error finding similar cases: {str(e)}")
        
        return similar_cases[:2]  # Return top 2 similar cases
    
    def extract_entities_from_query(self, query: str) -> Dict:
        """
        Extract legal entities from the user query.
        
        Args:
            query (str): User query
            
        Returns:
            Dict: Extracted entities
        """
        # Simple entity extraction for legal terms
        entities = {
            'legal_terms': self._extract_legal_terms(query),
            'dates': [],
            'monetary_amounts': [],
            'case_citations': [],
            'statutes': []
        }
        return entities
    
    def classify_legal_area(self, query: str) -> Tuple[str, float]:
        """
        Classify the legal area of the query using keyword matching.
        
        Args:
            query (str): User query
            
        Returns:
            Tuple[str, float]: Legal area and confidence score
        """
        return self.classify_legal_category(query)
    
    def generate_response(self, query: str) -> Dict:
        """
        Generate comprehensive legal response for user query.
        
        Args:
            query (str): User query
            
        Returns:
            Dict: Comprehensive response with sections, cases, analysis, intent, safety flags, and follow-up suggestions
            Dict: Comprehensive response with sections, cases, and analysis
        """
        try:
            # Classify legal area
            legal_area, confidence = self.classify_legal_area(query)
            
            # Find relevant sections
            relevant_sections = self.find_relevant_sections(query, legal_area)
            
            # Find similar cases
            similar_cases = self.find_similar_cases(query, legal_area)
            
            # Extract entities
            entities = self.extract_entities_from_query(query)
            
            # Generate response
            guidance = self._generate_guidance(legal_area)
            response = {
                "query": query,
                "legal_area": legal_area,
                "confidence": round(confidence, 3),
                "timestamp": datetime.now().isoformat(),
                "relevant_sections": relevant_sections,
                "similar_cases": similar_cases,
                "extracted_entities": entities,
                "recommendations": self._generate_recommendations(legal_area, relevant_sections),
                "next_steps": self._generate_next_steps(legal_area, entities),
                "intent": self.detect_intent(query),
                "safety_flags": self.safety_screen(query),
                "suggested_questions": self.suggest_followups(legal_area, entities.get('legal_terms', [])),
                "process": guidance.get('process', []),
                "penalties": guidance.get('penalties', []),
                "defenses": guidance.get('defenses', []),
                "authority_preparation": guidance.get('authority_prep', []),
                "timeline": guidance.get('timeline', [])
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "query": query,
                "error": str(e),
                "legal_area": "General Legal",
                "confidence": 0.0,
                "timestamp": datetime.now().isoformat(),
                "relevant_sections": [],
                "similar_cases": [],
                "extracted_entities": {},
                "recommendations": ["Please consult with a qualified attorney for specific legal advice."],
                "next_steps": ["Gather relevant documents", "Consult legal professional"]
            }
    
    def _generate_recommendations(self, legal_area: str, sections: List[Dict]) -> List[str]:
        """Generate recommendations based on legal area and relevant sections."""
        recommendations = []
        
        if legal_area == "Contract Law":
            recommendations = [
                "Review all contract terms carefully before signing",
                "Ensure all parties have legal capacity to enter the contract",
                "Document any modifications to the original agreement"
            ]
        elif legal_area == "Criminal Law":
            recommendations = [
                "Exercise your right to remain silent",
                "Request legal representation immediately",
                "Do not discuss the case without an attorney present"
            ]
        elif legal_area == "Property Law":
            recommendations = [
                "Conduct a thorough title search before purchase",
                "Review all property disclosures and inspections",
                "Understand local zoning and property regulations"
            ]
        else:
            recommendations = [
                "Gather all relevant documents and evidence",
                "Consult with a qualified attorney in the specific legal area",
                "Document all communications and interactions related to the matter"
            ]
        
        return recommendations
    
    def _generate_next_steps(self, legal_area: str, entities: Dict) -> List[str]:
        """Generate next steps based on legal area and extracted entities."""
        next_steps = ["Consult with a qualified attorney"]
        
        if entities.get("monetary_amounts"):
            next_steps.append("Calculate potential damages and costs")
        
        if entities.get("dates"):
            next_steps.append("Check statute of limitations and important deadlines")
        
        if entities.get("case_citations"):
            next_steps.append("Research cited cases for precedent analysis")
        
        if entities.get("statutes"):
            next_steps.append("Review relevant statutes and regulations")
        
        next_steps.append("Gather supporting documentation")
        
        return next_steps
    
    def get_legal_response(self, user_input: str) -> Union[str, Dict]:
        """
        Main interface method for getting legal responses (backward compatibility).
        
        Args:
            user_input (str): User query
            
        Returns:
            Union[str, Dict]: Legal response
        """
        response = self.generate_response(user_input)
        
        # For backward compatibility, return simple string if only basic response needed
        if response.get("relevant_sections"):
            best_section = response["relevant_sections"][0]
            return f"{response['legal_area']}: {best_section['content']}"
        else:
            return f"{response['legal_area']}: General legal guidance recommended."
    
    def _is_legal_query(self, query: str) -> bool:
        """
        Determine if a query is legal-related.
        
        Args:
            query (str): User query
            
        Returns:
            bool: True if legal-related, False if casual
        """
        query = query.lower()
        
        # Check for casual phrases
        casual_phrases = [
            'hi', 'hello', 'hey', 'howdy', 'yo',
            'how are you', "what's up", 'sup',
            'thank', 'thanks', 'thank you', 'thx',
            'bye', 'goodbye', 'see you', 'later',
            'who are you', 'what are you', 'your name',
            'good morning', 'good afternoon', 'good evening',
            'how do you do', "what's new"
        ]
        
        if any(phrase in query for phrase in casual_phrases):
            return False
            
        # Check for legal terms
        for category_terms in self.legal_categories.values():
            if any(term in query for term in category_terms):
                return True
                
        # If query is very short, likely casual
        if len(query.split()) <= 2:
            return False
            
        # Default to legal if we're not sure
        return True
    
    def _get_casual_response(self, query: str) -> Dict:
        """
        Generate a response for casual queries.
        
        Args:
            query (str): User query
            
        Returns:
            Dict: Response with answer and metadata
        """
        query = query.lower().strip()
        
        # Handle greetings
        if any(word in query for word in ['hi', 'hello', 'hey', 'howdy', 'yo']):
            return {
                'answer': random.choice(self.casual_responses['greeting']),
                'confidence': 1.0,
                'type': 'casual',
                'category': 'greeting'
            }
        
        # Handle how are you
        if any(phrase in query for phrase in ['how are you', "how's it going", "what's up", 'sup']):
            return {
                'answer': random.choice(self.casual_responses['how_are_you']),
                'confidence': 1.0,
                'type': 'casual',
                'category': 'greeting'
            }
        
        # Handle thanks
        if any(word in query for word in ['thank', 'thanks', 'thx', 'appreciate']):
            return {
                'answer': random.choice(self.casual_responses['thanks']),
                'confidence': 1.0,
                'type': 'casual',
                'category': 'gratitude'
            }
        
        # Handle goodbyes
        if any(word in query for word in ['bye', 'goodbye', 'see you', 'later']):
            return {
                'answer': random.choice(self.casual_responses['goodbye']),
                'confidence': 1.0,
                'type': 'casual',
                'category': 'goodbye'
            }
        
        # Handle bot identity
        if any(phrase in query for phrase in ['who are you', 'what are you', 'your name']):
            return {
                'answer': random.choice(self.casual_responses['identity']),
                'confidence': 1.0,
                'type': 'casual',
                'category': 'identity'
            }
        
        # Fallback for other casual queries
        return {
            'answer': random.choice(self.casual_responses['fallback']),
            'confidence': 0.8,
            'type': 'casual',
            'category': 'unknown'
        }

    def get_detailed_response(self, user_input: str) -> Dict:
        """
        Get detailed legal response with full analysis.
        
        Args:
            user_input (str): User query
            
        Returns:
            Dict: Detailed response
        """
        # First check if this is a casual query
        if not self._is_legal_query(user_input):
            return self._get_casual_response(user_input)
            
        # Otherwise, generate legal response
        return self.generate_response(user_input)
    
    def get_response(self, user_input: str) -> Dict[str, any]:
        """
        Get appropriate response for user input, handling both legal and casual queries.
        Uses the LLM service to determine if the query is legal or casual.
        
        Args:
            user_input: User's input text
            
        Returns:
            Dict containing response details
        """
        # First get the legal response (we'll use it if this is a legal query)
        legal_response = self.get_legal_response(user_input)
        
        # Use LLM service to get the most appropriate response
        final_response = llm_get_response(
            query=user_input,
            legal_response=legal_response.get('answer') if legal_response else None
        )
        
        # Determine if this was a legal or casual response
        is_legal = is_legal_query(user_input)
        
        # Return the response in the expected format
        if is_legal and legal_response:
            # If it's a legal query and we have a legal response, use that
            return legal_response
        else:
            # Otherwise, use the casual response from LLM
            return {
                'answer': final_response,
                'is_legal': False,
                'confidence': 1.0,
                'category': 'casual',
                'source': 'llm_casual_response'
            }
    
    def save_query_log(self, query: str, response: Dict, log_file: str = "query_log.json"):
        """
        Save query and response for analysis and improvement.
        
        Args:
            query (str): User query
            response (Dict): Generated response
            log_file (str): Log file path
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "legal_area": response.get("legal_area"),
                "confidence": response.get("confidence"),
                "response_quality": "logged"
            }
            
            # Create models directory if it doesn't exist
            models_dir = os.path.join(self.model_dir, "models")
            os.makedirs(models_dir, exist_ok=True)
            
            # Append to log file
            log_path = os.path.join(models_dir, log_file)
            
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_entry)
            
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving query log: {str(e)}")


# Global service instance
nlp_service = None

# Expose casual conversation methods
def is_casual_query(query: str) -> bool:
    """Check if a query is casual (non-legal)."""
    global nlp_service
    if nlp_service is None:
        nlp_service = initialize_service()
    return not nlp_service._is_legal_query(query)

def get_casual_response(query: str) -> Dict:
    """Get a response for casual queries."""
    global nlp_service
    if nlp_service is None:
        nlp_service = initialize_service()
    return nlp_service._get_casual_response(query)

def initialize_service(model_dir: str = None) -> LegalNLPService:
    """
    Initialize the global NLP service instance.
    
    Args:
        model_dir (str): Directory containing models
        
    Returns:
        LegalNLPService: Initialized service
    """
    global nlp_service
    if nlp_service is None:
        nlp_service = LegalNLPService(model_dir)
    return nlp_service

def get_legal_response(user_input: str) -> str:
    """
    Get legal response (backward compatibility function).
    
    Args:
        user_input (str): User query
        
    Returns:
        str: Legal response
    """
    global nlp_service
    if nlp_service is None:
        nlp_service = initialize_service()
    
    return nlp_service.get_legal_response(user_input)

def get_detailed_legal_response(user_input: str) -> Dict:
    """
    Get detailed legal response with full analysis.
    
    Args:
        user_input (str): User query
        
    Returns:
        Dict: Detailed response
    """
    global nlp_service
    if nlp_service is None:
        nlp_service = initialize_service()
    
    response = nlp_service.get_detailed_response(user_input)
    # Normalize to ensure expected keys exist for downstream printing/tests
    if not isinstance(response, dict):
        response = {
            'answer': str(response),
            'confidence': 0.0,
            'category': 'general',
            'legal_area': 'General Legal'
        }
    if 'legal_area' not in response:
        # Derive from category if possible
        response['legal_area'] = response.get('category', 'General Legal') or 'General Legal'
    if 'confidence' not in response:
        response['confidence'] = 0.0
    if 'category' not in response:
        response['category'] = 'general'
    return response
    

def predict_answer(user_input: str) -> str:
    """
    Predict answer for user input (main chatbot interface).
    
    Args:
        user_input (str): User query
        
    Returns:
        str: Predicted answer/response
    """
    global nlp_service
    
    # Initialize service if not already done
    if nlp_service is None:
        nlp_service = initialize_service()
    
    if nlp_service is None:
        return "Legal service is not properly initialized. Please try again later."
    
    # First check if this is a casual query
    if not nlp_service._is_legal_query(user_input):
        response = nlp_service._get_casual_response(user_input)
        return response.get('answer', "Hello! How can I assist you today?")
    
    try:
        # Process as legal query
        response = nlp_service.get_detailed_response(user_input)
        
        # If we have a valid response with good confidence, return it
        if response and 'answer' in response and response.get('confidence', 0) > 0.3:
            return response['answer']
        
        # Fallback to simple response
        simple_response = nlp_service.get_legal_response(user_input)
        if simple_response and simple_response != "I don't have information on that specific legal topic.":
            return simple_response
        
        # Final fallback
        return "I'm sorry, I couldn't find a specific answer to your legal question. Could you try rephrasing or providing more details?"
        
    except Exception as e:
        logger.error(f"Error in predict_answer: {str(e)}")
        return "I encountered an error while processing your request. Please try again later."


# Example usage and testing
if __name__ == "__main__":
    print("Initializing NyayaShield NLP Service...")
    
    # Initialize service
    service = initialize_service()
    
    # Test queries
    test_queries = [
        "I need help with a contract dispute over payment terms",
        "What are my rights if I'm arrested?",
        "How do I transfer property ownership to my children?",
        "My employer is not paying overtime wages",
        "I was injured in a car accident due to negligence"
    ]
    
    print("\n" + "="*60)
    print("TESTING NLP SERVICE")
    print("="*60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nTest Query {i}: {query}")
        print("-" * 50)
        
        # Get basic response
        basic_response = get_legal_response(query)
        print(f"Basic Response: {basic_response}")
        
        # Get detailed response
        detailed_response = get_detailed_legal_response(query)
        legal_area = detailed_response.get('legal_area') or detailed_response.get('category', 'General Legal')
        print(f"Legal Area: {legal_area}")
        print(f"Confidence: {detailed_response.get('confidence', 0.0)}")
        
        sections = detailed_response.get('relevant_sections') or []
        if sections:
            print("Top Relevant Section:")
            section = sections[0]
            print(f"  - {section.get('section','Section')}: {section.get('content','')[:100]}...")
        
        similar_cases = detailed_response.get('similar_cases') or []
        if similar_cases:
            print("Similar Cases:")
            for case in similar_cases:
                print(f"  - {case.get('case','Case')}: {case.get('holding','')[:80]}...")
        
        recs = detailed_response.get('recommendations') or []
        print(f"Recommendations: {recs[:2]}")
    
    print("\n" + "="*60)
    print("NLP Service testing completed successfully!")
    print("="*60)
