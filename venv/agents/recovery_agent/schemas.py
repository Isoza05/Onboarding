from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import uuid

class RecoveryStatus(str, Enum):
    """Estados de recuperación"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

class RecoveryAction(str, Enum):
    """Tipos de acciones de recuperación"""
    AGENT_RESTART = "agent_restart"
    PIPELINE_ROLLBACK = "pipeline_rollback"
    STATE_RESTORATION = "state_restoration"
    RETRY_OPERATION = "retry_operation"
    CIRCUIT_BREAKER_RESET = "circuit_breaker_reset"
    DEPENDENCY_CHECK = "dependency_check"
    RESOURCE_CLEANUP = "resource_cleanup"
    CACHE_CLEAR = "cache_clear"
    SERVICE_HEALTH_CHECK = "service_health_check"
    CONFIGURATION_RELOAD = "configuration_reload"
    WORKFLOW_RESUMPTION = "workflow_resumption"

class RecoveryStrategy(str, Enum):
    """Estrategias de recuperación"""
    IMMEDIATE_RETRY = "immediate_retry"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    CIRCUIT_BREAKER = "circuit_breaker"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    STATE_ROLLBACK = "state_rollback"
    SERVICE_RESTART = "service_restart"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    BYPASS_AND_CONTINUE = "bypass_and_continue"

class RecoveryPriority(str, Enum):
    """Prioridad de recuperación"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class RecoveryRequest(BaseModel):
    """Request para recuperación de errores"""
    session_id: str
    employee_id: str
    recovery_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Información del error
    error_classification_id: str
    error_category: str
    error_severity: str
    failed_agent_id: Optional[str] = None
    
    # Estrategia de recuperación
    recovery_strategy: RecoveryStrategy
    recovery_actions: List[RecoveryAction]
    recovery_priority: RecoveryPriority = RecoveryPriority.MEDIUM
    
    # Configuración de recuperación
    max_retry_attempts: int = 3
    retry_delay_seconds: int = 5
    timeout_minutes: int = 30
    allow_partial_recovery: bool = True
    
    # Context y metadata
    error_context: Dict[str, Any] = Field(default_factory=dict)
    recovery_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Tiempos
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None

class RecoveryAttempt(BaseModel):
    """Intento individual de recuperación"""
    attempt_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    attempt_number: int
    recovery_action: RecoveryAction
    
    # Estado del intento
    status: RecoveryStatus = RecoveryStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Resultados
    success: bool = False
    result_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    
    # Métricas
    resource_usage: Dict[str, Any] = Field(default_factory=dict)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)

class SystemRecoveryState(BaseModel):
    """Estado del sistema durante recuperación"""
    recovery_id: str
    session_id: str
    employee_id: str
    
    # Estado general
    overall_status: RecoveryStatus
    recovery_progress: float = 0.0  # 0-100%
    
    # Estados de componentes
    agent_states: Dict[str, str] = Field(default_factory=dict)
    service_states: Dict[str, str] = Field(default_factory=dict)
    pipeline_state: Dict[str, Any] = Field(default_factory=dict)
    
    # Snapshot de datos
    pre_recovery_snapshot: Dict[str, Any] = Field(default_factory=dict)
    current_state_snapshot: Dict[str, Any] = Field(default_factory=dict)
    
    # Métricas de recuperación
    recovery_metrics: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    recovery_started_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated_at: datetime = Field(default_factory=datetime.utcnow)

class RecoveryResult(BaseModel):
    """Resultado de recuperación"""
    recovery_id: str
    session_id: str
    employee_id: str
    
    # Estado final
    final_status: RecoveryStatus
    success: bool
    recovery_completed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Resumen de recuperación
    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    recovery_duration_seconds: float = 0.0
    
    # Acciones ejecutadas
    recovery_attempts: List[RecoveryAttempt] = Field(default_factory=list)
    actions_executed: List[RecoveryAction] = Field(default_factory=list)
    
    # Estados restaurados
    restored_agents: List[str] = Field(default_factory=list)
    restored_services: List[str] = Field(default_factory=list)
    pipeline_status: str = "unknown"
    
    # Impacto de la recuperación
    impact_analysis: Dict[str, Any] = Field(default_factory=dict)
    performance_impact: Dict[str, Any] = Field(default_factory=dict)
    
    # Próximos pasos
    next_actions: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    requires_manual_review: bool = False
    
    # Escalación si es necesaria
    escalation_required: bool = False
    escalation_reason: Optional[str] = None
    escalation_target: Optional[str] = None
    
    # Lecciones aprendidas
    lessons_learned: List[str] = Field(default_factory=list)
    preventive_measures: List[str] = Field(default_factory=list)

class RecoveryConfiguration(BaseModel):
    """Configuración de recuperación"""
    recovery_config_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Configuración de reintentos
    default_max_retries: int = 3
    default_retry_delay: int = 5
    exponential_backoff_factor: float = 2.0
    max_backoff_delay: int = 300  # 5 minutos
    
    # Configuración de timeouts
    default_recovery_timeout: int = 30  # minutos
    agent_restart_timeout: int = 60  # segundos
    service_health_check_timeout: int = 30  # segundos
    
    # Configuración de circuit breaker
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 60  # segundos
    
    # Configuración de recursos
    max_concurrent_recoveries: int = 3
    resource_usage_threshold: float = 0.8  # 80%
    
    # Configuración de escalación
    escalation_timeout_minutes: int = 45
    critical_escalation_timeout_minutes: int = 15
    
    # Configuración de monitoreo
    health_check_interval_seconds: int = 30
    metrics_collection_enabled: bool = True
    detailed_logging_enabled: bool = True