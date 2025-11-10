from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import uuid

class AgentStateStatus(str, Enum):
    """Estados posibles de un agente"""
    IDLE = "idle"
    PROCESSING = "processing"  
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"
    PAUSED = "paused"

class OnboardingPhase(str, Enum):
    """Fases del proceso de onboarding"""
    INITIATED = "initiated"
    DATA_COLLECTION = "data_collection"
    DATA_AGGREGATION = "data_aggregation"
    PROCESSING_PIPELINE = "processing_pipeline"
    ERROR_HANDLING = "error_handling"
    COMPLETED = "completed"

class AgentState(BaseModel):
    """Estado individual de un agente"""
    agent_id: str
    status: AgentStateStatus = AgentStateStatus.IDLE
    current_task: Optional[str] = None
    progress: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class EmployeeContext(BaseModel):
    """Contexto completo de un empleado en onboarding"""
    employee_id: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    phase: OnboardingPhase = OnboardingPhase.INITIATED
    
    # Datos del empleado
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    processed_data: Dict[str, Any] = Field(default_factory=dict)
    validation_results: Dict[str, Any] = Field(default_factory=dict)
    
    # Estado de agentes
    agent_states: Dict[str, AgentState] = Field(default_factory=dict)
    
    # Metadatos del proceso
    started_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    priority: int = 1
    requires_manual_review: bool = False
    
    # Configuraciones específicas
    config: Dict[str, Any] = Field(default_factory=dict)

class SystemState(BaseModel):
    """Estado global del sistema"""
    active_sessions: Dict[str, EmployeeContext] = Field(default_factory=dict)
    agent_registry: Dict[str, AgentState] = Field(default_factory=dict)
    system_metrics: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class StateEvent(BaseModel):
    """Evento de cambio de estado"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_id: str
    session_id: Optional[str] = None
    event_type: str  # "state_change", "data_update", "error", etc.
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    