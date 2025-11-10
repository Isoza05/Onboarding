from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import uuid

class HandoffPriority(str, Enum):
    """Prioridad de handoff"""
    EMERGENCY = "emergency"      # <5 min
    CRITICAL = "critical"        # <15 min  
    HIGH = "high"               # <1 hour
    MEDIUM = "medium"           # <4 hours
    LOW = "low"                 # <24 hours

class HandoffStatus(str, Enum):
    """Estados de handoff"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"

class SpecialistType(str, Enum):
    """Tipos de especialistas"""
    IT_SPECIALIST = "it_specialist"
    HR_MANAGER = "hr_manager"
    LEGAL_SPECIALIST = "legal_specialist"
    SECURITY_SPECIALIST = "security_specialist"
    COMPLIANCE_OFFICER = "compliance_officer"
    SYSTEM_ADMIN = "system_admin"
    BUSINESS_ANALYST = "business_analyst"
    EXECUTIVE = "executive"

class NotificationChannel(str, Enum):
    """Canales de notificación"""
    SLACK = "slack"
    TEAMS = "teams"
    EMAIL = "email"
    SMS = "sms"
    DASHBOARD = "dashboard"
    WEBHOOK = "webhook"

class HandoffRequest(BaseModel):
    """Request para handoff a especialista humano"""
    session_id: str
    employee_id: str
    handoff_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Origen del handoff
    source_agent: str  # error_classification_agent, recovery_agent, etc.
    source_request_id: str  # classification_id, recovery_id, etc.
    
    # Clasificación del problema
    error_category: str
    error_severity: str
    handoff_priority: HandoffPriority
    
    # Context preservation
    error_context: Dict[str, Any] = Field(default_factory=dict)
    recovery_attempts: List[Dict[str, Any]] = Field(default_factory=list)
    employee_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Routing preferences
    preferred_specialist_type: Optional[SpecialistType] = None
    department_routing: Optional[str] = None
    escalation_level: int = 1  # 1-4
    
    # Urgency and SLA
    requires_immediate_attention: bool = False
    sla_deadline: Optional[datetime] = None
    business_impact: str = "medium"
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    handoff_deadline: Optional[datetime] = None

class SpecialistProfile(BaseModel):
    """Perfil de especialista"""
    specialist_id: str
    name: str
    specialist_type: SpecialistType
    department: str
    
    # Availability
    is_available: bool = True
    current_workload: int = 0  # Number of active cases
    max_concurrent_cases: int = 5
    
    # Capabilities
    expertise_areas: List[str] = Field(default_factory=list)
    handling_categories: List[str] = Field(default_factory=list)
    priority_levels: List[HandoffPriority] = Field(default_factory=list)
    
    # Contact info
    email: str
    slack_id: Optional[str] = None
    teams_id: Optional[str] = None
    phone: Optional[str] = None
    
    # Performance metrics
    average_resolution_time_hours: float = 24.0
    success_rate: float = 0.95
    customer_satisfaction: float = 4.5
    
    # Schedule
    business_hours_start: str = "09:00"
    business_hours_end: str = "17:00"
    timezone: str = "UTC"
    available_weekends: bool = False

class SpecialistAssignment(BaseModel):
    """Asignación de especialista"""
    assignment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    handoff_id: str
    
    # Specialist info
    assigned_specialist: SpecialistProfile
    assignment_method: str  # "automatic", "manual", "escalated"
    assignment_confidence: float = 0.0
    
    # Assignment details
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    assignment_reason: str
    expected_resolution_time: Optional[datetime] = None
    
    # Status tracking
    specialist_notified: bool = False
    specialist_acknowledged: bool = False
    work_started_at: Optional[datetime] = None
    
    # Backup assignments
    backup_specialists: List[SpecialistProfile] = Field(default_factory=list)
    escalation_chain: List[str] = Field(default_factory=list)

class ContextPackage(BaseModel):
    """Paquete de contexto para handoff"""
    package_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    handoff_id: str
    
    # Employee context
    employee_data: Dict[str, Any] = Field(default_factory=dict)
    employee_journey: List[Dict[str, Any]] = Field(default_factory=list)
    current_pipeline_stage: str
    
    # Error context
    error_timeline: List[Dict[str, Any]] = Field(default_factory=list)
    failed_operations: List[Dict[str, Any]] = Field(default_factory=list)
    recovery_attempts_log: List[Dict[str, Any]] = Field(default_factory=list)
    
    # System context
    system_state_snapshot: Dict[str, Any] = Field(default_factory=dict)
    agent_states: Dict[str, str] = Field(default_factory=dict)
    configuration_snapshot: Dict[str, Any] = Field(default_factory=dict)
    
    # Business context
    business_impact_assessment: Dict[str, Any] = Field(default_factory=dict)
    sla_status: Dict[str, Any] = Field(default_factory=dict)
    stakeholder_impact: List[str] = Field(default_factory=list)
    
    # Documentation
    relevant_documents: List[Dict[str, Any]] = Field(default_factory=list)
    screenshots: List[str] = Field(default_factory=list)
    logs_extract: List[str] = Field(default_factory=list)
    
    # Recommendations
    suggested_actions: List[str] = Field(default_factory=list)
    escalation_recommendations: List[str] = Field(default_factory=list)
    
    # Package metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    package_completeness: float = 0.0  # 0-1
    critical_info_missing: List[str] = Field(default_factory=list)

class EscalationTicket(BaseModel):
    """Ticket de escalación"""
    ticket_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    handoff_id: str
    
    # Ticket details
    title: str
    description: str
    category: str
    priority: HandoffPriority
    severity: str
    
    # Assignment
    assigned_to: str
    assigned_team: str
    created_by: str = "human_handoff_agent"
    
    # Status
    status: str = "open"
    resolution: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    
    # Context
    context_package_id: str
    employee_id: str
    session_id: str
    
    # Tracking
    time_to_assignment_minutes: Optional[float] = None
    time_to_resolution_minutes: Optional[float] = None
    escalation_count: int = 0
    
    # Communication
    comments: List[Dict[str, Any]] = Field(default_factory=list)
    attachments: List[str] = Field(default_factory=list)
    
    # SLA tracking
    sla_target_hours: float = 24.0
    sla_breach: bool = False
    sla_warning_sent: bool = False

class NotificationEvent(BaseModel):
    """Evento de notificación"""
    notification_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    handoff_id: str
    
    # Notification details
    notification_type: str  # "assignment", "escalation", "resolution", etc.
    channel: NotificationChannel
    recipient: str
    recipient_type: str  # "individual", "team", "group"
    
    # Message
    subject: str
    message: str
    template_used: Optional[str] = None
    
    # Delivery
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    
    # Status
    status: str = "pending"  # pending, sent, delivered, failed, acknowledged
    delivery_attempts: int = 0
    last_attempt_at: Optional[datetime] = None
    
    # Metadata
    priority: HandoffPriority = HandoffPriority.MEDIUM
    requires_acknowledgment: bool = False
    expires_at: Optional[datetime] = None
    
    # Response tracking
    response_required: bool = False
    response_deadline: Optional[datetime] = None
    response_received_at: Optional[datetime] = None
    response_data: Dict[str, Any] = Field(default_factory=dict)

class HandoffResult(BaseModel):
    """Resultado de handoff"""
    handoff_id: str
    session_id: str
    employee_id: str
    
    # Final status
    final_status: HandoffStatus
    success: bool
    handoff_completed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Assignment results
    specialist_assignment: Optional[SpecialistAssignment] = None
    context_package: Optional[ContextPackage] = None
    escalation_ticket: Optional[EscalationTicket] = None
    
    # Notifications sent
    notifications_sent: List[NotificationEvent] = Field(default_factory=list)
    successful_notifications: int = 0
    failed_notifications: int = 0
    
    # Handoff metrics
    time_to_assignment_minutes: Optional[float] = None
    context_preservation_score: float = 0.0
    handoff_quality_score: float = 0.0
    
    # Resolution tracking
    specialist_response_time: Optional[float] = None
    issue_resolution_status: str = "pending"
    resolution_provided: Optional[str] = None
    
    # Follow-up
    follow_up_required: bool = False
    follow_up_scheduled: Optional[datetime] = None
    next_check_in: Optional[datetime] = None
    
    # Escalation path
    escalation_path_clear: bool = True
    escalation_instructions: List[str] = Field(default_factory=list)
    backup_contacts: List[str] = Field(default_factory=list)
    
    # Business impact
    business_continuity_maintained: bool = False
    customer_impact_minimized: bool = False
    sla_compliance_status: str = "unknown"
    
    # Lessons learned
    handoff_effectiveness: str = "unknown"
    improvement_suggestions: List[str] = Field(default_factory=list)
    process_gaps_identified: List[str] = Field(default_factory=list)
    
    # Audit trail
    handoff_timeline: List[Dict[str, Any]] = Field(default_factory=list)
    communication_log: List[Dict[str, Any]] = Field(default_factory=list)
    decision_log: List[Dict[str, Any]] = Field(default_factory=list)

class HandoffConfiguration(BaseModel):
    """Configuración de handoff"""
    config_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Response time SLAs by priority
    emergency_response_minutes: int = 5
    critical_response_minutes: int = 15
    high_response_minutes: int = 60
    medium_response_hours: int = 4
    low_response_hours: int = 24
    
    # Escalation timeouts
    specialist_response_timeout_minutes: int = 30
    escalation_interval_minutes: int = 60
    max_escalation_levels: int = 4
    
    # Routing configuration
    auto_assignment_enabled: bool = True
    load_balancing_enabled: bool = True
    backup_assignment_enabled: bool = True
    
    # Notification configuration
    default_notification_channels: List[NotificationChannel] = Field(
        default_factory=lambda: [NotificationChannel.SLACK, NotificationChannel.EMAIL]
    )
    notification_retry_attempts: int = 3
    notification_retry_interval_minutes: int = 5
    
    # Business hours
    business_hours_start: str = "09:00"
    business_hours_end: str = "17:00" 
    business_timezone: str = "UTC"
    weekend_support_available: bool = False
    
    # Context preservation
    context_package_completeness_threshold: float = 0.8
    max_context_package_size_mb: int = 50
    context_retention_days: int = 90
    
    # Quality assurance
    handoff_quality_threshold: float = 0.8
    specialist_performance_tracking: bool = True
    customer_satisfaction_tracking: bool = True