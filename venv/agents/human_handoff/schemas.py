from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import uuid

class EscalationLevel(str, Enum):
    """Niveles de escalación"""
    EMERGENCY = "emergency"      # <5 min
    CRITICAL = "critical"        # <15 min  
    HIGH = "high"               # <1 hour
    MEDIUM = "medium"           # <4 hours
    LOW = "low"                 # <24 hours

class HandoffStatus(str, Enum):
    """Estados del handoff"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    FAILED = "failed"

class SpecialistType(str, Enum):
    """Tipos de especialistas"""
    IT_SPECIALIST = "it_specialist"
    HR_MANAGER = "hr_manager"
    LEGAL_COUNSEL = "legal_counsel"
    SECURITY_ANALYST = "security_analyst"
    COMPLIANCE_OFFICER = "compliance_officer"
    DEPARTMENT_MANAGER = "department_manager"
    SYSTEM_ADMIN = "system_admin"
    CISO = "ciso"
    EXECUTIVE = "executive"

class NotificationChannel(str, Enum):
    """Canales de notificación"""
    SLACK = "slack"
    TEAMS = "teams"
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    DASHBOARD = "dashboard"

class EscalationDepartment(str, Enum):
    """Departamentos de escalación"""
    IT_DEPARTMENT = "it_department"
    HR_DEPARTMENT = "hr_department"
    LEGAL_DEPARTMENT = "legal_department"
    SECURITY_DEPARTMENT = "security_department"
    COMPLIANCE_DEPARTMENT = "compliance_department"
    MANAGEMENT = "management"
    EXECUTIVE_OFFICE = "executive_office"

class HandoffRequest(BaseModel):
    """Request para escalación humana"""
    session_id: str
    employee_id: str
    escalation_level: EscalationLevel
    error_classification: Dict[str, Any]
    recovery_attempts: Dict[str, Any]
    context_preservation_required: bool = True
    specialist_preferences: List[SpecialistType] = Field(default_factory=list)
    urgency_reason: Optional[str] = None
    business_impact: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SpecialistAssignment(BaseModel):
    """Asignación de especialista"""
    assignment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    specialist_type: SpecialistType
    department: EscalationDepartment
    specialist_name: str
    specialist_contact: str
    backup_specialist: Optional[str] = None
    estimated_response_time: int  # minutes
    sla_deadline: datetime
    assignment_reason: str
    assignment_timestamp: datetime = Field(default_factory=datetime.utcnow)

class ContextPackage(BaseModel):
    """Paquete completo de contexto para handoff"""
    package_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    employee_id: str
    
    # Contexto del empleado
    employee_context: Dict[str, Any]
    process_timeline: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Contexto del error
    error_summary: Dict[str, Any]
    recovery_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Estado del sistema
    agent_states: Dict[str, Any] = Field(default_factory=dict)
    pipeline_status: Dict[str, Any] = Field(default_factory=dict)
    
    # Documentación relevante
    relevant_documents: List[str] = Field(default_factory=list)
    configuration_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Contexto de negocio
    business_impact: str
    urgency_justification: str
    escalation_path: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

class EscalationTicket(BaseModel):
    """Ticket de escalación"""
    ticket_id: str = Field(default_factory=lambda: f"ESC-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}")
    session_id: str
    employee_id: str
    
    # Información básica
    title: str
    description: str
    escalation_level: EscalationLevel
    category: str
    
    # Asignación
    assigned_department: EscalationDepartment
    assigned_specialist: SpecialistAssignment
    
    # Estado y timing
    status: HandoffStatus = HandoffStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    sla_deadline: datetime
    
    # Contexto y resolución
    context_package_id: str
    resolution_notes: Optional[str] = None
    resolution_time: Optional[datetime] = None
    
    # Tracking
    status_updates: List[Dict[str, Any]] = Field(default_factory=list)
    escalation_history: List[Dict[str, Any]] = Field(default_factory=list)

class NotificationEvent(BaseModel):
    """Evento de notificación"""
    notification_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_id: str
    session_id: str
    
    # Destinatario y canal
    recipient: str
    channel: NotificationChannel
    specialist_type: SpecialistType
    
    # Contenido
    subject: str
    message: str
    priority_flag: bool = False
    
    # Estado de entrega
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    
    # Metadata
    template_used: str
    retry_count: int = 0
    max_retries: int = 3

class HandoffResult(BaseModel):
    """Resultado de escalación humana"""
    handoff_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    employee_id: str
    
    # Estado del handoff
    success: bool
    handoff_status: HandoffStatus
    
    # Asignaciones realizadas
    specialist_assignments: List[SpecialistAssignment] = Field(default_factory=list)
    
    # Contexto y comunicación
    context_package: ContextPackage
    tickets_created: List[EscalationTicket] = Field(default_factory=list)
    notifications_sent: List[NotificationEvent] = Field(default_factory=list)
    
    # Métricas y timing
    response_time_minutes: float
    estimated_resolution_time: Optional[int] = None  # minutes
    
    # Tracking y seguimiento
    tracking_dashboard_url: Optional[str] = None
    escalation_chain_active: bool = False
    
    # Próximos pasos
    immediate_actions_required: List[str] = Field(default_factory=list)
    monitoring_requirements: List[str] = Field(default_factory=list)
    
    # Metadatos
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow)
    handoff_agent_id: str = "human_handoff_agent"
    
    # Integración con otros sistemas
    external_ticket_refs: Dict[str, str] = Field(default_factory=dict)  # JIRA, ServiceNow, etc.
    audit_trail_refs: List[str] = Field(default_factory=list)

# Configuraciones del sistema
class SpecialistDirectory(BaseModel):
    """Directorio de especialistas"""
    it_specialists: List[Dict[str, str]] = Field(default_factory=list)
    hr_managers: List[Dict[str, str]] = Field(default_factory=list)
    legal_counsel: List[Dict[str, str]] = Field(default_factory=list)
    security_analysts: List[Dict[str, str]] = Field(default_factory=list)
    compliance_officers: List[Dict[str, str]] = Field(default_factory=list)
    executives: List[Dict[str, str]] = Field(default_factory=list)

class EscalationRules(BaseModel):
    """Reglas de escalación automática"""
    error_category_routing: Dict[str, List[SpecialistType]] = Field(default_factory=dict)
    severity_sla_mapping: Dict[EscalationLevel, int] = Field(default_factory=dict)  # minutes
    department_fallbacks: Dict[EscalationDepartment, EscalationDepartment] = Field(default_factory=dict)
    after_hours_routing: Dict[str, str] = Field(default_factory=dict)
    emergency_contacts: List[str] = Field(default_factory=list)