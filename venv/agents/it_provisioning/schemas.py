from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from enum import Enum
from shared.models import Priority

class ITRequestType(str, Enum):
    """Tipos de solicitudes IT"""
    NEW_HIRE = "new_hire"
    EQUIPMENT_PROVISION = "equipment_provision"
    ACCESS_GRANT = "access_grant"
    CREDENTIAL_CREATION = "credential_creation"

class SecurityLevel(str, Enum):
    """Niveles de seguridad para acceso"""
    BASIC = "basic"
    STANDARD = "standard"
    ELEVATED = "elevated"
    EXECUTIVE = "executive"

class EquipmentType(str, Enum):
    """Tipos de equipamiento"""
    LAPTOP_WINDOWS = "laptop_windows"
    LAPTOP_MAC = "laptop_mac"
    MONITOR_24 = "monitor_24"
    MONITOR_27 = "monitor_27"
    PERIPHERALS = "peripherals"
    MOBILE_DEVICE = "mobile_device"

class ITCredentials(BaseModel):
    """Credenciales IT generadas"""
    username: str
    email: str
    temporary_password: str
    domain_access: str
    vpn_credentials: Optional[str] = None
    badge_access: Optional[str] = None
    employee_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    must_change_password: bool = True

class EquipmentAssignment(BaseModel):
    """Asignación de equipamiento"""
    laptop: Dict[str, str] = Field(default_factory=dict)
    monitor: Optional[Dict[str, str]] = None
    peripherals: List[Dict[str, str]] = Field(default_factory=list)
    mobile_device: Optional[Dict[str, str]] = None
    software_licenses: List[str] = Field(default_factory=list)
    total_items: int = 0

class AccessPermissions(BaseModel):
    """Permisos de acceso asignados"""
    systems: List[str] = Field(default_factory=list)
    applications: List[str] = Field(default_factory=list)
    file_shares: List[str] = Field(default_factory=list)
    network_drives: List[str] = Field(default_factory=list)
    vpn_access: bool = False
    remote_access: bool = False

class SecuritySetup(BaseModel):
    """Configuración de seguridad"""
    badge_access: str
    parking_permit: Optional[str] = None
    security_clearance: SecurityLevel = SecurityLevel.BASIC
    two_factor_auth: bool = False
    security_training_required: bool = True
    background_check_status: str = "pending"

class ITProvisioningRequest(BaseModel):
    """Solicitud de provisioning IT"""
    employee_id: str
    session_id: str
    
    # Datos del empleado (del Data Aggregator)
    personal_data: Dict[str, Any]
    position_data: Dict[str, Any]
    contractual_data: Dict[str, Any]
    
    # Especificaciones IT
    security_level: SecurityLevel = SecurityLevel.STANDARD
    equipment_specs: Dict[str, Any] = Field(default_factory=dict)
    special_requirements: List[str] = Field(default_factory=list)
    
    # Configuración
    priority: Priority = Priority.MEDIUM
    request_type: ITRequestType = ITRequestType.NEW_HIRE
    processing_deadline: Optional[datetime] = None

class ITProvisioningResult(BaseModel):
    """Resultado del provisioning IT"""
    success: bool
    employee_id: str
    session_id: str
    request_id: str = Field(default_factory=lambda: f"IT-REQ-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    
    # Resultados del provisioning
    credentials: Optional[ITCredentials] = None
    equipment: Optional[EquipmentAssignment] = None
    access_permissions: Optional[AccessPermissions] = None
    security_setup: Optional[SecuritySetup] = None
    
    # Metadatos
    processing_time: float = 0.0
    it_contact: str = "help@company.com"
    setup_instructions: List[str] = Field(default_factory=list)
    
    # Control de calidad
    credentials_created: int = 0
    equipment_assigned: int = 0
    permissions_granted: int = 0
    security_configured: bool = False
    
    # Estado y próximos pasos
    ready_for_contract: bool = False
    next_actions: List[str] = Field(default_factory=list)
    requires_manual_review: bool = False
    
    # Errores
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class ITDepartmentResponse(BaseModel):
    """Respuesta simulada del departamento IT"""
    request_id: str
    employee_id: str
    status: str = "completed"
    processing_time_minutes: float
    
    credentials: ITCredentials
    equipment: EquipmentAssignment
    access_permissions: AccessPermissions
    security_setup: SecuritySetup
    
    setup_instructions: List[str] = Field(default_factory=list)
    it_contact: str = "help@company.com"
    completion_notes: List[str] = Field(default_factory=list)

class ITRequestStatus(str, Enum):
    """Estados de solicitudes IT"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_APPROVAL = "requires_approval"

class ITSimulatorConfig(BaseModel):
    """Configuración del simulador IT"""
    response_delay_min: int = 120  # 2 minutos
    response_delay_max: int = 480  # 8 minutos
    failure_rate: float = 0.05  # 5% de fallos
    approval_required_rate: float = 0.10  # 10% requiere aprobación
    
    credential_templates: Dict[str, str] = Field(default_factory=dict)
    equipment_inventory: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    access_levels: Dict[str, List[str]] = Field(default_factory=dict)