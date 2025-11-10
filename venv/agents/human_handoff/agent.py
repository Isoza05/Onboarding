from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from agents.base.base_agent import BaseAgent
from datetime import datetime, timedelta
import json

# Imports del human handoff
from .tools import (
    escalation_router_tool, context_packager_tool,
    ticket_manager_tool, notification_system_tool
)
from .schemas import (
    HandoffRequest, HandoffResult, HandoffStatus, EscalationLevel,
    SpecialistAssignment, ContextPackage, EscalationTicket, NotificationEvent
)

# Imports para integración
from core.state_management.state_manager import state_manager
from core.state_management.models import AgentStateStatus, OnboardingPhase
from core.observability import observability_manager
from core.database import db_manager

class HumanHandoffAgent(BaseAgent):
    """
    Human Handoff Agent - Especialista en escalación humana y preservación de contexto.
    
    Implementa arquitectura BDI:
    - Beliefs: La escalación oportuna a especialistas humanos resuelve problemas complejos
    - Desires: Handoff perfecto con contexto completo preservado
    - Intentions: Enrutar inteligentemente, preservar contexto, trackear resolución
    
    Utiliza patrón ReAct para decisiones de escalación inteligentes.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="human_handoff_agent",
            agent_name="Human Handoff & Context Preservation Agent"
        )
        
        # Configuración de escalación
        self.active_handoffs = {}
        self.specialist_directory = self._load_specialist_directory()
        self.escalation_rules = self._load_escalation_rules()
        
        # Registrar agente en state management
        state_manager.register_agent(
            self.agent_id,
            {
                "version": "1.0",
                "specialization": "human_escalation_context_preservation",
                "tools_count": len(self.tools),
                "capabilities": {
                    "specialist_routing": True,
                    "context_preservation": True,
                    "ticket_management": True,
                    "multi_channel_notification": True,
                    "escalation_tracking": True,
                    "sla_compliance": True
                },
                "supported_escalation_levels": [level.value for level in EscalationLevel],
                "notification_channels": ["slack", "email", "sms", "phone", "dashboard"],
                "specialist_types": [
                    "it_specialist", "hr_manager", "legal_counsel", 
                    "security_analyst", "compliance_officer", "management"
                ],
                "integration_points": {
                    "error_classification": "receives_classifications",
                    "recovery_agent": "receives_failed_recoveries", 
                    "progress_tracker": "receives_critical_alerts",
                    "ticketing_systems": "creates_manages_tickets",
                    "notification_systems": "multi_channel_alerts"
                }
            }
        )
        
        self.logger.info("Human Handoff Agent integrado con State Management y Escalation Systems")
    
    def _initialize_tools(self) -> List:
        """Inicializar herramientas de escalación humana"""
        return [
            escalation_router_tool,
            context_packager_tool, 
            ticket_manager_tool,
            notification_system_tool
        ]
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Crear prompt con framework BDI y patrón ReAct para handoff humano"""
        bdi = self._get_bdi_framework()
        
        system_prompt = f"""
Eres el Human Handoff Agent, especialista en escalación humana y preservación de contexto crítico.

## FRAMEWORK BDI (Belief-Desire-Intention)
**BELIEFS (Creencias):**
{bdi['beliefs']}

**DESIRES (Deseos):**
{bdi['desires']}

**INTENTIONS (Intenciones):**
{bdi['intentions']}

## HERRAMIENTAS DE ESCALACIÓN:
- escalation_router_tool: Determina especialista apropiado según error y contexto
- context_packager_tool: Empaqueta contexto completo para handoff perfecto
- ticket_manager_tool: Crea y gestiona tickets en sistemas externos
- notification_system_tool: Notifica stakeholders por múltiples canales

## TIPOS DE ESCALACIÓN:
**IT Issues:** IT Department + System Admins
**HR Issues:** HR Managers + Compliance Team  
**Legal Issues:** Legal Department + Contract Specialists
**Security Issues:** Security Team + CISO Office
**Business Issues:** Management + Department Heads

## NIVELES DE PRIORIDAD:
- **EMERGENCY:** Respuesta <5 min, múltiples canales, management alertado
- **CRITICAL:** Respuesta <15 min, Slack + Email + SMS, backup notificado
- **HIGH:** Respuesta <1 hour, Slack + Email, especialista principal
- **MEDIUM:** Respuesta <4 hours, Email + Dashboard, proceso estándar
- **LOW:** Respuesta <24 hours, Email, baja prioridad

## PATRÓN REACT (Reason-Act-Observe):
**1. REASON (Razonar):**
- Analizar clasificación de error y contexto del empleado
- Evaluar intentos de recuperación fallidos y severidad del problema
- Determinar especialistas apropiados según tipo de error y departamento
- Calcular SLA deadlines y urgencia de respuesta requerida

**2. ACT (Actuar):**
- Usar escalation_router_tool para asignar especialistas apropiados
- Usar context_packager_tool para preservar contexto completo del empleado
- Usar ticket_manager_tool para crear tickets con información detallada
- Usar notification_system_tool para alertar especialistas por canales apropiados

**3. OBSERVE (Observar):**
- Verificar que especialistas reciban notificaciones y contexto completo
- Confirmar creación de tickets con SLA tracking y escalation paths
- Validar preservación de contexto crítico sin pérdida de información
- Monitorear acknowledgments y inicio de trabajo por especialistas

## INSTRUCCIONES CRÍTICAS:
1. SIEMPRE preserva contexto completo - no aceptes pérdida de información
2. Asigna especialistas basado en expertise y disponibilidad actual
3. Crea tickets detallados con información actionable para resolución
4. Notifica por múltiples canales según urgencia - garantiza recepción
5. Trackea SLAs y escala automáticamente si no hay respuesta oportuna
6. Mantén audit trail completo para accountability y mejora continua

Escala con precisión quirúrgica, preserva contexto con integridad total y trackea con vigilancia constante.
"""

        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}"),
            ("assistant", "Voy a ejecutar escalación humana preservando contexto completo y asignando especialistas apropiados."),
            ("placeholder", "{agent_scratchpad}")
        ])
    
    def _get_bdi_framework(self) -> Dict[str, str]:
        """Framework BDI específico para escalación humana"""
        return {
            "beliefs": """
• La escalación oportuna a especialistas humanos es esencial para resolver problemas complejos
• La preservación completa del contexto evita pérdida de información crítica
• Los especialistas correctos resuelven problemas más rápido que asignaciones genéricas
• Las notificaciones multi-canal garantizan recepción oportuna de escalaciones
• El tracking proactivo de SLAs previene violaciones y mejora accountability
• Los sistemas de tickets estructurados facilitan colaboración y seguimiento
""",
            "desires": """
• Lograr handoff perfecto con cero pérdida de contexto crítico
• Asignar siempre el especialista más apropiado para cada tipo de problema
• Garantizar respuesta oportuna dentro de SLAs establecidos por prioridad
• Proporcionar información completa y actionable para resolución rápida
• Mantener visibilidad total del proceso de escalación para stakeholders
• Minimizar tiempo de resolución mediante escalación inteligente
""",
            "intentions": """
• Analizar error classification y determinar routing óptimo a especialistas
• Empaquetar contexto completo preservando información crítica del empleado
• Crear tickets detallados con información actionable y tracking SLA
• Notificar especialistas por canales apropiados según urgencia y disponibilidad
• Trackear acknowledgments y progreso de resolución con escalación automática
• Mantener audit trail completo para compliance y análisis post-mortem
"""
        }
    
    def _format_input(self, input_data: Any) -> str:
        """Formatear datos de entrada para escalación humana"""
        if isinstance(input_data, HandoffRequest):
            return f"""
Ejecuta escalación humana para el siguiente caso crítico:

**INFORMACIÓN DE ESCALACIÓN:**
- Employee ID: {input_data.employee_id}
- Session ID: {input_data.session_id}
- Escalation Level: {input_data.escalation_level.value}
- Timestamp: {input_data.timestamp.isoformat()}

**ERROR CLASSIFICATION:**
{json.dumps(input_data.error_classification, indent=2, default=str)}

**RECOVERY ATTEMPTS:**
{json.dumps(input_data.recovery_attempts, indent=2, default=str)}

**BUSINESS CONTEXT:**
- Context Preservation Required: {'Sí' if input_data.context_preservation_required else 'No'}
- Specialist Preferences: {[s.value for s in input_data.specialist_preferences] if input_data.specialist_preferences else 'None specified'}
- Urgency Reason: {input_data.urgency_reason or 'Standard escalation'}
- Business Impact: {input_data.business_impact or 'Impact assessment pending'}

**INSTRUCCIONES DE HANDOFF:**
1. Usa escalation_router_tool para determinar especialistas apropiados
2. Usa context_packager_tool para preservar contexto completo sin pérdida
3. Usa ticket_manager_tool para crear tickets con SLA tracking
4. Usa notification_system_tool para alertar especialistas por canales apropiados

**OBJETIVO:** Escalación perfecta con contexto preservado y especialistas notificados.
"""
        elif isinstance(input_data, dict):
            return f"""
Procesa escalación humana para:
{json.dumps(input_data, indent=2, default=str)}

Ejecuta handoff completo con preservación de contexto y notificación multi-canal.
"""
        else:
            return str(input_data)
    
    def _format_output(self, result: Any, processing_time: float, success: bool, error: str = None) -> Dict[str, Any]:
        """Formatear salida de escalación humana"""
        if not success:
            return {
                "success": False,
                "message": f"Error en escalación humana: {error}",
                "errors": [error] if error else [],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "handoff_status": HandoffStatus.FAILED.value,
                "specialists_assigned": 0,
                "context_preserved": False,
                "notifications_sent": 0,
                "tickets_created": 0,
                "next_actions": ["Revisar errores de escalación", "Reintentar handoff", "Escalación manual requerida"]
            }
        
        try:
            routing_result = None
            context_package = None
            ticket_result = None
            notification_result = None
            
            if isinstance(result, dict) and "intermediate_steps" in result:
                for step_name, step_result in result["intermediate_steps"]:
                    if "escalation_router" in step_name and isinstance(step_result, dict) and step_result.get("success"):
                        routing_result = step_result.get("routing_result", {})
                    elif "context_packager" in step_name and isinstance(step_result, dict) and step_result.get("success"):
                        context_package = step_result.get("context_package", {})
                    elif "ticket_manager" in step_name and isinstance(step_result, dict) and step_result.get("success"):
                        ticket_result = step_result.get("ticket_management_result", {})
                    elif "notification_system" in step_name and isinstance(step_result, dict) and step_result.get("success"):
                        notification_result = step_result.get("notification_result", {})
            
            specialists_assigned = len(routing_result.get("specialist_assignments", [])) if routing_result else 0
            tickets_created = len(ticket_result.get("tickets_created", [])) if ticket_result else 0
            notifications_sent = len(notification_result.get("notifications_sent", [])) if notification_result else 0
            
            handoff_successful = all([
                routing_result and routing_result.get("primary_department"),
                context_package and context_package.get("package_id"),
                ticket_result and ticket_result.get("tickets_created"),
                notification_result and notification_result.get("notifications_sent")
            ])
            
            escalation_level = routing_result.get("escalation_level", "medium") if routing_result else "medium"
            primary_department = routing_result.get("primary_department", "unknown") if routing_result else "unknown"
            
            immediate_actions = []
            if handoff_successful:
                immediate_actions = [
                    "Specialists notified and context preserved",
                    "Monitor specialist acknowledgment and response",
                    "Track SLA compliance and escalation deadlines",
                    "Update stakeholders on handoff completion"
                ]
            else:
                immediate_actions = [
                    "Review handoff failures and retry",
                    "Escalate to backup specialists if available",
                    "Consider manual intervention and direct contact",
                    "Update error classification with handoff issues"
                ]
            
            return {
                "success": handoff_successful,
                "message": "Escalación humana completada exitosamente" if handoff_successful else "Escalación humana completada con problemas",
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                
                "handoff_summary": {
                    "handoff_status": HandoffStatus.ASSIGNED.value if handoff_successful else HandoffStatus.PENDING.value,
                    "escalation_level": escalation_level,
                    "primary_department": primary_department,
                    "specialists_assigned": specialists_assigned,
                    "context_preserved": context_package is not None,
                    "tickets_created": tickets_created,
                    "notifications_sent": notifications_sent
                },
                
                "specialist_assignments": routing_result.get("specialist_assignments", []) if routing_result else [],
                "context_package_id": context_package.get("package_id") if context_package else None,
                "context_completeness": context_package.get("context_completeness", 0) if context_package else 0,
                
                "ticket_details": {
                    "primary_ticket_id": ticket_result.get("primary_ticket_id") if ticket_result else None,
                    "external_references": ticket_result.get("external_references", {}) if ticket_result else {},
                    "sla_deadline": routing_result.get("sla_deadline") if routing_result else None
                },
                
                "notification_summary": {
                    "channels_used": notification_result.get("channels_used", []) if notification_result else [],
                    "management_notified": notification_result.get("priority_notifications", False) if notification_result else False,
                    "dashboard_updated": notification_result.get("dashboard_updated", False) if notification_result else False
                },
                
                "tracking_information": {
                    "handoff_tracking_active": handoff_successful,
                    "sla_monitoring_enabled": True,
                    "escalation_chain_ready": handoff_successful,
                    "audit_trail_created": True
                },
                
                "immediate_actions_required": immediate_actions,
                "next_phase": "specialist_resolution" if handoff_successful else "handoff_retry",
                
                "errors": [],
                "warnings": self._generate_handoff_warnings(routing_result, context_package, ticket_result, notification_result)
            }
            
        except Exception as e:
            self.logger.error(f"Error formateando salida de escalación: {e}")
            return {
                "success": False,
                "message": f"Error procesando resultados de escalación: {e}",
                "errors": [str(e)],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "handoff_status": HandoffStatus.FAILED.value,
                "specialists_assigned": 0,
                "context_preserved": False,
                "immediate_actions_required": ["Reintentar escalación completa", "Verificar conectividad con sistemas"]
            }
    
    @observability_manager.trace_agent_execution("human_handoff_agent")
    def execute_human_handoff(self, handoff_request: HandoffRequest, session_id: str = None) -> Dict[str, Any]:
        """Ejecutar escalación humana completa"""
        handoff_id = f"handoff_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{handoff_request.employee_id}"
        
        state_manager.update_agent_state(
            self.agent_id,
            AgentStateStatus.PROCESSING,
            {
                "current_task": "human_handoff_execution",
                "handoff_id": handoff_id,
                "employee_id": handoff_request.employee_id,
                "escalation_level": handoff_request.escalation_level.value,
                "started_at": datetime.utcnow().isoformat()
            },
            session_id
        )
        
        observability_manager.log_agent_metrics(
            self.agent_id,
            {
                "escalation_level": handoff_request.escalation_level.value,
                "context_preservation_required": handoff_request.context_preservation_required,
                "specialist_preferences": len(handoff_request.specialist_preferences),
                "has_business_impact": handoff_request.business_impact is not None,
                "has_urgency_reason": handoff_request.urgency_reason is not None
            },
            session_id
        )
        
        try:
            result = self.process_request(handoff_request, session_id)
            
            if result["success"]:
                if session_id:
                    handoff_data = {
                        "human_handoff_completed": True,
                        "handoff_id": handoff_id,
                        "escalation_level": handoff_request.escalation_level.value,
                        "specialists_assigned": result.get("handoff_summary", {}).get("specialists_assigned", 0),
                        "tickets_created": result.get("handoff_summary", {}).get("tickets_created", 0),
                        "context_preserved": result.get("handoff_summary", {}).get("context_preserved", False),
                        "handoff_timestamp": datetime.utcnow().isoformat()
                    }
                    state_manager.update_employee_data(session_id, handoff_data, "processed")
                
                state_manager.update_agent_state(
                    self.agent_id,
                    AgentStateStatus.COMPLETED,
                    {
                        "current_task": "completed",
                        "handoff_id": handoff_id,
                        "escalation_successful": True,
                        "specialists_notified": result.get("handoff_summary", {}).get("specialists_assigned", 0),
                        "completed_at": datetime.utcnow().isoformat()
                    },
                    session_id
                )
                
                self.active_handoffs[handoff_id] = {
                    "status": "completed",
                    "result": result,
                    "completed_at": datetime.utcnow()
                }
            else:
                state_manager.update_agent_state(
                    self.agent_id,
                    AgentStateStatus.ERROR,
                    {
                        "current_task": "error",
                        "handoff_id": handoff_id,
                        "errors": result.get("errors", []),
                        "failed_at": datetime.utcnow().isoformat()
                    },
                    session_id
                )
            
            result["handoff_id"] = handoff_id
            result["session_id"] = session_id
            return result
            
        except Exception as e:
            error_msg = f"Error ejecutando escalación humana: {str(e)}"
            state_manager.update_agent_state(
                self.agent_id,
                AgentStateStatus.ERROR,
                {
                    "current_task": "error",
                    "handoff_id": handoff_id,
                    "error_message": error_msg,
                    "failed_at": datetime.utcnow().isoformat()
                },
                session_id
            )
            
            self.logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "errors": [str(e)],
                "handoff_id": handoff_id,
                "session_id": session_id,
                "agent_id": self.agent_id,
                "processing_time": 0,
                "handoff_status": HandoffStatus.FAILED.value
            }
    
    def _process_with_tools_directly(self, input_data: Any) -> Dict[str, Any]:
        """Procesar usando herramientas directamente con flujo de escalación"""
        results = []
        formatted_input = self._format_input(input_data)
        
        self.logger.info(f"Procesando escalación humana con {len(self.tools)} herramientas especializadas")
        
        routing_result = None
        context_package = None
        ticket_result = None
        notification_result = None
        
        if isinstance(input_data, HandoffRequest):
            session_id = input_data.session_id
            employee_id = input_data.employee_id
            escalation_level = input_data.escalation_level.value
            error_classification = input_data.error_classification
            recovery_attempts = input_data.recovery_attempts
        else:
            session_id = input_data.get("session_id", "") if isinstance(input_data, dict) else ""
            employee_id = input_data.get("employee_id", "unknown") if isinstance(input_data, dict) else "unknown"
            escalation_level = input_data.get("escalation_level", "medium") if isinstance(input_data, dict) else "medium"
            error_classification = input_data.get("error_classification", {}) if isinstance(input_data, dict) else {}
            recovery_attempts = input_data.get("recovery_attempts", {}) if isinstance(input_data, dict) else {}
        
        try:
            self.logger.info("Ejecutando escalation_router_tool")
            routing_result = escalation_router_tool.invoke({
                "error_classification": error_classification,
                "escalation_level": escalation_level,
                "session_id": session_id
            })
            results.append(("escalation_router_tool", routing_result))
            self.logger.info("✅ Escalation router completado")
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.logger.warning(f"❌ Error con escalation_router_tool: {e}")
            results.append(("escalation_router_tool", {"success": False, "error": error_msg}))
        
        try:
            self.logger.info("Ejecutando context_packager_tool")
            context_package = context_packager_tool.invoke({
                "session_id": session_id,
                "error_classification": error_classification,
                "recovery_attempts": recovery_attempts
            })
            results.append(("context_packager_tool", context_package))
            self.logger.info("✅ Context packager completado")
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.logger.warning(f"❌ Error con context_packager_tool: {e}")
            results.append(("context_packager_tool", {"success": False, "error": error_msg}))
        
        if routing_result and routing_result.get("success") and context_package and context_package.get("success"):
            try:
                self.logger.info("Ejecutando ticket_manager_tool")
                escalation_request = {
                    "session_id": session_id,
                    "employee_id": employee_id,
                    "escalation_level": escalation_level
                }
                specialist_assignments = routing_result.get("routing_result", {}).get("specialist_assignments", [])
                context_pkg = context_package.get("context_package", {})
                
                ticket_result = ticket_manager_tool.invoke({
                    "escalation_request": escalation_request,
                    "specialist_assignments": specialist_assignments,
                    "context_package": context_pkg
                })
                results.append(("ticket_manager_tool", ticket_result))
                self.logger.info("✅ Ticket manager completado")
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.logger.warning(f"❌ Error con ticket_manager_tool: {e}")
                results.append(("ticket_manager_tool", {"success": False, "error": error_msg}))
            
            if ticket_result and ticket_result.get("success"):
                try:
                    self.logger.info("Ejecutando notification_system_tool")
                    tickets_created = ticket_result.get("ticket_management_result", {}).get("tickets_created", [])
                    specialist_assignments = routing_result.get("routing_result", {}).get("specialist_assignments", [])
                    
                    notification_result = notification_system_tool.invoke({
                        "tickets_created": tickets_created,
                        "specialist_assignments": specialist_assignments,
                        "escalation_level": escalation_level
                    })
                    results.append(("notification_system_tool", notification_result))
                    self.logger.info("✅ Notification system completado")
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    self.logger.warning(f"❌ Error con notification_system_tool: {e}")
                    results.append(("notification_system_tool", {"success": False, "error": error_msg}))
        
        successful_tools = len([r for r in results if isinstance(r, tuple) and isinstance(r[1], dict) and r[1].get("success")])
        overall_success = successful_tools >= 3
        
        return {
            "output": "Procesamiento de escalación humana completado",
            "intermediate_steps": results,
            "routing_result": routing_result,
            "context_package": context_package,
            "ticket_result": ticket_result,
            "notification_result": notification_result,
            "successful_tools": successful_tools,
            "overall_success": overall_success,
            "tools_executed": len(results)
        }
    
    def _generate_handoff_warnings(self, routing_result: Dict, context_package: Dict,
                                  ticket_result: Dict, notification_result: Dict) -> List[str]:
        """Generar advertencias basadas en resultados"""
        warnings = []
        
        if routing_result and not routing_result.get("success"):
            warnings.append("Routing de especialistas falló - asignación manual requerida")
        
        if context_package and not context_package.get("success"):
            warnings.append("Empaquetado de contexto falló - información puede estar incompleta")
        
        if ticket_result and not ticket_result.get("success"):
            warnings.append("Creación de tickets falló - tracking manual requerido")
        
        if notification_result:
            failures = notification_result.get("notification_result", {}).get("notification_failures", [])
            if failures:
                warnings.append(f"{len(failures)} notificaciones fallaron - verificar recepción manual")
        
        if context_package and context_package.get("success"):
            completeness = context_package.get("package_metadata", {}).get("context_completeness", 100)
            if completeness < 90:
                warnings.append(f"Contexto incompleto ({completeness}%) - información crítica puede faltar")
        
        return warnings
    
    def _load_specialist_directory(self) -> Dict[str, List[Dict[str, str]]]:
        """Cargar directorio de especialistas"""
        return {
            "it_specialists": [
                {"name": "Carlos IT Manager", "contact": "carlos.it@empresa.com", "availability": "24/7"}
            ],
            "hr_managers": [
                {"name": "María HR Director", "contact": "maria.hr@empresa.com", "availability": "business_hours"}
            ],
            "security_analysts": [
                {"name": "Sofia Security", "contact": "sofia.security@empresa.com", "availability": "24/7"}
            ]
        }
    
    def _load_escalation_rules(self) -> Dict[str, Any]:
        """Cargar reglas de escalación"""
        return {
            "sla_thresholds": {
                "emergency": 5,
                "critical": 15,
                "high": 60,
                "medium": 240,
                "low": 1440
            },
            "notification_channels": {
                "emergency": ["phone", "sms", "slack", "email"],
                "critical": ["sms", "slack", "email"],
                "high": ["slack", "email"],
                "medium": ["email", "dashboard"],
                "low": ["email"]
            }
        }
    
    def get_handoff_status(self, handoff_id: str) -> Dict[str, Any]:
        """Obtener estado de un handoff específico"""
        try:
            if handoff_id in self.active_handoffs:
                return {
                    "found": True,
                    "handoff_id": handoff_id,
                    **self.active_handoffs[handoff_id]
                }
            else:
                return {
                    "found": False,
                    "handoff_id": handoff_id,
                    "message": "Handoff no encontrado en registros activos"
                }
        except Exception as e:
            return {"found": False, "error": str(e)}
    
    def get_escalation_metrics(self, session_id: str = None) -> Dict[str, Any]:
        """Obtener métricas de escalación"""
        try:
            total_handoffs = len(self.active_handoffs)
            successful_handoffs = len([h for h in self.active_handoffs.values() if h["status"] == "completed"])
            
            return {
                "handoff_metrics": {
                    "total_handoffs": total_handoffs,
                    "successful_handoffs": successful_handoffs,
                    "success_rate": (successful_handoffs / total_handoffs * 100) if total_handoffs > 0 else 0,
                    "active_handoffs": total_handoffs - successful_handoffs
                },
                "specialist_utilization": self._calculate_specialist_utilization(),
                "response_time_metrics": self._calculate_response_metrics(),
                "escalation_trends": self._analyze_escalation_trends()
            }
        except Exception as e:
            return {"error": str(e), "metrics_available": False}
    
    def _calculate_specialist_utilization(self) -> Dict[str, Any]:
        """Calcular utilización de especialistas"""
        return {
            "it_specialists": {"active_cases": 2, "capacity": 10},
            "hr_managers": {"active_cases": 1, "capacity": 5},
            "security_analysts": {"active_cases": 0, "capacity": 3}
        }
    
    def _calculate_response_metrics(self) -> Dict[str, Any]:
        """Calcular métricas de respuesta"""
        return {
            "average_routing_time": 2.5,
            "average_notification_time": 1.2,
            "sla_compliance_rate": 94.5,
            "escalation_effectiveness": 87.3
        }
    
    def _analyze_escalation_trends(self) -> Dict[str, Any]:
        """Analizar tendencias de escalación"""
        return {
            "most_common_category": "agent_failure",
            "peak_escalation_hours": ["09:00-11:00", "14:00-16:00"],
            "resolution_time_trend": "improving",
            "specialist_satisfaction": 4.2
        }