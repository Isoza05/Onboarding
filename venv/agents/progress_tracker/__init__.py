"""
Progress Tracker Agent Module

Este módulo contiene el Progress Tracker Agent, especializado en monitoreo de pipeline
y garantía de calidad para el sistema de onboarding automatizado.

Componentes principales:
- ProgressTrackerAgent: Agente principal de monitoreo
- Herramientas especializadas: step_completion, quality_gates, sla_monitor, escalation
- Motor de reglas: Configuraciones de quality gates, SLA y escalaciones
- Schemas: Modelos de datos para métricas y resultados

El Progress Tracker supervisa el pipeline secuencial:
IT Provisioning → Contract Management → Meeting Coordination
"""

from .agent import ProgressTrackerAgent
from .schemas import (
    ProgressTrackerRequest,
    ProgressTrackerResult, 
    PipelineProgressSnapshot,
    PipelineStage,
    AgentStatus,
    QualityGateStatus,
    SLAStatus,
    EscalationLevel
)

__all__ = [
    'ProgressTrackerAgent',
    'ProgressTrackerRequest',
    'ProgressTrackerResult',
    'PipelineProgressSnapshot', 
    'PipelineStage',
    'AgentStatus',
    'QualityGateStatus',
    'SLAStatus',
    'EscalationLevel'
]

__version__ = "1.0.0"
__author__ = "Onboarding Automation Team"