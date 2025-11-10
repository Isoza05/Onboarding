from typing import Dict, Any, List, Optional
from langchain.tools import BaseTool
from datetime import datetime, timedelta
import json
import asyncio
from .schemas import (
    RecoveryAction, RecoveryStatus, RecoveryAttempt, SystemRecoveryState,
    RecoveryStrategy, RecoveryPriority
)

class RetryManagerTool(BaseTool):
    """Herramienta para gestionar reintentos automáticos"""
    name: str = "retry_manager_tool"
    description: str = "Gestiona reintentos automáticos con diferentes estrategias de backoff"

    def _run(self, recovery_request: Dict[str, Any], 
             failed_operation: Dict[str, Any],
             retry_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Gestionar reintentos de operaciones fallidas"""
        try:
            from core.state_management.state_manager import state_manager
            
            session_id = recovery_request.get("session_id")
            recovery_strategy = recovery_request.get("recovery_strategy", "immediate_retry")
            max_attempts = recovery_request.get("max_retry_attempts", 3)
            
            # Configuración por defecto
            default_config = {
                "base_delay": 5,
                "exponential_factor": 2.0,
                "max_delay": 300,
                "jitter": True
            }
            
            config = {**default_config, **(retry_config or {})}
            
            retry_attempts = []
            current_attempt = 1
            success = False
            
            while current_attempt <= max_attempts and not success:
                attempt = RecoveryAttempt(
                    attempt_number=current_attempt,
                    recovery_action=RecoveryAction.RETRY_OPERATION,
                    started_at=datetime.utcnow()
                )
                
                try:
                    # Calcular delay para este intento
                    delay = self._calculate_retry_delay(
                        current_attempt, recovery_strategy, config
                    )
                    
                    if current_attempt > 1:
                        self._wait_with_monitoring(delay, session_id)
                    
                    # Ejecutar retry de la operación
                    retry_result = self._execute_retry_operation(
                        failed_operation, session_id, current_attempt
                    )
                    
                    # Actualizar attempt
                    attempt.completed_at = datetime.utcnow()
                    attempt.duration_seconds = (attempt.completed_at - attempt.started_at).total_seconds()
                    attempt.success = retry_result.get("success", False)
                    attempt.result_data = retry_result
                    
                    if attempt.success:
                        attempt.status = RecoveryStatus.SUCCESS
                        success = True
                    else:
                        attempt.status = RecoveryStatus.FAILED
                        attempt.error_message = retry_result.get("error", "Retry failed")
                    
                except Exception as e:
                    attempt.completed_at = datetime.utcnow()
                    attempt.duration_seconds = (attempt.completed_at - attempt.started_at).total_seconds()
                    attempt.status = RecoveryStatus.FAILED
                    attempt.error_message = str(e)
                    attempt.success = False
                
                retry_attempts.append(attempt.dict())
                current_attempt += 1
            
            # Generar resultado final
            successful_attempts = len([a for a in retry_attempts if a["success"]])
            
            return {
                "success": success,
                "retry_strategy": recovery_strategy,
                "total_attempts": len(retry_attempts),
                "successful_attempts": successful_attempts,
                "failed_attempts": len(retry_attempts) - successful_attempts,
                "retry_attempts": retry_attempts,
                "final_result": retry_attempts[-1] if retry_attempts else None,
                "next_action": "success" if success else "escalate_to_human",
                "recommendations": self._generate_retry_recommendations(retry_attempts, recovery_strategy)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error in retry manager: {str(e)}",
                "retry_attempts": [],
                "total_attempts": 0,
                "next_action": "escalate_to_human"
            }

    def _calculate_retry_delay(self, attempt_number: int, strategy: str, 
                              config: Dict[str, Any]) -> float:
        """Calcular delay para retry basado en estrategia"""
        base_delay = config.get("base_delay", 5)
        
        if strategy == "immediate_retry":
            return 0.1  # Casi inmediato
        elif strategy == "exponential_backoff":
            factor = config.get("exponential_factor", 2.0)
            delay = base_delay * (factor ** (attempt_number - 1))
            max_delay = config.get("max_delay", 300)
            return min(delay, max_delay)
        elif strategy == "linear_backoff":
            return base_delay * attempt_number
        else:
            return base_delay

    def _wait_with_monitoring(self, delay_seconds: float, session_id: str):
        """Esperar con monitoreo de estado del sistema"""
        import time
        
        # Para delays largos, dividir en chunks para permitir monitoreo
        chunk_size = 5.0  # 5 segundos por chunk
        remaining = delay_seconds
        
        while remaining > 0:
            sleep_time = min(chunk_size, remaining)
            time.sleep(sleep_time)
            remaining -= sleep_time
            
            # Verificar si el sistema requiere cancelación
            if remaining > 0:
                self._check_system_health(session_id)

    def _check_system_health(self, session_id: str):
        """Verificar salud del sistema durante espera"""
        try:
            from core.state_management.state_manager import state_manager
            
            # Verificar estado del empleado
            context = state_manager.get_employee_context(session_id)
            if not context:
                raise Exception("Employee context lost during retry wait")
            
            # Verificar carga del sistema (simulado)
            # En implementación real, esto verificaría métricas reales
            pass
            
        except Exception as e:
            # Log pero no interrumpir el retry
            pass

    def _execute_retry_operation(self, failed_operation: Dict[str, Any], 
                                session_id: str, attempt_number: int) -> Dict[str, Any]:
        """Ejecutar retry de operación específica"""
        operation_type = failed_operation.get("operation_type", "unknown")
        agent_id = failed_operation.get("agent_id")
        
        # Simular retry basado en tipo de operación
        if operation_type == "agent_processing":
            return self._retry_agent_processing(agent_id, session_id, attempt_number)
        elif operation_type == "data_validation":
            return self._retry_data_validation(failed_operation, session_id)
        elif operation_type == "external_api_call":
            return self._retry_external_api(failed_operation, session_id)
        else:
            # Retry genérico
            return self._retry_generic_operation(failed_operation, session_id)

    def _retry_agent_processing(self, agent_id: str, session_id: str, 
                               attempt_number: int) -> Dict[str, Any]:
        """Retry específico para procesamiento de agentes"""
        try:
            from core.state_management.state_manager import state_manager
            
            # Obtener estado actual del agente
            agent_state = state_manager.get_agent_state(agent_id, session_id)
            if not agent_state:
                return {"success": False, "error": "Agent state not found"}
            
            # Simular retry del agente
            # En implementación real, esto realmente reintentaría la operación del agente
            success_probability = 0.7 + (attempt_number * 0.1)  # Mejor probabilidad en intentos posteriores
            
            import random
            if random.random() < success_probability:
                # Simular éxito
                state_manager.update_agent_state(
                    agent_id,
                    AgentStateStatus.COMPLETED,
                    {
                        "retry_attempt": attempt_number,
                        "retry_success": True,
                        "completed_at": datetime.utcnow().isoformat()
                    },
                    session_id
                )
                
                return {
                    "success": True,
                    "agent_id": agent_id,
                    "retry_attempt": attempt_number,
                    "recovery_method": "agent_restart_retry"
                }
            else:
                return {
                    "success": False,
                    "error": f"Agent {agent_id} retry failed on attempt {attempt_number}",
                    "retry_attempt": attempt_number
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _retry_data_validation(self, failed_operation: Dict[str, Any], 
                              session_id: str) -> Dict[str, Any]:
        """Retry específico para validación de datos"""
        try:
            # Simular retry de validación
            validation_data = failed_operation.get("validation_data", {})
            
            # En implementación real, esto reintentaría la validación con datos mejorados
            return {
                "success": True,
                "validation_passed": True,
                "recovery_method": "data_revalidation"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _retry_external_api(self, failed_operation: Dict[str, Any], 
                           session_id: str) -> Dict[str, Any]:
        """Retry específico para APIs externas"""
        try:
            # Simular retry de API externa
            api_endpoint = failed_operation.get("api_endpoint", "unknown")
            
            # En implementación real, esto reintentaría la llamada API
            import random
            if random.random() < 0.8:  # 80% probabilidad de éxito
                return {
                    "success": True,
                    "api_response": {"status": "success", "data": "mock_data"},
                    "recovery_method": "api_retry"
                }
            else:
                return {
                    "success": False,
                    "error": f"API {api_endpoint} still unavailable"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _retry_generic_operation(self, failed_operation: Dict[str, Any], 
                                session_id: str) -> Dict[str, Any]:
        """Retry genérico para operaciones no específicas"""
        # Simular retry genérico con probabilidad de éxito
        import random
        success = random.random() < 0.6  # 60% probabilidad de éxito
        
        return {
            "success": success,
            "recovery_method": "generic_retry",
            "error": None if success else "Generic operation retry failed"
        }

    def _generate_retry_recommendations(self, retry_attempts: List[Dict], 
                                      strategy: str) -> List[str]:
        """Generar recomendaciones basadas en intentos de retry"""
        recommendations = []
        
        if not retry_attempts:
            return ["No retry attempts available for analysis"]
        
        success_rate = len([a for a in retry_attempts if a["success"]]) / len(retry_attempts)
        avg_duration = sum(a.get("duration_seconds", 0) for a in retry_attempts) / len(retry_attempts)
        
        if success_rate < 0.3:
            recommendations.append("Low retry success rate - consider alternative recovery strategy")
        
        if avg_duration > 30:
            recommendations.append("High retry duration - optimize operation or increase timeout")
        
        if strategy == "immediate_retry" and len(retry_attempts) > 1:
            recommendations.append("Consider exponential backoff for better success rate")
        
        # Análisis de patrones de error
        error_patterns = {}
        for attempt in retry_attempts:
            if not attempt["success"] and attempt.get("error_message"):
                error_msg = attempt["error_message"][:50]  # Truncar para agrupación
                error_patterns[error_msg] = error_patterns.get(error_msg, 0) + 1
        
        if error_patterns:
            most_common_error = max(error_patterns.items(), key=lambda x: x[1])
            recommendations.append(f"Most common error pattern: {most_common_error[0]}")
        
        return recommendations

class StateRestorerTool(BaseTool):
    """Herramienta para restaurar estados del sistema"""
    name: str = "state_restorer_tool"
    description: str = "Restaura estados de agentes y sistema a puntos conocidos estables"

    def _run(self, recovery_request: Dict[str, Any],
             target_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Restaurar estado del sistema"""
        try:
            from core.state_management.state_manager import state_manager
            
            session_id = recovery_request.get("session_id")
            recovery_id = recovery_request.get("recovery_id")
            
            # Crear snapshot del estado actual antes de restauración
            pre_restoration_snapshot = self._create_state_snapshot(session_id)
            
            restoration_results = []
            
            # 1. Restaurar estados de agentes
            agent_restoration = self._restore_agent_states(session_id, target_state)
            restoration_results.append(("agent_states", agent_restoration))
            
            # 2. Restaurar datos del empleado
            employee_restoration = self._restore_employee_data(session_id, target_state)
            restoration_results.append(("employee_data", employee_restoration))
            
            # 3. Restaurar estado del pipeline
            pipeline_restoration = self._restore_pipeline_state(session_id, target_state)
            restoration_results.append(("pipeline_state", pipeline_restoration))
            
            # 4. Verificar integridad post-restauración
            integrity_check = self._verify_restoration_integrity(session_id)
            restoration_results.append(("integrity_check", integrity_check))
            
            # Calcular éxito general
            successful_restorations = len([r for r in restoration_results if r[1].get("success", False)])
            total_restorations = len(restoration_results)
            success_rate = successful_restorations / total_restorations if total_restorations > 0 else 0
            
            # Crear snapshot post-restauración
            post_restoration_snapshot = self._create_state_snapshot(session_id)
            
            return {
                "success": success_rate >= 0.75,  # 75% de éxito mínimo
                "recovery_id": recovery_id,
                "session_id": session_id,
                "restoration_timestamp": datetime.utcnow().isoformat(),
                "restoration_results": restoration_results,
                "success_rate": success_rate,
                "successful_restorations": successful_restorations,
                "total_restorations": total_restorations,
                "pre_restoration_snapshot": pre_restoration_snapshot,
                "post_restoration_snapshot": post_restoration_snapshot,
                "integrity_verified": integrity_check.get("success", False),
                "next_actions": self._determine_post_restoration_actions(restoration_results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error in state restoration: {str(e)}",
                "restoration_results": [],
                "next_actions": ["escalate_to_human", "manual_state_review"]
            }

    def _create_state_snapshot(self, session_id: str) -> Dict[str, Any]:
        """Crear snapshot completo del estado actual"""
        try:
            from core.state_management.state_manager import state_manager
            
            # Obtener contexto del empleado
            employee_context = state_manager.get_employee_context(session_id)
            
            snapshot = {
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": session_id,
                "employee_context": None,
                "agent_states": {},
                "system_overview": state_manager.get_system_overview()
            }
            
            if employee_context:
                snapshot["employee_context"] = {
                    "employee_id": employee_context.employee_id,
                    "phase": employee_context.phase.value if hasattr(employee_context.phase, 'value') else str(employee_context.phase),
                    "raw_data_keys": list(employee_context.raw_data.keys()) if employee_context.raw_data else [],
                    "processed_data_keys": list(employee_context.processed_data.keys()) if employee_context.processed_data else [],
                    "agent_states_count": len(employee_context.agent_states)
                }
                
                # Snapshot de estados de agentes
                for agent_id, agent_state in employee_context.agent_states.items():
                    snapshot["agent_states"][agent_id] = {
                        "status": agent_state.status.value if hasattr(agent_state.status, 'value') else str(agent_state.status),
                        "last_updated": agent_state.last_updated.isoformat() if agent_state.last_updated else None,
                        "error_count": len(agent_state.errors) if agent_state.errors else 0,
                        "has_data": bool(agent_state.data)
                    }
            
            return snapshot
            
        except Exception as e:
            return {
                "error": f"Failed to create snapshot: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }

    def _restore_agent_states(self, session_id: str, 
                             target_state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Restaurar estados de agentes a estado estable"""
        try:
            from core.state_management.state_manager import state_manager
            from core.state_management.models import AgentStateStatus
            
            employee_context = state_manager.get_employee_context(session_id)
            if not employee_context:
                return {"success": False, "error": "Employee context not found"}
            
            restored_agents = []
            failed_agents = []
            
            for agent_id, agent_state in employee_context.agent_states.items():
                try:
                    # Determinar estado objetivo
                    if target_state and agent_id in target_state.get("agent_states", {}):
                        target_status = target_state["agent_states"][agent_id]
                    else:
                        # Estado por defecto basado en el estado actual
                        current_status = agent_state.status
                        if current_status == AgentStateStatus.ERROR:
                            target_status = AgentStateStatus.IDLE
                        elif current_status == AgentStateStatus.PROCESSING:
                            # Verificar si lleva mucho tiempo processing
                            if agent_state.last_updated:
                                time_diff = datetime.utcnow() - agent_state.last_updated
                                if time_diff.total_seconds() > 1800:  # 30 minutos
                                    target_status = AgentStateStatus.IDLE
                                else:
                                    continue  # Dejar en processing
                            else:
                                target_status = AgentStateStatus.IDLE
                        else:
                            continue  # No restaurar si está en estado válido
                    
                    # Restaurar estado del agente
                    restore_success = state_manager.update_agent_state(
                        agent_id,
                        target_status,
                        {
                            "restored_at": datetime.utcnow().isoformat(),
                            "restored_from": agent_state.status.value if hasattr(agent_state.status, 'value') else str(agent_state.status),
                            "restoration_reason": "recovery_state_restoration"
                        },
                        session_id
                    )
                    
                    if restore_success:
                        restored_agents.append({
                            "agent_id": agent_id,
                            "previous_status": agent_state.status.value if hasattr(agent_state.status, 'value') else str(agent_state.status),
                            "restored_status": target_status.value if hasattr(target_status, 'value') else str(target_status)
                        })
                    else:
                        failed_agents.append({
                            "agent_id": agent_id,
                            "error": "State update failed"
                        })
                        
                except Exception as e:
                    failed_agents.append({
                        "agent_id": agent_id,
                        "error": str(e)
                    })
            
            return {
                "success": len(failed_agents) == 0,
                "restored_agents": restored_agents,
                "failed_agents": failed_agents,
                "restoration_count": len(restored_agents),
                "restoration_summary": f"{len(restored_agents)} agents restored, {len(failed_agents)} failed"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Agent state restoration failed: {str(e)}",
                "restored_agents": [],
                "failed_agents": []
            }

    def _restore_employee_data(self, session_id: str, 
                              target_state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Restaurar datos del empleado a estado consistente"""
        try:
            from core.state_management.state_manager import state_manager
            
            employee_context = state_manager.get_employee_context(session_id)
            if not employee_context:
                return {"success": False, "error": "Employee context not found"}
            
            restoration_actions = []
            
            # 1. Limpiar datos corruptos o inconsistentes
            if employee_context.processed_data:
                cleaned_data = self._clean_processed_data(employee_context.processed_data)
                if cleaned_data != employee_context.processed_data:
                    state_manager.update_employee_data(session_id, cleaned_data, "cleaned")
                    restoration_actions.append("processed_data_cleaned")
            
            # 2. Verificar y restaurar datos críticos
            critical_data_check = self._verify_critical_employee_data(employee_context)
            if not critical_data_check["valid"]:
                # Restaurar datos críticos desde raw_data si es posible
                restored_data = self._restore_critical_data(employee_context)
                if restored_data:
                    state_manager.update_employee_data(session_id, restored_data, "restored")
                    restoration_actions.append("critical_data_restored")
            
            # 3. Actualizar phase si es necesario
            if employee_context.phase.value == "error_handling":
                # Determinar phase apropiado basado en estado de agentes
                appropriate_phase = self._determine_appropriate_phase(employee_context)
                if appropriate_phase != employee_context.phase:
                    employee_context.phase = appropriate_phase
                    restoration_actions.append(f"phase_updated_to_{appropriate_phase.value}")
            
            return {
                "success": True,
                "restoration_actions": restoration_actions,
                "employee_id": employee_context.employee_id,
                "current_phase": employee_context.phase.value if hasattr(employee_context.phase, 'value') else str(employee_context.phase),
                "data_integrity_verified": True            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Employee data restoration failed: {str(e)}",
                "restoration_actions": []
            }

    def _restore_pipeline_state(self, session_id: str, 
                               target_state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Restaurar estado del pipeline a punto estable"""
        try:
            from core.state_management.state_manager import state_manager
            from core.state_management.models import OnboardingPhase
            
            employee_context = state_manager.get_employee_context(session_id)
            if not employee_context:
                return {"success": False, "error": "Employee context not found"}
            
            pipeline_actions = []
            
            # 1. Evaluar estado actual del pipeline
            pipeline_health = self._assess_pipeline_health(employee_context)
            
            # 2. Restaurar pipeline según salud
            if pipeline_health["status"] == "blocked":
                # Desbloquear pipeline
                unblock_result = self._unblock_pipeline(employee_context, session_id)
                if unblock_result["success"]:
                    pipeline_actions.append("pipeline_unblocked")
                
            elif pipeline_health["status"] == "inconsistent":
                # Sincronizar estados
                sync_result = self._synchronize_pipeline_states(employee_context, session_id)
                if sync_result["success"]:
                    pipeline_actions.append("pipeline_synchronized")
            
            # 3. Verificar continuidad del pipeline
            continuity_check = self._verify_pipeline_continuity(employee_context)
            if not continuity_check["can_continue"]:
                # Establecer punto de continuación seguro
                safe_point = self._establish_safe_continuation_point(employee_context)
                pipeline_actions.append(f"safe_point_set_{safe_point}")
            
            return {
                "success": len(pipeline_actions) > 0 or pipeline_health["status"] == "healthy",
                "pipeline_health": pipeline_health,
                "pipeline_actions": pipeline_actions,
                "can_continue": continuity_check.get("can_continue", False),
                "next_stage": continuity_check.get("next_stage", "unknown")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Pipeline state restoration failed: {str(e)}",
                "pipeline_actions": []
            }

    def _verify_restoration_integrity(self, session_id: str) -> Dict[str, Any]:
        """Verificar integridad después de la restauración"""
        try:
            from core.state_management.state_manager import state_manager
            
            employee_context = state_manager.get_employee_context(session_id)
            if not employee_context:
                return {"success": False, "error": "Employee context not found"}
            
            integrity_checks = []
            
            # 1. Verificar consistencia de estados de agentes
            agent_consistency = self._check_agent_state_consistency(employee_context)
            integrity_checks.append(("agent_consistency", agent_consistency))
            
            # 2. Verificar integridad de datos
            data_integrity = self._check_data_integrity(employee_context)
            integrity_checks.append(("data_integrity", data_integrity))
            
            # 3. Verificar sincronización del pipeline
            pipeline_sync = self._check_pipeline_synchronization(employee_context)
            integrity_checks.append(("pipeline_sync", pipeline_sync))
            
            # Calcular score de integridad
            passed_checks = len([c for c in integrity_checks if c[1].get("passed", False)])
            total_checks = len(integrity_checks)
            integrity_score = passed_checks / total_checks if total_checks > 0 else 0
            
            return {
                "success": integrity_score >= 0.8,  # 80% de checks deben pasar
                "integrity_score": integrity_score,
                "passed_checks": passed_checks,
                "total_checks": total_checks,
                "integrity_checks": integrity_checks,
                "system_stable": integrity_score >= 0.9
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Integrity verification failed: {str(e)}",
                "integrity_score": 0.0
            }

    def _clean_processed_data(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Limpiar datos procesados corruptos"""
        cleaned_data = {}
        
        for key, value in processed_data.items():
            # Remover campos con valores None o vacíos inválidos
            if value is not None and value != "" and value != {}:
                # Limpiar timestamps inválidos
                if key.endswith("_at") or key.endswith("_timestamp"):
                    try:
                        if isinstance(value, str):
                            datetime.fromisoformat(value.replace("Z", "+00:00"))
                        cleaned_data[key] = value
                    except ValueError:
                        # Skip invalid timestamps
                        continue
                else:
                    cleaned_data[key] = value
        
        return cleaned_data

    def _verify_critical_employee_data(self, employee_context) -> Dict[str, Any]:
        """Verificar datos críticos del empleado"""
        critical_fields = ["employee_id", "first_name", "last_name", "email"]
        missing_fields = []
        
        for field in critical_fields:
            if field not in employee_context.raw_data or not employee_context.raw_data[field]:
                missing_fields.append(field)
        
        return {
            "valid": len(missing_fields) == 0,
            "missing_fields": missing_fields,
            "data_completeness": (len(critical_fields) - len(missing_fields)) / len(critical_fields)
        }

    def _restore_critical_data(self, employee_context) -> Optional[Dict[str, Any]]:
        """Restaurar datos críticos desde fuentes disponibles"""
        # En implementación real, esto buscaría datos en backups o fuentes alternativas
        restored_data = {}
        
        # Intentar restaurar desde processed_data si raw_data está corrupto
        if employee_context.processed_data:
            for field in ["employee_id", "first_name", "last_name", "email"]:
                if field in employee_context.processed_data:
                    restored_data[field] = employee_context.processed_data[field]
        
        return restored_data if restored_data else None

    def _determine_appropriate_phase(self, employee_context):
        """Determinar phase apropiado basado en estado de agentes"""
        from core.state_management.models import OnboardingPhase, AgentStateStatus
        
        # Contar agentes en diferentes estados
        completed_agents = 0
        processing_agents = 0
        error_agents = 0
        
        for agent_state in employee_context.agent_states.values():
            if agent_state.status == AgentStateStatus.COMPLETED:
                completed_agents += 1
            elif agent_state.status == AgentStateStatus.PROCESSING:
                processing_agents += 1
            elif agent_state.status == AgentStateStatus.ERROR:
                error_agents += 1
        
        # Determinar phase apropiado
        if error_agents > 0:
            return OnboardingPhase.ERROR_HANDLING
        elif processing_agents > 0:
            return OnboardingPhase.PROCESSING_PIPELINE
        elif completed_agents >= 3:  # Data collection completado
            return OnboardingPhase.PROCESSING_PIPELINE
        else:
            return OnboardingPhase.DATA_COLLECTION

    def _assess_pipeline_health(self, employee_context) -> Dict[str, Any]:
        """Evaluar salud actual del pipeline"""
        from core.state_management.models import AgentStateStatus
        
        agent_statuses = [state.status for state in employee_context.agent_states.values()]
        
        # Contar estados
        error_count = len([s for s in agent_statuses if s == AgentStateStatus.ERROR])
        processing_count = len([s for s in agent_statuses if s == AgentStateStatus.PROCESSING])
        completed_count = len([s for s in agent_statuses if s == AgentStateStatus.COMPLETED])
        
        # Determinar estado de salud
        if error_count > 0:
            status = "blocked"
        elif processing_count > 0 and completed_count > 0:
            status = "inconsistent"  # Algunos completados, otros aún procesando
        elif completed_count >= 3:
            status = "healthy"
        else:
            status = "in_progress"
        
        return {
            "status": status,
            "error_count": error_count,
            "processing_count": processing_count,
            "completed_count": completed_count,
            "total_agents": len(agent_statuses)
        }

    def _unblock_pipeline(self, employee_context, session_id: str) -> Dict[str, Any]:
        """Desbloquear pipeline resolviendo errores críticos"""
        from core.state_management.state_manager import state_manager
        from core.state_management.models import AgentStateStatus
        
        unblocked_agents = []
        
        for agent_id, agent_state in employee_context.agent_states.items():
            if agent_state.status == AgentStateStatus.ERROR:
                # Intentar resetear agente a estado IDLE
                success = state_manager.update_agent_state(
                    agent_id,
                    AgentStateStatus.IDLE,
                    {
                        "reset_at": datetime.utcnow().isoformat(),
                        "reset_reason": "pipeline_unblock",
                        "previous_errors": agent_state.errors
                    },
                    session_id
                )
                
                if success:
                    unblocked_agents.append(agent_id)
        
        return {
            "success": len(unblocked_agents) > 0,
            "unblocked_agents": unblocked_agents,
            "unblock_count": len(unblocked_agents)
        }

    def _synchronize_pipeline_states(self, employee_context, session_id: str) -> Dict[str, Any]:
        """Sincronizar estados inconsistentes del pipeline"""
        # En implementación real, esto sincronizaría estados entre agentes
        return {
            "success": True,
            "synchronized_agents": list(employee_context.agent_states.keys()),
            "synchronization_method": "state_alignment"
        }

    def _verify_pipeline_continuity(self, employee_context) -> Dict[str, Any]:
        """Verificar si el pipeline puede continuar"""
        from core.state_management.models import AgentStateStatus
        
        # Verificar si hay agentes críticos completados
        critical_agents = ["initial_data_collection_agent", "confirmation_data_agent", "documentation_agent"]
        critical_completed = 0
        
        for agent_id in critical_agents:
            if agent_id in employee_context.agent_states:
                if employee_context.agent_states[agent_id].status == AgentStateStatus.COMPLETED:
                    critical_completed += 1
        
        can_continue = critical_completed >= 2  # Al menos 2 de 3 críticos
        
        # Determinar próxima etapa
        if critical_completed >= 3:
            next_stage = "sequential_processing"
        elif critical_completed >= 1:
            next_stage = "data_collection_completion"
        else:
            next_stage = "data_collection_restart"
        
        return {
            "can_continue": can_continue,
            "critical_completed": critical_completed,
            "next_stage": next_stage,
            "continuity_score": critical_completed / len(critical_agents)
        }

    def _establish_safe_continuation_point(self, employee_context) -> str:
        """Establecer punto seguro de continuación"""
        from core.state_management.models import AgentStateStatus
        
        completed_agents = [
            agent_id for agent_id, state in employee_context.agent_states.items()
            if state.status == AgentStateStatus.COMPLETED
        ]
        
        if len(completed_agents) >= 3:
            return "data_aggregation"
        elif len(completed_agents) >= 1:
            return "data_collection_partial"
        else:
            return "data_collection_restart"

    def _check_agent_state_consistency(self, employee_context) -> Dict[str, Any]:
        """Verificar consistencia entre estados de agentes"""
        inconsistencies = []
        
        # Verificar que no haya agentes duplicados en processing
        processing_agents = [
            agent_id for agent_id, state in employee_context.agent_states.items()
            if state.status.value == "processing"
        ]
        
        if len(processing_agents) > 3:  # Máximo 3 agentes processing simultáneamente
            inconsistencies.append("too_many_processing_agents")
        
        # Verificar timestamps consistentes
        for agent_id, state in employee_context.agent_states.items():
            if state.last_updated and state.last_updated > datetime.utcnow():
                inconsistencies.append(f"future_timestamp_{agent_id}")
        
        return {
            "passed": len(inconsistencies) == 0,
            "inconsistencies": inconsistencies,
            "consistency_score": 1.0 if len(inconsistencies) == 0 else 0.5
        }

    def _check_data_integrity(self, employee_context) -> Dict[str, Any]:
        """Verificar integridad de datos del empleado"""
        integrity_issues = []
        
        # Verificar que employee_id sea consistente
        raw_id = employee_context.raw_data.get("employee_id")
        context_id = employee_context.employee_id
        
        if raw_id and raw_id != context_id:
            integrity_issues.append("employee_id_mismatch")
        
        # Verificar que datos críticos existan
        critical_fields = ["employee_id", "first_name", "last_name"]
        for field in critical_fields:
            if not employee_context.raw_data.get(field):
                integrity_issues.append(f"missing_critical_field_{field}")
        
        return {
            "passed": len(integrity_issues) == 0,
            "integrity_issues": integrity_issues,
            "data_completeness": 1.0 if len(integrity_issues) == 0 else 0.8
        }

    def _check_pipeline_synchronization(self, employee_context) -> Dict[str, Any]:
        """Verificar sincronización del pipeline"""
        # Verificar que la phase del empleado coincida con estados de agentes
        from core.state_management.models import OnboardingPhase, AgentStateStatus
        
        current_phase = employee_context.phase
        expected_phase = self._determine_appropriate_phase(employee_context)
        
        return {
            "passed": current_phase == expected_phase,
            "current_phase": current_phase.value if hasattr(current_phase, 'value') else str(current_phase),
            "expected_phase": expected_phase.value if hasattr(expected_phase, 'value') else str(expected_phase),
            "sync_score": 1.0 if current_phase == expected_phase else 0.7
        }

    def _determine_post_restoration_actions(self, restoration_results: List) -> List[str]:
        """Determinar acciones post-restauración"""
        actions = []
        
        # Analizar resultados de restauración
        successful_results = [r for r in restoration_results if r[1].get("success", False)]
        success_rate = len(successful_results) / len(restoration_results) if restoration_results else 0
        
        if success_rate >= 0.8:
            actions.extend([
                "resume_pipeline_execution",
                "monitor_system_stability",
                "validate_data_consistency"
            ])
        elif success_rate >= 0.5:
            actions.extend([
                "partial_pipeline_restart",
                "manual_verification_required",
                "enhanced_monitoring"
            ])
        else:
            actions.extend([
                "escalate_to_human_specialist",
                "full_system_review_required",
                "consider_rollback_to_previous_state"
            ])
        
        return actions

# En la línea 930-940, reemplaza el __init__ de CircuitBreakerTool:

class CircuitBreakerTool(BaseTool):
    """Herramienta para gestionar circuit breakers del sistema"""
    name: str = "circuit_breaker_tool"
    description: str = "Gestiona circuit breakers para prevenir cascading failures"

    def _run(self, recovery_request: Dict[str, Any],
             service_health_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Gestionar circuit breakers del sistema"""
        try:
            session_id = recovery_request.get("session_id")
            recovery_id = recovery_request.get("recovery_id")
            
            # Estados de circuit breakers (usando variables locales en lugar de atributos)
            circuit_states = {}
            failure_counts = {}
            last_failure_times = {}
            
            # Configuración por defecto de circuit breaker
            config = {
                "failure_threshold": 5,
                "recovery_timeout_seconds": 60,
                "half_open_max_calls": 3,
                "success_threshold": 2
            }
            
            circuit_actions = []
            service_states = {}
            
            # Obtener servicios a monitorear
            services_to_check = self._identify_services_to_monitor(recovery_request)
            
            for service_name in services_to_check:
                # Evaluar estado del circuit breaker para este servicio
                circuit_evaluation = self._evaluate_circuit_breaker(
                    service_name, config, service_health_data, circuit_states, 
                    failure_counts, last_failure_times
                )
                
                service_states[service_name] = circuit_evaluation
                
                # Actualizar estados locales
                circuit_states[service_name] = circuit_evaluation["circuit_state"]
                failure_counts[service_name] = circuit_evaluation["failure_count"]
                if circuit_evaluation.get("last_failure"):
                    last_failure_times[service_name] = datetime.fromisoformat(circuit_evaluation["last_failure"])
                
                # Ejecutar acciones basadas en estado del circuit
                if circuit_evaluation["action_required"]:
                    action_result = self._execute_circuit_action(
                        service_name, circuit_evaluation["recommended_action"], session_id
                    )
                    circuit_actions.append(action_result)
            
            # Generar reporte de circuit breakers
            circuit_report = self._generate_circuit_breaker_report(service_states, circuit_actions)
            
            return {
                "success": True,
                "recovery_id": recovery_id,
                "session_id": session_id,
                "circuit_breaker_timestamp": datetime.utcnow().isoformat(),
                "services_monitored": list(service_states.keys()),
                "service_states": service_states,
                "circuit_actions": circuit_actions,
                "circuit_report": circuit_report,
                "system_protection_active": any(
                    state["circuit_state"] != "closed" for state in service_states.values()
                ),
                "recommendations": self._generate_circuit_recommendations(service_states)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error in circuit breaker management: {str(e)}",
                "circuit_actions": [],
                "system_protection_active": False
            }

    def _identify_services_to_monitor(self, recovery_request: Dict[str, Any]) -> List[str]:
        """Identificar servicios que necesitan circuit breaker monitoring"""
        services = [
            "state_management_service",
            "database_service", 
            "external_api_service",
            "notification_service",
            "file_storage_service"
        ]
        
        # Agregar servicios específicos basados en el error
        error_category = recovery_request.get("error_category", "")
        if "integration" in error_category:
            services.append("external_integration_service")
        if "database" in error_category:
            services.append("mongodb_service")
        
        return services

    def _evaluate_circuit_breaker(self, service_name: str, config: Dict[str, Any],
                                 health_data: Optional[Dict[str, Any]],
                                 circuit_states: Dict[str, str],
                                 failure_counts: Dict[str, int],
                                 last_failure_times: Dict[str, datetime]) -> Dict[str, Any]:
        """Evaluar estado de circuit breaker para un servicio"""
        current_time = datetime.utcnow()
        
        # Obtener estado actual del circuit
        current_state = circuit_states.get(service_name, "closed")
        failure_count = failure_counts.get(service_name, 0)
        last_failure = last_failure_times.get(service_name)
        
        # Evaluar salud del servicio
        service_health = self._check_service_health(service_name, health_data)
        
        # Determinar nuevo estado del circuit
        new_state = current_state
        action_required = False
        recommended_action = None
        
        if current_state == "closed":
            # Circuit cerrado - funcionamiento normal
            if not service_health["healthy"]:
                failure_count += 1
                
                if failure_count >= config["failure_threshold"]:
                    new_state = "open"
                    action_required = True
                    recommended_action = "open_circuit"
        
        elif current_state == "open":
            # Circuit abierto - prevenir más llamadas
            if last_failure:
                time_since_failure = (current_time - last_failure).total_seconds()
                if time_since_failure >= config["recovery_timeout_seconds"]:
                    new_state = "half_open"
                    action_required = True
                    recommended_action = "transition_to_half_open"
        
        elif current_state == "half_open":
            # Circuit semi-abierto - probar recuperación
            if service_health["healthy"]:
                # Éxito - resetear y cerrar circuit
                new_state = "closed"
                failure_count = 0
                action_required = True
                recommended_action = "close_circuit"
            else:
                # Fallo - volver a abrir
                new_state = "open"
                failure_count += 1
                action_required = True
                recommended_action = "reopen_circuit"
        
        # Actualizar última vez de fallo si hubo fallo
        if not service_health["healthy"]:
            last_failure_times[service_name] = current_time
        
        return {
            "service_name": service_name,
            "circuit_state": new_state,
            "failure_count": failure_count,
            "service_healthy": service_health["healthy"],
            "service_response_time": service_health.get("response_time_ms", 0),
            "action_required": action_required,
            "recommended_action": recommended_action,
            "last_failure": last_failure.isoformat() if last_failure else None,
            "evaluation_timestamp": current_time.isoformat()
        }

    def _check_service_health(self, service_name: str, 
                             health_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Verificar salud de un servicio específico"""
        if health_data and service_name in health_data:
            return health_data[service_name]
        
        # Simulación de health check
        import random
        
        # Diferentes servicios tienen diferentes probabilidades de salud
        health_probabilities = {
            "state_management_service": 0.95,
            "database_service": 0.90,
            "external_api_service": 0.70,
            "notification_service": 0.85,
            "file_storage_service": 0.88
        }
        
        probability = health_probabilities.get(service_name, 0.80)
        healthy = random.random() < probability
        
        return {
            "healthy": healthy,
            "response_time_ms": random.randint(50, 300) if healthy else random.randint(5000, 10000),
            "status_code": 200 if healthy else random.choice([500, 503, 504]),
            "last_check": datetime.utcnow().isoformat()
        }

    def _execute_circuit_action(self, service_name: str, action: str, 
                               session_id: str) -> Dict[str, Any]:
        """Ejecutar acción de circuit breaker"""
        try:
            action_result = {
                "service_name": service_name,
                "action": action,
                "timestamp": datetime.utcnow().isoformat(),
                "success": False
            }
            
            if action == "open_circuit":
                # Abrir circuit - prevenir llamadas al servicio
                action_result.update({
                    "success": True,
                    "description": f"Circuit opened for {service_name} - preventing further calls",
                    "protection_active": True
                })
            
            elif action == "close_circuit":
                # Cerrar circuit - restaurar funcionamiento normal
                action_result.update({
                    "success": True,
                    "description": f"Circuit closed for {service_name} - normal operation restored",
                    "protection_active": False
                })
            
            elif action == "transition_to_half_open":
                # Transición a semi-abierto - probar recuperación
                action_result.update({
                    "success": True,
                    "description": f"Circuit transitioned to half-open for {service_name} - testing recovery",
                    "protection_active": True,
                    "testing_recovery": True
                })
            
            elif action == "reopen_circuit":
                # Reabrir circuit - el servicio aún no está listo
                action_result.update({
                    "success": True,
                    "description": f"Circuit reopened for {service_name} - service still unhealthy",
                    "protection_active": True
                })
            
            return action_result
            
        except Exception as e:
            return {
                "service_name": service_name,
                "action": action,
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def _generate_circuit_breaker_report(self, service_states: Dict[str, Any],
                                        circuit_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generar reporte de estado de circuit breakers"""
        # Contar estados
        state_counts = {}
        for state_info in service_states.values():
            state = state_info["circuit_state"]
            state_counts[state] = state_counts.get(state, 0) + 1
        
        # Servicios problemáticos
        unhealthy_services = [
            name for name, state in service_states.items()
            if not state["service_healthy"]
        ]
        
        # Acciones ejecutadas
        actions_by_type = {}
        for action in circuit_actions:
            action_type = action["action"]
            actions_by_type[action_type] = actions_by_type.get(action_type, 0) + 1
        
        return {
            "total_services_monitored": len(service_states),
            "circuit_state_distribution": state_counts,
            "unhealthy_services": unhealthy_services,
            "unhealthy_service_count": len(unhealthy_services),
            "actions_executed": len(circuit_actions),
            "actions_by_type": actions_by_type,
            "system_protection_level": self._calculate_protection_level(state_counts),
            "overall_system_health": 1.0 - (len(unhealthy_services) / len(service_states)) if service_states else 1.0
        }

    def _calculate_protection_level(self, state_counts: Dict[str, int]) -> str:
        """Calcular nivel de protección del sistema"""
        open_circuits = state_counts.get("open", 0)
        half_open_circuits = state_counts.get("half_open", 0)
        total_circuits = sum(state_counts.values())
        
        if total_circuits == 0:
            return "none"
        
        protection_ratio = (open_circuits + half_open_circuits) / total_circuits
        
        if protection_ratio >= 0.7:
            return "high"
        elif protection_ratio >= 0.4:
            return "medium"
        elif protection_ratio > 0:
            return "low"
        else:
            return "none"

    def _generate_circuit_recommendations(self, service_states: Dict[str, Any]) -> List[str]:
        """Generar recomendaciones basadas en estado de circuits"""
        recommendations = []
        
        # Contar servicios por estado
        open_count = len([s for s in service_states.values() if s["circuit_state"] == "open"])
        unhealthy_count = len([s for s in service_states.values() if not s["service_healthy"]])
        
        if open_count > 0:
            recommendations.append(f"{open_count} circuit breaker(s) open - investigate service health")
        
        if unhealthy_count > len(service_states) * 0.5:
            recommendations.append("High number of unhealthy services - check system-wide issues")
        
        # Recomendaciones específicas por servicio
        for service_name, state in service_states.items():
            if state["circuit_state"] == "open" and state["failure_count"] > 10:
                recommendations.append(f"Service {service_name} has excessive failures - requires manual intervention")
        
        if not recommendations:
            recommendations.append("Circuit breaker system operating normally")
        
        return recommendations

class WorkflowResumerTool(BaseTool):
    """Herramienta para reanudar workflows interrumpidos"""
    name: str = "workflow_resumer_tool"
    description: str = "Reanuda workflows del pipeline desde puntos de control seguros"

    def _run(self, recovery_request: Dict[str, Any],
             checkpoint_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Reanudar workflow desde punto de control"""
        try:
            from core.state_management.state_manager import state_manager
            
            session_id = recovery_request.get("session_id")
            recovery_id = recovery_request.get("recovery_id")
            
            # Identificar punto de reanudación apropiado
            resume_point = self._identify_resume_point(session_id, checkpoint_data)
            
            # Preparar datos para reanudación
            resume_data = self._prepare_resume_data(session_id, resume_point)
            
            # Ejecutar reanudación del workflow
            resume_result = self._execute_workflow_resume(session_id, resume_point, resume_data)
            
            return {
                "success": resume_result.get("success", False),
                "recovery_id": recovery_id,
                "session_id": session_id,
                "resume_timestamp": datetime.utcnow().isoformat(),
                "resume_point": resume_point,
                "resume_result": resume_result,
                "workflow_status": resume_result.get("workflow_status", "unknown"),
                "next_steps": resume_result.get("next_steps", []),
                "estimated_completion_time": resume_result.get("estimated_completion_time")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error resuming workflow: {str(e)}",
                "resume_point": "unknown",
                "workflow_status": "failed"
            }

    def _identify_resume_point(self, session_id: str, 
                              checkpoint_data: Optional[Dict[str, Any]]) -> str:
        """Identificar punto apropiado para reanudar workflow"""
        try:
            from core.state_management.state_manager import state_manager
            from core.state_management.models import AgentStateStatus
            
            employee_context = state_manager.get_employee_context(session_id)
            if not employee_context:
                return "restart_from_beginning"
            
            # Evaluar estado de agentes críticos
            critical_agents = {
                "initial_data_collection_agent": False,
                "confirmation_data_agent": False,
                "documentation_agent": False
            }
            
            for agent_id in critical_agents:
                if agent_id in employee_context.agent_states:
                    agent_state = employee_context.agent_states[agent_id]
                    if agent_state.status == AgentStateStatus.COMPLETED:
                        critical_agents[agent_id] = True
            
            # Determinar punto de reanudación
            completed_count = sum(critical_agents.values())
            
            if            completed_count >= 3:
                return "data_aggregation_checkpoint"
            elif completed_count >= 2:
                return "partial_data_collection_resume"
            elif completed_count >= 1:
                return "continue_data_collection"
            else:
                return "restart_data_collection"
            
        except Exception as e:
            return "safe_restart_point"

    def _prepare_resume_data(self, session_id: str, resume_point: str) -> Dict[str, Any]:
        """Preparar datos necesarios para reanudación"""
        try:
            from core.state_management.state_manager import state_manager
            
            employee_context = state_manager.get_employee_context(session_id)
            if not employee_context:
                return {}
            
            resume_data = {
                "session_id": session_id,
                "employee_id": employee_context.employee_id,
                "resume_point": resume_point,
                "employee_data": employee_context.raw_data,
                "processed_data": employee_context.processed_data,
                "current_phase": employee_context.phase.value if hasattr(employee_context.phase, 'value') else str(employee_context.phase)
            }
            
            # Agregar datos específicos según punto de reanudación
            if resume_point == "data_aggregation_checkpoint":
                # Recopilar resultados de agentes completados
                agent_results = {}
                for agent_id, agent_state in employee_context.agent_states.items():
                    if agent_state.status.value == "completed" and agent_state.data:
                        agent_results[agent_id] = agent_state.data
                
                resume_data["completed_agent_results"] = agent_results
                
            elif resume_point == "partial_data_collection_resume":
                # Identificar qué agentes necesitan completarse
                incomplete_agents = []
                for agent_id in ["initial_data_collection_agent", "confirmation_data_agent", "documentation_agent"]:
                    if agent_id not in employee_context.agent_states or employee_context.agent_states[agent_id].status.value != "completed":
                        incomplete_agents.append(agent_id)
                
                resume_data["incomplete_agents"] = incomplete_agents
            
            return resume_data
            
        except Exception as e:
            return {"error": str(e)}

    def _execute_workflow_resume(self, session_id: str, resume_point: str, 
                                resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar reanudación del workflow"""
        try:
            workflow_actions = []
            
            if resume_point == "data_aggregation_checkpoint":
                # Proceder directamente a agregación de datos
                result = self._resume_at_data_aggregation(session_id, resume_data)
                workflow_actions.append(("data_aggregation_initiated", result))
                
            elif resume_point == "partial_data_collection_resume":
                # Completar agentes faltantes
                result = self._resume_partial_data_collection(session_id, resume_data)
                workflow_actions.append(("partial_collection_resumed", result))
                
            elif resume_point == "continue_data_collection":
                # Continuar desde donde se quedó
                result = self._continue_data_collection(session_id, resume_data)
                workflow_actions.append(("data_collection_continued", result))
                
            elif resume_point == "restart_data_collection":
                # Reiniciar completamente data collection
                result = self._restart_data_collection(session_id, resume_data)
                workflow_actions.append(("data_collection_restarted", result))
                
            else:
                # Punto de reanudación no reconocido
                return {
                    "success": False,
                    "error": f"Unknown resume point: {resume_point}",
                    "workflow_status": "failed"
                }
            
            # Evaluar éxito general
            successful_actions = len([a for a in workflow_actions if a[1].get("success", False)])
            overall_success = successful_actions > 0
            
            return {
                "success": overall_success,
                "workflow_actions": workflow_actions,
                "workflow_status": "resumed" if overall_success else "failed",
                "next_steps": self._determine_next_workflow_steps(resume_point, workflow_actions),
                "estimated_completion_time": self._estimate_workflow_completion(resume_point)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Workflow resume execution failed: {str(e)}",
                "workflow_status": "failed"
            }

    def _resume_at_data_aggregation(self, session_id: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Reanudar en punto de agregación de datos"""
        try:
            # Simular inicio del Data Aggregator Agent
            from core.state_management.state_manager import state_manager
            from core.state_management.models import AgentStateStatus
            
            # Actualizar estado para proceder a data aggregation
            success = state_manager.update_agent_state(
                "data_aggregator_agent",
                AgentStateStatus.PROCESSING,
                {
                    "resumed_at": datetime.utcnow().isoformat(),
                    "resume_reason": "recovery_workflow_resume",
                    "available_data_sources": list(resume_data.get("completed_agent_results", {}).keys())
                },
                session_id
            )
            
            return {
                "success": success,
                "action": "data_aggregation_initiated",
                "ready_for_sequential_pipeline": True,
                "available_data_sources": len(resume_data.get("completed_agent_results", {}))
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _resume_partial_data_collection(self, session_id: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Reanudar data collection parcial"""
        try:
            from core.state_management.state_manager import state_manager
            from core.state_management.models import AgentStateStatus
            
            incomplete_agents = resume_data.get("incomplete_agents", [])
            resumed_agents = []
            
            for agent_id in incomplete_agents:
                # Resetear agente para reintento
                success = state_manager.update_agent_state(
                    agent_id,
                    AgentStateStatus.IDLE,
                    {
                        "reset_for_resume": True,
                        "resume_timestamp": datetime.utcnow().isoformat()
                    },
                    session_id
                )
                
                if success:
                    resumed_agents.append(agent_id)
            
            return {
                "success": len(resumed_agents) > 0,
                "resumed_agents": resumed_agents,
                "incomplete_agents_count": len(incomplete_agents),
                "ready_for_retry": True
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _continue_data_collection(self, session_id: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Continuar data collection desde estado actual"""
        try:
            # Verificar qué agentes pueden continuar
            from core.state_management.state_manager import state_manager
            
            employee_context = state_manager.get_employee_context(session_id)
            if not employee_context:
                return {"success": False, "error": "Employee context not found"}
            
            continuable_agents = []
            for agent_id, agent_state in employee_context.agent_states.items():
                if agent_state.status.value in ["idle", "waiting"]:
                    continuable_agents.append(agent_id)
            
            return {
                "success": len(continuable_agents) > 0,
                "continuable_agents": continuable_agents,
                "can_proceed": True
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _restart_data_collection(self, session_id: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Reiniciar data collection completamente"""
        try:
            from core.state_management.state_manager import state_manager
            from core.state_management.models import AgentStateStatus
            
            # Resetear todos los agentes de data collection
            data_collection_agents = [
                "initial_data_collection_agent",
                "confirmation_data_agent", 
                "documentation_agent"
            ]
            
            reset_agents = []
            for agent_id in data_collection_agents:
                success = state_manager.update_agent_state(
                    agent_id,
                    AgentStateStatus.IDLE,
                    {
                        "full_restart": True,
                        "restart_timestamp": datetime.utcnow().isoformat(),
                        "restart_reason": "recovery_full_restart"
                    },
                    session_id
                )
                
                if success:
                    reset_agents.append(agent_id)
            
            return {
                "success": len(reset_agents) == len(data_collection_agents),
                "reset_agents": reset_agents,
                "ready_for_fresh_start": True
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _determine_next_workflow_steps(self, resume_point: str, 
                                     workflow_actions: List) -> List[str]:
        """Determinar próximos pasos del workflow"""
        next_steps = []
        
        if resume_point == "data_aggregation_checkpoint":
            next_steps.extend([
                "Execute Data Aggregator Agent",
                "Validate consolidated data quality",
                "Proceed to Sequential Processing Pipeline"
            ])
        elif resume_point == "partial_data_collection_resume":
            next_steps.extend([
                "Complete remaining data collection agents",
                "Validate all collected data",
                "Proceed to data aggregation"
            ])
        elif resume_point == "continue_data_collection":
            next_steps.extend([
                "Resume pending data collection tasks",
                "Monitor agent completion",
                "Prepare for data aggregation"
            ])
        elif resume_point == "restart_data_collection":
            next_steps.extend([
                "Re-initiate all data collection agents",
                "Monitor fresh data collection process",
                "Ensure data quality standards"
            ])
        
        return next_steps

    def _estimate_workflow_completion(self, resume_point: str) -> str:
        """Estimar tiempo de completación del workflow"""
        completion_estimates = {
            "data_aggregation_checkpoint": "5-10 minutes",
            "partial_data_collection_resume": "10-20 minutes", 
            "continue_data_collection": "15-25 minutes",
            "restart_data_collection": "20-30 minutes"
        }
        
        return completion_estimates.get(resume_point, "20-30 minutes")

# Export tools
retry_manager_tool = RetryManagerTool()
state_restorer_tool = StateRestorerTool()
circuit_breaker_tool = CircuitBreakerTool()
workflow_resumer_tool = WorkflowResumerTool()
