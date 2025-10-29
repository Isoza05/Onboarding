from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from agents.base.base_agent import BaseAgent
from datetime import datetime
import json
import asyncio

# Imports de orchestrator
from .tools import (
    pattern_selector_tool, task_distributor_tool,
    state_coordinator_tool, progress_monitor_tool
)
from .schemas import (
    OrchestrationRequest, OrchestrationResult, OrchestrationState,
    OrchestrationPhase, AgentType
)
from .workflows import (
    data_collection_workflow, execute_data_collection_orchestration,
    get_workflow_status, test_workflow_connectivity
)

# Imports para integración
from core.state_management.state_manager import state_manager
from core.state_management.models import AgentStateStatus, OnboardingPhase
from core.observability import observability_manager
from core.database import db_manager

class OrchestratorAgent(BaseAgent):
    """
    Agente Orquestador principal - Coordina todos los agentes del sistema.
    
    Implementa arquitectura BDI:
    - Beliefs: La coordinación eficiente optimiza el proceso de onboarding
    - Desires: Orquestar seamlessly todos los agentes para máxima eficiencia
    - Intentions: Coordinar flujos, distribuir tareas, monitorear progreso, manejar errores
    
    Utiliza LangGraph para orchestración de workflows complejos.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="orchestrator_agent",
            agent_name="Orchestrator Agent (LangGraph Manager)"
        )
        
        # Configuración de orquestación
        self.max_concurrent_workflows = 5
        self.default_timeout_minutes = 30
        self.active_orchestrations = {}
        
        # Verificar estado del workflow
        self.workflow_status = get_workflow_status()
        
        # Registrar agente en state management
        state_manager.register_agent(
            self.agent_id,
            {
                "version": "1.0",
                "specialization": "workflow_orchestration_coordination",
                "tools_count": len(self.tools),
                "workflow_capabilities": {
                    "concurrent_orchestration": True,
                    "langgraph_workflows": True,
                    "multi_agent_coordination": True,
                    "progress_monitoring": True,
                    "error_handling": True
                },
                "supported_patterns": [
                    "concurrent_data_collection",
                    "sequential_processing", 
                    "error_recovery",
                    "escalation_handoff"
                ],
                "workflow_status": self.workflow_status
            }
        )
        self.logger.info("Orchestrator Agent integrado con State Management y LangGraph")

    def _initialize_tools(self) -> List:
        """Inicializar herramientas de orquestación"""
        return [
            pattern_selector_tool,
            task_distributor_tool,
            state_coordinator_tool,
            progress_monitor_tool
        ]

    def _create_prompt(self) -> ChatPromptTemplate:
        """Crear prompt con framework BDI y patrón ReAct para orquestación"""
        bdi = self._get_bdi_framework()
        
        system_prompt = f"""
Eres el Orchestrator Agent, el coordinador maestro de todo el sistema de onboarding.

## FRAMEWORK BDI (Belief-Desire-Intention)
**BELIEFS (Creencias):**
{bdi['beliefs']}

**DESIRES (Deseos):**
{bdi['desires']}

**INTENTIONS (Intenciones):**
{bdi['intentions']}

## HERRAMIENTAS DE ORQUESTACIÓN:
- pattern_selector_tool: Selecciona patrón óptimo de orquestación según empleado
- task_distributor_tool: Distribuye tareas entre agentes con dependencias y timing
- state_coordinator_tool: Coordina estados entre agentes y State Management
- progress_monitor_tool: Monitorea progreso, SLAs y genera alertas de escalación

## AGENTES COORDINADOS:
- Initial Data Collection Agent: Procesamiento de datos iniciales
- Confirmation Data Agent: Validación contractual y generación de ofertas
- Documentation Agent (CSA): Análisis y validación de documentación

## PATRONES DE ORQUESTACIÓN:
1. **CONCURRENT_DATA_COLLECTION**: Ejecuta los 3 agentes simultáneamente
2. **SEQUENTIAL_PROCESSING**: Procesamiento secuencial (IT → Contract → Meeting)
3. **ERROR_RECOVERY**: Manejo y recuperación de errores
4. **ESCALATION_HANDOFF**: Escalación a intervención humana

## WORKFLOWS LANGGRAPH:
- Utiliza workflows definidos para coordinar flujos complejos
- Maneja estados distribuidos entre múltiples agentes
- Implementa monitoreo continuo y puntos de control
- Gestiona timeouts, reintentos y escalaciones automáticas

## PATRÓN REACT (Reason-Act-Observe):
**1. REASON (Razonar):**
- Analizar tipo de empleado y seleccionar patrón de orquestación óptimo
- Evaluar dependencias entre agentes y determinar orden de ejecución
- Considerar SLAs, prioridades y recursos disponibles
- Identificar puntos críticos de control y escalación

**2. ACT (Actuar):**
- Seleccionar patrón con pattern_selector_tool
- Distribuir tareas con task_distributor_tool basado en capacidades de agentes
- Coordinar ejecución usando workflows LangGraph
- Monitorear progreso continuo con progress_monitor_tool
- Sincronizar estados con state_coordinator_tool

**3. OBSERVE (Observar):**
- Verificar completion de agentes y calidad de resultados
- Monitorear adherencia a SLAs y detectar cuellos de botella
- Evaluar necesidad de escalación o intervención manual
- Consolidar resultados y generar reportes de orquestación

## CRITERIOS DE ÉXITO:
- Todos los agentes del DATA COLLECTION HUB completados exitosamente
- Score de calidad general > 70%
- Tiempo total < 30 minutos (configurable por prioridad)
- Sincronización perfecta con Common State Management
- Cero pérdida de datos entre agentes

## INSTRUCCIONES CRÍTICAS:
1. SIEMPRE selecciona el patrón de orquestación apropiado antes de ejecutar
2. Distribuye tareas considerando capacidades y limitaciones de cada agente
3. Monitorea progreso continuamente y reacciona a desviaciones SLA
4. Coordina estados para mantener consistencia en todo el sistema
5. Escalada inmediatamente cuando se detecten problemas críticos
6. Mantén trazabilidad completa para auditoría y debugging

Coordina con precisión militar, eficiencia industrial y supervisión inteligente.
"""
        
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}"),
            ("assistant", "Voy a orquestar el proceso de onboarding coordinando todos los agentes necesarios de manera óptima."),
            ("placeholder", "{agent_scratchpad}")
        ])

    def _get_bdi_framework(self) -> Dict[str, str]:
        """Framework BDI específico para orquestación"""
        return {
            "beliefs": """
• La orquestación coordinada mejora drásticamente la eficiencia del onboarding
• Cada agente tiene capacidades específicas que deben ser optimizadas
• La ejecución concurrente reduce tiempos sin comprometer calidad
• El monitoreo continuo previene fallos en cascada
• La coordinación de estados evita inconsistencias y pérdida de datos
• Los patrones de orquestación deben adaptarse al tipo de empleado y contexto
""",
            "desires": """
• Coordinar seamlessly todos los agentes para máxima eficiencia operacional
• Optimizar tiempos de procesamiento sin comprometer calidad de resultados
• Mantener visibilidad completa del progreso y estado de cada agente
• Detectar y resolver problemas antes de que impacten el proceso
• Proporcionar experiencia fluida y consistente para cada nuevo empleado
• Escalar automáticamente según complejidad y prioridad del caso
""",
            "intentions": """
• Seleccionar patrón de orquestación óptimo según características del empleado
• Distribuir tareas inteligentemente considerando capacidades y cargas de agentes
• Ejecutar workflows usando LangGraph para máximo control y flexibilidad
• Monitorear progreso en tiempo real con alertas proactivas de SLA
• Coordinar estados entre agentes manteniendo consistencia global
• Manejar errores y escalaciones con recuperación automática cuando sea posible
"""
        }

    def _format_input(self, input_data: Any) -> str:
        """Formatear datos de entrada para orquestación"""
        if isinstance(input_data, OrchestrationRequest):
            return f"""
Ejecuta orquestación completa de onboarding para el siguiente empleado:

**INFORMACIÓN DEL EMPLEADO:**
- ID: {input_data.employee_id}
- Session ID: {input_data.session_id or 'No asignado'}
- Patrón solicitado: {input_data.orchestration_pattern.value}
- Prioridad: {input_data.priority.value}

**DATOS DEL EMPLEADO:**
{json.dumps(input_data.employee_data, indent=2, default=str)}

**DATOS CONTRACTUALES:**
{json.dumps(input_data.contract_data, indent=2, default=str)}

**DOCUMENTOS ADJUNTOS:** {len(input_data.documents)} archivos

**AGENTES REQUERIDOS:**
{', '.join([agent.value for agent in input_data.required_agents])}

**REQUISITOS ESPECIALES:**
{chr(10).join([f"- {req}" for req in input_data.special_requirements]) if input_data.special_requirements else "- Ninguno"}

**CONFIGURACIÓN DE AGENTES:**
{json.dumps(input_data.agent_config, indent=2, default=str) if input_data.agent_config else "- Configuración por defecto"}

INSTRUCCIONES DE ORQUESTACIÓN:
1. Usa pattern_selector_tool para optimizar patrón según características del empleado
2. Usa task_distributor_tool para distribuir tareas entre los agentes requeridos
3. Ejecuta workflow LangGraph para coordinación concurrente de DATA COLLECTION HUB
4. Usa progress_monitor_tool para monitoreo continuo y alertas SLA
5. Usa state_coordinator_tool para sincronizar estados entre agentes
6. Consolida resultados y proporciona reporte completo de orquestación

Objetivo: Completar DATA COLLECTION HUB (Initial Data + Confirmation + Documentation) con máxima eficiencia.
"""
        elif isinstance(input_data, dict):
            return f"""
Orquesta el proceso de onboarding para:
{json.dumps(input_data, indent=2, default=str)}

Ejecuta orquestación completa coordinando todos los agentes necesarios.
"""
        else:
            return str(input_data)

    def _format_output(self, result: Any, processing_time: float, success: bool, error: str = None) -> Dict[str, Any]:
        """Formatear salida de orquestración"""
        if not success:
            return {
                "success": False,
                "message": f"Error en orquestación: {error}",
                "errors": [error] if error else [],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "orchestration_status": "failed",
                "agents_coordinated": 0,
                "workflow_executed": False,
                "next_actions": ["Revisar errores de orquestación", "Reintentar con configuración ajustada"]
            }

        try:
            # Si tenemos resultado directo del workflow
            if isinstance(result, dict) and "workflow_result" in result:
                workflow_result = result["workflow_result"]
                
                # Extraer datos del workflow result
                agent_results = workflow_result.get("agent_results", {})
                consolidated_data = workflow_result.get("consolidated_data", {})
                processing_summary = consolidated_data.get("processing_summary", {})
                
                return {
                    "success": workflow_result.get("success", False),
                    "message": "Orquestación de onboarding completada",
                    "agent_id": self.agent_id,
                    "processing_time": processing_time,
                    "orchestration_id": workflow_result.get("orchestration_id"),
                    "session_id": workflow_result.get("session_id"),
                    "employee_id": workflow_result.get("employee_id"),
                    "orchestration_status": workflow_result.get("completion_status", "completed"),
                    
                    # Resumen de ejecución
                    "orchestration_summary": {
                        "workflow_completed": workflow_result.get("success", False),
                        "agents_executed": len(agent_results),
                        "agents_successful": processing_summary.get("successful_agents", 0),
                        "overall_quality_score": processing_summary.get("overall_quality_score", 0.0)
                    },
                    "agents_coordinated": len(agent_results),
                    "workflow_executed": True,
                    "data_collection_hub_completed": processing_summary.get("successful_agents", 0) >= 3,
                    
                    # Resultados detallados
                    "agent_results": agent_results,
                    "consolidated_employee_data": consolidated_data.get("employee_data", {}),
                    "validation_results": consolidated_data.get("validation_results", {}),
                    
                    # Métricas y calidad
                    "overall_quality_score": processing_summary.get("overall_quality_score", 0.0),
                    "workflow_steps_completed": len(workflow_result.get("workflow_steps", [])),
                    "processing_summary": processing_summary,
                    
                    # Próximos pasos
                    "next_phase": "sequential_processing_pipeline" if processing_summary.get("successful_agents", 0) >= 3 else "error_handling",
                    "next_actions": [
                        "Proceder a DATA AGGREGATION & VALIDATION POINT",
                        "Iniciar IT Provisioning Agent", 
                        "Configurar Contract Management Agent"
                    ] if processing_summary.get("successful_agents", 0) >= 3 else [
                        "Revisar agentes fallidos",
                        "Reintentar DATA COLLECTION HUB",
                        "Considerar escalación manual"
                    ],
                    
                    # Control de errores
                    "errors": workflow_result.get("errors", []),
                    "requires_escalation": len(workflow_result.get("errors", [])) > 0,
                    "manual_review_needed": processing_summary.get("overall_quality_score", 0) < 70.0
                }

            # Fallback para compatibilidad
            return {
                "success": True,
                "message": "Procesamiento de orquestación completado",
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "orchestration_status": "completed",
                "agents_coordinated": 0,
                "workflow_executed": False,
                "overall_quality_score": 0.0,
                "next_actions": ["Verificar resultados de herramientas de orquestación"]
            }

        except Exception as e:
            self.logger.error(f"Error formateando salida de orquestación: {e}")
            return {
                "success": False,
                "message": f"Error procesando resultados de orquestación: {e}",
                "errors": [str(e)],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "orchestration_status": "error",
                "workflow_executed": False
            }

    @observability_manager.trace_agent_execution("orchestrator_agent")
    async def orchestrate_onboarding_process(self, orchestration_request: OrchestrationRequest, session_id: str = None) -> Dict[str, Any]:
        """Orquestar proceso completo de onboarding usando LangGraph workflows"""
        
        # Generar orchestration_id si no existe
        orchestration_id = f"orch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{orchestration_request.employee_id}"
        
        # Actualizar estado del orchestrator: PROCESSING
        state_manager.update_agent_state(
            self.agent_id,
            AgentStateStatus.PROCESSING,
            {
                "current_task": "workflow_orchestration",
                "orchestration_id": orchestration_id,
                "employee_id": orchestration_request.employee_id,
                "pattern": orchestration_request.orchestration_pattern.value,
                "required_agents": [agent.value for agent in orchestration_request.required_agents],
                "started_at": datetime.utcnow().isoformat()
            },
            session_id
        )

        # Registrar métricas
        observability_manager.log_agent_metrics(
            self.agent_id,
            {
                "orchestration_pattern": orchestration_request.orchestration_pattern.value,
                "agents_required": len(orchestration_request.required_agents),
                "employee_priority": orchestration_request.priority.value,
                "has_special_requirements": len(orchestration_request.special_requirements) > 0,
                "documents_count": len(orchestration_request.documents)
            },
            session_id
        )

        try:
            # Preparar datos para workflow LangGraph
            workflow_request = {
                "orchestration_id": orchestration_id,
                "employee_id": orchestration_request.employee_id,
                "session_id": session_id or orchestration_request.session_id,
                "employee_data": orchestration_request.employee_data,
                "contract_data": orchestration_request.contract_data,
                "documents": orchestration_request.documents,
                "orchestration_config": {
                    "pattern": orchestration_request.orchestration_pattern.value,
                    "priority": orchestration_request.priority.value,
                    "special_requirements": orchestration_request.special_requirements,
                    "agent_config": orchestration_request.agent_config,
                    "deadline": orchestration_request.deadline.isoformat() if orchestration_request.deadline else None,
                    "timeout_minutes": self.default_timeout_minutes
                }
            }

            # Ejecutar workflow LangGraph
            self.logger.info(f"Ejecutando workflow LangGraph para orchestration_id: {orchestration_id}")
            workflow_result = await execute_data_collection_orchestration(workflow_request)

            # Procesar resultado del workflow
            if workflow_result.get("success", False):
                # Actualizar State Management con resultados consolidados
                if session_id:
                    consolidated_data = workflow_result.get("consolidated_data", {})
                    state_manager.update_employee_data(
                        session_id,
                        {
                            "orchestration_completed": True,
                            "orchestration_id": orchestration_id,
                            "data_collection_results": consolidated_data,
                            "workflow_summary": workflow_result.get("processing_summary", {}),
                            "next_phase": "sequential_processing"
                        },
                        "processed"
                    )

                # Actualizar estado del orchestrator: COMPLETED
                state_manager.update_agent_state(
                    self.agent_id,
                    AgentStateStatus.COMPLETED,
                    {
                        "current_task": "completed",
                        "orchestration_id": orchestration_id,
                        "agents_coordinated": len(workflow_result.get("agent_results", {})),
                        "overall_success": workflow_result.get("success", False),
                        "quality_score": workflow_result.get("processing_summary", {}).get("overall_quality_score", 0),
                        "completed_at": datetime.utcnow().isoformat()
                    },
                    session_id
                )
                
                # Registrar en orquestaciones activas
                self.active_orchestrations[orchestration_id] = {
                    "status": "completed",
                    "result": workflow_result,
                    "completed_at": datetime.utcnow()
                }

            else:
                # Error en workflow
                state_manager.update_agent_state(
                    self.agent_id,
                    AgentStateStatus.ERROR,
                    {
                        "current_task": "error",
                        "orchestration_id": orchestration_id,
                        "errors": workflow_result.get("errors", []),
                        "failed_at": datetime.utcnow().isoformat()
                    },
                    session_id
                )

            # Agregar información de sesión al resultado
            result = {
                **workflow_result,
                "session_id": session_id,
                "orchestrator_agent_id": self.agent_id,
                "orchestration_timestamp": datetime.utcnow().isoformat()
            }

            return result

        except Exception as e:
            # Error durante orquestación
            error_msg = f"Error ejecutando orquestación: {str(e)}"
            
            state_manager.update_agent_state(
                self.agent_id,
                AgentStateStatus.ERROR,
                {
                    "current_task": "error",
                    "orchestration_id": orchestration_id,
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
                "orchestration_id": orchestration_id,
                "session_id": session_id,
                "agent_id": self.agent_id,
                "processing_time": 0,
                "orchestration_status": "failed"
            }

    def _process_with_tools_directly(self, input_data: Any) -> Dict[str, Any]:
        """Procesar usando herramientas directamente - bridge para compatibilidad"""
        try:
            # Si recibimos OrchestrationRequest, ejecutar workflow completo
            if isinstance(input_data, OrchestrationRequest):
                # Ejecutar workflow de forma síncrona (para compatibilidad con base class)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    result = loop.run_until_complete(
                        self.orchestrate_onboarding_process(input_data)
                    )
                    return {"workflow_result": result, "success": result.get("success", False)}
                finally:
                    loop.close()
            
            # Fallback: usar herramientas individuales para testing
            results = []
            formatted_input = self._format_input(input_data)
            
            self.logger.info(f"Procesando con herramientas de orquestación: {len(self.tools)} herramientas")
            
            # Ejecutar herramientas de orquestación
            for tool in self.tools:
                try:
                    self.logger.info(f"Ejecutando herramienta: {tool.name}")
                    
                    if tool.name == "pattern_selector_tool":
                        result = tool.invoke({
                            "selection_criteria": {"employee_type": "full_time", "priority": "medium"},
                            "employee_context": {"department": "IT"},
                            "system_state": {}
                        })
                        
                    elif tool.name == "task_distributor_tool":
                        result = tool.invoke({
                            "orchestration_pattern": "concurrent_data_collection",
                            "agent_assignments": [
                                {"agent_type": "initial_data_collection_agent", "task_description": "Process initial data"}
                            ],
                            "distribution_strategy": {}
                        })
                        
                    elif tool.name == "state_coordinator_tool":
                        result = tool.invoke({
                            "session_id": "test_session",
                            "agent_states": {"test_agent": {"status": "completed"}},
                            "coordination_action": "validate"
                        })
                        
                    elif tool.name == "progress_monitor_tool":
                        result = tool.invoke({
                            "orchestration_state": {
                                "session_id": "test_session",
                                "started_at": datetime.utcnow().isoformat(),
                                "current_phase": "data_collection_concurrent"
                            },
                            "monitoring_criteria": {},
                            "sla_thresholds": {}
                        })
                        
                    else:
                        result = f"Herramienta {tool.name} procesada"

                    results.append((tool.name, result))
                    self.logger.info(f"✅ Herramienta {tool.name} completada")

                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    self.logger.warning(f"❌ Error con herramienta {tool.name}: {e}")
                    results.append((tool.name, error_msg))

            return {
                "output": "Procesamiento de orquestación con herramientas completado",
                "intermediate_steps": results,
                "tools_executed": len(results),
                "workflow_status": get_workflow_status()
            }

        except Exception as e:
            self.logger.error(f"Error en procesamiento directo: {e}")
            return {
                "output": f"Error en procesamiento: {str(e)}",
                "intermediate_steps": [],
                "success": False
            }

    def get_orchestration_status(self, orchestration_id: str) -> Dict[str, Any]:
        """Obtener estado de una orquestración específica"""
        try:
            if orchestration_id in self.active_orchestrations:
                return {
                    "found": True,
                    "orchestration_id": orchestration_id,
                    **self.active_orchestrations[orchestration_id]
                }
            else:
                return {
                    "found": False,
                    "orchestration_id": orchestration_id,
                    "message": "Orquestación no encontrada en registros activos"
                }
        except Exception as e:
            return {"found": False, "error": str(e)}

    def get_integration_status(self, session_id: str = None) -> Dict[str, Any]:
        """Obtener estado de integración completo"""
        try:
            # Estado del orchestrator
            agent_state = state_manager.get_agent_state(self.agent_id, session_id)
            
            # Contexto del empleado si existe sesión
            employee_context = None
            if session_id:
                employee_context = state_manager.get_employee_context(session_id)
            
            # Estado del workflow
            workflow_status = get_workflow_status()
            
            # Overview del sistema
            system_overview = state_manager.get_system_overview()
            
            return {
                "agent_state": {
                    "status": agent_state.status if agent_state else "not_registered",
                    "last_updated": agent_state.last_updated.isoformat() if agent_state and agent_state.last_updated else None,
                    "data": agent_state.data if agent_state else {}
                },
                "workflow_status": workflow_status,
                "active_orchestrations": len(self.active_orchestrations),
                "employee_context": {
                    "employee_id": employee_context.employee_id if employee_context else None,
                    "phase": employee_context.phase.value if employee_context and hasattr(employee_context.phase, 'value') else str(employee_context.phase) if employee_context else None,
                    "session_id": session_id,
                    "has_processed_data": bool(employee_context.processed_data) if employee_context else False
                } if employee_context else None,
                "system_overview": system_overview,
                "integration_success": True
            }
        except Exception as e:
            self.logger.error(f"Error obteniendo estado de integración: {e}")
            return {
                "integration_success": False,
                "error": str(e),
                "agent_state": {"status": "error"},
                "workflow_status": {"workflow_available": False}
            }

    async def test_full_integration(self) -> Dict[str, Any]:
        """Test completo de integración del orchestrator"""
        try:
            # Test de conectividad workflow
            connectivity_test = await test_workflow_connectivity()
            
            # Test de herramientas
            tools_test = len(self.tools) == 4
            
            # Test de state management
            state_test = state_manager.get_agent_state(self.agent_id) is not None
            
            return {
                "orchestrator_integration": "success",
                "workflow_connectivity": connectivity_test.get("connectivity_test", "unknown"),
                "tools_available": tools_test,
                "state_management": state_test,
                "agents_in_workflow": self.workflow_status.get("agents_initialized", 0),
                "ready_for_orchestration": all([
                    connectivity_test.get("connectivity_test") == "passed",
                    tools_test,
                    state_test
                ])
            }
        except Exception as e:
            return {
                "orchestrator_integration": "failed",
                "error": str(e)
            }