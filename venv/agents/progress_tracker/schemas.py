from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
from shared.models import Priority

class PipelineStage(str, Enum):
    """Etapas del pipeline de onboarding"""
    DATA_COLLECTION = "data_collection"
    DATA_AGGREGATION = "data_aggregation"
    IT_PROVISIONING = "it_provisioning"
    CONTRACT_MANAGEMENT = "contract_management"
    MEETING_COORDINATION = "meeting_coordination"
    ONBOARDING_EXECUTION = "onboarding_execution"
    COMPLETED = "completed"

class AgentStatus(str, Enum):
    """Estados de agentes en el pipeline"""
    WAITING = "waiting"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ESCALATED = "escalated"

class QualityGateStatus(str, Enum):
    """Estados de quality gates"""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    BYPASS = "bypass"
    MANUAL_REVIEW = "manual_review"

class SLAStatus(str, Enum):
    """Estados de SLA"""
    ON_TIME = "on_time"
    AT_RISK = "at_risk"
    BREACHED = "breached"
    EXTENDED = "extended"

class EscalationLevel(str, Enum):
    """Niveles de escalación"""
    NONE = "none"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class EscalationType(str, Enum):
    """Tipos de escalación"""
    SLA_BREACH = "sla_breach"
    QUALITY_FAILURE = "quality_failure"
    AGENT_FAILURE = "agent_failure"
    SYSTEM_ERROR = "system_error"
    MANUAL_INTERVENTION = "manual_intervention"

class StepCompletionMetrics(BaseModel):
    """Métricas de completitud de pasos"""
    step_id: str
    agent_id: str
    stage: PipelineStage
    status: AgentStatus
    
    # Timing metrics
    started_at: datetime
    completed_at: Optional[datetime] = None
    processing_duration: Optional[float] = None  # seconds
    
    # Progress metrics
    progress_percentage: float = Field(ge=0.0, le=100.0, default=0.0)
    subtasks_completed: int = 0
    subtasks_total: int = 0
    
    # Quality metrics
    success_indicators: Dict[str, bool] = Field(default_factory=dict)
    error_count: int = 0
    retry_count: int = 0
    
    # Output validation
    output_validated: bool = False
    output_quality_score: float = Field(ge=0.0, le=100.0, default=0.0)

class QualityGate(BaseModel):
    """Configuración de quality gate"""
    gate_id: str
    stage: PipelineStage
    gate_name: str
    description: str
    
    # Validation criteria
    required_fields: List[str] = Field(default_factory=list)
    quality_thresholds: Dict[str, float] = Field(default_factory=dict)
    validation_rules: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Gate configuration
    is_mandatory: bool = True
    can_bypass: bool = False
    bypass_authorization_level: str = "manager"
    
    # Failure handling
    failure_action: str = "block"  # block, warning, escalate
    retry_allowed: bool = True
    max_retries: int = 3

class QualityGateResult(BaseModel):
    """Resultado de evaluación de quality gate"""
    gate_id: str
    employee_id: str
    session_id: str
    stage: PipelineStage
    
    # Evaluation results
    status: QualityGateStatus
    overall_score: float = Field(ge=0.0, le=100.0)
    passed: bool = False
    
    # Detailed results
    field_validations: Dict[str, bool] = Field(default_factory=dict)
    threshold_checks: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    rule_evaluations: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Issues and recommendations
    critical_issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    # Metadata
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    evaluator: str = "progress_tracker_agent"
    bypass_reason: Optional[str] = None

class SLAConfiguration(BaseModel):
    """Configuración de SLA por agente/stage"""
    sla_id: str
    stage: PipelineStage
    agent_id: str
    
    # Time limits
    target_duration_minutes: int
    warning_threshold_minutes: int
    critical_threshold_minutes: int
    breach_threshold_minutes: int
    
    # Business rules
    business_hours_only: bool = True
    exclude_weekends: bool = True
    timezone: str = "America/Costa_Rica"
    
    # Escalation configuration
    auto_escalate_on_warning: bool = False
    auto_escalate_on_critical: bool = True
    escalation_contacts: List[str] = Field(default_factory=list)
    
    # Flexibility
    extension_allowed: bool = True
    max_extensions: int = 2
    extension_duration_minutes: int = 30

class SLAMonitoringResult(BaseModel):
    """Resultado de monitoreo de SLA"""
    sla_id: str
    employee_id: str
    session_id: str
    stage: PipelineStage
    agent_id: str
    
    # Current status
    status: SLAStatus
    elapsed_time_minutes: float
    remaining_time_minutes: float
    
    # Threshold analysis
    within_target: bool
    within_warning: bool
    within_critical: bool
    is_breached: bool
    
    # Timing details
    started_at: datetime
    target_completion: datetime
    warning_threshold_time: datetime
    critical_threshold_time: datetime
    breach_time: datetime
    
    # Extensions
    extensions_used: int = 0
    extension_time_added: int = 0
    
    # Predictions
    predicted_completion: Optional[datetime] = None
    breach_probability: float = Field(ge=0.0, le=1.0, default=0.0)
    
    # Metadata
    monitored_at: datetime = Field(default_factory=datetime.utcnow)

class EscalationRule(BaseModel):
    """Regla de escalación automática"""
    rule_id: str
    rule_name: str
    escalation_type: EscalationType
    escalation_level: EscalationLevel
    
    # Trigger conditions
    trigger_conditions: Dict[str, Any] = Field(default_factory=dict)
    
    # Actions
    notification_recipients: List[str] = Field(default_factory=list)
    automatic_actions: List[str] = Field(default_factory=list)
    escalation_message_template: str = ""
    
    # Configuration
    cooldown_minutes: int = 30  # Prevent spam
    max_escalations_per_session: int = 5
    requires_acknowledgment: bool = True

class EscalationEvent(BaseModel):
    """Evento de escalación"""
    escalation_id: str = Field(default_factory=lambda: f"ESC-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    employee_id: str
    session_id: str
    stage: PipelineStage
    
    # Escalation details
    escalation_type: EscalationType
    escalation_level: EscalationLevel
    triggered_by: str  # rule_id or manual
    
    # Context
    trigger_reason: str
    affected_agent: str
    current_metrics: Dict[str, Any] = Field(default_factory=dict)
    
    # Actions taken
    notifications_sent: List[str] = Field(default_factory=list)
    automatic_actions_executed: List[str] = Field(default_factory=list)
    
    # Status tracking
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    escalation_message: str = ""

class PipelineProgressSnapshot(BaseModel):
    """Snapshot completo del progreso del pipeline"""
    snapshot_id: str = Field(default_factory=lambda: f"SNAP-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    employee_id: str
    session_id: str
    
    # Overall progress
    current_stage: PipelineStage
    overall_progress_percentage: float = Field(ge=0.0, le=100.0)
    estimated_completion_time: Optional[datetime] = None
    
    # Stage progress
    stage_metrics: Dict[PipelineStage, StepCompletionMetrics] = Field(default_factory=dict)
    
    # Quality status
    quality_gates_passed: int = 0
    quality_gates_total: int = 0
    overall_quality_score: float = Field(ge=0.0, le=100.0, default=0.0)
    
    # SLA status
    sla_compliance_percentage: float = Field(ge=0.0, le=100.0, default=100.0)
    stages_on_time: int = 0
    stages_at_risk: int = 0
    stages_breached: int = 0
    
    # Issues and escalations
    active_escalations: int = 0
    critical_issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Predictions
    success_probability: float = Field(ge=0.0, le=1.0, default=1.0)
    risk_factors: List[str] = Field(default_factory=list)
    
    # Metadata
    captured_at: datetime = Field(default_factory=datetime.utcnow)

class ProgressTrackerRequest(BaseModel):
    """Solicitud de monitoreo de progreso"""
    employee_id: str
    session_id: str
    monitoring_scope: str = "full_pipeline"  # full_pipeline, current_stage, specific_agent
    
    # Monitoring configuration
    include_quality_gates: bool = True
    include_sla_monitoring: bool = True
    include_escalation_check: bool = True
    
    # Specific monitoring targets
    target_stages: List[PipelineStage] = Field(default_factory=list)
    target_agents: List[str] = Field(default_factory=list)
    
    # Reporting preferences
    detailed_metrics: bool = True
    include_predictions: bool = True
    include_recommendations: bool = True

class ProgressTrackerResult(BaseModel):
    """Resultado del Progress Tracker Agent"""
    success: bool
    employee_id: str
    session_id: str
    tracker_id: str = Field(default_factory=lambda: f"TRACK-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    
    # Main results
    progress_snapshot: Optional[PipelineProgressSnapshot] = None
    quality_gate_results: List[QualityGateResult] = Field(default_factory=list)
    sla_monitoring_results: List[SLAMonitoringResult] = Field(default_factory=list)
    escalation_events: List[EscalationEvent] = Field(default_factory=list)
    
    # Summary metrics
    pipeline_health_score: float = Field(ge=0.0, le=100.0, default=100.0)
    completion_confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    estimated_time_remaining_minutes: Optional[float] = None
    
    # Status indicators
    pipeline_blocked: bool = False
    requires_manual_intervention: bool = False
    escalation_required: bool = False
    
    # Actionable insights
    immediate_actions_required: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    risk_mitigation_suggestions: List[str] = Field(default_factory=list)
    
    # Processing metadata
    processing_time: float = 0.0
    monitoring_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Error handling
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

# Default configurations
DEFAULT_QUALITY_GATES = {
    PipelineStage.DATA_AGGREGATION: QualityGate(
        gate_id="data_aggregation_gate",
        stage=PipelineStage.DATA_AGGREGATION,
        gate_name="Data Quality Gate",
        description="Validates consolidated data quality before sequential pipeline",
        required_fields=["employee_id", "personal_data", "position_data", "contractual_data"],
        quality_thresholds={
            "overall_quality_score": 70.0,
            "completeness_score": 80.0,
            "consistency_score": 85.0
        },
        is_mandatory=True,
        can_bypass=False
    ),
    PipelineStage.IT_PROVISIONING: QualityGate(
        gate_id="it_provisioning_gate", 
        stage=PipelineStage.IT_PROVISIONING,
        gate_name="IT Setup Quality Gate",
        description="Validates IT credentials and system access before contract management",
        required_fields=["credentials_created", "system_access_granted", "equipment_assigned"],
        quality_thresholds={
            "provisioning_success_rate": 90.0,
            "security_compliance_score": 95.0
        },
        is_mandatory=True,
        can_bypass=True,
        bypass_authorization_level="it_manager"
    ),
    PipelineStage.CONTRACT_MANAGEMENT: QualityGate(
        gate_id="contract_management_gate",
        stage=PipelineStage.CONTRACT_MANAGEMENT,
        gate_name="Contract Legal Gate",
        description="Validates contract generation and legal compliance",
        required_fields=["contract_generated", "legal_validation_passed", "signature_completed"],
        quality_thresholds={
            "compliance_score": 90.0,
            "legal_validation_score": 95.0
        },
        is_mandatory=True,
        can_bypass=False
    ),
    PipelineStage.MEETING_COORDINATION: QualityGate(
        gate_id="meeting_coordination_gate",
        stage=PipelineStage.MEETING_COORDINATION,
        gate_name="Meeting Setup Gate",
        description="Validates meeting scheduling and stakeholder engagement",
        required_fields=["stakeholders_engaged", "meetings_scheduled", "calendar_integration_active"],
        quality_thresholds={
            "stakeholder_engagement_score": 80.0,
            "scheduling_efficiency_score": 75.0
        },
        is_mandatory=True,
        can_bypass=True,
        bypass_authorization_level="hr_manager"
    )
}

DEFAULT_SLA_CONFIGURATIONS = {
    PipelineStage.DATA_AGGREGATION: SLAConfiguration(
        sla_id="data_aggregation_sla",
        stage=PipelineStage.DATA_AGGREGATION,
        agent_id="data_aggregator_agent",
        target_duration_minutes=5,
        warning_threshold_minutes=4,
        critical_threshold_minutes=6,
        breach_threshold_minutes=8
    ),
    PipelineStage.IT_PROVISIONING: SLAConfiguration(
        sla_id="it_provisioning_sla",
        stage=PipelineStage.IT_PROVISIONING,
        agent_id="it_provisioning_agent",
        target_duration_minutes=10,
        warning_threshold_minutes=8,
        critical_threshold_minutes=12,
        breach_threshold_minutes=15
    ),
    PipelineStage.CONTRACT_MANAGEMENT: SLAConfiguration(
        sla_id="contract_management_sla", 
        stage=PipelineStage.CONTRACT_MANAGEMENT,
        agent_id="contract_management_agent",
        target_duration_minutes=15,
        warning_threshold_minutes=12,
        critical_threshold_minutes=18,
        breach_threshold_minutes=20
    ),
    PipelineStage.MEETING_COORDINATION: SLAConfiguration(
        sla_id="meeting_coordination_sla",
        stage=PipelineStage.MEETING_COORDINATION, 
        agent_id="meeting_coordination_agent",
        target_duration_minutes=8,
        warning_threshold_minutes=6,
        critical_threshold_minutes=10,
        breach_threshold_minutes=12
    )
}

DEFAULT_ESCALATION_RULES = [
    EscalationRule(
        rule_id="sla_breach_critical",
        rule_name="Critical SLA Breach",
        escalation_type=EscalationType.SLA_BREACH,
        escalation_level=EscalationLevel.CRITICAL,
        trigger_conditions={"sla_status": "breached", "stage_criticality": "high"},
        notification_recipients=["hr_manager@company.com", "it_manager@company.com"],
        automatic_actions=["pause_pipeline", "create_incident_ticket"],
        escalation_message_template="CRITICAL: SLA breach detected for {employee_id} in {stage}. Immediate attention required."
    ),
    EscalationRule(
        rule_id="quality_gate_failure",
        rule_name="Quality Gate Failure",
        escalation_type=EscalationType.QUALITY_FAILURE,
        escalation_level=EscalationLevel.WARNING,
        trigger_conditions={"quality_gate_status": "failed", "retry_attempts": 3},
        notification_recipients=["team_lead@company.com", "hr_coordinator@company.com"],
        automatic_actions=["flag_for_manual_review"],
        escalation_message_template="Quality gate failure for {employee_id}. Manual review required."
    ),
    EscalationRule(
        rule_id="agent_failure_recovery",
        rule_name="Agent Failure Recovery",
        escalation_type=EscalationType.AGENT_FAILURE,
        escalation_level=EscalationLevel.CRITICAL,
        trigger_conditions={"agent_status": "failed", "error_count": 3},
        notification_recipients=["system_admin@company.com", "devops_team@company.com"],
        automatic_actions=["restart_agent", "create_support_ticket"],
        escalation_message_template="Agent failure detected: {agent_id}. System intervention required."
    )
]