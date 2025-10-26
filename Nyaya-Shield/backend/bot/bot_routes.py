from flask import Blueprint, request, jsonify
from bot_controller import LegalBotController

bot_bp = Blueprint('bot_bp', __name__)

# Initialize the bot controller
bot_controller = LegalBotController()

@bot_bp.route("/chat", methods=["POST"])
def chat():
    """Main chat endpoint for legal queries"""
    try:
        data = request.get_json()
        user_input = data.get("message", "")

        if not user_input.strip():
            return jsonify({
                "response": "Please enter a valid legal query.",
                "confidence": "0.000",
                "category": "invalid",
                "source": "system"
            })

        # Get detailed response from bot controller
        result = bot_controller.get_detailed_response(user_input)
        
        return jsonify({
            "response": result['answer'],
            "confidence": f"{result['confidence']:.3f}",
            "category": result['category'],
            "source": result['source']
        })
        
    except Exception as e:
        return jsonify({
            "response": f"Sorry, I encountered an error: {str(e)}",
            "confidence": "0.000",
            "category": "error",
            "source": "system"
        })

@bot_bp.route("/chat/simple", methods=["POST"])
def simple_chat():
    """Simple chat endpoint (backward compatibility)"""
    try:
        data = request.get_json()
        user_input = data.get("message", "")

        if not user_input.strip():
            return jsonify({"response": "Please enter a valid legal query."})

        # Get simple response from bot controller
        response = bot_controller.get_bot_response(user_input)
        
        return jsonify({"response": response})
        
    except Exception as e:
        return jsonify({
            "response": f"Sorry, I encountered an error: {str(e)}"
        })

@bot_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    try:
        # Try to load the model to check if it's available
        model_data = bot_controller.load_model()
        return jsonify({
            "status": "healthy",
            "model_loaded": True,
            "qa_pairs_count": len(model_data['qa_pairs'])
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "model_loaded": False,
            "error": str(e)
        }), 500

@bot_bp.route("/model/info", methods=["GET"])
def model_info():
    """Get model information"""
    try:
        model_data = bot_controller.load_model()
        
        # Count categories and sources
        categories = {}
        sources = {}
        
        for qa_pair in model_data['qa_pairs']:
            category = qa_pair.get('category', 'unknown')
            source = qa_pair.get('source', 'unknown')
            
            categories[category] = categories.get(category, 0) + 1
            sources[source] = sources.get(source, 0) + 1
        
        return jsonify({
            "total_qa_pairs": len(model_data['qa_pairs']),
            "categories": categories,
            "sources": sources,
            "vector_dimensions": model_data['question_vectors'].shape
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500
