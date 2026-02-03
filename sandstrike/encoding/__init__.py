"""
Encoding module for Avenlis SandStrike.

This module provides various encoding/decoding methods for adversarial prompts
to test evasion techniques and bypass security filters.
"""

from .encoders import (
    PromptEncoder,
    EncodingMethod,
    get_available_methods,
    parse_encoding_methods
)

__all__ = [
    'PromptEncoder',
    'EncodingMethod', 
    'get_available_methods',
    'parse_encoding_methods'
]
