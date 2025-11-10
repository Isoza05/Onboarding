from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from agents.base.base_agent import BaseAgent
from datetime import datetime, timedelta
import json

# Imports del recovery agent
from .tools import (
    retry_manager_tool, state_restorer_tool,
    circuit_breaker_tool, workflow_resumer_tool
)
from .schemas import (
    RecoveryRequest, RecoveryResult, RecoveryStatus, RecoveryAction,
    RecoveryStrategy, RecoveryPriority, SystemRecoveryState, RecoveryAttempt
)

# Imports para integración
from core.state_management.state_manager import state_manager
from core.state_management.models import AgentStateStatus, OnboardingPhase
from core.observability import observability_manager
from core.database import db_manager

class RecoveryAgent(BaseAgent):
    """
    Recovery Agent - Especialista en recuperación automática y restauración de estados.
    
    Implementa arquitectura BDI:
    - Beliefs: La recuperación automática rápida minimiza el impacto en el negocio
    - Desires: Restaurar operaciones normales con mínima intervención humana
    - Intentions: Ejecutar recuperación, restaurar estados, reanudar workflows
    
    Recibe clasificaciones del Error Classification Agent y ejecuta estrategias
    de recuperación automática apropiadas.
    """

    def __init__(self):
        super().__init__(
            agent_id="recovery_agent",
            agent_name="System Recovery & State Restoration Agent"
        )
        
        # Configuración específica del recovery
        self.active_recoveries = {}
        self.recovery_history = {}
        self.circuit_breaker_states = {}
        self.recovery_metrics = {
            "total_recoveries": 0,
            "successful_recoveries": 0,
            "failed_recoveries": 0,
            "average_recovery_time": 0.0
        }
        
        # Registrar agente en state management
        state_manager.register_agent(
            self.agent_id,
            {
                "version": "1.0",
                "specialization": "system_recovery_state_restoration",
                "tools_count": len(self.tools),
                "capabilities": {
                    "automatic_retry": True,
                    "state_restoration": True,
                    "circuit_breaker_management": True,
                    "workflow_resumption": True,
                    "rollback_recovery": True,
                    "graceful_degradation": True
                },
                "recovery_strategies": [strategy.value for strategy in RecoveryStrategy],
                "recovery_actions": [action.value for action in RecoveryAction],
                "recovery_priorities": [priority.value for priority in RecoveryPriority],
                "integration_points": {
                    "error_classification_agent": "source",
                    "human_handoff_agent": "escalation_target",
                    "state_management": "active",
                    "observability": "active",
                    "circuit_breakers": "managed"
                }
            }
        )
        
        self.logger.info("Recovery Agent integrado con State Management y Error Handling System")

    def _initialize_tools(self) -> List:
        """Inicializar herramientas de recuperación"""
        return [
            retry_manager_tool,
            state_restorer_tool,
            circuit_breaker_tool,
            workflow_resumer_tool
        ]

    def _create_prompt(self) -> ChatPromptTemplate:
        """Crear prompt con framework BDI y patrón ReAct para recuperación"""
        bdi = self._get_bdi_framework()
        
        system_prompt = f"""
Eres el Recovery Agent, especialista en recuperación automática y restauración de estados del sistema de onboarding.

## FRAMEWORK BDI (Belief-Desire-Intention)
**BELIEFS (Creencias):**
{bdi['beliefs']}

**DESIRES (Deseos):**
{bdi['desires']}

**INTENTIONS (Intenciones):**
{bdi['intentions']}

## HERRAMIENTAS DE RECUPERACIÓN:
- retry_manager_tool: Gestiona reintentos automáticos con estrategias de backoff inteligentes
- state_restorer_tool: Restaura estados de agentes y sistema a puntos conocidos estables
- circuit_breaker_tool: Gestiona circuit breakers para prevenir cascading failures
- workflow_resumer_tool: Reanuda workflows interrumpidos desde checkpoints seguros

## ESTRATEGIAS DE RECUPERACIÓN:
- **IMMEDIATE_RETRY**: Reintentos inmediatos para errores transitorios
- **EXPONENTIAL_BACKOFF**: Reintentos con delays exponenciales para sobrecarga
- **CIRCUIT_BREAKER**: Protección contra cascading failures
- **GRACEFUL_DEGRADATION**: Operación reducida manteniendo funcionalidad crítica
- **STATE_ROLLBACK**: Rollback a estados previos conocidos estables
- **SERVICE_RESTART**: Reinicio de servicios específicos problemáticos
- **BYPASS_AND_CONTINUE**: Bypass de componentes fallidos para continuar pipeline

## ACCIONES DE RECUPERACIÓN:
- **AGENT_RESTART**: Reinicio de agentes específicos con limpieza de estado
- **PIPELINE_ROLLBACK**: Rollback del pipeline a checkpoint anterior
- **STATE_RESTORATION**: Restauración de estados a snapshots válidos
- **RETRY_OPERATION**: Reintento de operaciones fallidas con configuración optimizada
- **CIRCUIT_BREAKER_RESET**: Reset de circuit breakers cuando servicios se recuperan
- **DEPENDENCY_CHECK**: Verificación y reparación de dependencias
- **RESOURCE_CLEANUP**: Limpieza de recursos bloqueados o corruptos
- **CACHE_CLEAR**: Limpieza de caches para eliminar datos stale

## NIVELES DE PRIORIDAD:
- **EMERGENCY**: Recuperación inmediata - sistema completamente bloqueado
- **CRITICAL**: Alta prioridad - funcionalidad crítica afectada
- **HIGH**: Prioridad alta - impacto significativo en operaciones
- **MEDIUM**: Prioridad media - degradación parcial de servicio
- **LOW**: Prioridad baja - problemas menores sin impacto crítico

## PATRÓN REACT (Reason-Act-Observe):
**1. REASON (Razonar):**
- Analizar clasificación de error recibida del Error Classification Agent
- Evaluar estado actual del sistema y agentes afectados
- Determinar estrategia de recuperación óptima basada en tipo y severidad
- Identificar dependencias y riesgos de la recuperación propuesta

**2. ACT (Actuar):**
- Ejecutar retry_manager_tool para reintentos automáticos inteligentes
- Usar state_restorer_tool para rollback y restauración de estados
- Aplicar circuit_breaker_tool para protección contra failures en cascada
- Implementar workflow_resumer_tool para continuar desde checkpoints

**3. OBSERVE (Observar):**
- Verificar que recuperación restaure funcionalidad sin efectos secundarios
- Confirmar que estados restaurados sean consistentes y válidos
- Validar que pipeline pueda continuar desde punto de recuperación
- Monitorear salud del sistema post-recuperación para detectar regresiones

## CRITERIOS DE ÉXITO DE RECUPERACIÓN:
- **Funcionalidad Restaurada**: Sistema operando dentro de parámetros normales
- **Estado Consistente**: Todos los componentes en estados válidos y sincronizados
- **Pipeline Operativo**: Workflow puede continuar desde punto de recuperación
- **Performance Aceptable**: Tiempos de respuesta dentro de rangos esperados
- **Sin Degradación**: No hay impacto negativo en otros componentes

## ESCALACIÓN A HUMAN HANDOFF:
- **Múltiples Intentos Fallidos**: >3 intentos de recuperación sin éxito
- **Corrupción de Datos**: Detección de inconsistencias críticas de datos
- **Dependencias Externas**: Fallos en sistemas externos fuera de control
- **Tiempo Límite Excedido**: Recuperación toma más del timeout configurado
- **Riesgo de Seguridad**: Detección de problemas de seguridad o compliance

## INTEGRACIÓN CON SISTEMA:
- **Input**: Recibe RecoveryRequest del Error Classification Agent
- **State Management**: Actualiza y restaura estados de agentes y empleados
- **Circuit Breakers**: Gestiona protección contra cascading failures
- **Observability**: Registra métricas y trazas de recuperación
- **Output**: Produce RecoveryResult para Human Handoff o Progress Tracker

## INSTRUCCIONES CRÍTICAS:
1. SIEMPRE evalúa riesgo antes de ejecutar recuperación automática
2. Usa estrategia menos invasiva primero, escalando según necesidad
3. Mantén snapshots de estado antes de modificaciones críticas
4. Verifica integridad del sistema después de cada acción de recuperación
5. Escala a Human Handoff cuando recuperación automática no es viable
6. Documenta lecciones aprendidas para mejorar estrategias futuras

Recupera con precisión quirúrgica, restaura con integridad absoluta y reanuda con continuidad perfecta.
"""

        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}"),
            ("assistant", "Voy a ejecutar la recuperación del sistema usando la estrategia más apropiada para restaurar operaciones normales."),
            ("placeholder", "{agent_scratchpad}")
        ])

    def _get_bdi_framework(self) -> Dict[str, str]:
        """Framework BDI específico para recuperación"""
        return {
            "beliefs": """
• La recuperación automática rápida minimiza el tiempo de inactividad y impacto en el negocio
• Los errores transitorios a menudo se resuelven con reintentos inteligentes y backoff apropiado
• La restauración de estados a puntos conocidos estables es más segura que reparaciones ad-hoc
• Los circuit breakers previenen cascading failures y protegen la estabilidad del sistema
• La reanudación de workflows desde checkpoints preserva trabajo completado y reduce reprocessing
• La escalación temprana a humanos es preferible a intentos de recuperación prolongados
""",
            "desires": """
• Restaurar operaciones normales del sistema con mínima intervención humana requerida
• Minimizar tiempo de recuperación mientras se mantiene integridad de datos y estado
• Prevenir propagación de errores a otros componentes del sistema
• Preservar trabajo completado y continuar desde puntos de progreso válidos
• Proporcionar recuperación transparente que no impacte la experiencia del empleado
• Generar insights de recuperación para prevenir futuros problemas similares
""",
            "intentions": """
• Evaluar y ejecutar estrategias de recuperación apropiadas basadas en clasificación de errores
• Implementar reintentos inteligentes con backoff exponencial para errores transitorios
• Restaurar estados de agentes y sistema a snapshots conocidos estables cuando sea necesario
• Gestionar circuit breakers para proteger contra cascading failures y sobrecargas
• Reanudar workflows interrumpidos desde checkpoints seguros preservando progreso
• Escalar a Human Handoff cuando recuperación automática no sea viable o segura
"""
        }

    def _format_input(self, input_data: Any) -> str:
        """Formatear datos de entrada para recuperación"""
        if isinstance(input_data, RecoveryRequest):
            return f"""
Ejecuta recuperación del sistema para el siguiente caso:

**INFORMACIÓN DE RECUPERACIÓN:**
- Recovery ID: {input_data.recovery_id}
- Employee ID: {input_data.employee_id}
- Session ID: {input_data.session_id}
- Error Classification ID: {input_data.error_classification_id}

**DETALLES DEL ERROR:**
- Categoría: {input_data.error_category}
- Severidad: {input_data.error_severity}
- Agente Fallido: {input_data.failed_agent_id or 'No especificado'}

**ESTRATEGIA DE RECUPERACIÓN:**
- Estrategia: {input_data.recovery_strategy.value}
- Acciones: {[action.value for action in input_data.recovery_actions]}
- Prioridad: {input_data.recovery_priority.value}

**CONFIGURACIÓN DE RECUPERACIÓN:**
- Máximos reintentos: {input_data.max_retry_attempts}
- Delay entre reintentos: {input_data.retry_delay_seconds}s
- Timeout: {input_data.timeout_minutes} minutos
- Permite recuperación parcial: {'Sí' if input_data.allow_partial_recovery else 'No'}

**CONTEXTO DEL ERROR:**
{json.dumps(input_data.error_context, indent=2, default=str)}

**INSTRUCCIONES DE RECUPERACIÓN:**
1. Usa retry_manager_tool para reintentos automáticos si la estrategia lo requiere
2. Usa state_restorer_tool para restauración de estados si hay corrupción
3. Usa circuit_breaker_tool para gestión de protección del sistema
4. Usa workflow_resumer_tool para reanudar desde checkpoints seguros

**OBJETIVO:** Restaurar operaciones normales minimizando tiempo de inactividad e impacto.
"""

        elif isinstance(input_data, dict):
            return f"""
Ejecuta recuperación para el siguiente error:
{json.dumps(input_data, indent=2, default=str)}

Ejecuta recuperación completa usando herramientas apropiadas.
"""
        else:
            return str(input_data)

    def _format_output(self, result: Any, processing_time: float, success: bool, error: str = None) -> Dict[str, Any]:
        """Formatear salida de recuperación"""
        if not success:
            return {
                "success": False,
                "message": f"Error en recuperación: {error}",
                "errors": [error] if error else [],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "recovery_status": RecoveryStatus.FAILED.value,
                "recovery_actions_executed": [],
                "system_recovered": False,
                "requires_escalation": True,
                "next_actions": ["Escalación a Human Handoff requerida"]
            }

        try:
            # Extraer resultados de herramientas
            retry_result = None
            state_restoration_result = None
            circuit_breaker_result = None
            workflow_resume_result = None

            if isinstance(result, dict) and "intermediate_steps" in result:
                for step_name, step_result in result["intermediate_steps"]:
                    if "retry_manager_tool" in step_name and isinstance(step_result, dict):
                        retry_result = step_result
                    elif "state_restorer_tool" in step_name and isinstance(step_result, dict):
                        state_restoration_result = step_result
                    elif "circuit_breaker_tool" in step_name and isinstance(step_result, dict):
                        circuit_breaker_result = step_result
                    elif "workflow_resumer_tool" in step_name and isinstance(step_result, dict):
                        workflow_resume_result = step_result

            # Determinar estado de recuperación
            recovery_status = self._determine_recovery_status(
                retry_result, state_restoration_result, 
                circuit_breaker_result, workflow_resume_result
            )

            # Generar resumen de acciones ejecutadas
            actions_executed = self._extract_recovery_actions(
                retry_result, state_restoration_result,
                circuit_breaker_result, workflow_resume_result
            )

            # Evaluar si el sistema se recuperó completamente
            system_recovered = self._evaluate_system_recovery(
                recovery_status, actions_executed
            )

            # Determinar si requiere escalación
            requires_escalation = (
                recovery_status in [RecoveryStatus.FAILED, RecoveryStatus.TIMEOUT] or
                not system_recovered
            )

            # Generar próximas acciones
            next_actions = self._generate_recovery_next_actions(
                recovery_status, system_recovered, requires_escalation
            )

            # Generar recomendaciones
            recommendations = self._generate_recovery_recommendations(
                actions_executed, recovery_status
            )

            # Calcular métricas de recuperación
            recovery_metrics = self._calculate_recovery_metrics(
                actions_executed, processing_time, system_recovered
            )

            return {
                "success": system_recovered,
                "message": "Recuperación del sistema completada" if system_recovered else "Recuperación parcial o fallida",
                "agent_id": self.agent_id,
                "processing_time": processing_time,

                # Estado de recuperación
                "recovery_status": recovery_status.value if isinstance(recovery_status, RecoveryStatus) else str(recovery_status),
                "system_recovered": system_recovered,
                "recovery_completed_at": datetime.utcnow().isoformat(),

                # Resultados detallados
                "retry_result": retry_result,
                "state_restoration_result": state_restoration_result,
                "circuit_breaker_result": circuit_breaker_result,
                "workflow_resume_result": workflow_resume_result,

                # Acciones y métricas
                "recovery_actions_executed": actions_executed,
                "recovery_metrics": recovery_metrics,
                "recovery_duration_seconds": processing_time,

                # Próximos pasos
                "next_actions": next_actions,
                "recommendations": recommendations,
                "requires_escalation": requires_escalation,
                "escalation_reason": self._determine_escalation_reason(recovery_status, system_recovered),

                # Estado del sistema post-recuperación
                "system_health_score": self._calculate_system_health_score(
                    state_restoration_result, circuit_breaker_result
                ),
                "pipeline_operational": self._assess_pipeline_operational_status(workflow_resume_result),

                # Metadatos
                "errors": [],
                "warnings": self._generate_recovery_warnings(actions_executed, recovery_status)
            }

        except Exception as e:
            self.logger.error(f"Error formateando salida de recuperación: {e}")
            return {
                "success": False,
                "message": f"Error procesando recuperación: {e}",
                "errors": [str(e)],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "recovery_status": RecoveryStatus.FAILED.value,
                "requires_escalation": True
            }

    def _determine_recovery_status(self, retry_result: Optional[Dict],
                                 state_result: Optional[Dict],
                                 circuit_result: Optional[Dict],
                                 workflow_result: Optional[Dict]) -> RecoveryStatus:
        """Determinar estado general de recuperación"""
        results = [retry_result, state_result, circuit_result, workflow_result]
        valid_results = [r for r in results if r and isinstance(r, dict)]
        
        if not valid_results:
            return RecoveryStatus.FAILED
        
        successful_results = [r for r in valid_results if r.get("success", False)]
        success_rate = len(successful_results) / len(valid_results)
        
        if success_rate >= 0.8:
            return RecoveryStatus.SUCCESS
        elif success_rate >= 0.5:
            return RecoveryStatus.PARTIAL
        else:
            return RecoveryStatus.FAILED

    def _extract_recovery_actions(self, retry_result: Optional[Dict],
                                state_result: Optional[Dict],
                                circuit_result: Optional[Dict],
                                workflow_result: Optional[Dict]) -> List[str]:
        """Extraer acciones de recuperación ejecutadas"""
        actions = []
        
        if retry_result and retry_result.get("success"):
            actions.append(f"retry_executed_{retry_result.get('total_attempts', 0)}_attempts")
        
        if state_result and state_result.get("success"):
            restored_count = state_result.get("successful_restorations", 0)
            actions.append(f"state_restored_{restored_count}_components")
        
        if circuit_result and circuit_result.get("success"):
            actions_executed = len(circuit_result.get("circuit_actions", []))
            actions.append(f"circuit_breaker_managed_{actions_executed}_services")
        
        if workflow_result and workflow_result.get("success"):
            resume_point = workflow_result.get("resume_point", "unknown")
            actions.append(f"workflow_resumed_from_{resume_point}")
        
        return actions

    def _evaluate_system_recovery(self, recovery_status: RecoveryStatus,
                                actions_executed: List[str]) -> bool:
        """Evaluar si el sistema se recuperó completamente"""
        # Sistema se considera recuperado si:
        # 1. Estado de recuperación es SUCCESS
        # 2. Se ejecutaron acciones significativas
        # 3. No hay indicadores de fallo crítico
        
        return (
            recovery_status == RecoveryStatus.SUCCESS and
            len(actions_executed) > 0 and
            not any("failed" in action.lower() for action in actions_executed)
        )

    def _generate_recovery_next_actions(self, recovery_status: RecoveryStatus,
                                      system_recovered: bool,
                                      requires_escalation: bool) -> List[str]:
        """Generar próximas acciones post-recuperación"""
        actions = []
        
        if system_recovered:
            actions.extend([
                "Resume normal pipeline operations",
                "Monitor system stability for next 30 minutes",
                "Validate data integrity post-recovery",
                "Update recovery metrics and success rates"
            ])
        elif recovery_status == RecoveryStatus.PARTIAL:
            actions.extend([
                "Complete remaining recovery tasks manually",
                "Verify partially recovered components",
                "Monitor for potential secondary failures",
                "Prepare detailed handoff documentation"
            ])
        elif requires_escalation:
            actions.extend([
                "Escalate to Human Handoff Agent immediately",
                "Preserve current system state for analysis",
                "Generate comprehensive failure report",
                "Implement emergency containment measures"
            ])
        else:
            actions.extend([
                "Retry recovery with alternative strategy",
                "Gather additional diagnostic information",
                "Consider manual intervention points"
            ])
        
        return actions

    def _generate_recovery_recommendations(self, actions_executed: List[str],
                                        recovery_status: RecoveryStatus) -> List[str]:
        """Generar recomendaciones basadas en recuperación"""
        recommendations = []
        
        # Recomendaciones basadas en acciones ejecutadas
        if any("retry" in action for action in actions_executed):
            recommendations.append("Review retry configuration to optimize success rates")
        
        if any("state_restored" in action for action in actions_executed):
            recommendations.append("Implement more frequent state snapshots to reduce recovery time")
        
        if any("circuit_breaker" in action for action in actions_executed):
            recommendations.append("Review circuit breaker thresholds based on recovery patterns")
        
        # Recomendaciones basadas en estado de recuperación
        if recovery_status == RecoveryStatus.SUCCESS:
            recommendations.extend([
                "Document successful recovery strategy for future use",
                "Update recovery playbooks with lessons learned"
            ])
        elif recovery_status == RecoveryStatus.PARTIAL:
            recommendations.extend([
                "Investigate root causes of partial recovery",
                "Enhance recovery procedures for better completeness"
            ])
        elif recovery_status == RecoveryStatus.FAILED:
            recommendations.extend([
                "Conduct post-mortem analysis of recovery failures",
                "Consider additional recovery strategies and tools"
            ])
        
        return recommendations

    def _calculate_recovery_metrics(self, actions_executed: List[str],
                                  processing_time: float,
                                  system_recovered: bool) -> Dict[str, Any]:
        """Calcular métricas de recuperación"""
        return {
            "recovery_attempt_duration": processing_time,
            "actions_executed_count": len(actions_executed),
            "recovery_success": system_recovered,
            "recovery_efficiency": len(actions_executed) / max(1, processing_time),  # actions per second
            "system_downtime_seconds": processing_time if not system_recovered else 0,
            "recovery_complexity": "high" if len(actions_executed) > 3 else "medium" if len(actions_executed) > 1 else "low"
        }

    def _determine_escalation_reason(self, recovery_status: RecoveryStatus,
                                   system_recovered: bool) -> Optional[str]:
        """Determinar razón de escalación si es necesaria"""
        if system_recovered:
            return None
        
        if recovery_status == RecoveryStatus.FAILED:
            return "Automatic recovery failed - manual intervention required"
        elif recovery_status == RecoveryStatus.TIMEOUT:
            return "Recovery timeout exceeded - escalation for time-sensitive resolution"
        elif recovery_status == RecoveryStatus.PARTIAL:
            return "Partial recovery achieved - manual completion needed"
        else:
            return "Recovery status unclear - manual assessment required"

    def _calculate_system_health_score(self, state_result: Optional[Dict],
                                     circuit_result: Optional[Dict]) -> float:
        """Calcular score de salud del sistema post-recuperación"""
        health_factors = []
        
        # Factor de restauración de estado
        if state_result and state_result.get("success"):
            integrity_score = state_result.get("integrity_verified", False)
            health_factors.append(1.0 if integrity_score else 0.7)
        
        # Factor de circuit breakers
        if circuit_result and circuit_result.get("success"):
            circuit_report = circuit_result.get("circuit_report", {})
            system_health = circuit_report.get("overall_system_health", 0.5)
            health_factors.append(system_health)
        
        # Si no hay datos, asumir salud parcial
        if not health_factors:
            return 0.5
        
        return sum(health_factors) / len(health_factors)

    def _assess_pipeline_operational_status(self, workflow_result: Optional[Dict]) -> bool:
        """Evaluar si el pipeline está operacional"""
        if not workflow_result:
            return False
        
        return (
            workflow_result.get("success", False) and
            workflow_result.get("workflow_status") in ["resumed", "ready"]
        )

    def _generate_recovery_warnings(self, actions_executed: List[str],
                                  recovery_status: RecoveryStatus) -> List[str]:
        """Generar warnings sobre la recuperación"""
        warnings = []
        
        # Warning si se ejecutaron muchas acciones
        if len(actions_executed) > 5:
            warnings.append("High number of recovery actions executed - system may be unstable")
        
        # Warning si recuperación fue parcial
        if recovery_status == RecoveryStatus.PARTIAL:
            warnings.append("Partial recovery achieved - monitor system closely")
        
        # Warning si no se ejecutaron acciones principales
        if not any("retry" in action or "state_restored" in action for action in actions_executed):
            warnings.append("No primary recovery actions executed - recovery may be incomplete")
        
        return warnings

    @observability_manager.trace_agent_execution("recovery_agent")
    def execute_recovery(self, recovery_request: RecoveryRequest,
                        session_id: str = None) -> Dict[str, Any]:
        """Ejecutar recuperación completa del sistema"""
        recovery_id = recovery_request.recovery_id
        
        # Actualizar estado: PROCESSING
        state_manager.update_agent_state(
            self.agent_id,
            AgentStateStatus.PROCESSING,
            {
                "current_task": "system_recovery",
                "recovery_id": recovery_id,
                "employee_id": recovery_request.employee_id,
                "recovery_strategy": recovery_request.recovery_strategy.value,
                "recovery_priority": recovery_request.recovery_priority.value,
                "started_at": datetime.utcnow().isoformat()
            },
            session_id
        )
        
        # Registrar métricas iniciales
        observability_manager.log_agent_metrics(
            self.agent_id,
            {
                "recovery_strategy": recovery_request.recovery_strategy.value,
                "recovery_priority": recovery_request.recovery_priority.value,
                "error_category": recovery_request.error_category,
                "error_severity": recovery_request.error_severity,
                "max_retry_attempts": recovery_request.max_retry_attempts,
                "actions_planned": len(recovery_request.recovery_actions)
            },
            session_id
        )
        
        # Crear snapshot del estado pre-recuperación
        pre_recovery_state = self._create_recovery_state_snapshot(recovery_request, session_id)
        
        try:
            # Procesar con el método base
            result = self.process_request(recovery_request, session_id)
            
            # Crear snapshot del estado post-recuperación
            post_recovery_state = self._create_recovery_state_snapshot(recovery_request, session_id)
            
            # Si la recuperación fue exitosa, actualizar State Management
            if result["success"]:
                # Actualizar datos del empleado con resultados de recuperación
                if session_id:
                    recovery_data = {
                        "recovery_completed": True,
                        "recovery_id": recovery_id,
                        "recovery_status": result.get("recovery_status"),
                        "system_recovered": result.get("system_recovered", False),
                        "recovery_actions": result.get("recovery_actions_executed", []),
                        "recovery_duration": result.get("processing_time", 0),
                        "recovery_timestamp": datetime.utcnow().isoformat()
                    }
                    
                    # Actualizar phase si la recuperación fue exitosa
                    phase_update = None
                    if result.get("system_recovered"):
                        phase_update = "processing_pipeline"  # Volver a pipeline normal
                    
                    state_manager.update_employee_data(
                        session_id,
                        recovery_data,
                        phase_update or "recovered"
                    )
                
                # Actualizar estado: COMPLETED
                state_manager.update_agent_state(
                    self.agent_id,
                    AgentStateStatus.COMPLETED,
                    {
                        "current_task": "completed",
                        "recovery_id": recovery_id,
                        "recovery_status": result.get("recovery_status"),
                        "system_recovered": result.get("system_recovered", False),
                        "actions_executed": len(result.get("recovery_actions_executed", [])),
                        "completed_at": datetime.utcnow().isoformat()
                    },
                    session_id
                )
                
                # Almacenar en historial de recuperaciones
                self.recovery_history[recovery_id] = {
                    "status": "completed",
                    "result": result,
                    "pre_recovery_state": pre_recovery_state,
                    "post_recovery_state": post_recovery_state,
                    "completed_at": datetime.utcnow()
                }
                
                # Actualizar métricas globales
                self.recovery_metrics["total_recoveries"] += 1
                if result.get("system_recovered"):
                    self.recovery_metrics["successful_recoveries"] += 1
                else:
                    self.recovery_metrics["failed_recoveries"] += 1
                
                # Actualizar tiempo promedio
                total_time = (self.recovery_metrics["average_recovery_time"] * 
                            (self.recovery_metrics["total_recoveries"] - 1) + 
                            result.get("processing_time", 0))
                self.recovery_metrics["average_recovery_time"] = total_time / self.recovery_metrics["total_recoveries"]
                
            else:
                # Error en recuperación
                state_manager.update_agent_state(
                    self.agent_id,
                    AgentStateStatus.ERROR,
                    {
                        "current_task": "error",
                        "recovery_id": recovery_id,
                        "errors": result.get("errors", []),
                        "failed_at": datetime.utcnow().isoformat()
                    },
                    session_id
                )
                
                # Actualizar métricas de fallo
                self.recovery_metrics["total_recoveries"] += 1
                self.recovery_metrics["failed_recoveries"] += 1
            
            # Agregar información de sesión y estados al resultado
            result.update({
                "recovery_id": recovery_id,
                "session_id": session_id,
                "pre_recovery_state": pre_recovery_state,
                "post_recovery_state": post_recovery_state,
                "recovery_metrics_updated": self.recovery_metrics
            })
            
            return result
            
        except Exception as e:
            # Error durante recuperación
            error_msg = f"Error ejecutando recuperación: {str(e)}"
            state_manager.update_agent_state(
                self.agent_id,
                AgentStateStatus.ERROR,
                {
                    "current_task": "error",
                    "recovery_id": recovery_id,
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
                "recovery_id": recovery_id,
                "session_id": session_id,
                "agent_id": self.agent_id,
                "processing_time": 0,
                "recovery_status": RecoveryStatus.FAILED.value,
                "requires_escalation": True
            }

    def _create_recovery_state_snapshot(self, recovery_request: RecoveryRequest,
                                      session_id: str) -> Dict[str, Any]:
        """Crear snapshot del estado del sistema para recuperación"""
        try:
            from core.state_management.state_manager import state_manager
            
            # Obtener contexto del empleado
            employee_context = state_manager.get_employee_context(session_id)
            
            snapshot = {
                "timestamp": datetime.utcnow().isoformat(),
                "recovery_id": recovery_request.recovery_id,
                "session_id": session_id,
                "employee_id": recovery_request.employee_id,
                "system_overview": state_manager.get_system_overview()
            }
            
            if employee_context:
                snapshot.update({
                    "employee_phase": employee_context.phase.value if hasattr(employee_context.phase, 'value') else str(employee_context.phase),
                    "agent_states_summary": {
                        agent_id: {
                            "status": state.status.value if hasattr(state.status, 'value') else str(state.status),
                            "error_count": len(state.errors) if state.errors else 0,
                            "has_data": bool(state.data)
                        }
                        for agent_id, state in employee_context.agent_states.items()
                    },
                    "data_completeness": {
                        "raw_data_fields": len(employee_context.raw_data) if employee_context.raw_data else 0,
                        "processed_data_fields": len(employee_context.processed_data) if employee_context.processed_data else 0
                    }
                })
            
            return snapshot
            
        except Exception as e:
            return {
                "error": f"Failed to create recovery snapshot: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
                "recovery_id": recovery_request.recovery_id
            }

    def _process_with_tools_directly(self, input_data: Any) -> Dict[str, Any]:
        """Procesar usando herramientas directamente con flujo específico de recuperación"""
        results = []
        formatted_input = self._format_input(input_data)
        self.logger.info(f"Procesando recuperación con {len(self.tools)} herramientas especializadas")
        
        # Variables para almacenar resultados
        retry_result = None
        state_restoration_result = None
        circuit_breaker_result = None
        workflow_resume_result = None
        
        # Preparar datos según el tipo de entrada
        if isinstance(input_data, RecoveryRequest):
            recovery_request = input_data
            session_id = recovery_request.session_id
            recovery_strategy = recovery_request.recovery_strategy
            recovery_actions = recovery_request.recovery_actions
        else:
            # Fallback para datos genéricos
            recovery_request = input_data if isinstance(input_data, dict) else {}
            session_id = recovery_request.get("session_id", "") if isinstance(recovery_request, dict) else ""
            recovery_strategy = RecoveryStrategy.IMMEDIATE_RETRY  # Default
            recovery_actions = [RecoveryAction.RETRY_OPERATION]  # Default
        
        # Determinar qué herramientas ejecutar basado en estrategia y acciones
        tools_to_execute = self._determine_tools_for_recovery(recovery_strategy, recovery_actions)
        
        # 1. Ejecutar Retry Manager (si está en la estrategia)
        if "retry_manager" in tools_to_execute:
            try:
                self.logger.info("Ejecutando retry_manager_tool")
                
                # Preparar datos de operación fallida
                failed_operation = {
                    "operation_type": "agent_processing",
                    "agent_id": recovery_request.failed_agent_id if hasattr(recovery_request, 'failed_agent_id') else "unknown",
                    "error_context": recovery_request.error_context if hasattr(recovery_request, 'error_context') else {}
                }
                
                retry_result = retry_manager_tool.invoke({
                    "recovery_request": recovery_request.dict() if hasattr(recovery_request, 'dict') else recovery_request,
                    "failed_operation": failed_operation,
                    "retry_config": {
                        "base_delay": recovery_request.retry_delay_seconds if hasattr(recovery_request, 'retry_delay_seconds') else 5,
                        "max_attempts": recovery_request.max_retry_attempts if hasattr(recovery_request, 'max_retry_attempts') else 3
                    }
                })
                
                results.append(("retry_manager_tool", retry_result))
                self.logger.info("✅ Retry management completado")
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.logger.warning(f"❌ Error con retry_manager_tool: {e}")
                results.append(("retry_manager_tool", {"success": False, "error": error_msg}))
        
        # 2. Ejecutar State Restorer (si está en la estrategia)
        if "state_restorer" in tools_to_execute:
            try:
                self.logger.info("Ejecutando state_restorer_tool")
                
                state_restoration_result = state_restorer_tool.invoke({
                    "recovery_request": recovery_request.dict() if hasattr(recovery_request, 'dict') else recovery_request,
                    "target_state": None  # Permitir que la herramienta determine el estado objetivo
                })
                
                results.append(("state_restorer_tool", state_restoration_result))
                self.logger.info("✅ State restoration completado")
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.logger.warning(f"❌ Error con state_restorer_tool: {e}")
                results.append(("state_restorer_tool", {"success": False, "error": error_msg}))
        
        # 3. Ejecutar Circuit Breaker (siempre para protección)
        try:
            self.logger.info("Ejecutando circuit_breaker_tool")
            
            circuit_breaker_result = circuit_breaker_tool.invoke({
                "recovery_request": recovery_request.dict() if hasattr(recovery_request, 'dict') else recovery_request,
                "service_health_data": None  # La herramienta hará health checks
            })
            
            results.append(("circuit_breaker_tool", circuit_breaker_result))
            self.logger.info("✅ Circuit breaker management completado")
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.logger.warning(f"❌ Error con circuit_breaker_tool: {e}")
            results.append(("circuit_breaker_tool", {"success": False, "error": error_msg}))
        
        # 4. Ejecutar Workflow Resumer (si la recuperación anterior fue exitosa)
        if ("workflow_resumer" in tools_to_execute and 
            (retry_result and retry_result.get("success")) or 
            (state_restoration_result and state_restoration_result.get("success"))):
            
            try:
                self.logger.info("Ejecutando workflow_resumer_tool")
                
                workflow_resume_result = workflow_resumer_tool.invoke({
                    "recovery_request": recovery_request.dict() if hasattr(recovery_request, 'dict') else recovery_request,
                    "checkpoint_data": None  # La herramienta determinará el checkpoint
                })
                
                results.append(("workflow_resumer_tool", workflow_resume_result))
                self.logger.info("✅ Workflow resumption completado")
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.logger.warning(f"❌ Error con workflow_resumer_tool: {e}")
                results.append(("workflow_resumer_tool", {"success": False, "error": error_msg}))
        
        # Evaluar éxito general
        successful_tools = len([r for r in results if isinstance(r, tuple) and isinstance(r[1], dict) and r[1].get("success")])
        overall_success = successful_tools >= len(tools_to_execute) * 0.6  # 60% de éxito mínimo
        
        return {
            "output": "Recuperación del sistema completada",
            "intermediate_steps": results,
            "retry_result": retry_result,
            "state_restoration_result": state_restoration_result,
            "circuit_breaker_result": circuit_breaker_result,
            "workflow_resume_result": workflow_resume_result,
            "successful_tools": successful_tools,
            "overall_success": overall_success,
            "tools_executed": len(results)
        }

    def _determine_tools_for_recovery(self, recovery_strategy: RecoveryStrategy,
                                    recovery_actions: List[RecoveryAction]) -> List[str]:
        """Determinar qué herramientas ejecutar basado en estrategia y acciones"""
        tools = []
        
        # Basado en estrategia
        if recovery_strategy in [RecoveryStrategy.IMMEDIATE_RETRY, RecoveryStrategy.EXPONENTIAL_BACKOFF]:
            tools.append("retry_manager")
        
        if recovery_strategy in [RecoveryStrategy.STATE_ROLLBACK, RecoveryStrategy.GRACEFUL_DEGRADATION]:
            tools.append("state_restorer")
        
        if recovery_strategy == RecoveryStrategy.CIRCUIT_BREAKER:
            tools.append("circuit_breaker")
        
        # Basado en acciones específicas
        if RecoveryAction.RETRY_OPERATION in recovery_actions:
            tools.append("retry_manager")
        
        if RecoveryAction.STATE_RESTORATION in recovery_actions or RecoveryAction.PIPELINE_ROLLBACK in recovery_actions:
            tools.append("state_restorer")
        
        if RecoveryAction.CIRCUIT_BREAKER_RESET in recovery_actions:
            tools.append("circuit_breaker")
        
        # Workflow resumer para continuar después de recuperación
        if any(action in recovery_actions for action in [
            RecoveryAction.STATE_RESTORATION, 
            RecoveryAction.AGENT_RESTART,
            RecoveryAction.RETRY_OPERATION
        ]):
            tools.append("workflow_resumer")
        
        # Si no se determinaron herramientas específicas, usar retry como fallback
        if not tools:
            tools.append("retry_manager")
        
        return list(set(tools))  # Remove duplicates

    # Métodos auxiliares para el agente
    def get_recovery_status(self, recovery_id: str) -> Dict[str, Any]:
        """Obtener estado de una recuperación específica"""
        try:
            if recovery_id in self.recovery_history:
                return {
                    "found": True,
                    "recovery_id": recovery_id,
                    **self.recovery_history[recovery_id]
                }
            elif recovery_id in self.active_recoveries:
                return {
                    "found": True,
                    "recovery_id": recovery_id,
                    "status": "active",
                    **self.active_recoveries[recovery_id]
                }
            else:
                return {
                    "found": False,
                    "recovery_id": recovery_id,
                    "message": "Recovery not found in records"
                }
        except Exception as e:
            return {"found": False, "error": str(e)}

    def get_recovery_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de recuperación"""
        return {
            "recovery_metrics": self.recovery_metrics.copy(),
            "active_recoveries": len(self.active_recoveries),
            "recovery_history_count": len(self.recovery_history),
            "success_rate": (
                self.recovery_metrics["successful_recoveries"] / 
                max(1, self.recovery_metrics["total_recoveries"])
            ),
            "average_recovery_time_seconds": self.recovery_metrics["average_recovery_time"]
        }

    def validate_recovery_configuration(self) -> Dict[str, Any]:
        """Validar configuración de recuperación"""
        try:
            validation_issues = []
            
            # Verificar herramientas disponibles
            expected_tools = ["retry_manager_tool", "state_restorer_tool", "circuit_breaker_tool", "workflow_resumer_tool"]
            available_tools = [tool.name for tool in self.tools]
            
            for expected_tool in expected_tools:
                if expected_tool not in available_tools:
                    validation_issues.append(f"Missing recovery tool: {expected_tool}")
            
            # Verificar integración con State Management
            try:
                agent_state = state_manager.get_agent_state(self.agent_id)
                if not agent_state:
                    validation_issues.append("Agent not registered in State Management")
            except Exception as e:
                validation_issues.append(f"State Management integration issue: {e}")
            
            return {
                "configuration_valid": len(validation_issues) == 0,
                "validation_issues": validation_issues,
                "tools_available": len(available_tools),
                "expected_tools": len(expected_tools),
                "recovery_ready": len(validation_issues) == 0
            }
            
        except Exception as e:
            return {
                "configuration_valid": False,
                "error": str(e),
                "recovery_ready": False
            }