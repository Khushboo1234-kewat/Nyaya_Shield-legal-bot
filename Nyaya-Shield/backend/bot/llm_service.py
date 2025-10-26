"""
LLM Service for NyayaShield
==========================

This module provides integration with free LLM models for handling both legal
and casual conversations using Hugging Face's transformers.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
import torch
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
from sentence_transformers import SentenceTransformer, util
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMService:
    """
    Service for handling both legal and casual conversations using LLMs.
    Uses a zero-shot classification model to determine if a query is legal or casual,
    then routes to the appropriate response generator.
    """
    
    def __init__(self, device: str = None):
        """
        Initialize the LLM service.
        
        Args:
            device: Device to run the models on ('cuda' for GPU, 'cpu' for CPU)
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Initializing LLM service on device: {self.device}")
        
        # Initialize the zero-shot classifier for intent detection
        self.classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=0 if self.device == 'cuda' else -1
        )
        
        # Initialize the sentence transformer for semantic similarity
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2', device=self.device)
        
        # Legal categories for classification
        self.legal_labels = [
            'legal inquiry', 'law question', 'legal advice', 'legal information',
            'court case', 'lawyer', 'legal document', 'legal procedure',
            'criminal law', 'civil law', 'family law', 'property law',
            'constitutional law', 'corporate law', 'labor law', 'consumer law'
        ]
        
        # Casual conversation responses
        self.casual_responses = {
            'greeting': [
                "Hi there! I'm NyayaShield. How can I assist you today?",
                "Hello! I'm here to help. What can I do for you?",
                "Hey! How can I help you today?"
            ],
            'thanks': [
                "You're welcome! Let me know if you need anything else.",
                "Happy to help! Feel free to ask if you have more questions.",
                "My pleasure! Is there anything else you'd like to know?"
            ],
            'goodbye': [
                "Goodbye! Don't hesitate to return if you have more questions.",
                "Farewell! Remember, I'm here to help anytime.",
                "Goodbye! Take care!"
            ],
            'identity': [
                "I'm NyayaShield, your AI assistant. I can help answer questions or point you in the right direction.",
                "I'm your AI assistant, here to provide information and assistance. How can I help?",
                "I'm NyayaShield, designed to assist with your queries. What would you like to know?"
            ],
            'fallback': [
                "I'm not sure I understand. Could you rephrase that?",
                "I'm not sure how to respond to that. Could you ask in a different way?",
                "I might not have the answer to that. Would you like to ask something else?"
            ]
        }
    
    def is_legal_query(self, query: str, threshold: float = 0.5) -> bool:
        """
        Determine if a query is legal-related using zero-shot classification.
        
        Args:
            query: User's input text
            threshold: Confidence threshold for classification
            
        Returns:
            bool: True if the query is legal-related, False otherwise
        """
        try:
            # Get classification results
            result = self.classifier(
                query,
                candidate_labels=self.legal_labels,
                multi_label=True
            )
            
            # Get the maximum score for any legal label
            max_score = max(result['scores'])
            
            # If any legal label has a score above threshold, it's a legal query
            return max_score >= threshold
            
        except Exception as e:
            logger.error(f"Error in legal query classification: {e}")
            # Default to True to be safe (treat as legal query)
            return True
    
    def get_casual_response(self, query: str) -> str:
        """
        Generate a response for casual conversations.
        
        Args:
            query: User's input text
            
        Returns:
            str: Generated response
        """
        # Convert query to lowercase for matching
        query_lower = query.lower()
        
        # Check for greeting patterns
        if any(word in query_lower for word in ['hi', 'hello', 'hey', 'greetings']):
            return self._get_random_response('greeting')
            
        # Check for thanks/thank you
        if any(phrase in query_lower for phrase in ['thank', 'thanks', 'appreciate']):
            return self._get_random_response('thanks')
            
        # Check for goodbye
        if any(word in query_lower for word in ['bye', 'goodbye', 'see you', 'farewell']):
            return self._get_random_response('goodbye')
            
        # Check for identity questions
        if any(phrase in query_lower for phrase in ['who are you', 'what are you', 'your name']):
            return self._get_random_response('identity')
            
        # Fallback response
        return self._get_random_response('fallback')
    
    def _get_random_response(self, response_type: str) -> str:
        """Get a random response of the specified type."""
        responses = self.casual_responses.get(response_type, self.casual_responses['fallback'])
        return np.random.choice(responses)
    
    def get_response(self, query: str, legal_response: str = None) -> str:
        """
        Get an appropriate response for the query, using legal response if provided.
        
        Args:
            query: User's input text
            legal_response: Pre-generated legal response (if any)
            
        Returns:
            str: Generated response
        """
        # First, check if this is a legal query
        if self.is_legal_query(query):
            # If we have a legal response, use it
            if legal_response:
                return legal_response
            # Otherwise, indicate we don't have a legal response
            return "I'm not sure about the legal details of that question. Could you provide more context?"
        
        # For non-legal queries, use casual response
        return self.get_casual_response(query)


# Global instance
llm_service = LLMService()

# Utility functions for easy import
def is_legal_query(query: str) -> bool:
    """Check if a query is legal-related."""
    return llm_service.is_legal_query(query)

def get_casual_response(query: str) -> str:
    """Get a casual response for non-legal queries."""
    return llm_service.get_casual_response(query)

def get_response(query: str, legal_response: str = None) -> str:
    """Get an appropriate response for the query."""
    return llm_service.get_response(query, legal_response)

def initialize_llm_service(device: str = None) -> LLMService:
    """Initialize and return the LLM service."""
    global llm_service
    llm_service = LLMService(device=device)
    return llm_service
