"""
Documentation Agent (CSA) - Specialized in document analysis and validation
Handles vaccination cards, ID documents, CVs, personnel forms, photos, 
background checks, and academic titles.
"""

from .agent import DocumentationAgent
from .schemas import (
    DocumentationRequest,
    DocumentProcessingResult,
    DocumentType,
    DocumentFormat,
    ValidationStatus
)

__all__ = [
    'DocumentationAgent',
    'DocumentationRequest', 
    'DocumentProcessingResult',
    'DocumentType',
    'DocumentFormat',
    'ValidationStatus'
]