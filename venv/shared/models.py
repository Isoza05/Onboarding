from typing import Optional, Dict, Any, List
try:
    from pydantic import BaseModel, Field
except ImportError:
    # Fallback simple si pydantic no está disponible
    class BaseModel:
        pass
    def Field(**kwargs):
        return None

from datetime import datetime
from enum import Enum

class OnboardingStatus(str, Enum):
    """Estados del proceso de onboarding"""
    INITIATED = "initiated"
    DATA_COLLECTED = "data_collected"
    DATA_VALIDATED = "data_validated"
    PROCESSING = "processing"
    IT_PROVISIONED = "it_provisioned"
    CONTRACT_SIGNED = "contract_signed"
    MEETINGS_SCHEDULED = "meetings_scheduled"
    COMPLETED = "completed"
    ERROR = "error"
    ESCALATED = "escalated"

class Priority(str, Enum):
    """Niveles de prioridad"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AgentResponse(BaseModel):
    """Respuesta estándar de agentes"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_id: str
    processing_time: Optional[float] = None