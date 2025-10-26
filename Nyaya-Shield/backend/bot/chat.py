#!/usr/bin/env python3
"""
NyayaShield Terminal Chat Interface
==================================

Interactive command-line interface for the legal bot.
Allows users to ask legal queries directly in the terminal.
"""

import os
import sys
import signal
import joblib
import pandas as pd
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Add current directory to path for imports (optional in package context)
sys.path.append(os.path.dirname(__file__))

try:
    if __package__:
        from .nlp_service import get_detailed_legal_response, initialize_service
        from .bot_controller import LegalBotController
        from .preprocess import preprocess_legal_text
        from .train_model import load_combined_dataset, prepare_training_data, train_model, get_legal_answer
    else:
        raise ImportError
    NLP_AVAILABLE = True
except Exception:
    # Fallback: adjust sys.path and import using absolute package path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from bot.nlp_service import get_detailed_legal_response, initialize_service
    from bot.bot_controller import LegalBotController
    from bot.preprocess import preprocess_legal_text
    from bot.train_model import load_combined_dataset, prepare_training_data, train_model, get_legal_answer
    NLP_AVAILABLE = True

class TerminalChat:
    def __init__(self):
        self.bot_controller = None
        self.nlp_service = None
        self.model_data = None
        self.dataset_loaded = False
        self.session_start = datetime.now()
        self.query_count = 0
        self.model_path = os.path.join(os.path.dirname(__file__), "chatbot_model.pkl")
        
    def initialize_services(self):
        """Initialize bot services with complete pipeline"""
        if not NLP_AVAILABLE:
            print("❌ Bot modules not available. Please check your setup.")
            return False
            
        try:
            print("🔄 Initializing NyayaShield Legal Bot Pipeline...")
            print("📊 Loading and processing legal dataset...")
            
            # Check if trained model exists
            if not os.path.exists(self.model_path):
                print("🤖 No trained model found. Training new model from dataset...")
                success = self.train_fresh_model()
                if not success:
                    return False
            
            # Load the trained model
            print("📂 Loading trained model...")
            self.model_data = joblib.load(self.model_path)
            print(f"✅ Model loaded with {len(self.model_data['qa_pairs']):,} Q&A pairs")
            print(f"📈 Vector dimensions: {self.model_data['question_vectors'].shape}")
            
            # Initialize additional services
            try:
                self.nlp_service = initialize_service()
                print("✅ Advanced NLP Service initialized")
            except:
                print("⚠️ Advanced NLP Service unavailable, using core model")
            
            try:
                self.bot_controller = LegalBotController()
                print("✅ Bot Controller initialized")
            except:
                print("⚠️ Bot Controller unavailable, using direct model access")
            
            self.dataset_loaded = True
            return True
            
        except Exception as e:
            print(f"❌ Error initializing services: {e}")
            return False
    
    def train_fresh_model(self):
        """Train a fresh model from the dataset"""
        try:
            print("🔄 Training model from combined legal dataset...")
            success = train_model()
            if success:
                print("✅ Model training completed successfully!")
                return True
            else:
                print("❌ Model training failed")
                return False
        except Exception as e:
            print(f"❌ Training error: {e}")
            return False
    
    def print_welcome(self):
        """Print welcome message"""
        print("\n" + "="*60)
        print("🏛️  NYAYA SHIELD - LEGAL BOT TERMINAL INTERFACE")
        print("="*60)
        print("Welcome to your personal legal assistant!")
        print("Ask any legal question and get instant answers.")
        print("\nCommands:")
        print("  • Type your legal query and press Enter")
        print("  • 'help' - Show available commands")
        print("  • 'stats' - Show session statistics")
        print("  • 'clear' - Clear the screen")
        print("  • 'quit' or 'exit' - Exit the chat")
        print("="*60)
    
    def print_help(self):
        """Print help information"""
        print("\n📚 HELP - Legal Query Examples:")
        print("-" * 40)
        print("Criminal Law:")
        print("  • What is the punishment for theft?")
        print("  • How to file an FIR?")
        print("  • What are bail conditions?")
        print("\nFamily Law:")
        print("  • How to file for divorce?")
        print("  • What are child custody rights?")
        print("  • How to get maintenance?")
        print("\nConsumer Rights:")
        print("  • How to file consumer complaint?")
        print("  • What are defective product rights?")
        print("  • How to get refund?")
        print("\nProperty Law:")
        print("  • How to register property?")
        print("  • What are tenant rights?")
        print("  • How to resolve property disputes?")
        print("-" * 40)
    
    def print_stats(self):
        """Print session statistics"""
        session_duration = datetime.now() - self.session_start
        print(f"\n📊 SESSION STATISTICS:")
        print(f"  • Session started: {self.session_start.strftime('%H:%M:%S')}")
        print(f"  • Duration: {str(session_duration).split('.')[0]}")
        print(f"  • Queries asked: {self.query_count}")
        print(f"  • Average queries per minute: {self.query_count / max(session_duration.total_seconds() / 60, 1):.1f}")
    
    def get_response(self, query):
        """Get response using complete bot pipeline with trained model"""
        try:
            print("🔍 Processing query through legal dataset...")
            
            # Primary: Use trained model with full dataset
            if self.model_data:
                answer, similarity_score, category = get_legal_answer(query, self.model_data, top_k=3)
                
                # Get additional context from similar cases
                similar_cases = self.get_similar_cases(query, top_k=3)
                recommendations = self.generate_recommendations(category, similarity_score)
                legal_terms = self.extract_legal_terms(answer)
                
                return {
                    'answer': answer,
                    'confidence': similarity_score,
                    'category': category,
                    'source': 'trained_model',
                    'similar_cases': similar_cases,
                    'recommendations': recommendations,
                    'legal_terms': legal_terms,
                    'dataset_size': len(self.model_data['qa_pairs'])
                }
            
            # Secondary: Try advanced NLP service
            elif self.nlp_service and get_detailed_legal_response:
                print("🔄 Using advanced NLP service...")
                response_data = get_detailed_legal_response(query)
                return {
                    'answer': response_data.get('answer', 'No response generated'),
                    'confidence': response_data.get('confidence', 0.0),
                    'category': response_data.get('legal_area', 'unknown'),
                    'source': 'nlp_service',
                    'recommendations': response_data.get('recommendations', []),
                    'legal_terms': response_data.get('legal_terms', [])
                }
            
            # Tertiary: Fallback to bot controller
            elif self.bot_controller:
                print("🔄 Using bot controller...")
                response_data = self.bot_controller.get_detailed_response(query)
                return response_data
            
            else:
                return {
                    'answer': 'Bot services are not available. Please ensure the model is trained.',
                    'confidence': 0.0,
                    'category': 'error',
                    'source': 'system'
                }
                
        except Exception as e:
            return {
                'answer': f'Sorry, I encountered an error: {str(e)}',
                'confidence': 0.0,
                'category': 'error',
                'source': 'system'
            }
    
    def get_similar_cases(self, query, top_k=3):
        """Get similar legal cases from the dataset"""
        try:
            if not self.model_data:
                return []
            
            vectorizer = self.model_data['vectorizer']
            qa_pairs = self.model_data['qa_pairs']
            question_vectors = self.model_data['question_vectors']
            
            processed_query = preprocess_legal_text(query)
            query_vector = vectorizer.transform([processed_query])
            
            similarities = cosine_similarity(query_vector, question_vectors)[0]
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            similar_cases = []
            for idx in top_indices:
                if similarities[idx] > 0.3:  # Only include reasonably similar cases
                    similar_cases.append({
                        'question': qa_pairs[idx]['question'][:100] + '...',
                        'category': qa_pairs[idx]['category'],
                        'similarity': similarities[idx],
                        'source': qa_pairs[idx]['source']
                    })
            
            return similar_cases
        except:
            return []
    
    def generate_recommendations(self, category, confidence):
        """Generate contextual recommendations"""
        recommendations = []
        
        if confidence < 0.5:
            recommendations.append("Consider rephrasing your question for better results")
            recommendations.append("Consult with a legal professional for specific advice")
        
        category_recommendations = {
            'criminal': [
                "File FIR at nearest police station if crime occurred",
                "Gather evidence and witness statements",
                "Contact a criminal lawyer immediately"
            ],
            'family': [
                "Maintain all relevant documents (marriage certificate, etc.)",
                "Consider mediation before court proceedings",
                "Consult family court procedures"
            ],
            'consumer': [
                "Keep all purchase receipts and communications",
                "File complaint with consumer forum within 2 years",
                "Try resolving with company first"
            ],
            'property': [
                "Verify property documents thoroughly",
                "Check for any pending litigation",
                "Ensure proper registration and stamp duty payment"
            ]
        }
        
        if category.lower() in category_recommendations:
            recommendations.extend(category_recommendations[category.lower()][:2])
        
        return recommendations[:3]
    
    def extract_legal_terms(self, answer):
        """Extract legal terms from the answer"""
        legal_keywords = [
            'IPC', 'CrPC', 'Constitution', 'Article', 'Section', 'Act', 'Court', 'Judge',
            'Bail', 'FIR', 'Warrant', 'Appeal', 'Petition', 'Writ', 'Injunction',
            'Divorce', 'Custody', 'Maintenance', 'Alimony', 'Marriage', 'Adoption',
            'Contract', 'Agreement', 'Breach', 'Damages', 'Compensation', 'Liability',
            'Property', 'Registration', 'Stamp Duty', 'Mutation', 'Title', 'Deed'
        ]
        
        found_terms = []
        answer_upper = answer.upper()
        
        for term in legal_keywords:
            if term.upper() in answer_upper:
                found_terms.append(term)
        
        return found_terms[:5]
    
    def format_response(self, response_data):
        """Format the bot response for terminal display"""
        answer = response_data.get('answer', 'No response')
        confidence = response_data.get('confidence', 0.0)
        category = response_data.get('category', 'unknown')
        source = response_data.get('source', 'unknown')
        
        # Format confidence as percentage
        confidence_pct = confidence * 100
        
        # Choose confidence emoji
        if confidence_pct >= 80:
            conf_emoji = "🎯"
        elif confidence_pct >= 60:
            conf_emoji = "✅"
        elif confidence_pct >= 40:
            conf_emoji = "⚠️"
        else:
            conf_emoji = "❓"
        
        # Category emoji
        category_emojis = {
            'criminal': '⚖️',
            'family': '👨‍👩‍👧‍👦',
            'consumer': '🛒',
            'property': '🏠',
            'constitutional': '📜',
            'labour': '👷',
            'civil': '🏛️',
            'unknown': '❓',
            'error': '❌'
        }
        cat_emoji = category_emojis.get(category.lower(), '📚')
        
        print(f"\n{cat_emoji} LEGAL RESPONSE ({category.upper()}):")
        print("-" * 50)
        print(f"{answer}")
        print("-" * 50)
        print(f"{conf_emoji} Confidence: {confidence_pct:.1f}% | Source: {source}")
        
        # Show dataset info if available
        dataset_size = response_data.get('dataset_size')
        if dataset_size:
            print(f"📊 Trained on {dataset_size:,} legal Q&A pairs")
        
        # Show similar cases if available
        similar_cases = response_data.get('similar_cases', [])
        if similar_cases:
            print(f"\n🔍 SIMILAR CASES:")
            for i, case in enumerate(similar_cases[:2], 1):
                print(f"  {i}. {case['question']} (Similarity: {case['similarity']:.2f})")
        
        # Show recommendations if available
        recommendations = response_data.get('recommendations', [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"  {i}. {rec}")
        
        # Show legal terms if available
        legal_terms = response_data.get('legal_terms', [])
        if legal_terms:
            print(f"\n📖 LEGAL TERMS:")
            for term in legal_terms[:5]:
                print(f"  • {term}")
    
    def run(self):
        """Main chat loop"""
        # Handle Ctrl+C gracefully
        def signal_handler(sig, frame):
            print("\n\n👋 Thank you for using NyayaShield Legal Bot!")
            print("Stay informed, stay protected! 🛡️")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Initialize services
        if not self.initialize_services():
            print("❌ Failed to initialize bot services. Exiting...")
            return
        
        # Print welcome message
        self.print_welcome()
        
        # Show dataset info
        if self.model_data:
            print(f"\n📊 DATASET INFO:")
            print(f"  • Total Q&A pairs: {len(self.model_data['qa_pairs']):,}")
            print(f"  • Vector dimensions: {self.model_data['question_vectors'].shape}")
            
            # Show category distribution
            categories = {}
            for qa in self.model_data['qa_pairs']:
                cat = qa.get('category', 'unknown')
                categories[cat] = categories.get(cat, 0) + 1
            
            print(f"  • Categories: {', '.join([f'{k}({v})' for k, v in sorted(categories.items())[:5]])}")
        
        # Main chat loop
        while True:
            try:
                # Get user input
                user_input = input("\n🤔 Your legal query: ").strip()
                
                # Handle empty input
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\n👋 Thank you for using NyayaShield Legal Bot!")
                    print("Stay informed, stay protected! 🛡️")
                    break
                
                elif user_input.lower() == 'help':
                    self.print_help()
                    continue
                
                elif user_input.lower() == 'stats':
                    self.print_stats()
                    continue
                
                elif user_input.lower() == 'clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    self.print_welcome()
                    continue
                
                # Process legal query
                print("🔍 Processing your query...")
                self.query_count += 1
                
                response_data = self.get_response(user_input)
                self.format_response(response_data)
                
            except KeyboardInterrupt:
                print("\n\n👋 Thank you for using NyayaShield Legal Bot!")
                print("Stay informed, stay protected! 🛡️")
                break
            except EOFError:
                print("\n\n👋 Thank you for using NyayaShield Legal Bot!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                print("Please try again or type 'quit' to exit.")

def main():
    """Main function"""
    chat = TerminalChat()
    chat.run()

if __name__ == "__main__":
    main()
