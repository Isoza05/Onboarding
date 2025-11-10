from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import uuid

class ErrorSeverity(str, Enum):
    """Niveles de severidad de errores"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class ErrorCategory(str, Enum):
    """Categorías de errores"""
    AGENT_FAILURE = "agent_failure"
    SLA_BREACH = "sla_breach"
    QUALITY_FAILURE = "quality_failure"
    SYSTEM_ERROR = "system_error"
    DATA_VALIDATION = "data_validation"
    INTEGRATION_ERROR = "integration_error"
    SECURITY_ISSUE = "security_issue"
    BUSINESS_RULE_VIOLATION = "business_rule_violation"

class ErrorType(str, Enum):
    """Tipos específicos de errores"""
    # Agent Failures
    TIMEOUT = "timeout"
    PROCESSING_ERROR = "processing_error"
    DEPENDENCY_FAILURE = "dependency_failure"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    
    # SLA Breaches
    TIME_BREACH = "time_breach"
    QUALITY_BREACH = "quality_breach"
    PERFORMANCE_BREACH = "performance_breach"
    
    # Quality Issues
    VALIDATION_FAILURE = "validation_failure"
    COMPLETENESS_ISSUE = "completeness_issue"
    CONSISTENCY_ERROR = "consistency_error"
    
    # System Issues
    CONNECTIVITY_ERROR = "connectivity_error"
    AUTHENTICATION_ERROR = "authentication_error"
    CONFIGURATION_ERROR = "configuration_error"

class ErrorSource(str, Enum):
    """Fuentes de errores"""
    PROGRESS_TRACKER = "progress_tracker"
    AGENT_DIRECT = "agent_direct"
    QUALITY_GATE = "quality_gate"
    SLA_MONITOR = "sla_monitor"
    STATE_MANAGER = "state_manager"
    EXTERNAL_SYSTEM = "external_system"

class RecoveryStrategy(str, Enum):
    """Estrategias de recuperación recomendadas"""
    AUTOMATIC_RETRY = "automatic_retry"
    MANUAL_INTERVENTION = "manual_intervention"
    ESCALATION_REQUIRED = "escalation_required"
    ROLLBACK_RECOVERY = "rollback_recovery"
    HUMAN_HANDOFF = "human_handoff"
    SYSTEM_RESTART = "system_restart"
    NO_ACTION = "no_action"

class ErrorClassificationRequest(BaseModel):
    """Request para clasificación de errores"""
    session_id: str
    employee_id: str
    error_source: ErrorSource
    raw_error_data: Dict[str, Any]
    context_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    force_reclassification: bool = False

class ErrorPattern(BaseModel):
    """Patrón de error identificado"""
    pattern_id: str
    pattern_name: str
    frequency: int
    last_occurrence: datetime
    confidence_score: float
    related_agents: List[str] = Field(default_factory=list)
    common_context: Dict[str, Any] = Field(default_factory=dict)

class RootCauseAnalysis(BaseModel):
    """Análisis de causa raíz"""
    primary_cause: str
    contributing_factors: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    confidence_level: float
    analysis_method: str
    recommendations: List[str] = Field(default_factory=list)

class ErrorClassificationResult(BaseModel):
    """Resultado de clasificación de error"""
    classification_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    employee_id: str
    
    # Clasificación básica
    error_category: ErrorCategory
    error_type: ErrorType
    severity_level: ErrorSeverity
    
    # Análisis detallado
    root_cause_analysis: RootCauseAnalysis
    error_patterns: List[ErrorPattern] = Field(default_factory=list)
    
    # Contexto y metadata
    affected_agents: List[str] = Field(default_factory=list)
    pipeline_stage: str
    error_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Recuperación y escalación
    recovery_strategy: RecoveryStrategy
    escalation_path: List[str] = Field(default_factory=list)
    estimated_impact: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadatos de procesamiento
    classification_timestamp: datetime = Field(default_factory=datetime.utcnow)
    classifier_confidence: float
    requires_human_review: bool = False
    
    # Acciones recomendadas
    immediate_actions: List[str] = Field(default_factory=list)
    preventive_measures: List[str] = Field(default_factory=list)