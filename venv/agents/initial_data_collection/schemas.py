from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from shared.models import OnboardingStatus, Priority, AgentResponse

# Schemas de entrada
class RawEmailData(BaseModel):
    """Datos crudos del email recibido"""
    subject: str
    body: str
    sender: str
    received_at: datetime
    message_id: Optional[str] = None

# Schemas de datos estructurados
class EmployeeBasicInfo(BaseModel):
    """Información básica del empleado"""
    employee_id: Optional[str] = None
    id_card: str = Field(..., description="Cédula de identidad")
    type_of_hire: str = Field(default="New Hire")
    type_of_information: str = Field(default="New collaborator entry")
    passport: Optional[str] = None
    first_name: str
    middle_name: Optional[str] = None
    name_of_preference: Optional[str] = None
    last_name: str
    mothers_lastname: Optional[str] = None
    
    @validator('id_card')
    def validate_id_card(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('ID Card es requerido')
        return v.strip()

class EmployeePersonalInfo(BaseModel):
    """Información personal del empleado"""
    gender: Optional[str] = None
    english_level: Optional[str] = None
    birth_date: Optional[date] = None
    university: Optional[str] = None
    career: Optional[str] = None
    country_of_birth: Optional[str] = None
    marital_status: Optional[str] = None
    children: Optional[int] = 0
    nationality: Optional[str] = None
    district: Optional[str] = None

class PositionDetails(BaseModel):
    """Detalles de la posición"""
    customer: Optional[str] = None
    client_interview: Optional[str] = None
    position: Optional[str] = None
    position_area: Optional[str] = None
    technology: Optional[str] = None
    start_date: Optional[date] = None

class ProjectInfo(BaseModel):
    """Información del proyecto"""
    project_manager: Optional[str] = None
    office: Optional[str] = None
    collaborator_type: Optional[str] = None
    billable_type: Optional[str] = None
    contracting_type: Optional[str] = None
    contracting_time: Optional[str] = None
    contracting_office: Optional[str] = None
    reference_market: Optional[str] = None
    gm_total: Optional[str] = None
    partner_name: Optional[str] = None
    project_need: Optional[str] = None
    user_will_provide_windows_laptop: Optional[str] = None

class AddressDetails(BaseModel):
    """Detalles de dirección"""
    country: Optional[str] = None
    city: Optional[str] = None
    current_address: Optional[str] = None
    email: Optional[str] = None

class EmployeeData(BaseModel):
    """Datos completos del empleado"""
    basic_info: EmployeeBasicInfo
    personal_info: EmployeePersonalInfo
    position_details: PositionDetails
    project_info: ProjectInfo
    address_details: AddressDetails
    comments: Optional[str] = None
    
    # Metadatos del procesamiento
    raw_email: Optional[RawEmailData] = None
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)
    validation_results: Dict[str, Any] = Field(default_factory=dict)

# Schemas de salida
class DataCollectionResult(AgentResponse):
    """Resultado del proceso de recolección de datos"""
    employee_data: Optional[EmployeeData] = None
    validation_summary: Dict[str, Any] = Field(default_factory=dict)
    missing_fields: List[str] = Field(default_factory=list)
    data_quality_score: Optional[float] = None
    requires_manual_review: bool = False

# Esquemas de configuración
class DataValidationConfig(BaseModel):
    """Configuración para validación de datos"""
    required_fields: List[str] = [
        "basic_info.id_card",
        "basic_info.first_name", 
        "basic_info.last_name"
    ]
    email_validation: bool = True
    date_validation: bool = True
    name_validation: bool = True
    minimum_quality_score: float = 0.8