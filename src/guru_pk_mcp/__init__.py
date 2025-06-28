"""
Guru-PK MCP: AI Expert PK Debate System

A Model Context Protocol (MCP) server for facilitating philosophical debates
between AI-simulated thought leaders and experts.

This package provides tools for conducting structured debates between different
AI personas representing famous philosophers, entrepreneurs, and thought leaders.
"""

__version__ = "1.0.0"
__author__ = "Guru-PK Team"
__email__ = "noreply@guru-pk.com"

from .custom_personas import CustomPersonaManager
from .models import PKSession
from .personas import (
    PERSONAS,
    format_persona_info,
    generate_round_prompt,
    get_available_personas,
)
from .session_manager import SessionManager

__all__ = [
    "PKSession",
    "PERSONAS",
    "get_available_personas",
    "generate_round_prompt",
    "format_persona_info",
    "SessionManager",
    "CustomPersonaManager",
]
