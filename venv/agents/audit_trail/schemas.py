from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import uuid

class ComplianceStandard(str, Enum):
    """Estándares de compliance"""
    ISO_27001 = "iso_27001"
    SOX = "sox"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"

class AuditEventType(str, Enum):
    """Tipos de eventos auditables"""
    ERROR_CLASSIFIED = "error_classified"
    RECOVERY_ATTEMPTED = "recovery_attempted"
    HUMAN_HANDOFF_INITIATED = "human_handoff_initiated"
    DECISION_MADE = "decision_made"
    COMPLIANCE_CHECK = "compliance_check"
    DATA_ACCESS = "data_access"
    SYSTEM_STATE_CHANGE = "system_state_change"
    WORKFLOW_COMPLETED = "workflow_completed"
    ESCALATION_TRIGGERED = "escalation_triggered"

class AuditSeverity(str, Enum):
    """Severidad de eventos de auditoría"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ComplianceStatus(str, Enum):
    """Estado de compliance"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    PENDING_REVIEW = "pending_review"
    EXEMPTED = "exempted"

class AuditTrailRequest(BaseModel):
    """Request para audit trail"""
    session_id: str
    employee_id: str
    event_type: AuditEventType
    
    # Datos del evento
    event_data: Dict[str, Any] = Field(default_factory=dict)
    event_description: str = ""
    severity: AuditSeverity = AuditSeverity.INFO
    
    # Compliance requirements
    compliance_standards: List[ComplianceStandard] = Field(default_factory=list)
    require_full_traceability: bool = True
    
    # Context
    agent_id: Optional[str] = None
    workflow_stage: Optional[str] = None
    decision_points: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AuditEntry(BaseModel):
    """Entrada individual de audit trail"""
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    employee_id: str
    
    # Evento
    event_type: AuditEventType
    event_timestamp: datetime
    event_description: str
    severity: AuditSeverity
    
    # Contexto
    agent_id: Optional[str] = None
    workflow_stage: Optional[str] = None
    
    # Datos del evento
    event_data: Dict[str, Any] = Field(default_factory=dict)
    decision_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Compliance
    compliance_tags: List[str] = Field(default_factory=list)
    retention_period_days: int = 2555  # 7 años por defecto ISO 27001
    
    # Metadata
    created_by: str = "audit_trail_agent"
    checksum: Optional[str] = None  # Para integridad
    
class ComplianceReport(BaseModel):
    """Reporte de compliance"""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    employee_id: str
    
    # Compliance assessment
    compliance_standard: ComplianceStandard
    overall_status: ComplianceStatus
    compliance_score: float = Field(ge=0.0, le=100.0)
    
    # Detalles de compliance
    compliant_controls: List[str] = Field(default_factory=list)
    non_compliant_controls: List[str] = Field(default_factory=list)
    partial_controls: List[str] = Field(default_factory=list)
    
    # Gaps identificados
    compliance_gaps: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    # Risk assessment
    risk_level: str = "medium"
    risk_factors: List[str] = Field(default_factory=list)
    mitigation_actions: List[str] = Field(default_factory=list)
    
    # Timestamps
    assessment_date: datetime = Field(default_factory=datetime.utcnow)
    next_review_date: Optional[datetime] = None

class DecisionLog(BaseModel):
    """Log de decisiones para trazabilidad"""
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    employee_id: str
    
    # Decisión
    decision_point: str
    decision_made: str
    decision_rationale: str
    decision_maker: str  # agent_id o user_id
    
    # Contexto de la decisión
    available_options: List[str] = Field(default_factory=list)
    decision_criteria: Dict[str, Any] = Field(default_factory=dict)
    input_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Impacto
    expected_impact: str = ""
    actual_impact: Optional[str] = None
    success_criteria: List[str] = Field(default_factory=list)
    
    # Timestamps
    decision_timestamp: datetime = Field(default_factory=datetime.utcnow)
    impact_measured_at: Optional[datetime] = None

class AuditTrailResult(BaseModel):
    """Resultado de audit trail"""
    audit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    employee_id: str
    success: bool
    
    # Audit entries creadas
    audit_entries: List[AuditEntry] = Field(default_factory=list)
    decision_logs: List[DecisionLog] = Field(default_factory=list)
    compliance_reports: List[ComplianceReport] = Field(default_factory=list)
    
    # Métricas de auditoría
    total_events_logged: int = 0
    total_decisions_logged: int = 0
    compliance_score: float = 0.0
    traceability_completeness: float = 0.0
    
    # ISO 27001 specific metrics
    iso_27001_compliance: ComplianceStatus = ComplianceStatus.PENDING_REVIEW
    control_objectives_met: int = 0
    control_objectives_total: int = 0
    
    # Recommendations
    audit_recommendations: List[str] = Field(default_factory=list)
    compliance_improvements: List[str] = Field(default_factory=list)
    
    # Timestamps
    audit_started_at: datetime = Field(default_factory=datetime.utcnow)
    audit_completed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Errors during audit
    audit_errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class AuditConfiguration(BaseModel):
    """Configuración de auditoría"""
    config_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Retention policies
    default_retention_days: int = 2555  # 7 años
    critical_retention_days: int = 3650  # 10 años
    compliance_retention_days: int = 2555  # 7 años
    
    # Compliance standards activos
    active_standards: List[ComplianceStandard] = Field(default_factory=list)
    
    # Logging configuration
    log_all_decisions: bool = True
    log_data_access: bool = True
    log_system_changes: bool = True
    
    # ISO 27001 configuration
    iso_27001_enabled: bool = True
    control_framework_version: str = "2013"
    
    # Alerting
    compliance_alert_threshold: float = 70.0  # Alert if below 70%
    critical_event_immediate_alert: bool = True
    
    # Performance
    batch_size: int = 100
    async_processing: bool = True
    max_processing_time_seconds: int = 300