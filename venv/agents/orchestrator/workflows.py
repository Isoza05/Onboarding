from typing import Dict, Any, List, Optional, Annotated
from datetime import datetime, timedelta
import json
import asyncio
from enum import Enum

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from loguru import logger

# Imports de nuestros agentes y state management
from core.state_management.state_manager import state_manager
from core.state_management.models import AgentStateStatus, OnboardingPhase
from core.observability import observability_manager

# Import de agentes existentes
from agents.initial_data_collection.agent import InitialDataCollectionAgent
from agents.confirmation_data.agent import ConfirmationDataAgent
from agents.documentation.agent import DocumentationAgent

# Import de schemas y tools del orchestrator
from .schemas import (
    OrchestrationState, OrchestrationPhase, AgentType,
    TaskStatus, WorkflowStep, OrchestrationResult
)
from .tools import (
    pattern_selector_tool, task_distributor_tool,
    state_coordinator_tool, progress_monitor_tool
)

class WorkflowState(Dict):
    """Estado del workflow de LangGraph"""
    # Datos principales
    session_id: str
    employee_id: str
    orchestration_id: str
    
    # Estado de orquestación
    current_phase: OrchestrationPhase
    orchestration_config: Dict[str, Any]
    
    # Datos del empleado
    employee_data: Dict[str, Any]
    contract_data: Dict[str, Any]
    documents: List[Dict[str, Any]]
    
    # Resultados de agentes
    agent_results: Dict[str, Any]
    consolidated_data: Dict[str, Any]
    
    # Control de workflow
    workflow_steps: List[Dict[str, Any]]
    current_step: Optional[str]
    errors: List[str]
    
    # Timing y progreso
    started_at: datetime
    progress_percentage: float
    
    # Mensajes del workflow
    messages: Annotated[List[BaseMessage], add_messages]

class DataCollectionWorkflow:
    """Workflow principal para DATA COLLECTION HUB usando LangGraph"""
    
    def __init__(self):
        self.graph = None
        self.agents = {
            AgentType.INITIAL_DATA_COLLECTION.value: None,
            AgentType.CONFIRMATION_DATA.value: None,
            AgentType.DOCUMENTATION.value: None
        }
        self._setup_agents()
        self._build_graph()
        
    def _setup_agents(self):
        """Inicializar agentes del sistema"""
        try:
            self.agents[AgentType.INITIAL_DATA_COLLECTION.value] = InitialDataCollectionAgent()
            self.agents[AgentType.CONFIRMATION_DATA.value] = ConfirmationDataAgent()
            self.agents[AgentType.DOCUMENTATION.value] = DocumentationAgent()
            logger.info("Agentes del DATA COLLECTION HUB inicializados")
        except Exception as e:
            logger.error(f"Error inicializando agentes: {e}")
            raise
    
    def _build_graph(self):
        """Construir grafo de workflow con LangGraph"""
        try:
            # Crear grafo
            workflow = StateGraph(WorkflowState)
            
            # Agregar nodos del workflow
            workflow.add_node("initialize_orchestration", self._initialize_orchestration)
            workflow.add_node("select_pattern", self._select_orchestration_pattern)
            workflow.add_node("distribute_tasks", self._distribute_agent_tasks)
            workflow.add_node("execute_concurrent_collection", self._execute_concurrent_data_collection)
            workflow.add_node("coordinate_states", self._coordinate_agent_states)
            workflow.add_node("monitor_progress", self._monitor_workflow_progress)
            workflow.add_node("aggregate_results", self._aggregate_agent_results)
            workflow.add_node("finalize_orchestration", self._finalize_orchestration)
            workflow.add_node("handle_errors", self._handle_workflow_errors)
            
            # Definir flujo del workflow
            workflow.set_entry_point("initialize_orchestration")
            
            # Flujo principal
            workflow.add_edge("initialize_orchestration", "select_pattern")
            workflow.add_edge("select_pattern", "distribute_tasks")
            workflow.add_edge("distribute_tasks", "execute_concurrent_collection")
            workflow.add_edge("execute_concurrent_collection", "coordinate_states")
            workflow.add_edge("coordinate_states", "monitor_progress")
            
            # Conditional edges para manejo de progreso
            workflow.add_conditional_edges(
                "monitor_progress",
                self._should_continue_or_aggregate,
                {
                    "continue": "execute_concurrent_collection",
                    "aggregate": "aggregate_results",
                    "error": "handle_errors"
                }
            )
            
            workflow.add_edge("aggregate_results", "finalize_orchestration")
            workflow.add_edge("finalize_orchestration", END)
            workflow.add_edge("handle_errors", END)
            
            # Compilar el grafo
            self.graph = workflow.compile()
            logger.info("Workflow LangGraph construido exitosamente")
            
        except Exception as e:
            logger.error(f"Error construyendo workflow: {e}")
            raise
    
    async def _initialize_orchestration(self, state: WorkflowState) -> WorkflowState:
        """Inicializar orquestación"""
        try:
            logger.info(f"Inicializando orquestación para empleado: {state['employee_id']}")
            
            # Actualizar estado
            state["current_phase"] = OrchestrationPhase.INITIATED
            state["started_at"] = datetime.utcnow()
            state["progress_percentage"] = 0.0
            state["workflow_steps"] = []
            state["agent_results"] = {}
            state["errors"] = []
            
            # Crear contexto en State Management si no existe
            if not state.get("session_id"):
                session_id = state_manager.create_employee_context({
                    "employee_id": state["employee_id"],
                    "employee_data": state.get("employee_data", {}),
                    "contract_data": state.get("contract_data", {}),
                    "orchestration_id": state["orchestration_id"]
                })
                state["session_id"] = session_id
            
            # Agregar mensaje de inicio
            state["messages"].append(
                AIMessage(content=f"Orquestación iniciada para empleado {state['employee_id']}")
            )
            
            logger.info(f"Orquestación inicializada con session_id: {state.get('session_id')}")
            return state
            
        except Exception as e:
            logger.error(f"Error inicializando orquestación: {e}")
            state["errors"].append(f"Error en inicialización: {str(e)}")
            return state
    
    async def _select_orchestration_pattern(self, state: WorkflowState) -> WorkflowState:
        """Seleccionar patrón de orquestación"""
        try:
            logger.info("Seleccionando patrón de orquestación")
            
            # Preparar criterios de selección
            selection_criteria = {
                "employee_type": state.get("employee_data", {}).get("employment_type", "full_time"),
                "position_level": state.get("employee_data", {}).get("position_level", "mid"),
                "department": state.get("employee_data", {}).get("department", "general"),
                "priority": state.get("orchestration_config", {}).get("priority", "medium"),
                "special_requirements": state.get("orchestration_config", {}).get("special_requirements", [])
            }
            
            # Usar pattern_selector_tool
            pattern_result = pattern_selector_tool.invoke({
                "selection_criteria": selection_criteria,
                "employee_context": state.get("employee_data", {}),
                "system_state": {}
            })
            
            if pattern_result["success"]:
                state["orchestration_config"] = {
                    **state.get("orchestration_config", {}),
                    **pattern_result["orchestration_config"]
                }
                state["current_phase"] = OrchestrationPhase.DATA_COLLECTION_CONCURRENT
                
                # Crear workflow step
                step = {
                    "step_id": "pattern_selection",
                    "step_name": "Pattern Selection",
                    "status": TaskStatus.COMPLETED,
                    "result": pattern_result,
                    "completed_at": datetime.utcnow().isoformat()
                }
                state["workflow_steps"].append(step)
                
                logger.info(f"Patrón seleccionado: {pattern_result['selected_pattern']}")
            else:
                state["errors"].append(f"Error seleccionando patrón: {pattern_result.get('error', 'Unknown')}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error seleccionando patrón: {e}")
            state["errors"].append(f"Error en selección de patrón: {str(e)}")
            return state
    
    async def _distribute_agent_tasks(self, state: WorkflowState) -> WorkflowState:
        """Distribuir tareas a agentes"""
        try:
            logger.info("Distribuyendo tareas a agentes")
            
            # Preparar asignaciones de agentes
            agent_assignments = []
            
            # Initial Data Collection Agent
            agent_assignments.append({
                "agent_type": AgentType.INITIAL_DATA_COLLECTION.value,
                "agent_id": "initial_data_collection_agent",
                "task_description": "Procesar datos iniciales del empleado",
                "input_data": {
                    "employee_data": state.get("employee_data", {}),
                    "raw_email_data": state.get("employee_data", {})
                },
                "priority": "high",
                "estimated_duration": 180
            })
            
            # Confirmation Data Agent
            agent_assignments.append({
                "agent_type": AgentType.CONFIRMATION_DATA.value,
                "agent_id": "confirmation_data_agent",
                "task_description": "Validar términos contractuales",
                "input_data": {
                    "employee_data": state.get("employee_data", {}),
                    "contract_data": state.get("contract_data", {})
                },
                "priority": "high",
                "estimated_duration": 200
            })
            
            # Documentation Agent
            agent_assignments.append({
                "agent_type": AgentType.DOCUMENTATION.value,
                "agent_id": "documentation_agent",
                "task_description": "Validar documentación del empleado",
                "input_data": {
                    "employee_data": state.get("employee_data", {}),
                    "documents": state.get("documents", [])
                },
                "priority": "medium",
                "estimated_duration": 240
            })
            
            # Usar task_distributor_tool
            distribution_result = task_distributor_tool.invoke({
                "orchestration_pattern": "concurrent_data_collection",
                "agent_assignments": agent_assignments,
                "distribution_strategy": state.get("orchestration_config", {})
            })
            
            if distribution_result["success"]:
                state["distribution_plan"] = distribution_result["distribution_plan"]
                
                # Crear workflow step
                step = {
                    "step_id": "task_distribution",
                    "step_name": "Task Distribution",
                    "status": TaskStatus.COMPLETED,
                    "result": distribution_result,
                    "completed_at": datetime.utcnow().isoformat()
                }
                state["workflow_steps"].append(step)
                
                logger.info(f"Tareas distribuidas: {distribution_result['tasks_created']} tareas creadas")
            else:
                state["errors"].append(f"Error distribuyendo tareas: {distribution_result.get('error', 'Unknown')}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error distribuyendo tareas: {e}")
            state["errors"].append(f"Error en distribución de tareas: {str(e)}")
            return state
    
    async def _execute_concurrent_data_collection(self, state: WorkflowState) -> WorkflowState:
        """Ejecutar recolección concurrente de datos"""
        try:
            logger.info("Ejecutando recolección concurrente de datos")
            
            session_id = state.get("session_id")
            tasks = []
            
            # Preparar datos para cada agente
            employee_data = state.get("employee_data", {})
            contract_data = state.get("contract_data", {})
            documents = state.get("documents", [])
            
            # Crear tareas concurrentes para cada agente
            async def execute_initial_data_agent():
                try:
                    agent = self.agents[AgentType.INITIAL_DATA_COLLECTION.value]
                    # Simular procesamiento - en implementación real usaríamos los métodos del agente
                    result = {
                        "success": True,
                        "agent_id": "initial_data_collection_agent",
                        "processing_time": 2.5,
                        "structured_data": employee_data,
                        "validation_score": 85.0,
                        "completed_at": datetime.utcnow().isoformat()
                    }
                    return AgentType.INITIAL_DATA_COLLECTION.value, result
                except Exception as e:
                    return AgentType.INITIAL_DATA_COLLECTION.value, {"success": False, "error": str(e)}
            
            async def execute_confirmation_agent():
                try:
                    agent = self.agents[AgentType.CONFIRMATION_DATA.value]
                    # Simular procesamiento
                    result = {
                        "success": True,
                        "agent_id": "confirmation_data_agent", 
                        "processing_time": 3.2,
                        "validation_score": 78.5,
                        "contract_validated": True,
                        "offer_generated": True,
                        "completed_at": datetime.utcnow().isoformat()
                    }
                    return AgentType.CONFIRMATION_DATA.value, result
                except Exception as e:
                    return AgentType.CONFIRMATION_DATA.value, {"success": False, "error": str(e)}
            
            async def execute_documentation_agent():
                try:
                    agent = self.agents[AgentType.DOCUMENTATION.value]
                    # Simular procesamiento
                    result = {
                        "success": True,
                        "agent_id": "documentation_agent",
                        "processing_time": 4.1,
                        "compliance_score": 72.3,
                        "documents_validated": len(documents),
                        "validation_status": "requires_review",
                        "completed_at": datetime.utcnow().isoformat()
                    }
                    return AgentType.DOCUMENTATION.value, result
                except Exception as e:
                    return AgentType.DOCUMENTATION.value, {"success": False, "error": str(e)}
            
            # Ejecutar agentes concurrentemente
            tasks = [
                execute_initial_data_agent(),
                execute_confirmation_agent(),
                execute_documentation_agent()
            ]
            
            # Esperar resultados con timeout
            try:
                timeout = state.get("orchestration_config", {}).get("timeout_per_agent", 300)
                results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=timeout)
                
                # Procesar resultados
                for result in results:
                    if isinstance(result, tuple) and len(result) == 2:
                        agent_type, agent_result = result
                        state["agent_results"][agent_type] = agent_result
                        
                        # Actualizar State Management
                        if session_id and agent_result.get("success"):
                            state_manager.update_agent_state(
                                agent_result.get("agent_id", agent_type),
                                AgentStateStatus.COMPLETED,
                                agent_result,
                                session_id
                            )
                    elif isinstance(result, Exception):
                        logger.error(f"Error en ejecución de agente: {result}")
                        state["errors"].append(f"Error ejecutando agente: {str(result)}")
                
                # Crear workflow step
                step = {
                    "step_id": "concurrent_execution",
                    "step_name": "Concurrent Data Collection",
                    "status": TaskStatus.COMPLETED,
                    "agents_executed": len([r for r in results if isinstance(r, tuple)]),
                    "completed_at": datetime.utcnow().isoformat()
                }
                state["workflow_steps"].append(step)
                
                # Actualizar progreso
                state["progress_percentage"] = 60.0
                
                logger.info(f"Ejecución concurrente completada: {len(state['agent_results'])} agentes")
                
            except asyncio.TimeoutError:
                logger.warning("Timeout en ejecución concurrente de agentes")
                state["errors"].append("Timeout en ejecución de agentes")
            
            return state
            
        except Exception as e:
            logger.error(f"Error en ejecución concurrente: {e}")
            state["errors"].append(f"Error en ejecución concurrente: {str(e)}")
            return state
    
    async def _coordinate_agent_states(self, state: WorkflowState) -> WorkflowState:
        """Coordinar estados entre agentes"""
        try:
            logger.info("Coordinando estados entre agentes")
            
            session_id = state.get("session_id")
            agent_results = state.get("agent_results", {})
            
            # Preparar estados para coordinación
            agent_states = {}
            for agent_type, result in agent_results.items():
                if result.get("success"):
                    agent_states[result.get("agent_id", agent_type)] = {
                        "status": "completed",
                        "data": result,
                        "last_updated": result.get("completed_at", datetime.utcnow().isoformat())
                    }
                else:
                    agent_states[result.get("agent_id", agent_type)] = {
                        "status": "error",
                        "data": {"error": result.get("error", "Unknown error")},
                        "last_updated": datetime.utcnow().isoformat()
                    }
            
            # Usar state_coordinator_tool
            coordination_result = state_coordinator_tool.invoke({
                "session_id": session_id or "unknown",
                "agent_states": agent_states,
                "coordination_action": "sync"
            })
            
            if coordination_result["success"]:
                state["coordination_result"] = coordination_result["coordination_result"]
                
                # Crear workflow step
                step = {
                    "step_id": "state_coordination",
                    "step_name": "Agent State Coordination",
                    "status": TaskStatus.COMPLETED,
                    "result": coordination_result,
                    "completed_at": datetime.utcnow().isoformat()
                }
                state["workflow_steps"].append(step)
                
                logger.info(f"Estados coordinados: {len(coordination_result['coordination_result']['agents_coordinated'])} agentes")
            else:
                state["errors"].append(f"Error coordinando estados: {coordination_result.get('error', 'Unknown')}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error coordinando estados: {e}")
            state["errors"].append(f"Error en coordinación de estados: {str(e)}")
            return state
    
    async def _monitor_workflow_progress(self, state: WorkflowState) -> WorkflowState:
        """Monitorear progreso del workflow"""
        try:
            logger.info("Monitoreando progreso del workflow")
            
            # Preparar estado para monitoreo
            orchestration_state = {
                "session_id": state.get("session_id"),
                "started_at": state["started_at"].isoformat() if isinstance(state["started_at"], datetime) else state["started_at"],
                "current_phase": state["current_phase"],
                "workflow_steps": state.get("workflow_steps", []),
                "agent_results": state.get("agent_results", {})
            }
            
            # Usar progress_monitor_tool
            monitoring_result = progress_monitor_tool.invoke({
                "orchestration_state": orchestration_state,
                "monitoring_criteria": {"track_completion": True, "track_quality": True, "track_timing": True},
                "sla_thresholds": {"max_total_time_minutes": 30, "min_quality_score": 70.0}
            })
            
            if monitoring_result["success"]:
                state["progress_metrics"] = monitoring_result["progress_metrics"]
                state["sla_analysis"] = monitoring_result["sla_analysis"]
                state["progress_percentage"] = monitoring_result["progress_metrics"]["progress_percentage"]
                
                # Verificar si necesita escalación
                if monitoring_result["escalation_needed"]:
                    state["errors"].append("Escalación requerida por SLA")
                
                # Crear workflow step
                step = {
                    "step_id": "progress_monitoring",
                    "step_name": "Progress Monitoring",
                    "status": TaskStatus.COMPLETED,
                    "result": monitoring_result,
                    "completed_at": datetime.utcnow().isoformat()
                }
                state["workflow_steps"].append(step)
                
                logger.info(f"Progreso monitoreado: {state['progress_percentage']:.1f}%")
            else:
                state["errors"].append(f"Error monitoreando progreso: {monitoring_result.get('error', 'Unknown')}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error monitoreando progreso: {e}")
            state["errors"].append(f"Error en monitoreo de progreso: {str(e)}")
            return state
    
    def _should_continue_or_aggregate(self, state: WorkflowState) -> str:
        """Decidir si continuar, agregar o manejar errores"""
        try:
            # Verificar errores críticos
            errors = state.get("errors", [])
            if any("escalación" in error.lower() for error in errors):
                return "error"
            
            # Verificar si todos los agentes completaron
            agent_results = state.get("agent_results", {})
            required_agents = 3  # Initial Data, Confirmation, Documentation
            
            completed_agents = len([
                result for result in agent_results.values()
                if result.get("success", False)
            ])
            
            # Si todos completaron, ir a agregación
            if completed_agents >= required_agents:
                return "aggregate"
            
            # Si hay agentes fallidos y no se puede recuperar
            failed_agents = len([
                result for result in agent_results.values()
                if not result.get("success", False)
            ])
            
            if failed_agents > 1:  # Más de 1 fallo = error crítico
                return "error"
            
            # Verificar timeout
            progress_metrics = state.get("progress_metrics", {})
            elapsed_time = progress_metrics.get("elapsed_time_minutes", 0)
            
            if elapsed_time > 30:  # 30 minutos límite
                return "error"
            
            # Si llegamos aquí, seguir intentando
            return "continue"
            
        except Exception as e:
            logger.error(f"Error decidiendo flujo: {e}")
            return "error"
    
    async def _aggregate_agent_results(self, state: WorkflowState) -> WorkflowState:
        """Agregar resultados de agentes"""
        try:
            logger.info("Agregando resultados de agentes")
            
            agent_results = state.get("agent_results", {})
            consolidated_data = {
                "employee_data": {},
                "validation_results": {},
                "processing_summary": {
                    "agents_executed": len(agent_results),
                    "successful_agents": len([r for r in agent_results.values() if r.get("success", False)]),
                    "total_processing_time": sum([r.get("processing_time", 0) for r in agent_results.values()]),
                    "overall_success": True
                }
            }
            
            # Consolidar datos de cada agente
            for agent_type, result in agent_results.items():
                if result.get("success"):
                    if agent_type == AgentType.INITIAL_DATA_COLLECTION.value:
                        consolidated_data["employee_data"].update(result.get("structured_data", {}))
                        consolidated_data["validation_results"]["data_collection"] = {
                            "score": result.get("validation_score", 0),
                            "status": "completed"
                        }
                    
                    elif agent_type == AgentType.CONFIRMATION_DATA.value:
                        consolidated_data["validation_results"]["contract_validation"] = {
                            "score": result.get("validation_score", 0),
                            "contract_validated": result.get("contract_validated", False),
                            "offer_generated": result.get("offer_generated", False)
                        }
                    
                    elif agent_type == AgentType.DOCUMENTATION.value:
                        consolidated_data["validation_results"]["documentation"] = {
                            "compliance_score": result.get("compliance_score", 0),
                            "documents_validated": result.get("documents_validated", 0),
                            "validation_status": result.get("validation_status", "unknown")
                        }
                else:
                    consolidated_data["processing_summary"]["overall_success"] = False
            
            # Calcular score general
            validation_scores = []
            if "data_collection" in consolidated_data["validation_results"]:
                validation_scores.append(consolidated_data["validation_results"]["data_collection"]["score"])
            if "contract_validation" in consolidated_data["validation_results"]:
                validation_scores.append(consolidated_data["validation_results"]["contract_validation"]["score"])
            if "documentation" in consolidated_data["validation_results"]:
                validation_scores.append(consolidated_data["validation_results"]["documentation"]["compliance_score"])
            
            overall_score = sum(validation_scores) / len(validation_scores) if validation_scores else 0
            consolidated_data["processing_summary"]["overall_quality_score"] = overall_score
            
            state["consolidated_data"] = consolidated_data
            state["current_phase"] = OrchestrationPhase.DATA_AGGREGATION
            state["progress_percentage"] = 90.0
            
            # Crear workflow step
            step = {
                "step_id": "data_aggregation",
                "step_name": "Data Aggregation",
                "status": TaskStatus.COMPLETED,
                "result": consolidated_data,
                "completed_at": datetime.utcnow().isoformat()
            }
            state["workflow_steps"].append(step)
            
            logger.info(f"Resultados agregados: Score general {overall_score:.1f}%")
            return state
            
        except Exception as e:
            logger.error(f"Error agregando resultados: {e}")
            state["errors"].append(f"Error en agregación de datos: {str(e)}")
            return state
    
    async def _finalize_orchestration(self, state: WorkflowState) -> WorkflowState:
        """Finalizar orquestación"""
        try:
            logger.info("Finalizando orquestación")
            
            # Actualizar progreso final
            state["progress_percentage"] = 100.0
            state["current_phase"] = OrchestrationPhase.FINALIZATION
            
            # Crear resultado final
            final_result = {
                "orchestration_id": state["orchestration_id"],
                "session_id": state.get("session_id"),
                "employee_id": state["employee_id"],
                "success": len(state.get("errors", [])) == 0,
                "completion_status": "completed" if len(state.get("errors", [])) == 0 else "completed_with_errors",
                "final_phase": state["current_phase"],
                "agent_results": state.get("agent_results", {}),
                "consolidated_data": state.get("consolidated_data", {}),
                "processing_summary": state.get("consolidated_data", {}).get("processing_summary", {}),
                "workflow_steps": state.get("workflow_steps", []),
                "errors": state.get("errors", []),
                "started_at": state["started_at"],
                "completed_at": datetime.utcnow()
            }
            
            state["final_result"] = final_result
            
            # Actualizar State Management
            session_id = state.get("session_id")
            if session_id:
                state_manager.update_employee_data(
                    session_id,
                    {
                        "orchestration_completed": True,
                        "final_result": final_result,
                        "data_collection_phase": "completed"
                    },
                    "processed"
                )
            
            # Crear workflow step final
            step = {
                "step_id": "finalization",
                "step_name": "Orchestration Finalization",
                "status": TaskStatus.COMPLETED,
                "result": final_result,
                "completed_at": datetime.utcnow().isoformat()
            }
            state["workflow_steps"].append(step)
            
            # Agregar mensaje final
            state["messages"].append(
                AIMessage(content=f"Orquestación completada para empleado {state['employee_id']} con {len(state['agent_results'])} agentes")
            )
            
            logger.info(f"Orquestación finalizada: {final_result['completion_status']}")
            return state
            
        except Exception as e:
            logger.error(f"Error finalizando orquestación: {e}")
            state["errors"].append(f"Error en finalización: {str(e)}")
            return state
    
    async def _handle_workflow_errors(self, state: WorkflowState) -> WorkflowState:
        """Manejar errores del workflow"""
        try:
            logger.info("Manejando errores del workflow")
            
            errors = state.get("errors", [])
            
            # Crear resultado de error
            error_result = {
                "orchestration_id": state["orchestration_id"],
                "session_id": state.get("session_id"),
                "employee_id": state["employee_id"],
                "success": False,
                "completion_status": "failed",
                "final_phase": state.get("current_phase", OrchestrationPhase.ERROR_HANDLING),
                "errors": errors,
                "partial_results": state.get("agent_results", {}),
                "recovery_actions": [
                    "Revisar errores reportados",
                    "Reintentar agentes fallidos",
                    "Escalación a supervisión manual"
                ],
                "started_at": state["started_at"],
                "completed_at": datetime.utcnow()
            }
            
            state["final_result"] = error_result
            state["current_phase"] = OrchestrationPhase.ERROR_HANDLING
            
            # Agregar mensaje de error
            state["messages"].append(
                AIMessage(content=f"Orquestación falló para empleado {state['employee_id']} con {len(errors)} errores")
            )
            
            logger.warning(f"Workflow completado con errores: {len(errors)} errores encontrados")
            return state
            
        except Exception as e:
            logger.error(f"Error manejando errores del workflow: {e}")
            state["errors"].append(f"Error crítico en manejo de errores: {str(e)}")
            return state
    
    async def execute_workflow(self, orchestration_request: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar workflow completo de orquestación"""
        try:
            # Crear estado inicial
            initial_state = {
                "orchestration_id": orchestration_request.get("orchestration_id", f"orch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"),
                "employee_id": orchestration_request["employee_id"],
                "session_id": orchestration_request.get("session_id"),
                "employee_data": orchestration_request.get("employee_data", {}),
                "contract_data": orchestration_request.get("contract_data", {}),
                "documents": orchestration_request.get("documents", []),
                "orchestration_config": orchestration_request.get("orchestration_config", {}),
                "current_phase": OrchestrationPhase.INITIATED,
                "progress_percentage": 0.0,
                "messages": [HumanMessage(content=f"Iniciar onboarding para {orchestration_request['employee_id']}")],
                "workflow_steps": [],
                "agent_results": {},
                "errors": [],
                "started_at": datetime.utcnow()
            }
            
            logger.info(f"Ejecutando workflow para empleado: {orchestration_request['employee_id']}")
            
            # Ejecutar el grafo
            final_state = await self.graph.ainvoke(initial_state)
            
            # Extraer resultado final y asegurar que sea válido
            if "final_result" in final_state and final_state["final_result"]:
                result = final_state["final_result"]
                
                # Asegurar campos críticos
                result["success"] = result.get("success", len(final_state.get("errors", [])) == 0)
                result["session_id"] = final_state.get("session_id") or result.get("session_id")
                result["agent_results"] = final_state.get("agent_results", {})
                result["consolidated_data"] = final_state.get("consolidated_data", {})
                result["orchestration_id"] = final_state.get("orchestration_id", initial_state["orchestration_id"])
                
            else:
                # Crear resultado de fallback
                result = {
                    "success": len(final_state.get("errors", [])) == 0,
                    "orchestration_id": final_state.get("orchestration_id", initial_state["orchestration_id"]),
                    "session_id": final_state.get("session_id"),
                    "employee_id": orchestration_request["employee_id"],
                    "completion_status": "completed" if len(final_state.get("errors", [])) == 0 else "completed_with_errors",
                    "agent_results": final_state.get("agent_results", {}),
                    "consolidated_data": final_state.get("consolidated_data", {}),
                    "errors": final_state.get("errors", []),
                    "processing_summary": final_state.get("consolidated_data", {}).get("processing_summary", {}),
                    "workflow_steps": final_state.get("workflow_steps", [])
                }
            
            logger.info(f"Workflow completado: {result.get('completion_status', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Error ejecutando workflow: {e}")
            return {
                "success": False,
                "error": str(e),
                "orchestration_id": orchestration_request.get("orchestration_id", "unknown"),
                "session_id": orchestration_request.get("session_id"),
                "employee_id": orchestration_request.get("employee_id", "unknown"),
                "completion_status": "failed",
                "errors": [str(e)]
            }
# Instancia global del workflow
data_collection_workflow = DataCollectionWorkflow()

# Funciones auxiliares para uso externo
async def execute_data_collection_orchestration(orchestration_request: Dict[str, Any]) -> Dict[str, Any]:
    """Función principal para ejecutar orquestación del DATA COLLECTION HUB"""
    return await data_collection_workflow.execute_workflow(orchestration_request)

def get_workflow_status() -> Dict[str, Any]:
    """Obtener estado del workflow"""
    return {
        "workflow_available": data_collection_workflow.graph is not None,
        "agents_initialized": len([a for a in data_collection_workflow.agents.values() if a is not None]),
        "total_agents": len(data_collection_workflow.agents),
        "workflow_nodes": len(data_collection_workflow.graph.nodes) if data_collection_workflow.graph else 0
    }

async def test_workflow_connectivity() -> Dict[str, Any]:
    """Test de conectividad del workflow"""
    try:
        # Test básico de inicialización
        test_request = {
            "employee_id": "TEST_EMP_001",
            "employee_data": {"name": "Test Employee", "department": "IT"},
            "contract_data": {"salary": 50000, "currency": "USD"},
            "documents": []
        }
        
        # Solo verificar que el workflow se puede inicializar
        initial_state = {
            "orchestration_id": "test_workflow_connectivity",
            "employee_id": test_request["employee_id"],
            "employee_data": test_request["employee_data"],
            "contract_data": test_request["contract_data"],
            "documents": test_request["documents"],
            "orchestration_config": {},
            "current_phase": OrchestrationPhase.INITIATED,
            "progress_percentage": 0.0,
            "messages": [HumanMessage(content="Test connectivity")],
            "workflow_steps": [],
            "agent_results": {},
            "errors": [],
            "started_at": datetime.utcnow()
        }
        
        # Test solo de inicialización
        if data_collection_workflow.graph:
            return {
                "connectivity_test": "passed",
                "workflow_graph": "available",
                "agents_status": {
                    agent_type: "initialized" if agent else "not_initialized"
                    for agent_type, agent in data_collection_workflow.agents.items()
                }
            }
        else:
            return {"connectivity_test": "failed", "error": "Workflow graph not available"}
            
    except Exception as e:
        return {"connectivity_test": "failed", "error": str(e)}