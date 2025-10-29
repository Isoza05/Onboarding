from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date
from enum import Enum
from shared.models import Priority

class DocumentType(str, Enum):
    """Tipos de documentos soportados"""
    VACCINATION_CARD = "vaccination_card"
    ID_DOCUMENT = "id_document" 
    CV_RESUME = "cv_resume"
    PERSONNEL_FORM = "personnel_form"
    PHOTO = "photo"
    BACKGROUND_CHECK = "background_check"
    ACADEMIC_TITLES = "academic_titles"

class DocumentFormat(str, Enum):
    """Formatos de archivo soportados"""
    PDF = "pdf"
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    XLSX = "xlsx"
    DOC = "doc"
    DOCX = "docx"

class ValidationStatus(str, Enum):
    """Estados de validación de documentos"""
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    REQUIRES_REVIEW = "requires_review"
    EXPIRED = "expired"

class DocumentInfo(BaseModel):
    """Información de un documento individual"""
    document_id: str
    document_type: DocumentType
    file_name: str
    file_format: DocumentFormat
    file_size_kb: int
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    content_hash: Optional[str] = None
    
class MedicalValidation(BaseModel):
    """Resultados de validación médica"""
    vaccination_status: str
    health_certificate_valid: bool
    medical_restrictions: List[str] = []
    expiration_date: Optional[date] = None
    issuing_authority: Optional[str] = None

class IDAuthentication(BaseModel):
    """Resultados de autenticación de identidad"""
    identity_verified: bool
    document_authentic: bool
    cross_reference_match: bool
    extracted_info: Dict[str, str] = {}
    confidence_score: float = Field(ge=0.0, le=1.0)

class AcademicVerification(BaseModel):
    """Resultados de verificación académica"""
    titles_verified: List[Dict[str, Any]] = []
    institution_accredited: bool
    degree_level_confirmed: bool
    graduation_date_valid: bool
    overall_score: float = Field(ge=0.0, le=100.0)

class DocumentAnalysis(BaseModel):
    """Análisis completo de documento"""
    text_extraction_success: bool
    image_quality_score: float = Field(ge=0.0, le=100.0)
    content_classification: str
    key_data_extracted: Dict[str, Any] = {}
    processing_notes: List[str] = []

class DocumentationRequest(BaseModel):
    """Solicitud de procesamiento de documentos"""
    employee_id: str
    session_id: Optional[str] = None
    documents: List[DocumentInfo]
    processing_priority: Priority = Priority.MEDIUM
    special_requirements: List[str] = []
    compliance_standards: List[str] = ["general", "hr_standard"]
    
    @validator('documents')
    def validate_documents_not_empty(cls, v):
        if not v:
            raise ValueError("Al menos un documento es requerido")
        return v

class DocumentProcessingResult(BaseModel):
    """Resultado del procesamiento de documentos"""
    employee_id: str
    session_id: Optional[str] = None
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Resultados por documento
    document_analyses: Dict[str, DocumentAnalysis] = {}
    medical_validation: Optional[MedicalValidation] = None
    id_authentication: Optional[IDAuthentication] = None
    academic_verification: Optional[AcademicVerification] = None
    
    # Estado general
    overall_validation_status: ValidationStatus
    compliance_score: float = Field(ge=0.0, le=100.0)
    requires_human_review: bool = False
    missing_documents: List[DocumentType] = []
    
    # Acciones requeridas
    next_steps: List[str] = []
    escalation_needed: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }