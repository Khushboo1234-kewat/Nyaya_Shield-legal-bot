"""NyayaShield Legal Bot - Flask Application
==========================================

Main Flask application for NyayaShield legal assistance chatbot.
Integrates all backend components with comprehensive API endpoints.
"""

import os
import logging
import random
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

import sys

# Add the parent directory to Python path to allow absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import bot components with better error handling
bot_imports = {
    'nlp_service': ['predict_answer', 'get_detailed_legal_response', 'initialize_service', 'is_casual_query', 'get_casual_response'],
    'bot_controller': ['LegalBotController'],
    'preprocess': ['preprocess_legal_text', 'extract_legal_entities'],
    'train_model': ['get_legal_answer', 'load_combined_dataset'],
    'llm_service': ['get_response', 'initialize_llm_service'],
    'multi_dataset_search': ['search_legal_answer', 'get_search_engine'],
    'enhanced_response_handler': ['format_enhanced_response', 'get_enhanced_handler'],
    'response_formatter': ['format_user_friendly_response']
}

# Initialize all imported names to None
for module in bot_imports.values():
    for name in module:
        globals()[name] = None

# Initialize service variables
nlp_service = None
bot_controller = None

# Try to import all bot components
try:
    import joblib
    for module_name, names in bot_imports.items():
        try:
            module = __import__(f'bot.{module_name}', fromlist=names)
            for name in names:
                if hasattr(module, name):
                    globals()[name] = getattr(module, name)
        except ImportError as e:
            print(f"Warning: Could not import {module_name}: {e}")
    
    # Check if all required components were imported
    missing_imports = [name for name in globals().keys() 
                      if name in [n for names in bot_imports.values() for n in names] 
                      and globals()[name] is None]
    
    if missing_imports:
        print(f"Warning: Missing imports: {', '.join(missing_imports)}")
        print("Some features may not work properly.")
    else:
        print("All bot components imported successfully!")
        
except Exception as e:
    print(f"Error during imports: {e}")
    print("Some features may not work properly.")

# Ensure critical bot components are available via direct imports as a fallback
try:
    if (initialize_service is None) or (LegalBotController is None) or (get_legal_answer is None):
        try:
            from bot.nlp_service import initialize_service as _init_service_fallback, is_casual_query as _is_casual_fallback, get_casual_response as _get_casual_fallback, get_detailed_legal_response as _get_detailed_fallback
            from bot.bot_controller import LegalBotController as _LBC_fallback
            from bot.train_model import get_legal_answer as _get_legal_answer_fallback, load_combined_dataset as _lcd_fallback
            initialize_service = _init_service_fallback
            is_casual_query = _is_casual_fallback
            get_casual_response = _get_casual_fallback
            get_detailed_legal_response = _get_detailed_fallback
            LegalBotController = _LBC_fallback
            get_legal_answer = _get_legal_answer_fallback
            load_combined_dataset = _lcd_fallback
        except Exception as _fe:
            logger.error(f"Import fallback failed: {_fe}")
except Exception:
    pass

# Provide a safe fallback for get_response if LLM service is unavailable
if 'get_response' not in globals() or get_response is None:
    def get_response(query: str, legal_response: str = None) -> str:
        return legal_response or "I'm here to help with legal queries. Please provide more details."

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure critical bot components are present after logging is set up
try:
    if ('initialize_service' not in globals()) or (initialize_service is None) or (LegalBotController is None) or ('get_legal_answer' not in globals()) or (get_legal_answer is None):
        try:
            from bot.nlp_service import initialize_service as _init_service_fallback, is_casual_query as _is_casual_fallback, get_casual_response as _get_casual_fallback, get_detailed_legal_response as _get_detailed_fallback
            from bot.bot_controller import LegalBotController as _LBC_fallback
            from bot.train_model import get_legal_answer as _get_legal_answer_fallback, load_combined_dataset as _lcd_fallback
            initialize_service = _init_service_fallback
            is_casual_query = _is_casual_fallback
            get_casual_response = _get_casual_fallback
            get_detailed_legal_response = _get_detailed_fallback
            LegalBotController = _LBC_fallback
            get_legal_answer = _get_legal_answer_fallback
            load_combined_dataset = _lcd_fallback
            logger.info("Applied fallback imports for bot components")
        except Exception as _fe:
            logger.warning(f"Fallback import attempt failed: {_fe}")
except Exception as _e:
    logger.warning(f"Post-logging import guard encountered an error: {_e}")

# Initialize Flask app
app = Flask(
    __name__,
    static_folder='../frontend/static',
    template_folder='../frontend/templates'
)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nyayashield-dev-key-2024')
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
DATASET_THRESHOLD = 0.3
try:
    DATASET_THRESHOLD = float(os.environ.get('DATASET_THRESHOLD', '0.3'))
except Exception:
    DATASET_THRESHOLD = 0.3

# Enable CORS for all routes
CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])

# Initialize services and load models
try:
    # Initialize LLM service first (optional; controlled by ENABLE_LLM env var)
    enable_llm = os.environ.get('ENABLE_LLM', 'true').lower() == 'true'
    llm_service = None
    if enable_llm:
        logger.info("Initializing LLM service...")
        if 'initialize_llm_service' in globals() and initialize_llm_service:
            llm_service = initialize_llm_service()
            logger.info("✓ LLM Service initialized successfully")
        else:
            logger.warning("✗ LLM Service not available (optional)")
    else:
        logger.info("LLM service disabled (set ENABLE_LLM=false to disable)")
    
    # Initialize NLP service
    if initialize_service and LegalBotController:
        nlp_service = initialize_service()
        bot_controller = LegalBotController()
        logger.info("✓ NLP Service and Bot Controller initialized successfully")
    else:
        raise ImportError("Bot modules not available")
    
    # Load trained model for enhanced responses (global)
    model_path = os.path.join(os.path.dirname(__file__), 'bot', 'chatbot_model.pkl')
    if os.path.exists(model_path) and joblib:
        trained_model = joblib.load(model_path)
        logger.info(f"✓ Trained model loaded with {len(trained_model.get('qa_pairs', []))} Q&A pairs")
    else:
        trained_model = None
        logger.warning("✗ Trained model not found or joblib not available")

    # Optionally load per-category models if present
    trained_models_by_category = {}
    try:
        bot_dir = os.path.join(os.path.dirname(__file__), 'bot')
        for cat in ['ipc','consumer','crpc','family','property','it_act']:
            p = os.path.join(bot_dir, f"chatbot_model_{cat}.pkl")
            if os.path.exists(p):
                trained_models_by_category[cat] = joblib.load(p)
                logger.info(f"✓ Loaded category model: {cat} ({len(trained_models_by_category[cat].get('qa_pairs', []))} Q&A)")
    except Exception as e:
        logger.warning(f"Could not load category models: {e}")

    try:
        auto_train = os.environ.get('AUTO_TRAIN', 'true').lower() == 'true'
        if auto_train and not trained_models_by_category:
            try:
                from map_categories import main as map_main
                map_main()
                logger.info("✓ Dataset categorized successfully")
            except Exception as e:
                logger.warning(f"Category mapping skipped: {e}")
            try:
                from bot.train_model import train_models_by_category as train_by_cat
                res = train_by_cat()
                if res:
                    for cat in ['ipc','consumer','crpc','family','property','it_act']:
                        p = os.path.join(bot_dir, f"chatbot_model_{cat}.pkl")
                        if os.path.exists(p):
                            trained_models_by_category[cat] = joblib.load(p)
                    logger.info("✓ Auto-trained per-category models")
            except Exception as e:
                logger.warning(f"Auto-training failed: {e}")
    except Exception as e:
        logger.warning(f"Auto-train wrapper error: {e}")
    
    # Initialize multi-dataset search engine
    try:
        if search_legal_answer and get_search_engine:
            multi_search_engine = get_search_engine()
            logger.info("✓ Multi-dataset search engine initialized")
        else:
            multi_search_engine = None
            logger.warning("✗ Multi-dataset search not available, using fallback")
    except Exception as e:
        multi_search_engine = None
        logger.warning(f"Multi-dataset search initialization failed: {e}")
        
except Exception as e:
    logger.error(f"✗ Error initializing bot services: {e}")
    nlp_service = None
    bot_controller = None
    trained_model = None

def format_legal_response(user_input, answer, category, confidence, recommendations=None, legal_terms=None):
    """Format legal response to be more solution-oriented and practical."""
    response_parts = []
    
    # Ensure we have valid inputs
    if not answer:
        answer = "I'll help you understand this legal matter."
    if not category:
        category = 'general'
    if not recommendations:
        recommendations = []
    if not legal_terms:
        legal_terms = []
    
    # Start with a clear, direct response
    response_parts.append("🔍 **Understanding Your Situation**")
    response_parts.append("I'll help break this down in a practical way:")
    
    # Break down the legal information
    response_parts.append("\n📋 **Key Points**:")
    response_parts.append(f"• {answer}")
    
    # Add practical guidance
    response_parts.append("\n🚀 **Your Action Plan**:")
    
    # Check for road-related queries
    road_keywords = ['road', 'pothole', 'accident', 'highway', 'street', 'pavement']
    is_road_issue = any(keyword in user_input.lower() for keyword in road_keywords)
    
    category_lower = str(category or 'general').strip().lower()

    if is_road_issue:
        response_parts.extend([
            "1. **Immediate Actions**:",
            "   • Ensure your safety and move to a secure location",
            "   • Take clear photos/videos of the road condition and any damages",
            "   • Note the exact location (use GPS if possible) and time",
            "",
            "2. **Legal Rights & Protections**:",
            "   • Under the Indian Motor Vehicles Act, you can claim compensation for road accident injuries",
            "   • The Public Liability Insurance Act covers damages due to poor road conditions",
            "   • Right to file an RTI to know about road maintenance schedules and contracts",
            "",
            "3. **Next Steps**:",
            "   • File a police complaint (FIR) if there's been an accident or injury",
            "   • Report to local municipal corporation/RTO with evidence",
            "   • For compensation claims, gather:",
            "     - Medical reports (if injured)",
            "     - Repair estimates (for vehicle/property damage)",
            "     - Witness statements (if available)",
            "   • Contact a lawyer if you need to file for compensation"
        ])
    # IPC specific
    elif category_lower == 'ipc':
        response_parts.extend([
            "1. **Immediate Actions**:",
            "   • Preserve evidence (documents, CCTV, messages) relevant to the offense",
            "   • Note sections mentioned by police/notice, if any",
            "",
            "2. **Legal Process**:",
            "   • File/verify FIR, collect copy and FIR number",
            "   • Track investigation and chargesheet timeline",
            "",
            "3. **Next Steps**:",
            "   • Consult a criminal lawyer regarding defenses and bail",
            "   • Prepare witness list and supporting material"
        ])
    # Consumer specific
    elif category_lower == 'consumer':
        response_parts.extend([
            "1. **Immediate Actions**:",
            "   • Gather invoices, warranty cards, service emails, and chat logs",
            "   • Send a written complaint to the seller/service provider",
            "",
            "2. **Escalation**:",
            "   • If unresolved, file on the National Consumer Helpline/portal",
            "   • Compute claim value (refund/replacement/compensation)",
            "",
            "3. **Forum Filing**:",
            "   • Choose District/State/National Commission based on claim amount",
            "   • Attach evidence and affidavits while filing"
        ])
    # CrPC specific
    elif category_lower == 'crpc':
        response_parts.extend([
            "1. **Immediate Actions**:",
            "   • Ask for grounds of arrest and applicable sections",
            "   • Inform a family member/lawyer; request arrest memo",
            "",
            "2. **Process Milestones**:",
            "   • Production before magistrate ~24 hours",
            "   • Apply for bail/anticipatory bail as applicable",
            "",
            "3. **Preparation**:",
            "   • Maintain chronology of events and documents",
            "   • Follow summons and court dates strictly"
        ])
    # Family specific
    elif category_lower == 'family':
        response_parts.extend([
            "1. **Immediate Actions**:",
            "   • Collect marriage proofs, income proofs, and prior notices",
            "   • Consider counseling/mediation first",
            "",
            "2. **Case Options**:",
            "   • Mutual consent divorce vs. contested divorce",
            "   • Interim maintenance/custody applications",
            "",
            "3. **Documentation**:",
            "   • Prepare petition with grounds and reliefs",
            "   • Proof of residence/jurisdiction"
        ])
    # Property specific
    elif category_lower == 'property':
        response_parts.extend([
            "1. **Immediate Actions**:",
            "   • Collect title documents, sale deed, mutation, tax receipts",
            "   • Obtain encumbrance certificate and pending litigation search",
            "",
            "2. **Due Diligence**:",
            "   • Verify chain of title and measurements",
            "   • Check zoning and registration requirements",
            "",
            "3. **Dispute Handling**:",
            "   • Issue legal notice; explore mediation",
            "   • File civil suit/injunction if needed"
        ])
    # IT Act / Cyber specific
    elif category_lower in ('it_act', 'cyber'):
        response_parts.extend([
            "1. **Immediate Actions**:",
            "   • Preserve digital evidence (screenshots, headers, logs)",
            "   • Change passwords/enable 2FA; notify bank if relevant",
            "",
            "2. **Reporting**:",
            "   • Report at cybercrime portal and local police",
            "   • Note relevant IT Act sections and IPC add-ons",
            "",
            "3. **Follow-up**:",
            "   • Track FIR and investigation updates",
            "   • Coordinate with platform/ISP for data preservation"
        ])
    # Handle other general legal queries
    elif category == 'general' or (legal_terms and 'general' in str(legal_terms).lower()):
        response_parts.extend([
            "1. **Immediate Actions**:",
            "   • Ensure your safety first - move to a safe location if needed",
            "   • Document the situation with photos/videos if possible",
            "   • Note down important details (time, location, people involved)",
            "",
            "2. **Legal Protection**:",
            "   • You have the right to file a police complaint (FIR)",
            "   • Keep records of all relevant documents and communications",
            "   • Know that you have the right to legal representation",
            "",
            "3. **Next Steps**:",
            "   • Report the issue to the appropriate authorities",
            "   • Gather all relevant evidence and documentation",
            "   • Consider consulting a lawyer for specific legal advice"
        ])
    # Provide specific, actionable steps for IPC-related cases
    elif legal_terms and 'IPC' in str(legal_terms):
        response_parts.extend([
            "1. **Immediate Actions**:",
            "   • Preserve all documents, emails, and communications related to the case",
            "   • Make a timeline of events with dates and details",
            "   • Identify and gather potential witnesses if applicable",
            "",
            "2. **Understanding the Legal Process**:",
            "   • The case will typically go through these stages:",
            "     1. FIR/Complaint",
            "     2. Investigation",
            "     3. Chargesheet filing",
            "     4. Trial proceedings",
            "     5. Judgment",
            "",
            "3. **Your Rights**:",
            "   • Right to legal representation",
            "   • Right to remain silent",
            "   • Right to bail (in bailable offenses)",
            "   • Right to a fair trial"
        ])
    
    # Add detailed legal explanations
    if legal_terms:
        response_parts.append("\n📖 **Legal Breakdown**:")
        legal_glossary = {
            'IPC': "Indian Penal Code - The primary criminal code of India",
            'Section 420': "Cheating and dishonestly inducing delivery of property (Punishable with imprisonment up to 7 years)",
            'Section 467': "Forgery of valuable security, will, etc. (Punishable with imprisonment for life or up to 10 years)",
            'Section 468': "Forgery for purpose of cheating (Punishable with imprisonment up to 7 years and fine)",
            'Section 471': "Using as genuine a forged document (Punishable with up to 7 years or fine or both)",
            'Section 477A': "Falsification of accounts (Punishable with up to 7 years or fine or both)",
            'Prevention of Corruption Act': "Deals with offenses related to corruption by public servants"
        }
        
        for term in legal_terms[:5]:  # Show more terms if available
            if term in legal_glossary:
                response_parts.append(f"• **{term}**: {legal_glossary[term]}")
            elif 'Section' in term:
                response_parts.append(f"• **{term}**: Specific legal provision under Indian law")
    
    # Add confidence context
    if confidence < 0.6:
        response_parts.append("\n⚠️ **Note**: While I'm providing this information, I recommend "
                          "double-checking with official sources as legal matters can be complex.")
    
    # Add interactive elements with context-specific options
    help_map = {
        'ipc': [
            "1. Explain the FIR-to-trial process for the sections involved",
            "2. Assess bailable/non-bailable and bail strategies",
            "3. Outline common defenses and evidence requirements",
            "4. Draft a police complaint or reply to notices",
            "5. Provide a typical timeline and next hearings"
        ],
        'consumer': [
            "1. Draft complaint to seller/service provider",
            "2. Prepare filing for the correct consumer forum",
            "3. Calculate compensation/refund and interest",
            "4. Compile evidence bundle (bills, chats, emails)",
            "5. Explain expected timeline and hearings"
        ],
        'crpc': [
            "1. Guide anticipatory bail/bail application",
            "2. Prepare for 24-hour production and remand",
            "3. Explain chargesheet and discharge/quash routes",
            "4. Draft applications to the magistrate/court",
            "5. Outline trial stages and timelines"
        ],
        'family': [
            "1. Compare mutual consent vs contested routes",
            "2. Draft petitions for maintenance/custody",
            "3. Prepare mediation strategy and documents",
            "4. List evidence needed (income, expenses, care)",
            "5. Explain typical timelines and outcomes"
        ],
        'property': [
            "1. Verify title and prepare due diligence report",
            "2. Draft legal notice and reply",
            "3. Prepare injunction/possession suits",
            "4. Checklist for registration/stamp duty",
            "5. Estimate timelines and risks"
        ],
        'it_act': [
            "1. Draft cyber complaint with required annexures",
            "2. Advise on data preservation and 65B certificate",
            "3. Escalate with platform/ISP requests",
            "4. Coordinate with cyber cell for investigation",
            "5. Explain sections invoked and penalties"
        ],
        'general': [
            "1. Guide you through filing a formal complaint",
            "2. Explain your legal rights in this situation",
            "3. Help draft a notice to the concerned authorities",
            "4. Connect you with local legal aid if needed",
            "5. Explain the compensation process"
        ],
    }
    help_list = help_map.get(category_lower or 'general', help_map['general'])
    response_parts.extend(["\n💡 **How I Can Help You**:"] + help_list)
    
    # Add disclaimer (shorter and more direct)
    response_parts.append("\n🔹 *Remember*: I'm here to help you understand, but always verify "
                       "critical legal information with a qualified professional.")
    
    return "\n".join(response_parts)


# Concise summarizer for short bot replies
def concise_summarize(text: str, max_sentences: int = 2, max_chars: int = 380) -> str:
    """Return a concise version of the text limited by sentences and characters."""
    if not isinstance(text, str):
        text = str(text or "")
    t = text.strip()
    if not t:
        return "I couldn't find a direct legal answer. Please provide a bit more detail."
    # Split on sentence boundaries
    sentences = []
    for part in t.replace("\n", " ").split("."):
        s = part.strip()
        if s:
            sentences.append(s)
        if len(sentences) >= max_sentences:
            break
    summary = ". ".join(sentences)
    if not summary:
        summary = t[:max_chars]
    if len(summary) > max_chars:
        summary = summary[:max_chars].rstrip() + "…"
    # Ensure it ends cleanly
    if not summary.endswith(('.', '…')):
        summary += '.'
    return summary

# Lazy initializer to ensure services are available during first request
def ensure_services():
    global nlp_service, bot_controller
    try:
        if nlp_service is None:
            try:
                from bot.nlp_service import initialize_service as _init_service
                nlp_service = _init_service()
                logger.info("Initialized nlp_service via ensure_services()")
            except Exception as e:
                logger.error(f"ensure_services: failed to init nlp_service: {e}")
        if bot_controller is None:
            try:
                from bot.bot_controller import LegalBotController as _LBC
                bot_controller = _LBC()
                logger.info("Initialized bot_controller via ensure_services()")
            except Exception as e:
                logger.error(f"ensure_services: failed to init bot_controller: {e}")
    except Exception as e:
        logger.error(f"ensure_services error: {e}")

# Concise rights snippets and query detection
def build_warrantless_arrest_snippet() -> str:
    """Return a concise, jurisdiction-neutral guide for arrest without warrant."""
    return (
        "🛡️ **Arrest Without Warrant: Your Quick Rights Guide**\n\n"
        "**Immediate steps**\n"
        "- Stay calm; do not resist physically.\n"
        "- Politely ask: ‘Am I under arrest? On what grounds? Under which sections?’\n"
        "- You have the right to remain silent until you consult a lawyer.\n\n"
        "**Contact and documentation**\n"
        "- Ask police to inform a family member or your lawyer immediately.\n"
        "- Request an arrest memo and note officers’ names/badge numbers.\n"
        "- Do not sign blank or confessional papers. Read before signing.\n\n"
        "**Time limits and health**\n"
        "- You should be produced before a magistrate within ~24 hours (jurisdiction rules apply).\n"
        "- Request a medical check, and record any injuries.\n\n"
        "**If the arrest seems illegal**\n"
        "- Inform the magistrate at first production.\n"
        "- Consult a lawyer about bail and filing appropriate complaints.\n\n"
        "🔹 *Note*: Laws vary by country/state. This is general information—consult a qualified professional for specific advice."
    )


def is_warrantless_arrest_query(text: str) -> bool:
    """Heuristic keyword match for warrantless arrest queries."""
    if not text:
        return False
    t = text.lower()
    keywords = [
        "arrest without warrant",
        "police arrest without warrant",
        "no warrant arrest",
        "arrested without warrant",
        "police arrested me without warrant",
        "rights when arrested without",
        "what to do if police arrest without",
    ]
    return any(k in t for k in keywords)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        'error': 'Resource not found',
        'message': 'The requested resource could not be found.'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An internal server error occurred.'
    }), 500

@app.errorhandler(HTTPException)
def handle_exception(e):
    return jsonify({
        'error': e.name,
        'message': e.description
    }), e.code

# Health check endpoint
@app.route('/health')
def health_check():
    """Application health check"""
    try:
        ensure_services()
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'nlp_service': nlp_service is not None,
                'bot_controller': bot_controller is not None
            }
        }
        
        if bot_controller:
            try:
                model_data = bot_controller.load_model()
                status['services']['model_loaded'] = True
                status['model_info'] = {
                    'qa_pairs_count': len(model_data.get('qa_pairs', [])),
                    'has_vectorizer': 'vectorizer' in model_data,
                    'has_question_vectors': 'question_vectors' in model_data
                }
            except Exception:
                status['services']['model_loaded'] = False
                
        return jsonify(status)
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Main Pages
@app.route('/')
def home():
    """Home page"""
    return render_template('index.html')

@app.route('/chat')
def chat():
    """Chat interface page"""
    return render_template('chat.html')

@app.route('/login')
def login():
    """Login page"""
    return render_template('login.html')

@app.route('/register')
def register():
    """Registration page"""
    return render_template('register.html')

@app.route('/services')
def services():
    """Services overview page"""
    return render_template('service.html')

# Legal service pages
@app.route('/services/family')
def family():
    """Family law services"""
    return render_template('family.html')

@app.route('/services/consumer')
def consumer():
    """Consumer law services"""
    return render_template('consumer.html')

@app.route('/services/it_act')
def it_act():
    """IT Act services"""
    return render_template('it_act.html')

@app.route('/services/ipc')
def ipc():
    """Indian Penal Code services"""
    return render_template('ipc.html')

@app.route('/services/crpc')
def crpc():
    """Criminal Procedure Code services"""
    return render_template('crpc.html')

@app.route('/services/property')
def property_law():
    """Property law services"""
    return render_template('property.html')

@app.route('/services/ipc_chat')
def ipc_chat():
    """IPC chat page"""
    if 'session_id' not in session:
        session['session_id'] = f"session-{int(datetime.now().timestamp())}-{random.randint(1000,9999)}"
    return render_template('ipc_chat.html', domain='ipc', session_id=session['session_id'])

@app.route('/services/crpc_chat')
def crpc_chat():
    """CrPC chat page"""
    if 'session_id' not in session:
        session['session_id'] = f"session-{int(datetime.now().timestamp())}-{random.randint(1000,9999)}"
    return render_template('crpc_chat.html', domain='crpc', session_id=session['session_id'])

@app.route('/services/cyber_chat')
def cyber_chat():
    """Cyber Law chat page"""
    if 'session_id' not in session:
        session['session_id'] = f"session-{int(datetime.now().timestamp())}-{random.randint(1000,9999)}"
    return render_template('cyber_chat.html', domain='it_act', session_id=session['session_id'])

@app.route('/services/family_chat')
def family_chat():
    """Family Law chat page"""
    if 'session_id' not in session:
        session['session_id'] = f"session-{int(datetime.now().timestamp())}-{random.randint(1000,9999)}"
    return render_template('family_chat.html', domain='family', session_id=session['session_id'])

@app.route('/services/property_chat')
def property_chat():
    """Property Law chat page"""
    if 'session_id' not in session:
        session['session_id'] = f"session-{int(datetime.now().timestamp())}-{random.randint(1000,9999)}"
    return render_template('property_chat.html', domain='property', session_id=session['session_id'])

@app.route('/services/consumer_chat')
def consumer_chat():
    """Consumer Law chat page"""
    if 'session_id' not in session:
        session['session_id'] = f"session-{int(datetime.now().timestamp())}-{random.randint(1000,9999)}"
    return render_template('consumer_chat.html', domain='consumer', session_id=session['session_id'])

# Domain-scoped API route to forward to main chat with domain injected
@app.route('/api/chat/<domain>', methods=['POST'])
def api_chat_domain(domain):
    try:
        data = request.get_json() or {}
        # Inject/override domain
        data['domain'] = str(domain or '').strip().lower()
        # Reconstruct request by calling api_chat with modified data
        # Directly call handler using a manual request context replacement
        request_data = data
        # Monkey patch: emulate request.get_json() using local var
        # We'll pass through by setting a flag on flask.g if needed, but simpler: reuse logic below
        # Create a lightweight proxy by setting a special key
        request._cached_data = json.dumps(request_data).encode('utf-8')
        return api_chat()
    except Exception as e:
        logger.error(f"api_chat_domain error: {e}")
        return jsonify({'status':'error','message':str(e)}), 400

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Main chat API endpoint"""
    try:
        ensure_services()
        # Get JSON data from request
        data = request.get_json()
        user_input = data.get('message', '').strip()
        style = str(data.get('style', '')).lower() if isinstance(data, dict) else ''
        concise_pref = bool(data.get('concise')) if isinstance(data, dict) else False
        # Domain/category coming from UI pages (ipc, consumer, crpc, it_act, etc.)
        requested_domain = str(data.get('domain', '') or '').strip().lower()
        # Optional pipeline trace for debugging flow
        trace_enabled = os.environ.get('PIPELINE_TRACE', 'false').lower() == 'true'
        pipeline_trace = []
        def trace(step, **kwargs):
            if trace_enabled:
                item = {'step': step, 'ts': datetime.now().isoformat()}
                if kwargs:
                    item.update(kwargs)
                pipeline_trace.append(item)
        trace('request_received', domain=requested_domain, has_text=bool(user_input))
        
        if not user_input:
            return jsonify({
                'status': 'error',
                'message': 'No message provided',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        logger.info(f"Received chat message: {user_input}")
        trace('preprocess_done')
        
        # Initialize response structure
        response = {
            'status': 'success',
            'message': '',
            'is_legal': True,
            'confidence': 0.0,
            'category': 'general',
            'sources': [],
            'suggested_questions': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Use Multi-Dataset Search Engine for comprehensive search
            trace('starting_multi_dataset_search', domain=requested_domain)
            
            # Infer category from classifier if domain not provided
            if (not requested_domain) and nlp_service and hasattr(nlp_service, 'classify_legal_category'):
                try:
                    cat, cat_conf = nlp_service.classify_legal_category(user_input)
                    if cat and cat_conf >= 0.5:
                        requested_domain = str(cat).strip().lower()
                        trace('category_inferred', category=requested_domain, confidence=float(cat_conf))
                except Exception:
                    pass
            
            # Try multi-dataset search first, with robust fallback
            search_successful = False
            
            # Attempt 1: Multi-dataset search engine
            if search_legal_answer and not search_successful:
                try:
                    search_result = search_legal_answer(
                        query=user_input,
                        domain=requested_domain,
                        threshold=DATASET_THRESHOLD
                    )
                    
                    if search_result and search_result.get('answer'):
                        trace('multi_dataset_search_complete', 
                              confidence=search_result.get('confidence', 0),
                              found_matches=search_result.get('found_matches', 0))
                        
                        response.update({
                            'message': search_result.get('answer', ''),
                            'confidence': float(search_result.get('confidence', 0.0)),
                            'category': search_result.get('category', requested_domain or 'general'),
                            'sources': search_result.get('sources', []),
                            'source': 'multi_dataset_search',
                            'search_path': search_result.get('search_path', []),
                            'found_matches': search_result.get('found_matches', 0)
                        })
                        search_successful = True
                except Exception as e:
                    logger.warning(f"Multi-dataset search error: {e}")
                    trace('multi_dataset_search_error', error=str(e))
            
            # Attempt 2: Direct model search (fallback)
            if not search_successful:
                logger.info("Using direct model search fallback")
                selected_model = None
                
                # Try category-specific model first
                if requested_domain and 'trained_models_by_category' in globals() and trained_models_by_category:
                    selected_model = trained_models_by_category.get(requested_domain)
                    if selected_model:
                        logger.info(f"Using category model: {requested_domain}")
                
                # Fall back to global model
                if not selected_model and 'trained_model' in globals() and trained_model:
                    selected_model = trained_model
                    logger.info("Using global trained model")
                
                if selected_model and get_legal_answer:
                    try:
                        if selected_model is trained_model:
                            answer, similarity_score, category = get_legal_answer(
                                user_input, selected_model, top_k=3, category_filter=requested_domain or None
                            )
                        else:
                            answer, similarity_score, category = get_legal_answer(
                                user_input, selected_model, top_k=3
                            )
                        
                        response.update({
                            'message': answer,
                            'confidence': float(similarity_score),
                            'category': (category or requested_domain or 'general'),
                            'source': 'trained_model_direct'
                        })
                        search_successful = True
                        logger.info(f"Direct model search successful, confidence: {similarity_score:.3f}")
                    except Exception as e2:
                        logger.error(f"Direct model search also failed: {e2}", exc_info=True)
            
            # Final fallback if no answer found
            if not response.get('message'):
                response['message'] = "I searched across all legal datasets but couldn't find a close match. Please rephrase your question with more specific details about the legal issue, relevant sections, or applicable acts."
                response['is_legal'] = True
                response['source'] = 'no_dataset_match'
                response['confidence'] = 0.2
                trace('no_match_found')

            # Generate context-specific suggested questions unless no_dataset_match
            if is_legal and response.get('category') != 'casual' and response.get('message') and response.get('source') != 'no_dataset_match':
                if not response.get('suggested_questions'):  # Only if not already set by NLP service
                    response['suggested_questions'] = generate_contextual_suggestions(
                        user_input, 
                        response.get('message', ''),
                        response.get('category', '')
                    )

        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            # Try one more time with just the global model as last resort
            try:
                if 'trained_model' in globals() and trained_model and get_legal_answer:
                    answer, similarity_score, category = get_legal_answer(
                        user_input, trained_model, top_k=5, category_filter=None
                    )
                    response['message'] = answer
                    response['confidence'] = float(similarity_score)
                    response['category'] = category or 'general'
                    response['source'] = 'emergency_fallback'
                else:
                    raise Exception("No models available")
            except Exception as e2:
                logger.error(f"Emergency fallback also failed: {e2}")
                response['message'] = "I'm having trouble accessing the legal database right now. Please try again in a moment or rephrase your question with more specific details."
                response['is_legal'] = True
                response['source'] = 'error_fallback'
                response['confidence'] = 0.2
        
        # Normalize payload for frontend compatibility
        # Ensure both 'message' and legacy 'response' fields are present
        final_text = response.get('message') or response.get('response') or ''
        if not isinstance(final_text, str):
            final_text = str(final_text)

        # Normalize category to known service domains when possible
        try:
            known_cats = {'ipc','consumer','crpc','family','property','it_act'}
            current_cat = str(response.get('category') or '').strip().lower()
            if current_cat not in known_cats:
                if requested_domain in known_cats:
                    response['category'] = requested_domain
                elif 'ipc' in current_cat:
                    response['category'] = 'ipc'
                elif 'consumer' in current_cat:
                    response['category'] = 'consumer'
                elif 'crpc' in current_cat or 'criminal procedure' in current_cat:
                    response['category'] = 'crpc'
                elif 'family' in current_cat:
                    response['category'] = 'family'
                elif 'property' in current_cat:
                    response['category'] = 'property'
                elif 'it' in current_cat or 'cyber' in current_cat:
                    response['category'] = 'it_act'
        except Exception:
            pass

        # Format response based on source
        # IMPORTANT: Use user-friendly formatting for all dataset responses
        dataset_sources = {'multi_dataset_search', 'trained_model_direct', 'trained_model_fallback', 'emergency_fallback'}
        
        if response.get('source') in dataset_sources:
            # Use new user-friendly formatter
            if format_user_friendly_response and callable(format_user_friendly_response):
                try:
                    formatted_text = format_user_friendly_response(
                        query=user_input,
                        answer=final_text,
                        category=response.get('category', 'general')
                    )
                    logger.info("✓ Applied user-friendly formatting")
                except Exception as e:
                    logger.warning(f"User-friendly formatting failed, trying enhanced: {e}")
                    # Fallback to enhanced response handler
                    if format_enhanced_response and callable(format_enhanced_response):
                        try:
                            formatted_text = format_enhanced_response(
                                query=user_input,
                                answer=final_text,
                                confidence=response.get('confidence', 0.0),
                                category=response.get('category', 'general')
                            )
                        except Exception as e2:
                            logger.warning(f"Enhanced formatting also failed, using raw answer: {e2}")
                            formatted_text = final_text
                    else:
                        formatted_text = final_text
            else:
                # Fallback to raw answer if enhanced handler not available
                formatted_text = final_text
        elif response.get('source') == 'no_dataset_match':
            # Return explicit dataset no-match as-is
            formatted_text = final_text
        else:
            # For concise mode, return a short summary
            if response.get('concise') or concise_pref or style == 'concise':
                formatted_text = concise_summarize(final_text)
            else:
                # Step-by-step format for non-trained or low-confidence answers
                try:
                    formatted_text = format_legal_response(
                        user_input=user_input,
                        answer=final_text,
                        category=response.get('category', 'general'),
                        confidence=response.get('confidence', 0.0),
                        recommendations=None,
                        legal_terms=extract_legal_terms_from_answer(final_text) if callable(extract_legal_terms_from_answer) else []
                    )
                except Exception:
                    formatted_text = final_text

        response['message'] = formatted_text
        response['response'] = formatted_text
        # Apply confidence floor when we produced a meaningful message
        try:
            if response.get('message'):
                response['confidence'] = float(max(response.get('confidence') or 0.0, 0.35))
        except Exception:
            pass
        if not response.get('category'):
            response['category'] = 'general'
        # Ensure enhanced fields exist for UI rendering
        for key in ['process','penalties','defenses','authority_preparation','timeline','suggested_questions','intent','safety_flags','legal_terms','recommendations']:
            if key not in response:
                # lists default to []; dict default for safety_flags
                response[key] = {} if key == 'safety_flags' else ([] if key != 'intent' else '')
        
        if trace_enabled:
            response['pipeline_trace'] = pipeline_trace
        return jsonify(response)
            
    except Exception as e:
        logger.error(f"Chat API error: {e}")
        return jsonify({
            'response': f'Sorry, I encountered an error: {str(e)}',
            'confidence': 0.0,
            'category': 'error',
            'source': 'system',
            'timestamp': datetime.now().isoformat()
        }), 500

def generate_recommendations(category, confidence):
    """Generate contextual recommendations based on category and confidence"""
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
        ],
        'constitutional': [
            "File RTI application for information access",
            "Consider approaching High Court for writ petitions",
            "Gather supporting documents and evidence"
        ]
    }
    
    if category and category.lower() in category_recommendations:
        recommendations.extend(category_recommendations[category.lower()][:2])
    
    return recommendations[:3]

def generate_contextual_suggestions(user_query, answer, category):
    """Generate context-specific follow-up questions based on the query and answer"""
    import re
    suggestions = []
    
    # Extract key terms from user query and answer
    query_lower = user_query.lower()
    answer_lower = answer.lower() if answer else ''
    
    # Extract section numbers mentioned in the answer for IPC/CrPC
    section_pattern = r'[Ss]ection\s+(\d+[A-Za-z]?)'
    sections_found = re.findall(section_pattern, answer)
    
    cat_lower = (category or '').lower()
    
    # Priority 1: Add section-specific explanations for IPC/CrPC
    if sections_found and cat_lower in ['ipc', 'crpc']:
        for section in sections_found[:2]:  # Max 2 section suggestions
            act_name = "IPC" if cat_lower == 'ipc' else "CrPC"
            suggestions.append(f"Explain Section {section} of {act_name}")
    
    # Priority 2: Context-specific questions based on query content
    if 'theft' in query_lower or 'robbery' in query_lower or 'stolen' in query_lower:
        suggestions.extend([
            "What is the punishment for theft under IPC?",
            "How to file an FIR for theft?",
            "What are bailable and non-bailable offenses?"
        ])
    elif 'bail' in query_lower:
        suggestions.extend([
            "What is the procedure for getting bail?",
            "What are the rights of an arrested person?",
            "How to file a bail application?"
        ])
    elif 'arrest' in query_lower:
        suggestions.extend([
            "What are the rights of an arrested person?",
            "Can police arrest without a warrant?",
            "How long can police detain someone?"
        ])
    elif 'fir' in query_lower:
        suggestions.extend([
            "How to file an FIR online?",
            "What happens after filing an FIR?",
            "Can I get a copy of the FIR?"
        ])
    elif 'murder' in query_lower or '302' in query_lower:
        suggestions.extend([
            "What is the punishment for murder under IPC?",
            "What is the difference between culpable homicide and murder?",
            "Can murder charges be bailable?"
        ])
    elif 'divorce' in query_lower:
        suggestions.extend([
            "What are the grounds for divorce in India?",
            "How long does a divorce process take?",
            "What documents are needed for divorce?"
        ])
    elif 'property' in query_lower or 'land' in query_lower:
        suggestions.extend([
            "What documents prove property ownership?",
            "How to verify property title?",
            "What is the property registration process?"
        ])
    elif 'consumer' in query_lower or 'complaint' in query_lower:
        suggestions.extend([
            "How to file a consumer complaint?",
            "What is the time limit for consumer cases?",
            "What compensation can I claim?"
        ])
    elif 'cyber' in query_lower or 'online' in query_lower or 'hacking' in query_lower:
        suggestions.extend([
            "How to report a cybercrime?",
            "What evidence should I preserve?",
            "Which authority handles cybercrime complaints?"
        ])
    
    # Priority 3: Category-based fallback questions
    if not suggestions:
        category_fallbacks = {
            'ipc': [
                "What are the common IPC sections?",
                "What is the punishment for this offense?",
                "How to file an FIR for this case?"
            ],
            'crpc': [
                "What is the procedure for getting bail?",
                "What are the rights of an arrested person?",
                "How long does the trial process take?"
            ],
            'consumer': [
                "How to file a consumer complaint?",
                "What is the time limit for consumer cases?",
                "What compensation can I claim?"
            ],
            'family': [
                "What documents are needed for this case?",
                "Can this matter be resolved through mediation?",
                "How long does this legal process take?"
            ],
            'property': [
                "What documents prove property ownership?",
                "How to verify property title?",
                "What is the registration process?"
            ],
            'it_act': [
                "How to report a cybercrime?",
                "What evidence should I preserve?",
                "Which authority handles such complaints?"
            ]
        }
        
        if cat_lower in category_fallbacks:
            suggestions.extend(category_fallbacks[cat_lower])
    
    # Priority 4: Generic legal questions if nothing else matches
    if not suggestions:
        suggestions.extend([
            "What are my legal rights in this situation?",
            "What is the procedure to file a case?",
            "Do I need a lawyer for this?"
        ])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_suggestions = []
    for s in suggestions:
        if s not in seen:
            seen.add(s)
            unique_suggestions.append(s)
    
    return unique_suggestions[:3]  # Return max 3 suggestions

def extract_legal_terms_from_answer(answer):
    """Extract legal terms from the answer"""
    legal_keywords = [
        'IPC', 'CrPC', 'Constitution', 'Article', 'Section', 'Act', 'Court', 'Judge',
        'Bail', 'FIR', 'Warrant', 'Appeal', 'Petition', 'Writ', 'Injunction',
        'Divorce', 'Custody', 'Maintenance', 'Alimony', 'Marriage', 'Adoption',
        'Contract', 'Agreement', 'Breach', 'Damages', 'Compensation', 'Liability',
        'Property', 'Registration', 'Stamp Duty', 'Mutation', 'Title', 'Deed',
        'RTI', 'Consumer Forum', 'Deficiency', 'Service Tax', 'GST'
    ]
    
    found_terms = []
    answer_upper = answer.upper()
    
    for term in legal_keywords:
        if term.upper() in answer_upper:
            found_terms.append(term)
    
    return found_terms[:5]

@app.route('/api/chat/simple', methods=['POST'])
def api_simple_chat():
    """Simple chat API endpoint that uses multi-dataset search"""
    try:
        data = request.get_json()
        user_input = data.get('message', '').strip()
        domain = str(data.get('domain', '') or '').strip().lower() if isinstance(data, dict) else ''
        if not user_input:
            return jsonify({'response': 'Please enter a valid legal query.'})

        ensure_services()
        
        # Use multi-dataset search if available
        if search_legal_answer:
            try:
                search_result = search_legal_answer(
                    query=user_input,
                    domain=domain,
                    threshold=DATASET_THRESHOLD
                )
                return jsonify({
                    'response': search_result.get('answer', ''),
                    'confidence': float(search_result.get('confidence', 0.0)),
                    'category': search_result.get('category', domain or 'general'),
                    'sources': search_result.get('sources', []),
                    'source': 'multi_dataset_search',
                    'found_matches': search_result.get('found_matches', 0),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.warning(f"Multi-dataset search failed: {e}")
        
        # Fallback to single model approach
        sel_model = None
        if domain and 'trained_models_by_category' in globals():
            sel_model = trained_models_by_category.get(domain)
        if not sel_model:
            sel_model = trained_model

        if sel_model and get_legal_answer:
            try:
                if sel_model is trained_model:
                    ans, score, cat = get_legal_answer(user_input, sel_model, top_k=3, category_filter=domain or None)
                else:
                    ans, score, cat = get_legal_answer(user_input, sel_model, top_k=3)
                return jsonify({
                    'response': ans,
                    'confidence': float(score),
                    'category': (cat or domain or 'general'),
                    'source': 'trained_model_fallback',
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.warning(f"Fallback model retrieval failed: {e}")

        # No match found
        return jsonify({
            'response': "I searched across all legal datasets but couldn't find a close match. Please rephrase with more specifics (section, act, facts).",
            'source': 'no_dataset_match',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Simple chat API error: {e}")
        return jsonify({'response': f'Sorry, I encountered an error: {str(e)}'}), 500

@app.route('/api/preprocess', methods=['POST'])
def api_preprocess():
    """Text preprocessing API endpoint"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({
                'error': 'No text provided',
                'processed_text': '',
                'entities': {}
            }), 400
        
        # Preprocess text
        processed_text = preprocess_legal_text(text) if preprocess_legal_text else text
        
        # Extract entities
        entities = extract_legal_entities(text) if extract_legal_entities else {}
        
        return jsonify({
            'original_text': text,
            'processed_text': processed_text,
            'entities': entities,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Preprocess API error: {e}")
        return jsonify({
            'error': str(e),
            'processed_text': '',
            'entities': {}
        }), 500

@app.route('/api/model/info', methods=['GET'])
def api_model_info():
    """Get model information"""
    try:
        if not bot_controller:
            return jsonify({
                'error': 'Bot controller not available'
            }), 503
            
        model_data = bot_controller.load_model()
        
        # Analyze model data
        categories = {}
        sources = {}
        
        for qa_pair in model_data.get('qa_pairs', []):
            category = qa_pair.get('category', 'unknown')
            source = qa_pair.get('source', 'unknown')
            
            categories[category] = categories.get(category, 0) + 1
            sources[source] = sources.get(source, 0) + 1
        
        return jsonify({
            'total_qa_pairs': len(model_data.get('qa_pairs', [])),
            'categories': categories,
            'sources': sources,
            'has_vectorizer': 'vectorizer' in model_data,
            'has_question_vectors': 'question_vectors' in model_data,
            'vector_shape': str(model_data.get('question_vectors', {}).shape) if 'question_vectors' in model_data else None,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Model info API error: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/categories', methods=['GET'])
def api_categories():
    """Get available legal categories"""
    try:
        if nlp_service and hasattr(nlp_service, 'legal_categories'):
            categories = nlp_service.legal_categories
        else:
            # Default categories
            categories = {
                'criminal': ['fir', 'police', 'arrest', 'bail', 'ipc', 'crpc'],
                'civil': ['contract', 'property', 'tort', 'negligence'],
                'family': ['marriage', 'divorce', 'custody', 'maintenance'],
                'consumer': ['defective', 'service', 'complaint', 'refund'],
                'constitutional': ['rti', 'right to information', 'writ'],
                'labour': ['employment', 'salary', 'wages', 'workplace']
            }
        
        return jsonify({
            'categories': categories,
            'total_categories': len(categories),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Categories API error: {e}")
        return jsonify({
            'error': str(e),
            'categories': {}
        }), 500


 

# Development and production configuration
if __name__ == '__main__':
    # Development server
    logger.info("Starting NyayaShield Legal Bot Server...")
    logger.info(f"Debug mode: {app.config['DEBUG']}")
    
    # Check if services are properly initialized
    if nlp_service:
        logger.info("✓ NLP Service ready")
    else:
        logger.warning("✗ NLP Service not available")
        
    if bot_controller:
        logger.info("✓ Bot Controller ready")
    else:
        logger.warning("✗ Bot Controller not available")
    
    # Start the server
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=app.config['DEBUG'],
        threaded=True
    )
else:
    # Production server (when run with gunicorn, etc.)
    logger.info("NyayaShield Legal Bot initialized for production")
