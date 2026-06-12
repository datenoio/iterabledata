"""
Data validation framework.

Provides functions for validating data against rules and schemas.
"""

from .core import iterable
from .rules import ValidationError, register

__all__ = ["iterable", "register", "ValidationError"]
