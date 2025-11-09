from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from agents.base.base_agent import BaseAgent
from datetime import datetime, date, timedelta
import json

# Imports del meeting coordination
from .tools import (
    stakeholder_finder_tool, calendar_analyzer_tool,
    scheduler_optimizer_tool, invitation_manager_tool
)
from .schemas import (
    MeetingCoordinationRequest, MeetingCoordinationResult, OnboardingTimeline,
    MeetingSchedule, Stakeholder, StakeholderRole, MeetingType, MeetingPriority
)
from .calendar_simulator import calendar_simulator

# Imports para integración
from core.state_management.state_manager import state_manager
from core.state_management.models import AgentStateStatus, OnboardingPhase
from core.observability import observability_manager
from core.database import db_manager

class MeetingCoordinationAgent(BaseAgent):
    """
    Meeting Coordination Agent - Especialista en coordinación de calendarios y reuniones de onboarding.
    Implementa arquitectura BDI:
    - Beliefs: Las reuniones bien coordinadas aceleran la integración del empleado
    - Desires: Crear un timeline de onboarding optimizado con máxima participación de stakeholders
    - Intentions: Identificar stakeholders, analizar calendarios, optimizar programación y gestionar invitaciones
    
    Recibe resultados de: Contract Management Agent
    Produce: Timeline completo de reuniones de onboarding y sistema de recordatorios activo
    """
    
    def __init__(self):
        super().__init__(
            agent_id="meeting_coordination_agent",
            agent_name="Meeting Coordination & Calendar Specialist Agent"
        )
        
        # Configuración específica del coordinador
        self.calendar_simulator = calendar_simulator
        self.active_coordinations = {}
        self.stakeholder_database = {}
        
        # Registrar agente en state management
        state_manager.register_agent(
            self.agent_id,
            {
                "version": "1.0",
                "specialization": "meeting_coordination_calendar_management",
                "tools_count": len(self.tools),
                "capabilities": {
                    "stakeholder_identification": True,
                    "calendar_analysis": True,
                    "meeting_optimization": True,
                    "invitation_management": True,
                    "conflict_resolution": True,
                    "reminder_system": True
                },
                "supported_platforms": ["microsoft_teams", "outlook", "google_calendar"],
                "meeting_types": [mt.value for mt in MeetingType],
                "integration_points": {
                    "calendar_system": "microsoft_outlook",
                    "notification_system": "active",
                    "stakeholder_directory": "integrated"
                }
            }
        )
        self.logger.info("Meeting Coordination Agent integrado con State Management y Calendar System")
    
    def _initialize_tools(self) -> List:
        """Inicializar herramientas de coordinación de reuniones"""
        return [
            stakeholder_finder_tool,
            calendar_analyzer_tool, 
            scheduler_optimizer_tool,
            invitation_manager_tool
        ]
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Crear prompt con framework BDI y patrón ReAct para coordinación de reuniones"""
        bdi = self._get_bdi_framework()
        system_prompt = f"""
Eres el Meeting Coordination & Calendar Specialist Agent, experto en coordinación de reuniones y gestión de calendarios empresariales.

## FRAMEWORK BDI (Belief-Desire-Intention)
**BELIEFS (Creencias):**
{bdi['beliefs']}

**DESIRES (Deseos):**
{bdi['desires']}

**INTENTIONS (Intenciones):**
{bdi['intentions']}

## HERRAMIENTAS DE COORDINACIÓN:
- stakeholder_finder_tool: Identifica stakeholders clave y mapea roles según posición y departamento
- calendar_analyzer_tool: Analiza disponibilidad de calendarios y detecta conflictos potenciales
- scheduler_optimizer_tool: Optimiza programación considerando prioridades, dependencias y preferencias
- invitation_manager_tool: Gestiona invitaciones, recordatorios y sistema de notificaciones

## DATOS DE ENTRADA (CONTRACT MANAGEMENT AGENT):
1. **Personal Data**: Información del empleado, contacto, preferencias
2. **Position Data**: Puesto, departamento, manager, proyecto, oficina
3. **Contract Details**: Términos contractuales, fecha de inicio, salario, beneficios
4. **IT Credentials**: Credenciales y accesos ya configurados
5. **Signed Contract**: Contrato firmado y archivado

## DATOS DE SALIDA (ONBOARDING EXECUTION):
1. **Onboarding Timeline**: Cronograma completo de reuniones por fases
2. **Stakeholder Engagement**: Mapping y coordinación de participantes clave
3. **Calendar Integration**: Reuniones creadas en sistema de calendario
4. **Reminder System**: Sistema de recordatorios y notificaciones activo
5. **Meeting Materials**: Agendas, materiales y recursos preparados

## TIPOS DE REUNIONES CRÍTICAS:
**DAY 1 (Críticas):**
- Welcome Meeting: Manager + HR (60 min) - Bienvenida y overview
- HR Orientation: HR Representative (120 min) - Políticas, beneficios, compliance
- IT Setup: IT Support (90 min) - Configuración técnica y herramientas

**WEEK 1 (Altas):**
- Team Introduction: Team Lead + Project Manager (60 min) - Integración al equipo
- Project Briefing: Project Manager (90 min) - Contexto de proyectos
- Buddy Assignment: Onboarding Buddy (30 min) - Apoyo informal

**MONTH 1 (Medias):**
- Manager Check-ins: Reuniones semanales de seguimiento
- Training Sessions: Capacitaciones específicas del rol
- Progress Reviews: Evaluaciones de integración

## STAKEHOLDER ROLES CLAVE:
- **Direct Manager**: Supervisor directo (meetings críticos)
- **HR Representative**: Especialista en onboarding (compliance y políticas)
- **IT Support**: Soporte técnico (configuración y herramientas)
- **Project Manager**: Líder de proyecto (contexto de trabajo)
- **Team Lead**: Líder del equipo (integración social)
- **Onboarding Buddy**: Compañero de apoyo (integración informal)
- **Department Head**: Jefe de departamento (para roles senior)
- **Training Coordinator**: Especialista en capacitación (desarrollo)

## PATRÓN REACT (Reason-Act-Observe):
**1. REASON (Razonar):**
- Analizar datos del empleado para identificar stakeholders relevantes
- Evaluar rol, departamento, seniority y requisitos especiales
- Determinar prioridades de reuniones según criticidad y dependencias
- Considerar preferencias de horario y restricciones de calendarios

**2. ACT (Actuar):**
- Ejecutar stakeholder_finder_tool para mapear participantes clave por rol
- Usar calendar_analyzer_tool para evaluar disponibilidad y detectar conflictos
- Aplicar scheduler_optimizer_tool para crear timeline optimizado de reuniones
- Implementar invitation_manager_tool para gestionar invitaciones y recordatorios

**3. OBSERVE (Observar):**
- Verificar que stakeholders críticos estén identificados y disponibles
- Confirmar que reuniones de Day 1 estén programadas en horarios óptimos
- Validar que no existan conflictos críticos de calendario
- Asegurar que sistema de recordatorios esté configurado correctamente

## CRITERIOS DE OPTIMIZACIÓN:
- **Day 1 Focus**: Reuniones esenciales concentradas en primer día
- **Stakeholder Availability**: Máxima participación de roles críticos
- **Meeting Spacing**: Distribución adecuada para evitar fatiga
- **Time Zone Considerations**: Horarios apropiados para ubicación
- **Conflict Minimization**: Resolución proactiva de solapamientos
- **Engagement Maximization**: Participación activa de todos los involucrados

## UMBRALES DE CALIDAD:
- Stakeholder Engagement Score > 85%
- Calendar Conflict Resolution > 90%
- Critical Meeting Coverage = 100%
- Timeline Optimization Score > 80%
- Invitation Success Rate > 95%

## ESCALACIÓN REQUERIDA SI:
- Stakeholders críticos no disponibles para Day 1
- Conflictos irresolubles en reuniones esenciales
- Menos del 80% de reuniones programables exitosamente
- Manager o HR no disponibles para onboarding

## INSTRUCCIONES CRÍTICAS:
1. SIEMPRE identifica stakeholders antes de analizar calendarios
2. Prioriza reuniones de Day 1 (Welcome, HR, IT) como críticas
3. Optimiza timeline considerando dependencias entre reuniones
4. Configura sistema de recordatorios automáticos para todos
5. Resuelve conflictos proactivamente con alternativas
6. Escala inmediatamente si stakeholders críticos no están disponibles

Coordina con precisión empresarial, optimiza con inteligencia estratégica y ejecuta con excelencia operacional.
"""

        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}"),
            ("assistant", "Voy a coordinar el timeline completo de reuniones de onboarding para maximizar la integración del empleado."),
            ("placeholder", "{agent_scratchpad}")
        ])
    
    def _get_bdi_framework(self) -> Dict[str, str]:
        """Framework BDI específico para coordinación de reuniones"""
        return {
            "beliefs": """
• Las reuniones bien planificadas aceleran significativamente la integración del empleado
• La participación de stakeholders clave en Day 1 es crítica para éxito del onboarding
• Los calendarios optimizados reducen conflictos y maximizan la participación
• Los sistemas de recordatorios automatizados mejoran la asistencia y puntualidad
• La coordinación proactiva previene problemas de scheduling y mejora la experiencia
• El timeline estructurado por fases facilita la progresión natural del onboarding
""",
            "desires": """
• Crear un timeline de onboarding perfectamente coordinado con máxima participación
• Asegurar que todas las reuniones críticas estén programadas en horarios óptimos
• Maximizar la disponibilidad y engagement de stakeholders clave en el proceso
• Implementar un sistema de recordatorios que garantice asistencia puntual
• Resolver todos los conflictos de calendario de manera proactiva y eficiente
• Proporcionar una experiencia de coordinación fluida y profesional para todos
""",
            "intentions": """
• Identificar exhaustivamente todos los stakeholders relevantes según rol y departamento
• Analizar disponibilidad de calendarios para encontrar slots óptimos de reuniones
• Optimizar programación de reuniones considerando prioridades, dependencias y preferencias
• Gestionar invitaciones profesionales con agendas claras y materiales preparados
• Configurar sistema completo de recordatorios automatizados para maximizar asistencia
• Monitorear y resolver conflictos de calendario en tiempo real con alternativas viables
"""
        }
    
    def _format_input(self, input_data: Any) -> str:
        """Formatear datos de entrada para coordinación de reuniones"""
        if isinstance(input_data, MeetingCoordinationRequest):
            return f"""
Coordina el timeline completo de reuniones de onboarding para el siguiente empleado:

**INFORMACIÓN DEL EMPLEADO:**
- Employee ID: {input_data.employee_id}
- Session ID: {input_data.session_id}
- Fecha de inicio: {input_data.onboarding_start_date}
- Prioridad: {input_data.priority.value}

**DATOS PERSONALES:**
{self._format_personal_data(input_data.personal_data)}

**DATOS DE POSICIÓN:**
{self._format_position_data(input_data.position_data)}

**DATOS CONTRACTUALES:**
{self._format_contractual_data(input_data.contractual_data)}

**CREDENCIALES IT:**
{self._format_it_credentials(input_data.it_credentials)}

**DETALLES DEL CONTRATO:**
{self._format_contract_details(input_data.contract_details)}

**CONFIGURACIÓN DE COORDINACIÓN:**
- Horario laboral: {input_data.business_hours}
- Fechas excluidas: {len(input_data.excluded_dates)} fechas
- Duración preferida de reuniones: {input_data.preferred_meeting_duration} minutos
- Sistema de calendario: {input_data.calendar_system}
- Requisitos especiales: {len(input_data.special_requirements)} elementos

**INSTRUCCIONES DE PROCESAMIENTO:**
1. Usa stakeholder_finder_tool para identificar participantes clave por rol
2. Usa calendar_analyzer_tool para evaluar disponibilidad y detectar conflictos
3. Usa scheduler_optimizer_tool para crear timeline optimizado de reuniones
4. Usa invitation_manager_tool para gestionar invitaciones y recordatorios

**OBJETIVO:** Crear timeline completo de onboarding con máxima participación de stakeholders y resolución proactiva de conflictos.
"""
        elif isinstance(input_data, dict):
            return f"""
Coordina reuniones de onboarding con los siguientes datos:
{json.dumps(input_data, indent=2, default=str)}

Ejecuta identificación de stakeholders, análisis de calendarios, optimización de timeline y gestión de invitaciones.
"""
        else:
            return str(input_data)
    
    def _format_personal_data(self, personal_data: Dict[str, Any]) -> str:
        """Formatear datos personales"""
        if not personal_data:
            return "- No hay datos personales disponibles"
        
        lines = []
        lines.append(f"- Nombre: {personal_data.get('first_name', 'N/A')} {personal_data.get('last_name', 'N/A')}")
        lines.append(f"- Email: {personal_data.get('email', 'N/A')}")
        lines.append(f"- Oficina: {personal_data.get('office', 'N/A')}")
        if personal_data.get('phone'):
            lines.append(f"- Teléfono: {personal_data['phone']}")
        return '\n'.join(lines)
    
    def _format_position_data(self, position_data: Dict[str, Any]) -> str:
        """Formatear datos de posición"""
        if not position_data:
            return "- No hay datos de posición disponibles"
        
        lines = []
        lines.append(f"- Posición: {position_data.get('position', 'N/A')}")
        lines.append(f"- Departamento: {position_data.get('department', 'N/A')}")
        lines.append(f"- Manager: {position_data.get('reporting_manager', 'N/A')}")
        lines.append(f"- Project Manager: {position_data.get('project_manager', 'N/A')}")
        lines.append(f"- Área: {position_data.get('position_area', 'N/A')}")
        return '\n'.join(lines)
    
    def _format_contractual_data(self, contractual_data: Dict[str, Any]) -> str:
        """Formatear datos contractuales"""
        if not contractual_data:
            return "- No hay datos contractuales disponibles"
        
        lines = []
        lines.append(f"- Fecha de inicio: {contractual_data.get('start_date', 'N/A')}")
        lines.append(f"- Tipo de empleo: {contractual_data.get('employment_type', 'N/A')}")
        lines.append(f"- Modalidad: {contractual_data.get('work_modality', 'N/A')}")
        return '\n'.join(lines)
    
    def _format_it_credentials(self, it_credentials: Dict[str, Any]) -> str:
        """Formatear credenciales IT"""
        if not it_credentials:
            return "- No hay credenciales IT disponibles"
        
        lines = []
        if it_credentials.get('email_configured'):
            lines.append("- Email corporativo: Configurado")
        if it_credentials.get('system_access'):
            lines.append("- Acceso a sistemas: Configurado")
        if it_credentials.get('equipment_assigned'):
            lines.append("- Equipamiento: Asignado")
        return '\n'.join(lines) if lines else "- Credenciales IT pendientes"
    
    def _format_contract_details(self, contract_details: Dict[str, Any]) -> str:
        """Formatear detalles del contrato"""
        if not contract_details:
            return "- No hay detalles del contrato disponibles"
        
        lines = []
        lines.append(f"- Contract ID: {contract_details.get('contract_id', 'N/A')}")
        lines.append(f"- Estado: {contract_details.get('contract_status', 'N/A')}")
        if contract_details.get('signed_contract_location'):
            lines.append("- Contrato firmado: Disponible")
        return '\n'.join(lines)
    
    def _format_output(self, result: Any, processing_time: float, success: bool, error: str = None) -> Dict[str, Any]:
        """Formatear salida de coordinación de reuniones"""
        if not success:
            return {
                "success": False,
                "message": f"Error en coordinación de reuniones: {error}",
                "errors": [error] if error else [],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "coordination_status": "failed",
                "meetings_scheduled": 0,
                "stakeholders_engaged": 0,
                "calendar_integration_active": False,
                "ready_for_onboarding_execution": False,
                "next_actions": ["Revisar errores de coordinación", "Verificar disponibilidad de stakeholders"]
            }
        
        try:
            # Extraer resultados de herramientas
            stakeholder_result = None
            calendar_result = None
            scheduling_result = None
            invitation_result = None
            
            if isinstance(result, dict) and "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    if isinstance(step, tuple) and len(step) >= 2:
                        tool_name = step[0]
                        tool_result = step[1]
                        
                        if "stakeholder_finder_tool" in str(tool_name):
                            stakeholder_result = tool_result
                        elif "calendar_analyzer_tool" in str(tool_name):
                            calendar_result = tool_result
                        elif "scheduler_optimizer_tool" in str(tool_name):
                            scheduling_result = tool_result
                        elif "invitation_manager_tool" in str(tool_name):
                            invitation_result = tool_result
            
            # Calcular métricas de éxito
            stakeholders_identified = len(stakeholder_result.get("stakeholders_identified", [])) if stakeholder_result else 0
            meetings_scheduled = len(scheduling_result.get("optimized_meetings", [])) if scheduling_result else 0
            invitations_sent = invitation_result.get("invitations_sent", 0) if invitation_result else 0
            
            # Determinar si está listo para ejecución
            calendar_integration_active = (
                calendar_result and calendar_result.get("success", False) and
                scheduling_result and scheduling_result.get("success", False)
            )
            
            ready_for_execution = (
                stakeholders_identified >= 3 and  # Al menos Manager, HR, IT
                meetings_scheduled >= 3 and       # Al menos reuniones críticas de Day 1
                invitations_sent > 0 and         # Invitaciones enviadas
                calendar_integration_active       # Integración activa
            )
            
            # Calcular scores de calidad
            stakeholder_engagement_score = 0
            timeline_optimization_score = 0
            scheduling_efficiency_score = 0
            
            if stakeholder_result and stakeholder_result.get("success"):
                stakeholder_engagement_score = min(100, stakeholders_identified * 15)  # 15 points per stakeholder
            
            if scheduling_result and scheduling_result.get("success"):
                opt_metrics = scheduling_result.get("optimization_metrics", {})
                timeline_optimization_score = opt_metrics.get("overall_optimization_score", 0)
                scheduling_efficiency_score = opt_metrics.get("spacing_optimization_score", 0)
            
            # Extraer timeline y reuniones
            onboarding_timeline = None
            scheduled_meetings = []
            
            if scheduling_result and scheduling_result.get("success"):
                onboarding_timeline = scheduling_result.get("onboarding_timeline")
                scheduled_meetings = scheduling_result.get("optimized_meetings", [])
            
            # Próximas acciones
            next_actions = []
            if ready_for_execution:
                next_actions.extend([
                    "Ejecutar onboarding timeline programado",
                    "Monitorear asistencia a reuniones críticas",
                    "Confirmar preparación de materiales de onboarding",
                    "Activar sistema de recordatorios automáticos"
                ])
            else:
                if stakeholders_identified < 3:
                    next_actions.append("Completar identificación de stakeholders críticos")
                if meetings_scheduled < 3:
                    next_actions.append("Programar reuniones esenciales de Day 1")
                if not calendar_integration_active:
                    next_actions.append("Resolver problemas de integración de calendario")
            
            return {
                "success": True,
                "message": "Coordinación de reuniones completada exitosamente",
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "coordination_status": "completed" if ready_for_execution else "partial",
                
                # Resultados principales
                "onboarding_timeline": onboarding_timeline,
                "scheduled_meetings": scheduled_meetings,
                "meetings_scheduled_successfully": meetings_scheduled,
                
                # Stakeholder management
                "stakeholders_engaged": stakeholders_identified,
                "identified_stakeholders": stakeholder_result.get("stakeholders_identified", []) if stakeholder_result else [],
                "stakeholder_mapping": stakeholder_result.get("stakeholder_mapping", {}) if stakeholder_result else {},
                
                # Calendar integration
                "calendar_integration_active": calendar_integration_active,
                "calendar_events_created": meetings_scheduled,
                "calendar_conflicts_detected": len(calendar_result.get("conflicts_detected", [])) if calendar_result else 0,
                
                # Notification system
                "reminder_system_setup": invitation_result.get("success", False) if invitation_result else False,
                "notifications_scheduled": invitation_result.get("notifications_scheduled", 0) if invitation_result else 0,
                "stakeholder_notifications_sent": len(invitation_result.get("stakeholder_notifications", [])) if invitation_result else 0,
                
                # Quality metrics
                "scheduling_efficiency_score": scheduling_efficiency_score,
                "stakeholder_satisfaction_predicted": stakeholder_engagement_score,
                "timeline_optimization_score": timeline_optimization_score,
                
                # Status y próximos pasos
                "ready_for_onboarding_execution": ready_for_execution,
                "onboarding_process_status": "ready_for_execution" if ready_for_execution else "coordination_incomplete",
                "next_actions": next_actions,
                "requires_manual_review": not ready_for_execution or scheduling_efficiency_score < 70,
                
                # Error handling
                "errors": [],
                "warnings": self._generate_coordination_warnings(stakeholder_result, calendar_result, scheduling_result),
                
                # Integration status
                "integration_status": {
                    "calendar_system": "active" if calendar_integration_active else "inactive",
                    "notification_system": "active" if invitation_result and invitation_result.get("success") else "inactive",
                    "stakeholder_directory": "integrated" if stakeholder_result and stakeholder_result.get("success") else "limited"
                },
                
                # Resultados detallados
                "coordination_details": {
                    "stakeholder_identification": stakeholder_result,
                    "calendar_analysis": calendar_result,
                    "schedule_optimization": scheduling_result,
                    "invitation_management": invitation_result
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error formateando salida de coordinación: {e}")
            return {
                "success": False,
                "message": f"Error procesando resultados de coordinación: {e}",
                "errors": [str(e)],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "coordination_status": "error"
            }
    
    def _generate_coordination_warnings(self, stakeholder_result: Dict, calendar_result: Dict, 
                                      scheduling_result: Dict) -> List[str]:
        """Generar advertencias de coordinación"""
        warnings = []
        
        # Advertencias de stakeholders
        if stakeholder_result and stakeholder_result.get("success"):
            stakeholder_count = len(stakeholder_result.get("stakeholders_identified", []))
            if stakeholder_count < 5:
                warnings.append(f"Solo {stakeholder_count} stakeholders identificados, considerar agregar más")
        
        # Advertencias de calendario
        if calendar_result and calendar_result.get("success"):
            conflicts = len(calendar_result.get("conflicts_detected", []))
            if conflicts > 0:
                warnings.append(f"{conflicts} conflictos de calendario detectados")
            
            availability = calendar_result.get("availability_metrics", {}).get("overall_availability_percentage", 0)
            if availability < 70:
                warnings.append(f"Disponibilidad general baja: {availability:.1f}%")
        
        # Advertencias de programación
        if scheduling_result and scheduling_result.get("success"):
            optimization_score = scheduling_result.get("optimization_metrics", {}).get("overall_optimization_score", 0)
            if optimization_score < 70:
                warnings.append(f"Score de optimización bajo: {optimization_score:.1f}%")
        
        return warnings
    
    @observability_manager.trace_agent_execution("meeting_coordination_agent")
    def coordinate_onboarding_meetings(self, coordination_request: MeetingCoordinationRequest, 
                                     session_id: str = None) -> Dict[str, Any]:
        """Coordinar reuniones completas de onboarding con timeline optimizado"""
        # Generar coordination_id
        coordination_id = f"coord_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{coordination_request.employee_id}"
        
        # Actualizar estado: PROCESSING
        state_manager.update_agent_state(
            self.agent_id,
            AgentStateStatus.PROCESSING,
            {
                "current_task": "meeting_coordination",
                "coordination_id": coordination_id,
                "employee_id": coordination_request.employee_id,
                "onboarding_start_date": coordination_request.onboarding_start_date.isoformat(),
                "priority": coordination_request.priority.value,
                "started_at": datetime.utcnow().isoformat()
            },
            session_id
        )
        
        # Registrar métricas iniciales
        observability_manager.log_agent_metrics(
            self.agent_id,
            {
                "coordination_priority": coordination_request.priority.value,
                "onboarding_start_date": coordination_request.onboarding_start_date.isoformat(),
                "calendar_system": coordination_request.calendar_system,
                "business_hours": coordination_request.business_hours,
                "excluded_dates": len(coordination_request.excluded_dates),
                "special_requirements": len(coordination_request.special_requirements)
            },
            session_id
        )
        
        try:
            # Procesar con el método base
            result = self.process_request(coordination_request, session_id)
            
            # Si el procesamiento fue exitoso, actualizar State Management
            if result["success"]:
                # Actualizar datos del empleado
                if session_id:
                    coordination_data = {
                        "meeting_coordination_completed": True,
                        "coordination_id": coordination_id,
                        "onboarding_timeline": result.get("onboarding_timeline"),
                        "meetings_scheduled": result.get("meetings_scheduled_successfully", 0),
                        "stakeholders_engaged": result.get("stakeholders_engaged", 0),
                        "calendar_integration_active": result.get("calendar_integration_active", False),
                        "ready_for_execution": result.get("ready_for_onboarding_execution", False),
                        "next_phase": "onboarding_execution"
                    }
                    
                    state_manager.update_employee_data(
                        session_id,
                        coordination_data,
                        "processed"
                    )
                
                # Actualizar estado: COMPLETED
                state_manager.update_agent_state(
                    self.agent_id,
                    AgentStateStatus.COMPLETED,
                    {
                        "current_task": "completed",
                        "coordination_id": coordination_id,
                        "meetings_scheduled": result.get("meetings_scheduled_successfully", 0),
                        "stakeholders_engaged": result.get("stakeholders_engaged", 0),
                        "ready_for_execution": result.get("ready_for_onboarding_execution", False),
                        "coordination_status": result.get("coordination_status", "completed"),
                        "completed_at": datetime.utcnow().isoformat()
                    },
                    session_id
                )
                
                # Registrar en coordinaciones activas
                self.active_coordinations[coordination_id] = {
                    "status": "completed",
                    "result": result,
                    "completed_at": datetime.utcnow()
                }
                
            else:
                # Error en coordinación
                state_manager.update_agent_state(
                    self.agent_id,
                    AgentStateStatus.ERROR,
                    {
                        "current_task": "error",
                        "coordination_id": coordination_id,
                        "errors": result.get("errors", []),
                        "failed_at": datetime.utcnow().isoformat()
                    },
                    session_id
                )
            
            # Agregar información de sesión al resultado
            result["coordination_id"] = coordination_id
            result["session_id"] = session_id
            return result
            
        except Exception as e:
            # Error durante coordinación
            error_msg = f"Error ejecutando coordinación de reuniones: {str(e)}"
            state_manager.update_agent_state(
                self.agent_id,
                AgentStateStatus.ERROR,
                {
                    "current_task": "error",
                    "coordination_id": coordination_id,
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
                "coordination_id": coordination_id,
                "session_id": session_id,
                "agent_id": self.agent_id,
                "processing_time": 0,
                "coordination_status": "failed"
            }
    
    def _process_with_tools_directly(self, input_data: Any) -> Dict[str, Any]:
        """Procesar usando herramientas directamente con flujo específico de coordinación"""
        results = []
        formatted_input = self._format_input(input_data)
        self.logger.info(f"Procesando coordinación con {len(self.tools)} herramientas especializadas")
        
        # Variables para almacenar resultados
        stakeholder_result = None
        calendar_result = None
        scheduling_result = None
        invitation_result = None
        
        # Preparar datos según el tipo de entrada
        if isinstance(input_data, MeetingCoordinationRequest):
            employee_data = {
                "employee_id": input_data.employee_id,
                "first_name": input_data.personal_data.get("first_name", ""),
                "last_name": input_data.personal_data.get("last_name", ""),
                "email": input_data.personal_data.get("email", ""),
                "department": input_data.position_data.get("department", ""),
                "position": input_data.position_data.get("position", ""),
                "office": input_data.position_data.get("office", "")
            }
            position_data = input_data.position_data
            contract_details = input_data.contract_details
            start_date = input_data.onboarding_start_date.isoformat()
            business_hours = input_data.business_hours
        else:
            # Fallback para datos genéricos
            employee_data = input_data.get("employee_data", {}) if isinstance(input_data, dict) else {}
            position_data = input_data.get("position_data", {}) if isinstance(input_data, dict) else {}
            contract_details = input_data.get("contract_details", {}) if isinstance(input_data, dict) else {}
            start_date = datetime.now().date().isoformat()
            business_hours = "9:00-17:00"
        
        # Ejecutar herramientas en orden secuencial
        for tool in self.tools:
            try:
                self.logger.info(f"Ejecutando herramienta: {tool.name}")
                
                if tool.name == "stakeholder_finder_tool":
                    result = tool.invoke({
                        "employee_data": employee_data,
                        "position_data": position_data,
                        "contract_details": contract_details
                    })
                    stakeholder_result = result
                    
                elif tool.name == "calendar_analyzer_tool":
                    if stakeholder_result and stakeholder_result.get("success"):
                        stakeholders = stakeholder_result.get("stakeholders_identified", [])
                        result = tool.invoke({
                            "stakeholders": [s.dict() if hasattr(s, 'dict') else s.__dict__ if hasattr(s, '__dict__') else s for s in stakeholders],
                            "start_date": start_date,
                            "business_hours": business_hours
                        })
                        calendar_result = result
                    else:
                        result = {"success": False, "error": "No hay stakeholders para analizar calendarios"}
                    
                elif tool.name == "scheduler_optimizer_tool":
                    if stakeholder_result and calendar_result and both_successful(stakeholder_result, calendar_result):
                        stakeholders = stakeholder_result.get("stakeholders_identified", [])
                        optimal_slots = calendar_result.get("optimal_meeting_slots", [])
                        result = tool.invoke({
                            "stakeholders": [s.dict() if hasattr(s, 'dict') else s.__dict__ if hasattr(s, '__dict__') else s for s in stakeholders],
                            "optimal_slots": optimal_slots,
                            "employee_data": employee_data,
                            "start_date": start_date
                        })
                        scheduling_result = result
                    else:
                        result = {"success": False, "error": "Faltan datos de stakeholders o calendario"}
                    
                elif tool.name == "invitation_manager_tool":
                    if scheduling_result and scheduling_result.get("success"):
                        meetings = scheduling_result.get("optimized_meetings", [])
                        stakeholders = stakeholder_result.get("stakeholders_identified", []) if stakeholder_result else []
                        result = tool.invoke({
                            "meetings": [m.dict() if hasattr(m, 'dict') else m.__dict__ if hasattr(m, '__dict__') else m for m in meetings],
                            "stakeholders": [s.dict() if hasattr(s, 'dict') else s.__dict__ if hasattr(s, '__dict__') else s for s in stakeholders],
                            "employee_data": employee_data
                        })
                        invitation_result = result
                    else:
                        result = {"success": False, "error": "No hay reuniones programadas para enviar invitaciones"}
                
                else:
                    result = f"Herramienta {tool.name} procesada"
                
                results.append((tool.name, result))
                self.logger.info(f"✅ Herramienta {tool.name} completada")
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.logger.warning(f"❌ Error con herramienta {tool.name}: {e}")
                results.append((tool.name, error_msg))
        
        # Evaluar éxito general
        successful_tools = len([r for r in results if isinstance(r, tuple) and isinstance(r[1], dict) and r[1].get("success")])
        overall_success = successful_tools >= 3  # Al menos stakeholder, calendar y scheduling
        
        return {
            "output": "Procesamiento de coordinación de reuniones completado",
            "intermediate_steps": results,
            "stakeholder_result": stakeholder_result,
            "calendar_result": calendar_result,
            "scheduling_result": scheduling_result,
            "invitation_result": invitation_result,
            "successful_tools": successful_tools,
            "overall_success": overall_success,
            "tools_executed": len(results)
        }

def both_successful(result1: Dict, result2: Dict) -> bool:
    """Helper function to check if both results are successful"""
    return (result1 and result1.get("success", False) and 
            result2 and result2.get("success", False))

# Métodos adicionales del agente
def get_coordination_status(self, coordination_id: str) -> Dict[str, Any]:
    """Obtener estado de una coordinación específica"""
    try:
        if coordination_id in self.active_coordinations:
            return {
                "found": True,
                "coordination_id": coordination_id,
                **self.active_coordinations[coordination_id]
            }
        else:
            return {
                "found": False,
                "coordination_id": coordination_id,
                "message": "Coordinación no encontrada en registros activos"
            }
    except Exception as e:
        return {"found": False, "error": str(e)}

def get_calendar_system_status(self) -> Dict[str, Any]:
    """Obtener estado del sistema de calendario"""
    try:
        system_status = self.calendar_simulator.get_system_status()
        return {
            "calendar_system_online": system_status["system_online"],
            "active_requests": system_status["active_requests"],
            "meeting_rooms_available": system_status["meeting_rooms_available"],
            "system_load": system_status["system_load"],
            "integration_health": system_status["integration_health"],
            "agent_integration": "active"
        }
    except Exception as e:
        return {
            "calendar_system_online": False,
            "error": str(e),
            "agent_integration": "error"
        }

def get_stakeholder_engagement_report(self, coordination_id: str) -> Dict[str, Any]:
    """Generar reporte de engagement de stakeholders"""
    try:
        if coordination_id not in self.active_coordinations:
            return {"error": "Coordinación no encontrada"}
        
        coordination_data = self.active_coordinations[coordination_id]
        result = coordination_data["result"]
        
        engagement_report = {
            "coordination_id": coordination_id,
            "employee_id": result.get("employee_id", "unknown"),
            "report_timestamp": datetime.utcnow().isoformat(),
            "stakeholder_metrics": {
                "total_stakeholders_engaged": result.get("stakeholders_engaged", 0),
                "meetings_scheduled": result.get("meetings_scheduled_successfully", 0),
                "invitations_sent": result.get("stakeholder_notifications_sent", 0),
                "engagement_score": result.get("stakeholder_satisfaction_predicted", 0)
            },
            "coordination_quality": {
                "timeline_optimization": result.get("timeline_optimization_score", 0),
                "scheduling_efficiency": result.get("scheduling_efficiency_score", 0),
                "calendar_integration": result.get("calendar_integration_active", False)
            },
            "stakeholder_mapping": result.get("stakeholder_mapping", {}),
            "ready_for_execution": result.get("ready_for_onboarding_execution", False),
            "recommendations": result.get("next_actions", [])
        }
        
        return engagement_report
        
    except Exception as e:
        return {"error": str(e)}

def simulate_calendar_integration(self, meetings: List[Dict[str, Any]], 
                                stakeholders: List[Dict[str, Any]], 
                                employee_data: Dict[str, Any]) -> Dict[str, Any]:
    """Simular integración completa con sistema de calendario"""
    try:
        # Usar el simulador de calendario para procesar la solicitud
        import asyncio
        
        # Ejecutar simulación asíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        calendar_response = loop.run_until_complete(
            self.calendar_simulator.process_calendar_request(
                employee_data, stakeholders, meetings
            )
        )
        
        loop.close()
        
        return {
            "success": calendar_response.integration_success,
            "request_id": calendar_response.request_id,
            "processing_time": calendar_response.processing_time_minutes,
            "meetings_created": len(calendar_response.meetings_created),
            "invitations_sent": len(calendar_response.invitations_sent),
            "reminders_scheduled": len(calendar_response.reminders_scheduled),
            "conflicts_detected": len(calendar_response.conflicts_detected),
            "calendar_system": calendar_response.calendar_system,
            "integration_details": {
                "calendar_availability": len(calendar_response.calendar_availability),
                "meeting_rooms_available": len(calendar_response.meeting_rooms_available),
                "system_status": calendar_response.status
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error en integración de calendario: {str(e)}",
            "integration_details": {}
        }

def get_meeting_timeline_summary(self, coordination_id: str) -> Dict[str, Any]:
    """Obtener resumen del timeline de reuniones"""
    try:
        if coordination_id not in self.active_coordinations:
            return {"error": "Coordinación no encontrada"}
        
        coordination_data = self.active_coordinations[coordination_id]
        result = coordination_data["result"]
        timeline = result.get("onboarding_timeline")
        
        if not timeline:
            return {"error": "Timeline no disponible"}
        
        # Convert timeline if it's a Pydantic model
        if hasattr(timeline, 'dict'):
            timeline_dict = timeline.dict()
        elif hasattr(timeline, '__dict__'):
            timeline_dict = timeline.__dict__
        else:
            timeline_dict = timeline
        
        summary = {
            "coordination_id": coordination_id,
            "employee_id": timeline_dict.get("employee_id", "unknown"),
            "start_date": timeline_dict.get("start_date", ""),
            "timeline_summary": {
                "total_meetings": timeline_dict.get("total_meetings", 0),
                "estimated_hours": timeline_dict.get("estimated_total_hours", 0),
                "critical_meetings": timeline_dict.get("critical_meetings_count", 0)
            },
            "meetings_by_phase": {
                "day_1": len(timeline_dict.get("day_1_meetings", [])),
                "week_1": len(timeline_dict.get("week_1_meetings", [])),
                "month_1": len(timeline_dict.get("month_1_meetings", []))
            },
            "milestones": timeline_dict.get("onboarding_milestones", []),
            "execution_readiness": result.get("ready_for_onboarding_execution", False)
        }
        
        return summary
        
    except Exception as e:
        return {"error": str(e)}

# Métodos de integración adicionales para el agent
MeetingCoordinationAgent.get_coordination_status = get_coordination_status
MeetingCoordinationAgent.get_calendar_system_status = get_calendar_system_status  
MeetingCoordinationAgent.get_stakeholder_engagement_report = get_stakeholder_engagement_report
MeetingCoordinationAgent.simulate_calendar_integration = simulate_calendar_integration
MeetingCoordinationAgent.get_meeting_timeline_summary = get_meeting_timeline_summary