"""
NyayaShield Bot Package
=======================

This package contains the core bot functionality for the NyayaShield legal assistant.
"""

import logging as _logging

# Import key components to make them available at the package level
try:
    if __package__:
        from .nlp_service import (
            LegalNLPService,
            initialize_service,
            get_legal_response,
            get_detailed_legal_response,
            predict_answer,
        )
        # Bot controller is lightweight
        from .bot_controller import LegalBotController
    else:
        raise ImportError
except Exception:
    import os as _os
    import sys as _sys
    _current_dir = _os.path.dirname(_os.path.abspath(__file__))
    _parent_dir = _os.path.dirname(_current_dir)
    if _parent_dir not in _sys.path:
        _sys.path.insert(0, _parent_dir)
    from bot.nlp_service import (
        LegalNLPService,
        initialize_service,
        get_legal_response,
        get_detailed_legal_response,
        predict_answer,
    )
    from bot.bot_controller import LegalBotController

# LLM service (optional): guard imports so package import never fails
try:
    from .llm_service import (
        LLMService,
        get_response,
        is_legal_query,
        get_casual_response,
        initialize_llm_service,
    )
except Exception as _e:
    _logging.getLogger(__name__).warning(
        f"LLM optional components unavailable ({_e}). Core bot will still function."
    )
    LLMService = None

    def get_response(query: str, legal_response: str = None) -> str:
        return legal_response or "I'm here to help with legal queries. Please provide more details."

    def is_legal_query(query: str) -> bool:
        return True

    def get_casual_response(query: str) -> str:
        return "Hello! Ask a legal question to begin."

    def initialize_llm_service(device: str = None):
        return None

# Version information
__version__ = "1.0.0"

# Package metadata
__all__ = [
    'LegalNLPService',
    'LegalBotController',
    'initialize_service',
    'get_legal_response',
    'get_detailed_legal_response',
    'predict_answer',
    'get_response',
    'is_legal_query',
    'get_casual_response',
    'initialize_llm_service'
]
