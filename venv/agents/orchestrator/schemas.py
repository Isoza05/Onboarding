from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
from shared.models import Priority

class OrchestrationPattern(str, Enum):
    """Patrones de orquestación disponibles"""
    CONCURRENT_DATA_COLLECTION = "concurrent_data_collection"
    SEQUENTIAL_PROCESSING = "sequential_processing"
    ERROR_RECOVERY = "error_recovery"
    ESCALATION_HANDOFF = "escalation_handoff"

class AgentType(str, Enum):
    """Tipos de agentes en el sistema"""
    INITIAL_DATA_COLLECTION = "initial_data_collection_agent"
    CONFIRMATION_DATA = "confirmation_data_agent"
    DOCUMENTATION = "documentation_agent"
    IT_PROVISIONING = "it_provisioning_agent"
    CONTRACT_MANAGEMENT = "contract_management_agent"
    MEETING_COORDINATION = "meeting_coordination_agent"
    # ✅ AGREGAR AGENTES ERROR HANDLING
    ERROR_CLASSIFICATION = "error_classification_agent"
    RECOVERY_AGENT = "recovery_agent"
    HUMAN_HANDOFF = "human_handoff_agent"
    AUDIT_TRAIL = "audit_trail_agent"

class TaskStatus(str, Enum):
    """Estados de tareas"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"

class OrchestrationPhase(str, Enum):
    """Fases de orquestración"""
    INITIATED = "initiated"
    DATA_COLLECTION_CONCURRENT = "data_collection_concurrent"
    DATA_AGGREGATION = "data_aggregation"
    SEQUENTIAL_PROCESSING = "sequential_processing"
    FINALIZATION = "finalization"
    ERROR_HANDLING = "error_handling"
    # ✅ AGREGAR FASES ERROR HANDLING
    ERROR_CLASSIFICATION = "error_classification"
    ERROR_RECOVERY = "error_recovery"
    HUMAN_ESCALATION = "human_escalation"
    AUDIT_CONSOLIDATION = "audit_consolidation"

# ✅ NUEVOS SCHEMAS PARA ERROR HANDLING INTEGRATION
class ErrorHandlingTrigger(BaseModel):
    """Trigger que activó Error Handling"""
    trigger_type: str
    trigger_condition: str
    trigger_value: Any
    threshold: Optional[Any] = None
    description: str

class ErrorHandlingResult(BaseModel):
    """Resultado consolidado de Error Handling"""
    error_handling_executed: bool = False
    error_handling_success: bool = False
    
    # Results de cada fase
    classification_result: Optional[Dict[str, Any]] = None
    recovery_result: Optional[Dict[str, Any]] = None
    handoff_result: Optional[Dict[str, Any]] = None
    audit_result: Optional[Dict[str, Any]] = None
    
    # Summary
    phases_executed: List[str] = Field(default_factory=list)
    final_resolution: Optional[str] = None
    specialist_assigned: Optional[str] = None
    
    # Metrics
    total_processing_time: float = 0.0
    error_handling_quality_score: float = 0.0
    
    # Triggers que activaron Error Handling
    triggers: List[ErrorHandlingTrigger] = Field(default_factory=list)

class AgentTaskAssignment(BaseModel):
    """Asignación de tarea a un agente específico"""
    task_id: str
    agent_type: AgentType
    agent_id: str
    task_description: str
    input_data: Dict[str, Any]
    priority: Priority = Priority.MEDIUM
    dependencies: List[str] = Field(default_factory=list)
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    expected_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # ✅ AGREGAR CAMPOS ERROR HANDLING
    error_handling_triggered: bool = False
    error_handling_result: Optional[ErrorHandlingResult] = None

class WorkflowStep(BaseModel):
    """Paso individual del workflow"""
    step_id: str
    step_name: str
    agent_assignments: List[AgentTaskAssignment] = Field(default_factory=list)
    is_concurrent: bool = False
    completion_criteria: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    
    # ✅ AGREGAR ERROR HANDLING AL WORKFLOW STEP
    error_handling_enabled: bool = True
    error_handling_result: Optional[ErrorHandlingResult] = None

class OrchestrationRequest(BaseModel):
    """Solicitud completa de orquestación de onboarding"""
    employee_id: str
    session_id: Optional[str] = None
    
    # Datos del nuevo empleado
    employee_data: Dict[str, Any]
    contract_data: Dict[str, Any]
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Configuración de orquestración
    orchestration_pattern: OrchestrationPattern = OrchestrationPattern.CONCURRENT_DATA_COLLECTION
    priority: Priority = Priority.MEDIUM
    special_requirements: List[str] = Field(default_factory=list)
    deadline: Optional[datetime] = None
    
    # Configuración de agentes
    required_agents: List[AgentType] = Field(default_factory=list)
    agent_config: Dict[str, Any] = Field(default_factory=dict)
    
    # ✅ CONFIGURACIÓN ERROR HANDLING
    error_handling_config: Dict[str, Any] = Field(default_factory=dict)
    enable_auto_recovery: bool = True
    enable_human_escalation: bool = True
    enable_audit_trail: bool = True
    error_tolerance_level: str = "standard"  # "low", "standard", "high"

    @validator('required_agents')
    def validate_required_agents(cls, v):
        if not v:
            return [
                AgentType.INITIAL_DATA_COLLECTION,
                AgentType.CONFIRMATION_DATA, 
                AgentType.DOCUMENTATION
            ]
        return v

class OrchestrationState(BaseModel):
    """Estado completo de la orquestración"""
    orchestration_id: str
    session_id: str
    employee_id: str
    
    # Estado del workflow
    current_phase: OrchestrationPhase = OrchestrationPhase.INITIATED
    workflow_steps: List[WorkflowStep] = Field(default_factory=list)
    
    # Progreso general
    overall_progress: float = 0.0
    steps_completed: int = 0
    steps_total: int = 0
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    
    # Resultados consolidados
    agent_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    consolidated_data: Dict[str, Any] = Field(default_factory=dict)
    validation_results: Dict[str, Any] = Field(default_factory=dict)
    
    # Control de errores
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    requires_manual_intervention: bool = False
    escalation_level: int = 0
    
    # ✅ ESTADO ERROR HANDLING
    error_handling_active: bool = False
    error_handling_history: List[ErrorHandlingResult] = Field(default_factory=list)
    current_error_handling: Optional[ErrorHandlingResult] = None
    
    # Métricas
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)

class PatternSelectionCriteria(BaseModel):
    """Criterios para selección de patrón de orquestración"""
    employee_type: str
    position_level: str
    department: str
    location: str
    priority: Priority
    special_requirements: List[str] = Field(default_factory=list)
    compliance_level: str = "standard"
    
    # ✅ CRITERIOS ERROR HANDLING
    error_tolerance: str = "standard"  # "low", "standard", "high"
    auto_recovery_enabled: bool = True
    escalation_threshold: float = 30.0  # Quality score threshold

class OrchestrationResult(BaseModel):
    """Resultado final de la orquestración"""
    orchestration_id: str
    session_id: str
    employee_id: str
    
    # Estado final
    success: bool
    completion_status: str
    final_phase: OrchestrationPhase
    
    # Resultados por agente
    agent_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    consolidated_employee_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Métricas finales
    total_processing_time: float
    agents_executed: int
    tasks_completed: int
    tasks_failed: int
    overall_quality_score: float = Field(ge=0.0, le=100.0)
    
    # Próximos pasos
    next_steps: List[str] = Field(default_factory=list)
    requires_followup: bool = False
    escalation_needed: bool = False
    
    # Documentación generada
    generated_documents: List[str] = Field(default_factory=list)
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)
    
    # ✅ RESULTADOS ERROR HANDLING
    error_handling_executed: bool = False
    error_handling_results: List[ErrorHandlingResult] = Field(default_factory=list)
    final_error_handling_status: Optional[str] = None
    specialist_interventions: List[str] = Field(default_factory=list)
    
    # Timestamps
    started_at: datetime
    completed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ProgressMetrics(BaseModel):
    """Métricas de progreso para monitoring"""
    current_step: str
    steps_completed: int
    steps_total: int
    progress_percentage: float = Field(ge=0.0, le=100.0)
    estimated_time_remaining: Optional[int] = None
    quality_gates_passed: int = 0
    quality_gates_total: int = 0
    sla_status: str = "on_track"
    
    # ✅ MÉTRICAS ERROR HANDLING
    error_handling_interventions: int = 0
    recovery_attempts: int = 0
    escalations_triggered: int = 0

class TaskDistributionStrategy(BaseModel):
    """Estrategia para distribución de tareas"""
    strategy_type: str = "concurrent"
    max_concurrent_agents: int = 3
    priority_weights: Dict[str, float] = Field(default_factory=dict)
    dependency_rules: Dict[str, List[str]] = Field(default_factory=dict)
    timeout_settings: Dict[str, int] = Field(default_factory=dict)
    retry_policies: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # ✅ ESTRATEGIAS ERROR HANDLING
    error_handling_strategy: str = "immediate"  # "immediate", "batched", "end_of_workflow"
    auto_recovery_max_attempts: int = 3
    escalation_delay_minutes: int = 5

class SequentialPipelinePhase(str, Enum):
    """Fases específicas del Sequential Pipeline"""
    PIPELINE_INITIATED = "pipeline_initiated"
    IT_PROVISIONING = "it_provisioning"
    CONTRACT_MANAGEMENT = "contract_management"
    MEETING_COORDINATION = "meeting_coordination"
    PIPELINE_COMPLETED = "pipeline_completed"
    # ✅ AGREGAR FASE ERROR HANDLING
    PIPELINE_ERROR_HANDLING = "pipeline_error_handling"

class PipelineAgentResult(BaseModel):
    """Resultado estándar de agente del pipeline secuencial"""
    agent_id: str
    employee_id: str
    session_id: str
    success: bool
    processing_time: float
    
    # Agent-specific data
    agent_output: Dict[str, Any] = Field(default_factory=dict)
    next_agent_input: Dict[str, Any] = Field(default_factory=dict)
    
    # Quality and validation
    quality_score: float = Field(ge=0.0, le=100.0, default=0.0)
    validation_passed: bool = False
    ready_for_next_stage: bool = False
    
    # Error handling
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    requires_manual_review: bool = False
    
    # ✅ ERROR HANDLING ESPECÍFICO DEL AGENTE
    error_handling_triggered: bool = False
    error_handling_result: Optional[Dict[str, Any]] = None
    
    # Timing and metadata
    started_at: datetime
    completed_at: datetime = Field(default_factory=datetime.utcnow)

class SequentialPipelineRequest(BaseModel):
    """Solicitud para iniciar Sequential Pipeline"""
    employee_id: str
    session_id: str
    orchestration_id: str
    
    # Input from Data Aggregator
    consolidated_data: Dict[str, Any]
    aggregation_result: Dict[str, Any]
    data_quality_score: float
    
    # Pipeline configuration
    pipeline_priority: Priority = Priority.MEDIUM
    quality_gates_enabled: bool = True
    sla_monitoring_enabled: bool = True
    auto_escalation_enabled: bool = True
    
    # ✅ ERROR HANDLING CONFIGURATION
    error_handling_enabled: bool = True
    error_recovery_enabled: bool = True
    human_escalation_enabled: bool = True
    
    # Agent-specific configurations
    it_provisioning_config: Dict[str, Any] = Field(default_factory=dict)
    contract_management_config: Dict[str, Any] = Field(default_factory=dict)
    meeting_coordination_config: Dict[str, Any] = Field(default_factory=dict)

class SequentialPipelineResult(BaseModel):
    """Resultado completo del Sequential Pipeline"""
    success: bool
    employee_id: str
    session_id: str
    orchestration_id: str
    pipeline_id: str = Field(default_factory=lambda: f"PIPE-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    
    # Phase results
    it_provisioning_result: Optional[PipelineAgentResult] = None
    contract_management_result: Optional[PipelineAgentResult] = None
    meeting_coordination_result: Optional[PipelineAgentResult] = None
    
    # Final pipeline data
    employee_ready_for_onboarding: bool = False
    onboarding_timeline: Optional[Dict[str, Any]] = None
    stakeholders_engaged: List[str] = Field(default_factory=list)
    
    # Pipeline metrics
    total_processing_time: float = 0.0
    stages_completed: int = 0
    stages_total: int = 3
    overall_quality_score: float = Field(ge=0.0, le=100.0, default=0.0)
    
    # Quality gates and SLA
    quality_gates_passed: int = 0
    quality_gates_failed: int = 0
    sla_breaches: int = 0
    escalations_triggered: int = 0
    
    # ✅ ERROR HANDLING CONSOLIDADO
    error_handling_executed: bool = False
    error_handling_summary: Optional[ErrorHandlingResult] = None
    recovery_attempts_total: int = 0
    human_interventions: List[str] = Field(default_factory=list)
    
    # Next steps
    next_actions: List[str] = Field(default_factory=list)
    requires_followup: bool = False
    
    # Error handling
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Timestamps
    started_at: datetime
    completed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ✅ NUEVOS SCHEMAS ESPECÍFICOS PARA ERROR HANDLING INTEGRATION
class ErrorHandlingConfiguration(BaseModel):
    """Configuración completa de Error Handling para Orchestrator"""
    enabled: bool = True
    
    # Thresholds para activar Error Handling
    quality_score_threshold: float = 30.0
    max_errors_threshold: int = 3
    agent_failure_threshold: int = 2
    
    # Configuración por fase
    classification_config: Dict[str, Any] = Field(default_factory=dict)
    recovery_config: Dict[str, Any] = Field(default_factory=dict)
    handoff_config: Dict[str, Any] = Field(default_factory=dict)
    audit_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Timing y retries
    max_recovery_attempts: int = 3
    escalation_delay_seconds: int = 300  # 5 minutes
    audit_retention_days: int = 90

class OrchestratorErrorHandlingMetrics(BaseModel):
    """Métricas específicas de Error Handling del Orchestrator"""
    total_orchestrations: int = 0
    error_handling_triggered: int = 0
    error_handling_success_rate: float = 0.0
    
    # Por tipo de error
    data_collection_errors: int = 0
    sequential_pipeline_errors: int = 0
    quality_threshold_breaches: int = 0
    
    # Por resolución
    automatic_recoveries: int = 0
    human_escalations: int = 0
    unresolved_errors: int = 0
    
    # Timing
    average_error_handling_time: float = 0.0
    fastest_resolution: float = 0.0
    slowest_resolution: float = 0.0

# Sequential Pipeline Stage Dependencies
PIPELINE_STAGE_DEPENDENCIES = {
    SequentialPipelinePhase.IT_PROVISIONING: [],
    SequentialPipelinePhase.CONTRACT_MANAGEMENT: [SequentialPipelinePhase.IT_PROVISIONING],
    SequentialPipelinePhase.MEETING_COORDINATION: [SequentialPipelinePhase.CONTRACT_MANAGEMENT],
    # ✅ ERROR HANDLING puede activarse en cualquier momento
    SequentialPipelinePhase.PIPELINE_ERROR_HANDLING: []  # No dependencies
}

# Sequential Pipeline Quality Gate Requirements
PIPELINE_QUALITY_REQUIREMENTS = {
    SequentialPipelinePhase.IT_PROVISIONING: {
        "min_quality_score": 85.0,
        "required_outputs": ["credentials_created", "equipment_assigned", "access_granted"],
        "blocking_issues": ["security_clearance_failed", "equipment_unavailable"],
        "error_handling_triggers": ["provisioning_timeout", "security_validation_failed"]
    },
    SequentialPipelinePhase.CONTRACT_MANAGEMENT: {
        "min_quality_score": 90.0,
        "required_outputs": ["contract_generated", "legal_validation_passed", "signatures_completed"],
        "blocking_issues": ["legal_compliance_failed", "signature_process_failed"],
        "error_handling_triggers": ["contract_generation_failed", "legal_review_timeout"]
    },
    SequentialPipelinePhase.MEETING_COORDINATION: {
        "min_quality_score": 80.0,
        "required_outputs": ["stakeholders_identified", "meetings_scheduled", "timeline_created"],
        "blocking_issues": ["critical_stakeholders_unavailable", "calendar_system_error"],
        "error_handling_triggers": ["calendar_integration_failed", "stakeholder_availability_timeout"]
    },
    # ✅ ERROR HANDLING QUALITY REQUIREMENTS
    SequentialPipelinePhase.PIPELINE_ERROR_HANDLING: {
        "min_quality_score": 70.0,
        "required_outputs": ["error_classified", "recovery_attempted", "resolution_documented"],
        "blocking_issues": ["error_handling_system_failure"],
        "success_criteria": ["error_resolved_or_escalated"]
    }
}

# ✅ ERROR HANDLING TRIGGERS CONFIGURATION
ERROR_HANDLING_TRIGGERS = {
    "data_quality_threshold": {
        "threshold": 30.0,
        "comparison": "less_than",
        "description": "Data quality score below threshold"
    },
    "agent_failure_count": {
        "threshold": 2,
        "comparison": "greater_than_or_equal",
        "description": "Multiple agent failures detected"
    },
    "sequential_pipeline_failure": {
        "threshold": True,
        "comparison": "equals",
        "description": "Sequential pipeline execution failed"
    },
    "consolidation_failure": {
        "threshold": True,
        "comparison": "equals", 
        "description": "Data consolidation failed"
    },
    "sla_breach": {
        "threshold": True,
        "comparison": "equals",
        "description": "SLA breach detected"
    }
}

# ✅ ERROR HANDLING DEFAULT CONFIGURATION
DEFAULT_ERROR_HANDLING_CONFIG = ErrorHandlingConfiguration(
    enabled=True,
    quality_score_threshold=30.0,
    max_errors_threshold=3,
    agent_failure_threshold=2,
    classification_config={
        "auto_classify": True,
        "severity_mapping": {
            "low": ["warnings", "minor_data_issues"],
            "medium": ["agent_timeouts", "validation_failures"],
            "high": ["multiple_agent_failures", "quality_threshold_breach"],
            "critical": ["system_errors", "security_issues"]
        }
    },
    recovery_config={
        "auto_recovery": True,
        "max_attempts": 3,
        "strategies": ["immediate_retry", "exponential_backoff", "state_rollback"]
    },
    handoff_config={
        "auto_escalate": True,
        "escalation_criteria": ["recovery_failed", "critical_errors"],
        "specialist_routing": {
            "it_issues": "it_specialist",
            "hr_issues": "hr_manager", 
            "system_issues": "system_admin"
        }
    },
    audit_config={
        "comprehensive_logging": True,
        "compliance_standards": ["iso_27001"],
        "retention_days": 90
    }
)