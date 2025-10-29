from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from shared.models import OnboardingStatus, Priority, AgentResponse

# Schemas de entrada
class ContractTerms(BaseModel):
    """Términos contractuales"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    salary: Optional[float] = None
    currency: Optional[str] = "USD"
    employment_type: Optional[str] = None  # Full-time, Part-time, Contract
    work_modality: Optional[str] = None   # Remote, Hybrid, On-site
    probation_period: Optional[int] = None  # días
    benefits: List[str] = Field(default_factory=list)

class PositionInfo(BaseModel):
    """Información de la posición"""
    position_title: str
    department: Optional[str] = None
    reporting_manager: Optional[str] = None
    job_level: Optional[str] = None
    location: Optional[str] = None

class ConfirmationRequest(BaseModel):
    """Solicitud de confirmación de datos"""
    employee_id: str
    contract_terms: ContractTerms
    position_info: PositionInfo
    additional_notes: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    
    @validator('contract_terms')
    def validate_contract_terms(cls, v):
        if v.start_date and v.start_date < date.today():
            raise ValueError('Fecha de inicio no puede ser en el pasado')
        return v

# Schemas de salida
class ConfirmationResult(AgentResponse):
    """Resultado del proceso de confirmación"""
    confirmed_terms: Optional[ContractTerms] = None
    validated_position: Optional[PositionInfo] = None
    offer_letter_generated: bool = False
    commitment_letter_generated: bool = False
    validation_score: Optional[float] = None
    compliance_check: Dict[str, Any] = Field(default_factory=dict)
    next_actions: List[str] = Field(default_factory=list)

class ValidationConfig(BaseModel):
    """Configuración de validación"""
    salary_validation: bool = True
    date_validation: bool = True
    policy_compliance: bool = True
    manager_approval_required: bool = False
    minimum_validation_score: float = 0.85