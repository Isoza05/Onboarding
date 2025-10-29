from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from loguru import logger
import json
import uuid

from core.observability import observability_manager
from core.state_management.state_manager import state_manager
from core.state_management.models import AgentStateStatus, OnboardingPhase
from .schemas import (
    OrchestrationPattern, AgentType, TaskStatus, OrchestrationPhase,
    AgentTaskAssignment, WorkflowStep, PatternSelectionCriteria, 
    TaskDistributionStrategy, ProgressMetrics
)

# Schemas para herramientas
class PatternSelectorInput(BaseModel):
    """Input para selección de patrón de orquestración"""
    selection_criteria: Dict[str, Any] = Field(description="Criterios para selección de patrón")
    employee_context: Dict[str, Any] = Field(description="Contexto del empleado")
    system_state: Dict[str, Any] = Field(default={}, description="Estado actual del sistema")

class TaskDistributorInput(BaseModel):
    """Input para distribución de tareas"""
    orchestration_pattern: str = Field(description="Patrón de orquestración seleccionado")
    agent_assignments: List[Dict[str, Any]] = Field(description="Asignaciones de agentes")
    distribution_strategy: Dict[str, Any] = Field(default={}, description="Estrategia de distribución")

class StateCoordinatorInput(BaseModel):
    """Input para coordinación de estados"""
    session_id: str = Field(description="ID de sesión")
    agent_states: Dict[str, Any] = Field(description="Estados de agentes")
    coordination_action: str = Field(description="Acción de coordinación a realizar")

class ProgressMonitorInput(BaseModel):
    """Input para monitoreo de progreso"""
    orchestration_state: Dict[str, Any] = Field(description="Estado de orquestación")
    monitoring_criteria: Dict[str, Any] = Field(default={}, description="Criterios de monitoreo")
    sla_thresholds: Dict[str, Any] = Field(default={}, description="Umbrales SLA")

@tool(args_schema=PatternSelectorInput)
@observability_manager.trace_agent_execution("orchestrator_agent")
def pattern_selector_tool(
    selection_criteria: Dict[str, Any], 
    employee_context: Dict[str, Any],
    system_state: Dict[str, Any] = {}
) -> Dict[str, Any]:
    """
    Selecciona el patrón de orquestración óptimo basado en criterios del empleado.
    
    Args:
        selection_criteria: Criterios para selección (tipo empleado, nivel, departamento)
        employee_context: Contexto completo del empleado
        system_state: Estado actual del sistema
        
    Returns:
        Patrón seleccionado y configuración de orquestación
    """
    try:
        logger.info("Iniciando selección de patrón de orquestación")
        
        # Extraer criterios clave
        employee_type = selection_criteria.get("employee_type", "full_time")
        position_level = selection_criteria.get("position_level", "mid")
        department = selection_criteria.get("department", "general")
        priority = selection_criteria.get("priority", "medium")
        special_requirements = selection_criteria.get("special_requirements", [])
        
        # Lógica de selección de patrón
        selected_pattern = OrchestrationPattern.CONCURRENT_DATA_COLLECTION
        orchestration_config = {
            "max_concurrent_agents": 3,
            "timeout_per_agent": 300,  # 5 minutos
            "retry_policy": {"max_retries": 2, "backoff_factor": 1.5}
        }
        
        # Ajustar patrón basado en criterios
        if priority == "high" or "urgent" in special_requirements:
            orchestration_config["max_concurrent_agents"] = 5
            orchestration_config["timeout_per_agent"] = 180  # 3 minutos
            
        elif priority == "low":
            orchestration_config["max_concurrent_agents"] = 2
            orchestration_config["timeout_per_agent"] = 600  # 10 minutos
        
        # Configuración específica por departamento
        if department.lower() in ["engineering", "technology", "it"]:
            orchestration_config["specialized_validations"] = ["technical_skills", "security_clearance"]
            
        elif department.lower() in ["finance", "accounting", "legal"]:
            orchestration_config["specialized_validations"] = ["background_check", "compliance_strict"]
            
        elif department.lower() in ["sales", "marketing", "business"]:
            orchestration_config["specialized_validations"] = ["customer_facing", "communication_skills"]
        
        # Configuración por nivel de posición
        if position_level in ["senior", "executive", "director"]:
            orchestration_config["escalation_threshold"] = "low"
            orchestration_config["quality_gates"] = ["manager_approval", "hr_director_approval"]
            
        elif position_level in ["intern", "trainee"]:
            orchestration_config["simplified_workflow"] = True
            orchestration_config["mentor_assignment"] = True
        
        # Agentes requeridos basado en el patrón
        required_agents = [
            AgentType.INITIAL_DATA_COLLECTION.value,
            AgentType.CONFIRMATION_DATA.value,
            AgentType.DOCUMENTATION.value
        ]
        
        # Agregar agentes adicionales según requirements
        if "medical_clearance" in special_requirements:
            orchestration_config["medical_validation_strict"] = True
            
        if "security_clearance" in special_requirements:
            orchestration_config["security_background_check"] = True
            
        if "fast_track" in special_requirements:
            selected_pattern = OrchestrationPattern.CONCURRENT_DATA_COLLECTION
            orchestration_config["parallel_processing"] = True
        
        # Estimar duración del proceso
        base_duration = 1800  # 30 minutos base
        if priority == "high":
            base_duration = 900  # 15 minutos
        elif priority == "low":
            base_duration = 3600  # 60 minutos
            
        orchestration_config["estimated_duration"] = base_duration
        orchestration_config["sla_deadline"] = datetime.utcnow() + timedelta(seconds=base_duration)
        
        result = {
            "success": True,
            "selected_pattern": selected_pattern.value,
            "required_agents": required_agents,
            "orchestration_config": orchestration_config,
            "selection_rationale": {
                "employee_type": employee_type,
                "position_level": position_level,
                "department": department,
                "priority": priority,
                "special_considerations": special_requirements
            },
            "estimated_completion": (datetime.utcnow() + timedelta(seconds=base_duration)).isoformat(),
            "quality_gates": orchestration_config.get("quality_gates", ["basic_validation"]),
            "processing_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Patrón seleccionado: {selected_pattern.value} para empleado tipo {employee_type}")
        return result
        
    except Exception as e:
        logger.error(f"Error en selección de patrón: {e}")
        return {
            "success": False,
            "error": str(e),
            "selected_pattern": OrchestrationPattern.CONCURRENT_DATA_COLLECTION.value,
            "required_agents": [
                AgentType.INITIAL_DATA_COLLECTION.value,
                AgentType.CONFIRMATION_DATA.value,
                AgentType.DOCUMENTATION.value
            ],
            "orchestration_config": {
                "max_concurrent_agents": 3,
                "timeout_per_agent": 300,
                "fallback_mode": True
            }
        }

@tool(args_schema=TaskDistributorInput)
@observability_manager.trace_agent_execution("orchestrator_agent")
def task_distributor_tool(
    orchestration_pattern: str,
    agent_assignments: List[Dict[str, Any]],
    distribution_strategy: Dict[str, Any] = {}
) -> Dict[str, Any]:
    """
    Distribuye tareas a agentes según el patrón de orquestación.
    
    Args:
        orchestration_pattern: Patrón de orquestación a usar
        agent_assignments: Lista de asignaciones de agentes
        distribution_strategy: Estrategia de distribución
        
    Returns:
        Plan de distribución de tareas con timing y dependencias
    """
    try:
        logger.info(f"Iniciando distribución de tareas para patrón: {orchestration_pattern}")
        
        # Configuración por defecto
        default_strategy = {
            "strategy_type": "concurrent",
            "max_concurrent_agents": 3,
            "task_timeout": 300,
            "retry_policy": {"max_retries": 2, "backoff_seconds": 30}
        }
        
        strategy = {**default_strategy, **distribution_strategy}
        
        # Crear plan de distribución
        distribution_plan = {
            "pattern": orchestration_pattern,
            "strategy": strategy,
            "task_assignments": [],
            "execution_order": [],
            "dependencies": {},
            "timing_estimates": {}
        }
        
        # Procesar asignaciones según el patrón
        if orchestration_pattern == OrchestrationPattern.CONCURRENT_DATA_COLLECTION.value:
            # Distribución concurrente para DATA COLLECTION HUB
            concurrent_tasks = []
            
            for i, assignment in enumerate(agent_assignments):
                task_id = f"task_{uuid.uuid4().hex[:8]}"
                agent_type = assignment.get("agent_type", "unknown")
                
                task_assignment = {
                    "task_id": task_id,
                    "agent_type": agent_type,
                    "agent_id": assignment.get("agent_id", agent_type),
                    "task_description": assignment.get("task_description", f"Procesar con {agent_type}"),
                    "input_data": assignment.get("input_data", {}),
                    "priority": assignment.get("priority", "medium"),
                    "dependencies": [],  # Sin dependencias en modo concurrente
                    "estimated_duration": assignment.get("estimated_duration", 180),  # 3 minutos
                    "timeout": strategy["task_timeout"],
                    "retry_config": strategy["retry_policy"],
                    "execution_group": "concurrent_data_collection"
                }
                
                concurrent_tasks.append(task_assignment)
                distribution_plan["task_assignments"].append(task_assignment)
            
            # Orden de ejecución concurrente
            distribution_plan["execution_order"] = [{
                "group": "concurrent_data_collection",
                "tasks": [task["task_id"] for task in concurrent_tasks],
                "execution_type": "parallel",
                "wait_for_all": True
            }]
            
        elif orchestration_pattern == OrchestrationPattern.SEQUENTIAL_PROCESSING.value:
            # Distribución secuencial
            previous_task_id = None
            
            for i, assignment in enumerate(agent_assignments):
                task_id = f"task_{uuid.uuid4().hex[:8]}"
                agent_type = assignment.get("agent_type", "unknown")
                
                task_assignment = {
                    "task_id": task_id,
                    "agent_type": agent_type,
                    "agent_id": assignment.get("agent_id", agent_type),
                    "task_description": assignment.get("task_description", f"Procesar con {agent_type}"),
                    "input_data": assignment.get("input_data", {}),
                    "priority": assignment.get("priority", "medium"),
                    "dependencies": [previous_task_id] if previous_task_id else [],
                    "estimated_duration": assignment.get("estimated_duration", 240),
                    "timeout": strategy["task_timeout"],
                    "retry_config": strategy["retry_policy"],
                    "execution_group": f"sequential_step_{i}"
                }
                
                distribution_plan["task_assignments"].append(task_assignment)
                distribution_plan["dependencies"][task_id] = task_assignment["dependencies"]
                previous_task_id = task_id
            
            # Orden de ejecución secuencial
            distribution_plan["execution_order"] = [
                {
                    "group": f"sequential_step_{i}",
                    "tasks": [task["task_id"]],
                    "execution_type": "sequential",
                    "depends_on": f"sequential_step_{i-1}" if i > 0 else None
                }
                for i, task in enumerate(distribution_plan["task_assignments"])
            ]
        
        # Calcular estimaciones de tiempo
        total_estimated_time = 0
        if strategy["strategy_type"] == "concurrent":
            # Tiempo = el más lento de los agentes concurrentes
            max_duration = max([task.get("estimated_duration", 180) for task in distribution_plan["task_assignments"]], default=180)
            total_estimated_time = max_duration + 60  # Buffer de 1 minuto
        else:
            # Tiempo = suma de todos los agentes
            total_estimated_time = sum([task.get("estimated_duration", 240) for task in distribution_plan["task_assignments"]])
        
        distribution_plan["timing_estimates"] = {
            "total_estimated_seconds": total_estimated_time,
            "estimated_completion": (datetime.utcnow() + timedelta(seconds=total_estimated_time)).isoformat(),
            "sla_buffer_seconds": 300,  # 5 minutos de buffer
            "critical_path": [task["task_id"] for task in distribution_plan["task_assignments"][:1]]  # Primer task como crítico
        }
        
        # Configurar monitoring checkpoints
        distribution_plan["monitoring_checkpoints"] = [
            {
                "checkpoint_id": f"checkpoint_{i}",
                "check_time_seconds": int(total_estimated_time * (i+1) / 4),
                "criteria": "agent_progress_check"
            }
            for i in range(4)  # 4 checkpoints durante la ejecución
        ]
        
        result = {
            "success": True,
            "distribution_plan": distribution_plan,
            "tasks_created": len(distribution_plan["task_assignments"]),
            "execution_strategy": strategy["strategy_type"],
            "estimated_completion": distribution_plan["timing_estimates"]["estimated_completion"],
            "processing_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Plan de distribución creado: {len(distribution_plan['task_assignments'])} tareas")
        return result
        
    except Exception as e:
        logger.error(f"Error en distribución de tareas: {e}")
        return {
            "success": False,
            "error": str(e),
            "distribution_plan": {
                "pattern": orchestration_pattern,
                "task_assignments": [],
                "execution_order": [],
                "error_recovery": True
            }
        }

@tool(args_schema=StateCoordinatorInput)
@observability_manager.trace_agent_execution("orchestrator_agent")
def state_coordinator_tool(
    session_id: str,
    agent_states: Dict[str, Any],
    coordination_action: str
) -> Dict[str, Any]:
    """
    Coordina estados entre agentes y actualiza Common State Management.
    
    Args:
        session_id: ID de sesión para coordinación
        agent_states: Estados actuales de agentes
        coordination_action: Acción a realizar (sync, update, validate)
        
    Returns:
        Resultado de coordinación de estados
    """
    try:
        logger.info(f"Coordinando estados para sesión: {session_id}, acción: {coordination_action}")
        
        coordination_result = {
            "session_id": session_id,
            "action": coordination_action,
            "agents_coordinated": [],
            "state_updates": {},
            "synchronization_status": "success",
            "conflicts_resolved": 0
        }
        
        if coordination_action == "sync":
            # Sincronizar estados entre agentes
            for agent_id, state_data in agent_states.items():
                try:
                    # Obtener estado actual del agente
                    current_state = state_manager.get_agent_state(agent_id, session_id)
                    
                    if current_state:
                        # Verificar si hay conflictos de estado
                        conflicts = []
                        if state_data.get("status") != current_state.status.value:
                            conflicts.append(f"Status mismatch: {state_data.get('status')} vs {current_state.status.value}")
                        
                        if conflicts:
                            coordination_result["conflicts_resolved"] += len(conflicts)
                            # Resolver conflictos - preferir estado más reciente
                            latest_update = max(
                                state_data.get("last_updated", datetime.min.isoformat()),
                                current_state.last_updated.isoformat()
                            )
                            
                            if state_data.get("last_updated", "") == latest_update:
                                # Actualizar con estado proporcionado
                                state_manager.update_agent_state(
                                    agent_id,
                                    AgentStateStatus(state_data.get("status", "idle")),
                                    state_data.get("data", {}),
                                    session_id
                                )
                        
                        coordination_result["agents_coordinated"].append(agent_id)
                        coordination_result["state_updates"][agent_id] = {
                            "previous_status": current_state.status.value,
                            "current_status": state_data.get("status", current_state.status.value),
                            "conflicts_resolved": len(conflicts)
                        }
                    
                except Exception as e:
                    logger.warning(f"Error coordinando agente {agent_id}: {e}")
                    coordination_result["state_updates"][agent_id] = {"error": str(e)}
        
        elif coordination_action == "update":
            # Actualizar estados masivamente
            for agent_id, state_data in agent_states.items():
                try:
                    status = AgentStateStatus(state_data.get("status", "idle"))
                    data = state_data.get("data", {})
                    
                    success = state_manager.update_agent_state(agent_id, status, data, session_id)
                    
                    if success:
                        coordination_result["agents_coordinated"].append(agent_id)
                        coordination_result["state_updates"][agent_id] = {
                            "status": status.value,
                            "data_keys": list(data.keys()),
                            "updated": True
                        }
                    
                except Exception as e:
                    logger.warning(f"Error actualizando agente {agent_id}: {e}")
                    coordination_result["state_updates"][agent_id] = {"error": str(e)}
        
        elif coordination_action == "validate":
            # Validar consistencia de estados
            validation_issues = []
            
            for agent_id, expected_state in agent_states.items():
                current_state = state_manager.get_agent_state(agent_id, session_id)
                
                if not current_state:
                    validation_issues.append(f"Agente {agent_id} no encontrado en state management")
                    continue
                
                # Validar status
                expected_status = expected_state.get("status")
                if expected_status and current_state.status.value != expected_status:
                    validation_issues.append(f"Status mismatch en {agent_id}: esperado {expected_status}, actual {current_state.status.value}")
                
                # Validar datos críticos
                expected_data = expected_state.get("data", {})
                for key, expected_value in expected_data.items():
                    if key in current_state.data and current_state.data[key] != expected_value:
                        validation_issues.append(f"Data mismatch en {agent_id}.{key}")
                
                coordination_result["agents_coordinated"].append(agent_id)
            
            coordination_result["validation_issues"] = validation_issues
            coordination_result["synchronization_status"] = "valid" if not validation_issues else "issues_found"
        
        # Actualizar contexto del empleado si es necesario
        if session_id:
            employee_context = state_manager.get_employee_context(session_id)
            if employee_context:
                # Actualizar fase si todos los agentes están completados
                completed_agents = [
                    agent_id for agent_id, update in coordination_result["state_updates"].items()
                    if update.get("status") == "completed"
                ]
                
                if len(completed_agents) >= 3:  # Los 3 agentes del DATA COLLECTION HUB
                    state_manager.update_employee_data(
                        session_id,
                        {
                            "data_collection_completed": True,
                            "completed_agents": completed_agents,
                            "coordination_timestamp": datetime.utcnow().isoformat()
                        },
                        "processed"
                    )
        
        result = {
            "success": True,
            "coordination_result": coordination_result,
            "processing_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Coordinación completada: {len(coordination_result['agents_coordinated'])} agentes")
        return result
        
    except Exception as e:
        logger.error(f"Error en coordinación de estados: {e}")
        return {
            "success": False,
            "error": str(e),
            "coordination_result": {
                "session_id": session_id,
                "action": coordination_action,
                "synchronization_status": "failed",
                "agents_coordinated": []
            }
        }

@tool(args_schema=ProgressMonitorInput)
@observability_manager.trace_agent_execution("orchestrator_agent")
def progress_monitor_tool(
    orchestration_state: Dict[str, Any],
    monitoring_criteria: Dict[str, Any] = {},
    sla_thresholds: Dict[str, Any] = {}
) -> Dict[str, Any]:
    """
    Monitorea progreso de orquestación y verifica SLAs.
    
    Args:
        orchestration_state: Estado actual de orquestación
        monitoring_criteria: Criterios de monitoreo
        sla_thresholds: Umbrales SLA
        
    Returns:
        Reporte de progreso y alertas SLA
    """
    try:
        logger.info("Iniciando monitoreo de progreso de orquestación")
        
        # Configuración por defecto
        default_criteria = {
            "track_completion": True,
            "track_quality": True,
            "track_timing": True,
            "alert_on_delays": True
        }
        
        default_sla = {
            "max_total_time_minutes": 30,
            "max_agent_time_minutes": 5,
            "min_quality_score": 70.0,
            "max_error_rate": 0.1
        }
        
        criteria = {**default_criteria, **monitoring_criteria}
        sla = {**default_sla, **sla_thresholds}
        
        # Extraer datos del estado de orquestación
        session_id = orchestration_state.get("session_id", "unknown")
        started_at = orchestration_state.get("started_at")
        current_phase = orchestration_state.get("current_phase", "initiated")
        workflow_steps = orchestration_state.get("workflow_steps", [])
        agent_results = orchestration_state.get("agent_results", {})
        
        # Calcular métricas de progreso
        progress_metrics = {
            "session_id": session_id,
            "current_phase": current_phase,
            "monitoring_timestamp": datetime.utcnow().isoformat()
        }
        
        # Progreso de pasos
        total_steps = len(workflow_steps)
        completed_steps = len([step for step in workflow_steps if step.get("status") == "completed"])
        progress_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        progress_metrics.update({
            "steps_total": total_steps,
            "steps_completed": completed_steps,
            "progress_percentage": round(progress_percentage, 2)
        })
        
        # Timing analysis
        if started_at:
            try:
                start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                elapsed_time = (datetime.utcnow() - start_time).total_seconds()
                progress_metrics["elapsed_time_seconds"] = round(elapsed_time, 2)
                progress_metrics["elapsed_time_minutes"] = round(elapsed_time / 60, 2)
            except:
                progress_metrics["elapsed_time_seconds"] = 0
                progress_metrics["elapsed_time_minutes"] = 0
        
        # Análisis de agentes
        agent_analysis = {}
        total_quality_score = 0
        agents_with_scores = 0
        
        for agent_id, result in agent_results.items():
            if isinstance(result, dict):
                agent_metrics = {
                    "status": result.get("status", "unknown"),
                    "success": result.get("success", False),
                    "processing_time": result.get("processing_time", 0),
                    "quality_score": result.get("validation_score", result.get("compliance_score", 0))
                }
                
                # Acumular para score general
                if agent_metrics["quality_score"] > 0:
                    total_quality_score += agent_metrics["quality_score"]
                    agents_with_scores += 1
                
                agent_analysis[agent_id] = agent_metrics
        
        # Score de calidad general
        overall_quality_score = (total_quality_score / agents_with_scores) if agents_with_scores > 0 else 0
        progress_metrics["overall_quality_score"] = round(overall_quality_score, 2)
        
        # Análisis SLA
        sla_analysis = {
            "status": "compliant",
            "violations": [],
            "warnings": [],
            "time_remaining_minutes": None
        }
        
        # Verificar tiempo total
        elapsed_minutes = progress_metrics.get("elapsed_time_minutes", 0)
        max_minutes = sla["max_total_time_minutes"]
        
        if elapsed_minutes > max_minutes:
            sla_analysis["status"] = "violated"
            sla_analysis["violations"].append(f"Tiempo total excedido: {elapsed_minutes:.1f}min > {max_minutes}min")
        elif elapsed_minutes > (max_minutes * 0.8):
            sla_analysis["warnings"].append(f"Acercándose al límite de tiempo: {elapsed_minutes:.1f}min de {max_minutes}min")
        
        sla_analysis["time_remaining_minutes"] = max(0, max_minutes - elapsed_minutes)
        
        # Verificar calidad
        min_quality = sla["min_quality_score"]
        if overall_quality_score < min_quality and overall_quality_score > 0:
            sla_analysis["status"] = "at_risk"
            sla_analysis["warnings"].append(f"Score de calidad bajo límite: {overall_quality_score:.1f} < {min_quality}")
        
        # Verificar agentes individuales
        for agent_id, metrics in agent_analysis.items():
            agent_time = metrics.get("processing_time", 0) / 60  # convertir a minutos
            if agent_time > sla["max_agent_time_minutes"]:
                sla_analysis["warnings"].append(f"Agente {agent_id} excedió tiempo: {agent_time:.1f}min")
        
        # Determinar próximas acciones
        next_actions = []
        escalation_needed = False
        
        if sla_analysis["status"] == "violated":
            next_actions.append("Escalación inmediata requerida")
            escalation_needed = True
        elif sla_analysis["status"] == "at_risk":
            next_actions.append("Monitoreo intensivo")
            next_actions.append("Optimización de recursos")
        elif progress_percentage < 50 and elapsed_minutes > (max_minutes * 0.5):
            next_actions.append("Acelerar procesamiento")
            next_actions.append("Revisar cuellos de botella")
        else:
            next_actions.append("Continuar monitoreo normal")
        
        # Estimación de finalización
        if progress_percentage > 0 and elapsed_minutes > 0:
            estimated_total_time = (elapsed_minutes / progress_percentage) * 100
            estimated_remaining = max(0, estimated_total_time - elapsed_minutes)
            progress_metrics["estimated_completion_minutes"] = round(estimated_remaining, 1)
            progress_metrics["estimated_completion_time"] = (
                datetime.utcnow() + timedelta(minutes=estimated_remaining)
            ).isoformat()
        
        result = {
            "success": True,
            "progress_metrics": progress_metrics,
            "agent_analysis": agent_analysis,
            "sla_analysis": sla_analysis,
            "next_actions": next_actions,
            "escalation_needed": escalation_needed,
            "quality_gates": {
                "passed": len([a for a in agent_analysis.values() if a.get("success", False)]),
                "total": len(agent_analysis),
                "overall_score": overall_quality_score
            },
            "processing_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Monitoreo completado: {progress_percentage:.1f}% progreso, SLA {sla_analysis['status']}")
        return result
        
    except Exception as e:
        logger.error(f"Error en monitoreo de progreso: {e}")
        return {
            "success": False,
            "error": str(e),
            "progress_metrics": {
                "progress_percentage": 0,
                "status": "error"
            },
            "sla_analysis": {
                "status": "unknown",
                "violations": [f"Error en monitoreo: {str(e)}"]
            }
        }