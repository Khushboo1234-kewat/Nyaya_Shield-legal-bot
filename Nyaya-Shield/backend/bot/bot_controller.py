import os
import sys
import joblib
import logging
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Support running both as a module (python -m bot.bot_controller) and as a script (python bot/bot_controller.py)
try:
    if __package__:
        from .preprocess import preprocess_legal_text
    else:
        raise ImportError
except Exception:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from bot.preprocess import preprocess_legal_text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LegalBotController:
    def __init__(self):
        self.model_data = None
        self.model_path = os.path.join(os.path.dirname(__file__), "chatbot_model.pkl")
    
    def load_model(self):
        """Load the trained legal Q&A model"""
        if self.model_data is not None:
            return self.model_data
            
        model_paths = [
            self.model_path,  # Default path
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'chatbot_model.pkl'),  # Backend root
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'chatbot_model.pkl')  # Project root
        ]
        
        for path in model_paths:
            if os.path.exists(path):
                try:
                    logger.info(f"Attempting to load model from: {path}")
                    self.model_data = joblib.load(path)
                    logger.info(f"Successfully loaded legal model with {len(self.model_data.get('qa_pairs', []))} Q&A pairs")
                    return self.model_data
                except Exception as e:
                    logger.error(f"Failed to load model from {path}: {e}")
                    continue
        
        logger.error("No valid model file found. Please ensure the model is trained and placed in the correct location.")
        logger.info("Expected model files should contain a dictionary with 'qa_pairs' and 'vectorizer' keys.")
        return None
    
    def get_legal_answer(self, query, top_k=3):
        """Get the best legal answer for user query using similarity matching"""
        try:
            if not self.load_model():
                return {
                    'answer': "I'm sorry, but I'm having trouble accessing the legal knowledge base. "
                            "Please try again later or contact support if the issue persists.",
                    'confidence': 0.0,
                    'category': 'error'
                }
            
            if not hasattr(self, 'model_data') or not self.model_data:
                raise ValueError("Model data not loaded. Please ensure the model is properly trained and loaded.")
                
            vectorizer = self.model_data.get('vectorizer')
            qa_pairs = self.model_data.get('qa_pairs', [])
            question_vectors = self.model_data.get('question_vectors')
            
            if not all([vectorizer, qa_pairs, question_vectors is not None]):
                raise ValueError("Incomplete model data. Missing required components (vectorizer, qa_pairs, or question_vectors).")
            
            # Process user query
            try:
                processed_query = preprocess_legal_text(query)
            except:
                processed_query = query.lower().strip()
            
            query_vector = vectorizer.transform([processed_query])
            
            # Calculate similarity with all questions
            similarities = cosine_similarity(query_vector, question_vectors)[0]
            
            # Get top similar questions
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            best_match = qa_pairs[top_indices[0]]
            similarity_score = similarities[top_indices[0]]
            
            # If similarity is too low, provide a generic response
            if similarity_score < 0.1:
                return {
                    'answer': "I'm sorry, I don't have specific information about that legal query. Please consult with a legal professional for detailed advice.",
                    'confidence': similarity_score,
                    'category': 'unknown',
                    'source': 'fallback'
                }
            
            return {
                'answer': best_match['answer'],
                'confidence': similarity_score,
                'category': best_match['category'],
                'source': best_match['source']
            }
            
        except FileNotFoundError:
            return {
                'answer': "Legal model not found. Please train the model first by running train_model.py",
                'confidence': 0.0,
                'category': 'error',
                'source': 'system'
            }
        except Exception as e:
            return {
                'answer': f"Sorry, I encountered an error: {str(e)}",
                'confidence': 0.0,
                'category': 'error',
                'source': 'system'
            }
    
    def get_bot_response(self, user_message):
        """Main function to get bot response (backward compatibility)"""
        if not user_message or not user_message.strip():
            return "Please enter a valid legal query."
        
        result = self.get_legal_answer(user_message)
        return result['answer']
    
    def get_detailed_response(self, user_message):
        """Get detailed response with confidence and metadata"""
        if not user_message or not user_message.strip():
            return {
                'answer': "Please enter a valid legal query.",
                'confidence': 0.0,
                'category': 'invalid',
                'source': 'system'
            }
        
        return self.get_legal_answer(user_message)

# Global instance for backward compatibility
bot_controller = LegalBotController()

# Backward compatibility functions
def load_model():
    return bot_controller.load_model()

def get_bot_response(user_message):
    return bot_controller.get_bot_response(user_message)

def get_legal_answer(query, top_k=3):
    return bot_controller.get_legal_answer(query, top_k)

# Test functionality when run directly
if __name__ == "__main__":
    print("🧪 Testing Legal Bot Controller...")
    
    try:
        # Test model loading
        controller = LegalBotController()
        model_data = controller.load_model()
        print(f"✅ Model loaded successfully!")
        print(f"📊 Q&A pairs: {len(model_data['qa_pairs'])}")
        
        # Test queries
        test_queries = [
            "What is the punishment for murder?",
            "How to file a divorce case?",
            "What are consumer rights?"
        ]
        
        print("\n🔍 Testing legal queries:")
        for query in test_queries:
            result = controller.get_detailed_response(query)
            print(f"\n❓ Query: {query}")
            print(f"📝 Answer: {result['answer'][:100]}...")
            print(f"🎯 Confidence: {result['confidence']:.3f}")
            print(f"🏷️ Category: {result['category']}")
            print(f"📚 Source: {result['source']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure to train the model first: python train_model.py")
