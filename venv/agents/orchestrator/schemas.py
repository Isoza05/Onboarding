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

class TaskStatus(str, Enum):
    """Estados de tareas"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"

class OrchestrationPhase(str, Enum):
    """Fases de orquestación"""
    INITIATED = "initiated"
    DATA_COLLECTION_CONCURRENT = "data_collection_concurrent"
    DATA_AGGREGATION = "data_aggregation"
    SEQUENTIAL_PROCESSING = "sequential_processing"
    FINALIZATION = "finalization"
    ERROR_HANDLING = "error_handling"

class AgentTaskAssignment(BaseModel):
    """Asignación de tarea a un agente específico"""
    task_id: str
    agent_type: AgentType
    agent_id: str
    task_description: str
    input_data: Dict[str, Any]
    priority: Priority = Priority.MEDIUM
    dependencies: List[str] = Field(default_factory=list)  # IDs de tareas dependientes
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    expected_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

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

class OrchestrationRequest(BaseModel):
    """Solicitud completa de orquestación de onboarding"""
    employee_id: str
    session_id: Optional[str] = None
    
    # Datos del nuevo empleado
    employee_data: Dict[str, Any]  # Datos básicos del empleado
    contract_data: Dict[str, Any]  # Términos contractuales
    documents: List[Dict[str, Any]] = Field(default_factory=list)  # Documentos adjuntos
    
    # Configuración de orquestación
    orchestration_pattern: OrchestrationPattern = OrchestrationPattern.CONCURRENT_DATA_COLLECTION
    priority: Priority = Priority.MEDIUM
    special_requirements: List[str] = Field(default_factory=list)
    deadline: Optional[datetime] = None
    
    # Configuración de agentes
    required_agents: List[AgentType] = Field(default_factory=list)
    agent_config: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('required_agents')
    def validate_required_agents(cls, v):
        if not v:
            # Por defecto, usar los 3 agentes del DATA COLLECTION HUB
            return [
                AgentType.INITIAL_DATA_COLLECTION,
                AgentType.CONFIRMATION_DATA, 
                AgentType.DOCUMENTATION
            ]
        return v

class OrchestrationState(BaseModel):
    """Estado completo de la orquestación"""
    orchestration_id: str
    session_id: str
    employee_id: str
    
    # Estado del workflow
    current_phase: OrchestrationPhase = OrchestrationPhase.INITIATED
    workflow_steps: List[WorkflowStep] = Field(default_factory=list)
    
    # Progreso general
    overall_progress: float = 0.0  # Porcentaje 0-100
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
    escalation_level: int = 0  # 0=ninguna, 1=supervisor, 2=manager, 3=director
    
    # Métricas
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)

class PatternSelectionCriteria(BaseModel):
    """Criterios para selección de patrón de orquestación"""
    employee_type: str  # "full_time", "contractor", "intern"
    position_level: str  # "junior", "mid", "senior", "executive"
    department: str
    location: str
    priority: Priority
    special_requirements: List[str] = Field(default_factory=list)
    compliance_level: str = "standard"  # "standard", "high", "critical"

class OrchestrationResult(BaseModel):
    """Resultado final de la orquestación"""
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
    total_processing_time: float  # segundos
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
    estimated_time_remaining: Optional[int] = None  # segundos
    quality_gates_passed: int = 0
    quality_gates_total: int = 0
    sla_status: str = "on_track"  # "on_track", "at_risk", "breached"
    
class TaskDistributionStrategy(BaseModel):
    """Estrategia para distribución de tareas"""
    strategy_type: str = "concurrent"  # "concurrent", "sequential", "hybrid"
    max_concurrent_agents: int = 3
    priority_weights: Dict[str, float] = Field(default_factory=dict)
    dependency_rules: Dict[str, List[str]] = Field(default_factory=dict)
    timeout_settings: Dict[str, int] = Field(default_factory=dict)
    retry_policies: Dict[str, Dict[str, Any]] = Field(default_factory=dict)