"""
Avenlis SandStrike Library

A comprehensive Python library and CLI tool for AI red team testing and LLM security assessment.
"""

__version__ = "1.0.5"
__author__ = "Avenlis Technical Team"
__email__ = "tech@staterasolv.com"

from .api import AvenlisAPI
from .auth import AvenlisAuth
from .config import AvenlisConfig

__all__ = ["AvenlisAPI", "AvenlisAuth", "AvenlisConfig"]
