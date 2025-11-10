"""
Human Handoff Agent - Escalación Humana y Preservación de Contexto

Este módulo implementa el agente de escalación humana que maneja la transición
de problemas automatizados a especialistas humanos con preservación completa
del contexto.

Componentes:
- HumanHandoffAgent: Agente principal de escalación
- Herramientas especializadas: Router, Context Packager, Ticket Manager, Notifications
- Esquemas: Modelos para handoff, tickets, notificaciones y contexto
- Integración: State Management, Observability, Audit Trail
"""

from .agent import HumanHandoffAgent
from .schemas import (
    HandoffRequest, HandoffResult, HandoffStatus, EscalationLevel,
    SpecialistType, NotificationChannel, EscalationDepartment,
    SpecialistAssignment, ContextPackage, EscalationTicket, NotificationEvent
)
from .tools import (
    escalation_router_tool, context_packager_tool,
    ticket_manager_tool, notification_system_tool
)

__all__ = [
    "HumanHandoffAgent",
    "HandoffRequest", 
    "HandoffResult",
    "HandoffStatus",
    "EscalationLevel",
    "SpecialistType",
    "NotificationChannel", 
    "EscalationDepartment",
    "SpecialistAssignment",
    "ContextPackage",
    "EscalationTicket",
    "NotificationEvent",
    "escalation_router_tool",
    "context_packager_tool", 
    "ticket_manager_tool",
    "notification_system_tool"
]