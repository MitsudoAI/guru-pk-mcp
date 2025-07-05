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

from .dynamic_experts import DynamicExpertManager
from .models import PKSession
from .personas import (
    format_persona_info,
    generate_round_prompt,
)
from .session_manager import SessionManager

__all__ = [
    "PKSession",
    "generate_round_prompt",
    "format_persona_info",
    "SessionManager",
    "DynamicExpertManager",
]
