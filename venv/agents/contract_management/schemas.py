from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from enum import Enum
from shared.models import Priority

class ContractType(str, Enum):
    """Tipos de contratos"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACTOR = "contractor"
    INTERNSHIP = "internship"
    EXECUTIVE = "executive"

class ContractStatus(str, Enum):
    """Estados del contrato"""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    SIGNED = "signed"
    EXECUTED = "executed"
    CANCELLED = "cancelled"

class SignatureType(str, Enum):
    """Tipos de firma"""
    DIGITAL = "digital"
    ELECTRONIC = "electronic"
    PHYSICAL = "physical"
    DOCUSIGN = "docusign"

class ComplianceLevel(str, Enum):
    """Niveles de compliance"""
    BASIC = "basic"
    STANDARD = "standard"
    ENHANCED = "enhanced"
    EXECUTIVE = "executive"

class LegalClause(BaseModel):
    """Cláusula legal individual"""
    clause_id: str
    clause_type: str  # "employment_terms", "compensation", "benefits", "termination"
    title: str
    content: str
    is_mandatory: bool = True
    jurisdiction: str = "Costa Rica"
    legal_reference: Optional[str] = None

class CompensationDetails(BaseModel):
    """Detalles de compensación"""
    base_salary: float
    currency: str = "USD"
    payment_frequency: str = "monthly"  # monthly, biweekly, weekly
    bonus_structure: Optional[Dict[str, Any]] = None
    commission_structure: Optional[Dict[str, Any]] = None
    equity_grants: List[Dict[str, str]] = Field(default_factory=list)
    benefits_package: List[str] = Field(default_factory=list)
    total_compensation: Optional[float] = None

class EmploymentTerms(BaseModel):
    """Términos de empleo"""
    position_title: str
    department: str
    reporting_manager: str
    employment_type: ContractType
    start_date: date
    probation_period_days: int = 90
    work_schedule: str = "full_time"  # full_time, part_time, flexible
    work_location: str
    remote_work_allowed: bool = True
    travel_requirements: str = "minimal"

class BenefitsPackage(BaseModel):
    """Paquete de beneficios"""
    health_insurance: Dict[str, Any] = Field(default_factory=dict)
    dental_insurance: Optional[Dict[str, Any]] = None
    life_insurance: Optional[Dict[str, Any]] = None
    retirement_plan: Optional[Dict[str, Any]] = None
    vacation_days: int = 15
    sick_days: int = 10
    personal_days: int = 3
    professional_development: Optional[Dict[str, Any]] = None
    gym_membership: bool = False
    meal_allowance: Optional[float] = None
    transport_allowance: Optional[float] = None

class SignatureDetails(BaseModel):
    """Detalles de firma"""
    signature_type: SignatureType
    signer_name: str
    signer_title: str
    signer_email: str
    signature_date: Optional[datetime] = None
    signature_location: Optional[str] = None
    witness_required: bool = False
    notarization_required: bool = False
    ip_address: Optional[str] = None
    device_info: Optional[str] = None

class ContractGenerationRequest(BaseModel):
    """Solicitud de generación de contrato"""
    employee_id: str
    session_id: str
    
    # Datos del empleado (del IT Provisioning Agent)
    personal_data: Dict[str, Any]
    position_data: Dict[str, Any]
    contractual_data: Dict[str, Any]
    it_credentials: Dict[str, Any]
    
    # Configuración del contrato
    contract_type: ContractType = ContractType.FULL_TIME
    compliance_level: ComplianceLevel = ComplianceLevel.STANDARD
    priority: Priority = Priority.MEDIUM
    
    # Especificaciones adicionales
    special_clauses: List[str] = Field(default_factory=list)
    legal_requirements: List[str] = Field(default_factory=list)
    template_version: str = "v2024.1"

class ContractDocument(BaseModel):
    """Documento de contrato completo"""
    contract_id: str = Field(default_factory=lambda: f"CONT-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    employee_id: str
    
    # Metadatos del documento
    document_version: str = "1.0"
    template_version: str = "v2024.1"
    jurisdiction: str = "Costa Rica"
    language: str = "Spanish"
    
    # Contenido del contrato
    employment_terms: EmploymentTerms
    compensation_details: CompensationDetails
    benefits_package: BenefitsPackage
    legal_clauses: List[LegalClause] = Field(default_factory=list)
    
    # IT Integration
    it_provisions: Dict[str, Any] = Field(default_factory=dict)
    equipment_assignment: Dict[str, Any] = Field(default_factory=dict)
    
    # Firmas
    employee_signature: Optional[SignatureDetails] = None
    employer_signature: Optional[SignatureDetails] = None
    witness_signatures: List[SignatureDetails] = Field(default_factory=list)
    
    # Control de documento
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: ContractStatus = ContractStatus.DRAFT
    compliance_verified: bool = False
    legal_review_completed: bool = False

class ContractValidationResult(BaseModel):
    """Resultado de validación legal"""
    is_valid: bool
    compliance_score: float = Field(ge=0.0, le=100.0)
    legal_issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    # Validaciones específicas
    clause_validation: Dict[str, bool] = Field(default_factory=dict)
    compliance_checks: Dict[str, bool] = Field(default_factory=dict)
    jurisdiction_compliance: bool = True
    
    # Metadatos
    validator_id: str = "legal_validator_v1.0"
    validation_timestamp: datetime = Field(default_factory=datetime.utcnow)

class ContractManagementResult(BaseModel):
    """Resultado del Contract Management Agent"""
    success: bool
    employee_id: str
    session_id: str
    contract_id: str
    
    # Resultado principal
    contract_document: Optional[ContractDocument] = None
    validation_result: Optional[ContractValidationResult] = None
    
    # Proceso de firma
    signature_process_complete: bool = False
    signatures_collected: int = 0
    signatures_required: int = 2
    
    # Métricas de proceso
    processing_time: float = 0.0
    contract_generated: bool = False
    legal_validation_passed: bool = False
    compliance_verified: bool = False
    document_archived: bool = False
    
    # Estado y próximos pasos
    ready_for_meeting_coordination: bool = False
    next_actions: List[str] = Field(default_factory=list)
    requires_manual_review: bool = False
    
    # Errores y advertencias
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class HRDepartmentResponse(BaseModel):
    """Respuesta simulada del departamento HR"""
    request_id: str
    employee_id: str
    status: str = "completed"
    processing_time_minutes: float
    
    contract_template: Dict[str, Any]
    legal_clauses: List[LegalClause]
    compliance_requirements: Dict[str, Any]
    benefits_configuration: BenefitsPackage
    
    approval_workflow: List[str] = Field(default_factory=list)
    hr_contact: str = "hr@company.com"
    legal_contact: str = "legal@company.com"
    completion_notes: List[str] = Field(default_factory=list)

class HRSimulatorConfig(BaseModel):
    """Configuración del simulador HR"""
    response_delay_min: int = 180  # 3 minutos
    response_delay_max: int = 600  # 10 minutos
    legal_review_required_rate: float = 0.15  # 15% requiere revisión legal
    compliance_check_rate: float = 0.95  # 95% pasa compliance
    
    contract_templates: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    legal_clause_library: List[LegalClause] = Field(default_factory=list)
    benefits_packages: Dict[str, BenefitsPackage] = Field(default_factory=dict)

class ContractArchive(BaseModel):
    """Archivo de contrato"""
    archive_id: str = Field(default_factory=lambda: f"ARCH-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    contract_id: str
    employee_id: str
    
    # Archivos generados
    pdf_document: str  # Path o URL del PDF
    signed_document: Optional[str] = None  # Path del documento firmado
    metadata_file: str  # Path del archivo de metadatos
    
    # Información de archivo
    archive_location: str = "company_contract_repository"
    retention_period_years: int = 7
    access_level: str = "confidential"
    
    # Timestamps
    archived_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None