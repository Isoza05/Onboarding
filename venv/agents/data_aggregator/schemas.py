from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from enum import Enum
from shared.models import Priority

class ValidationLevel(str, Enum):
    """Niveles de validación"""
    BASIC = "basic"
    STANDARD = "standard" 
    STRICT = "strict"
    CRITICAL = "critical"

class DataConsistencyStatus(str, Enum):
    """Estado de consistencia de datos"""
    CONSISTENT = "consistent"
    MINOR_DISCREPANCIES = "minor_discrepancies"
    MAJOR_DISCREPANCIES = "major_discrepancies"
    INCONSISTENT = "inconsistent"

class FieldValidationStatus(str, Enum):
    """Estado de validación de campos individuales"""
    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"
    MISSING = "missing"
    CONFLICTED = "conflicted"

class PersonalData(BaseModel):
    """Datos personales consolidados"""
    employee_id: str
    id_card: Optional[str] = None  # Cédula
    passport: Optional[str] = None
    first_name: str
    middle_name: Optional[str] = None
    name_of_preference: Optional[str] = None
    last_name: str
    mothers_lastname: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    nationality: Optional[str] = None
    marital_status: Optional[str] = None
    children: Optional[int] = None
    english_level: Optional[str] = None
    
    # Información de contacto
    email: Optional[str] = None
    phone: Optional[str] = None
    
    # Dirección
    country: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    current_address: Optional[str] = None

class AcademicData(BaseModel):
    """Datos académicos consolidados"""
    university: Optional[str] = None
    career: Optional[str] = None
    degree_level: Optional[str] = None
    graduation_date: Optional[date] = None
    additional_certifications: List[str] = Field(default_factory=list)
    academic_verification_status: str = "pending"

class PositionData(BaseModel):
    """Datos de posición y proyecto consolidados"""
    position: str
    position_area: Optional[str] = None
    technology: Optional[str] = None
    customer: Optional[str] = None
    partner_name: Optional[str] = None
    project_manager: Optional[str] = None
    office: Optional[str] = None
    collaborator_type: Optional[str] = None
    billable_type: Optional[str] = None
    contracting_type: Optional[str] = None
    contracting_time: Optional[str] = None
    contracting_office: Optional[str] = None
    reference_market: Optional[str] = None
    project_need: Optional[str] = None
    
class ContractualData(BaseModel):
    """Datos contractuales consolidados"""
    start_date: date
    salary: Optional[float] = None
    currency: Optional[str] = None
    employment_type: Optional[str] = None
    work_modality: Optional[str] = None
    probation_period: Optional[int] = None
    benefits: List[str] = Field(default_factory=list)
    gm_total: Optional[float] = None  # GM Total percentage
    client_interview: Optional[bool] = None
    windows_laptop_provided: Optional[bool] = None

class DocumentationStatus(BaseModel):
    """Estado de documentación consolidado"""
    vaccination_card: FieldValidationStatus = FieldValidationStatus.MISSING
    id_document: FieldValidationStatus = FieldValidationStatus.MISSING
    cv_resume: FieldValidationStatus = FieldValidationStatus.MISSING
    photo: FieldValidationStatus = FieldValidationStatus.MISSING
    academic_titles: FieldValidationStatus = FieldValidationStatus.MISSING
    background_check: FieldValidationStatus = FieldValidationStatus.MISSING
    personnel_form: FieldValidationStatus = FieldValidationStatus.MISSING
    
    # Scores de validación
    medical_validation_score: Optional[float] = None
    identity_verification_score: Optional[float] = None
    academic_verification_score: Optional[float] = None
    overall_documentation_score: Optional[float] = None

class FieldValidation(BaseModel):
    """Validación de un campo específico"""
    field_name: str
    status: FieldValidationStatus
    source_values: Dict[str, Any] = Field(default_factory=dict)  # valor por fuente
    consolidated_value: Any = None
    confidence_score: float = Field(ge=0.0, le=100.0, default=0.0)
    discrepancies: List[str] = Field(default_factory=list)
    validation_notes: List[str] = Field(default_factory=list)

class CrossValidationResult(BaseModel):
    """Resultado de validación cruzada"""
    field_validations: List[FieldValidation] = Field(default_factory=list)
    consistency_checks: Dict[str, Any] = Field(default_factory=dict)
    overall_consistency_status: DataConsistencyStatus = DataConsistencyStatus.CONSISTENT
    consistency_score: float = Field(ge=0.0, le=100.0, default=100.0)
    critical_issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
class ConsolidatedEmployeeData(BaseModel):
    """Datos completos consolidados del empleado"""
    # Identificación
    employee_id: str
    session_id: Optional[str] = None
    consolidation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Datos consolidados por categoría
    personal_data: PersonalData
    academic_data: AcademicData
    position_data: PositionData
    contractual_data: ContractualData
    documentation_status: DocumentationStatus
    
    # Validación y consistencia
    cross_validation_result: CrossValidationResult
    data_completeness_percentage: float = Field(ge=0.0, le=100.0, default=0.0)
    validation_level_applied: ValidationLevel = ValidationLevel.STANDARD
    
    # Metadatos de fuentes
    source_data_quality: Dict[str, float] = Field(default_factory=dict)  # score por agente
    data_sources: List[str] = Field(default_factory=list)
    processing_notes: List[str] = Field(default_factory=list)

class AggregationRequest(BaseModel):
    """Solicitud de agregación de datos"""
    employee_id: str
    session_id: str
    
    # Resultados de agentes del DATA COLLECTION HUB
    initial_data_results: Dict[str, Any]
    confirmation_data_results: Dict[str, Any]
    documentation_results: Dict[str, Any]
    
    # Configuración de agregación
    validation_level: ValidationLevel = ValidationLevel.STANDARD
    priority: Priority = Priority.MEDIUM
    strict_validation_fields: List[str] = Field(default_factory=list)
    
    # Contexto adicional
    orchestration_context: Dict[str, Any] = Field(default_factory=dict)
    special_requirements: List[str] = Field(default_factory=list)

class ProcessingReadinessAssessment(BaseModel):
    """Evaluación de preparación para procesamiento"""
    ready_for_it_provisioning: bool = False
    ready_for_contract_management: bool = False
    ready_for_meeting_coordination: bool = False
    
    # Datos requeridos por fase
    it_provisioning_data: Dict[str, Any] = Field(default_factory=dict)
    contract_management_data: Dict[str, Any] = Field(default_factory=dict)
    meeting_coordination_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Bloqueos y dependencias
    blocking_issues: List[str] = Field(default_factory=list)
    missing_critical_data: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)

class AggregationResult(BaseModel):
    """Resultado completo de la agregación"""
    # Identificación
    employee_id: str
    session_id: str
    aggregation_id: str = Field(default_factory=lambda: f"agg_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    
    # Resultado principal
    success: bool
    consolidated_data: Optional[ConsolidatedEmployeeData] = None
    
    # Evaluación de preparación
    processing_readiness: ProcessingReadinessAssessment
    
    # Métricas de calidad
    overall_data_quality_score: float = Field(ge=0.0, le=100.0, default=0.0)
    completeness_score: float = Field(ge=0.0, le=100.0, default=0.0)
    consistency_score: float = Field(ge=0.0, le=100.0, default=0.0)
    reliability_score: float = Field(ge=0.0, le=100.0, default=0.0)
    
    # Control de proceso
    processing_time_seconds: float = 0.0
    agents_processed: List[str] = Field(default_factory=list)
    validation_passed: bool = False
    
    # Issues y recomendaciones
    critical_issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    
    # Para auditoria
    aggregation_log: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

class ValidationRule(BaseModel):
    """Regla de validación para campos específicos"""
    field_name: str
    rule_type: str  # "required", "format", "range", "cross_reference"
    rule_config: Dict[str, Any] = Field(default_factory=dict)
    severity: str = "error"  # "error", "warning", "info"
    description: str
    
class AggregationConfig(BaseModel):
    """Configuración para el proceso de agregación"""
    validation_rules: List[ValidationRule] = Field(default_factory=list)
    field_priority_weights: Dict[str, float] = Field(default_factory=dict)
    source_reliability_weights: Dict[str, float] = Field(default_factory=dict)
    consistency_thresholds: Dict[str, float] = Field(default_factory=dict)
    completeness_requirements: Dict[str, List[str]] = Field(default_factory=dict)
    
    # Configuraciones por defecto
    @classmethod
    def get_default_config(cls) -> 'AggregationConfig':
        return cls(
            field_priority_weights={
                "employee_id": 1.0,
                "first_name": 0.9,
                "last_name": 0.9,
                "id_card": 0.95,
                "email": 0.85,
                "start_date": 0.9,
                "position": 0.8,
                "salary": 0.8
            },
            source_reliability_weights={
                "initial_data_collection_agent": 0.8,
                "confirmation_data_agent": 0.9,
                "documentation_agent": 0.85
            },
            consistency_thresholds={
                "critical_fields": 95.0,
                "important_fields": 85.0,
                "optional_fields": 70.0
            },
            completeness_requirements={
                "it_provisioning": ["employee_id", "first_name", "last_name", "email", "position"],
                "contract_management": ["employee_id", "start_date", "salary", "position", "id_card"],
                "meeting_coordination": ["employee_id", "first_name", "email", "position", "project_manager"]
            }
        )

# Funciones auxiliares para mapeo de datos
def map_agent_data_to_personal_data(agent_results: Dict[str, Any]) -> PersonalData:
    """Mapear resultados de agentes a PersonalData"""
    # Esta función se implementará en el agente para extraer datos personales
    # de los diferentes formatos de resultados de agentes
    pass

def map_agent_data_to_position_data(agent_results: Dict[str, Any]) -> PositionData:
    """Mapear resultados de agentes a PositionData"""
    pass

def map_agent_data_to_contractual_data(agent_results: Dict[str, Any]) -> ContractualData:
    """Mapear resultados de agentes a ContractualData"""
    pass