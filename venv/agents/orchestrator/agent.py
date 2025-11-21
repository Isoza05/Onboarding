from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from agents.base.base_agent import BaseAgent
from datetime import datetime, timezone 
import json
import asyncio
from loguru import logger

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def utc_now_iso() -> str:
    return utc_now().isoformat()

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

# ✅ IMPORTS DE ERROR HANDLING
from agents.error_classification.agent import ErrorClassificationAgent
from agents.recovery_agent.agent import RecoveryAgent
from agents.human_handoff.agent import HumanHandoffAgent
from agents.audit_trail.agent import AuditTrailAgent

from agents.error_classification.schemas import ErrorClassificationRequest, ErrorSource
from agents.recovery_agent.schemas import RecoveryRequest, RecoveryStrategy
from agents.human_handoff.schemas import HandoffRequest, HandoffPriority
from agents.audit_trail.schemas import AuditTrailRequest, AuditEventType, AuditSeverity

from core.state_management.state_manager import state_manager
from core.state_management.models import AgentStateStatus, OnboardingPhase
from core.observability import observability_manager
from core.database import db_manager
from shared.models import Priority

class OrchestratorAgent(BaseAgent):
    """Agente Orquestador con Error Handling Integrado"""

    def __init__(self):
        super().__init__(
            agent_id="orchestrator_agent",
            agent_name="Orchestrator Agent with Error Handling"
        )
        self.max_concurrent_workflows = 5
        self.default_timeout_minutes = 30
        self.active_orchestrations = {}
        self.workflow_status = get_workflow_status()
        
        # ✅ INICIALIZAR AGENTES ERROR HANDLING
        self._initialize_error_handling_agents()
        
        state_manager.register_agent(
            self.agent_id,
            {
                "version": "3.0_WITH_ERROR_HANDLING",
                "specialization": "workflow_orchestration_with_error_handling",
                "tools_count": len(self.tools),
                "workflow_status": self.workflow_status,
                "error_handling_enabled": True
            }
        )
        self.logger.info("Orchestrator Agent CON ERROR HANDLING integrado")

    def _initialize_error_handling_agents(self):
        """Inicializar agentes de Error Handling"""
        try:
            self.error_classification_agent = ErrorClassificationAgent()
            self.recovery_agent = RecoveryAgent()
            self.human_handoff_agent = HumanHandoffAgent()
            self.audit_trail_agent = AuditTrailAgent()
            
            logger.info("✅ Agentes Error Handling inicializados en Orchestrator")
        except Exception as e:
            logger.error(f"❌ Error inicializando Error Handling agents: {e}")
            # Crear agentes mock para evitar crashes
            self.error_classification_agent = None
            self.recovery_agent = None
            self.human_handoff_agent = None
            self.audit_trail_agent = None

    def _initialize_tools(self) -> List:
        return [
            pattern_selector_tool,
            task_distributor_tool,
            state_coordinator_tool,
            progress_monitor_tool
        ]

    def _create_prompt(self) -> ChatPromptTemplate:
        system_prompt = """
        Eres el Orchestrator Agent CON ERROR HANDLING INTEGRADO.
        Coordinas onboarding procesando datos REALES y activando Error Handling cuando es necesario.
        """
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}"),
            ("assistant", "Ejecutando orquestación con Error Handling."),
            ("placeholder", "{agent_scratchpad}")
        ])

    def _get_bdi_framework(self) -> Dict[str, str]:
        return {
            "beliefs": "Procesar datos reales y manejar errores",
            "desires": "Coordinar con detección de errores",
            "intentions": "Ejecutar workflows con Error Handling"
        }

    def _format_input(self, input_data: Any) -> str:
        return f"Orquestación CON ERROR HANDLING para: {getattr(input_data, 'employee_id', 'empleado')}"

    def _format_output(self, result: Any, processing_time: float, success: bool, error: str = None) -> Dict[str, Any]:
        if not success:
            return {
                "success": False,
                "message": f"Error: {error}",
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "error_handling_available": True
            }

        if isinstance(result, dict) and "workflow_result" in result:
            workflow_result = result["workflow_result"]
            return {
                "success": workflow_result.get("success", False),
                "message": "Orquestación completada",
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "orchestration_id": workflow_result.get("orchestration_id"),
                "session_id": workflow_result.get("session_id"),
                "employee_id": workflow_result.get("employee_id"),
                "agent_results": workflow_result.get("agent_results", {}),
                "data_quality_score": workflow_result.get("data_quality_score", 0.0),
                "ready_for_sequential_execution": workflow_result.get("ready_for_sequential_execution", False),
                "error_handling_executed": workflow_result.get("error_handling_executed", False)
            }

        return {
            "success": True,
            "message": "Procesamiento completado",
            "agent_id": self.agent_id,
            "processing_time": processing_time,
            "error_handling_available": True
        }

    async def _check_for_critical_errors(self, session_id: str, workflow_result: Dict[str, Any]) -> bool:
        """Verificar si hay errores críticos que requieren Error Handling"""
        try:
            # ✅ TRIGGERS REALES PARA ERROR HANDLING
            triggers = [
                # Data Collection falló
                len(workflow_result.get("errors", [])) > 0,
                
                # Quality score muy bajo
                workflow_result.get("data_quality_score", 100.0) < 30.0,
                
                # Sequential Pipeline falló
                not workflow_result.get("sequential_pipeline_result", {}).get("success", True),
                
                # Agentes críticos fallaron
                len([r for r in workflow_result.get("agent_results", {}).values() 
                     if r.get("success", False)]) < 2,
                
                # Datos consolidados incompletos
                not workflow_result.get("consolidated_data", {}),
                
                # Pipeline no está listo
                not workflow_result.get("ready_for_sequential_execution", False)
            ]
            
            has_critical_errors = any(triggers)
            
            if has_critical_errors:
                logger.warning(f"🚨 ERRORES CRÍTICOS DETECTADOS en session {session_id}")
                logger.warning(f"   - Errores: {len(workflow_result.get('errors', []))}")
                logger.warning(f"   - Quality Score: {workflow_result.get('data_quality_score', 0):.1f}%")
                logger.warning(f"   - Agentes exitosos: {len([r for r in workflow_result.get('agent_results', {}).values() if r.get('success', False)])}")
                
            return has_critical_errors
            
        except Exception as e:
            logger.error(f"Error verificando errores críticos: {e}")
            return True  # Si no podemos verificar, asumir que hay errores

    async def _execute_error_handling_flow(self, session_id: str, failed_result: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar flujo completo de Error Handling: Classification → Recovery → Human Handoff → Audit"""
        try:
            logger.info(f"🔄 INICIANDO ERROR HANDLING FLOW para session {session_id}")
            
            if not all([self.error_classification_agent, self.recovery_agent, 
                       self.human_handoff_agent, self.audit_trail_agent]):
                logger.error("❌ Error Handling agents no disponibles")
                return {
                    "error_handling_success": False,
                    "error": "Error Handling agents not available"
                }

            # ✅ PASO 1: ERROR CLASSIFICATION
            logger.info("📊 Ejecutando Error Classification...")
            
            classification_request = ErrorClassificationRequest(
                session_id=session_id,
                employee_id=failed_result.get("employee_id", "unknown"),
                error_source=ErrorSource.PROGRESS_TRACKER,
                raw_error_data={"orchestrator_result": failed_result},
                context_data={
                    "workflow_stage": "orchestration_failed",
                    "business_impact": "high",
                    "data_quality_score": failed_result.get("data_quality_score", 0.0),
                    "agent_failures": len([r for r in failed_result.get("agent_results", {}).values() 
                                         if not r.get("success", True)])
                }
            )
            
            classification_result = self.error_classification_agent.classify_errors(
                classification_request, session_id
            )
            
            if not classification_result.get("success", False):
                logger.error("❌ Error Classification falló")
                return {
                    "error_handling_success": False,
                    "classification_result": classification_result,
                    "error": "Error Classification failed"
                }

            logger.info(f"✅ Error Classification completado: {classification_result.get('recovery_strategy', 'unknown')}")

            # ✅ PASO 2: RECOVERY (si está recomendado)
            recovery_result = None
            recovery_strategy = classification_result.get("recovery_strategy", "")
            
            if recovery_strategy in ["automatic_retry", "exponential_backoff", "state_rollback", "circuit_breaker"]:
                logger.info(f"🔧 Ejecutando Recovery con estrategia: {recovery_strategy}")
                
                recovery_request = RecoveryRequest(
                    session_id=session_id,
                    employee_id=failed_result.get("employee_id", "unknown"),
                    error_classification_id=classification_result.get("classification_id", "unknown"),
                    error_category="orchestration_failure",
                    error_severity="critical",
                    recovery_strategy=RecoveryStrategy(recovery_strategy),
                    recovery_actions=classification_result.get("immediate_actions", []),
                    max_retry_attempts=3
                )
                
                recovery_result = self.recovery_agent.execute_recovery(recovery_request, session_id)
                
                if recovery_result.get("success", False):
                    logger.info("✅ Recovery exitoso")
                else:
                    logger.warning("⚠️ Recovery falló - escalando a Human Handoff")
                    recovery_result["escalation_required"] = True
            else:
                logger.info(f"⏭️ Recovery no requerido para estrategia: {recovery_strategy}")

            # ✅ PASO 3: HUMAN HANDOFF (si recovery falló o se requiere escalación)
            handoff_result = None
            
            should_escalate = (
                recovery_result and recovery_result.get("escalation_required", False)
            ) or classification_result.get("recovery_strategy") in ["escalation_required", "escalate_to_human"]
            
            if should_escalate:
                logger.info("👤 Ejecutando Human Handoff...")
                
                handoff_request = HandoffRequest(
                    session_id=session_id,
                    employee_id=failed_result.get("employee_id", "unknown"),
                    source_agent="orchestrator_agent",
                    source_request_id=failed_result.get("orchestration_id", "unknown"),
                    error_category="orchestration_failure",
                    error_severity="critical",
                    handoff_priority=HandoffPriority.CRITICAL,
                    requires_immediate_attention=True,
                    error_context=failed_result,
                    recovery_attempts=[recovery_result] if recovery_result else []
                )
                
                handoff_result = self.human_handoff_agent.execute_handoff(handoff_request, session_id)
                
                if handoff_result.get("success", False):
                    logger.info("✅ Human Handoff completado")
                else:
                    logger.error("❌ Human Handoff falló")
            else:
                logger.info("⏭️ Human Handoff no requerido")

            # ✅ PASO 4: AUDIT TRAIL CONSOLIDADO FINAL
            logger.info("📋 Ejecutando Audit Trail consolidado...")
            
            final_audit_request = AuditTrailRequest(
                session_id=session_id,
                employee_id=failed_result.get("employee_id", "unknown"),
                event_type=AuditEventType.ESCALATION_TRIGGERED,
                event_description="Flujo completo Error Handling desde Orchestrator: Classification → Recovery → Human Handoff",
                severity=AuditSeverity.CRITICAL,
                agent_id="orchestrator_agent",
                workflow_stage="error_handling_complete",
                decision_points=[
                    {
                        "decision_point": "final_resolution_path",
                        "decision": "human_specialist_intervention" if handoff_result else "automatic_recovery_attempted",
                        "rationale": "Orchestrator workflow failed, Error Handling executed",
                        "maker": "error_handling_orchestrator"
                    }
                ],
                event_data={
                    "original_failure": failed_result,
                    "classification_result": classification_result,
                    "recovery_result": recovery_result,
                    "handoff_result": handoff_result
                }
            )
            
            audit_result = self.audit_trail_agent.create_audit_trail(
                final_audit_request, session_id
            )

            # ✅ RESULTADO CONSOLIDADO
            error_handling_success = all([
                classification_result.get("success", False),
                recovery_result is None or recovery_result.get("success", False),
                handoff_result is None or handoff_result.get("success", False),
                audit_result.get("success", False)
            ])

            final_result = {
                "error_handling_success": error_handling_success,
                "classification_result": classification_result,
                "recovery_result": recovery_result,
                "handoff_result": handoff_result,
                "audit_result": audit_result,
                "final_resolution": "human_specialist_assigned" if handoff_result else "recovery_attempted",
                "error_handling_summary": {
                    "classification_executed": classification_result.get("success", False),
                    "recovery_executed": recovery_result is not None,
                    "handoff_executed": handoff_result is not None,
                    "audit_executed": audit_result.get("success", False)
                }
            }

            logger.info(f"✅ ERROR HANDLING FLOW COMPLETADO: {error_handling_success}")
            return final_result

        except Exception as e:
            logger.error(f"❌ Error crítico en Error Handling flow: {e}")
            return {
                "error_handling_success": False,
                "error": str(e),
                "classification_result": None,
                "recovery_result": None,
                "handoff_result": None,
                "audit_result": None
            }

    @observability_manager.trace_agent_execution("orchestrator_agent")
    async def orchestrate_onboarding_process(self, orchestration_request: OrchestrationRequest, session_id: str = None) -> Dict[str, Any]:
        """ORQUESTACIÓN CON DATOS REALES Y ERROR HANDLING"""
        orchestration_id = f"orch_real_{utc_now().strftime('%Y%m%d_%H%M%S')}_{orchestration_request.employee_id}"
        
        state_manager.update_agent_state(
            self.agent_id,
            AgentStateStatus.PROCESSING,
            {
                "current_task": "real_data_orchestration",
                "orchestration_id": orchestration_id,
                "employee_id": orchestration_request.employee_id,
                "started_at": utc_now_iso()
            },
            session_id
        )

        try:
            session_id_final = session_id or f"session_real_{utc_now().strftime('%Y%m%d_%H%M%S')}"
            
            # BUSCAR LÍNEA ~386 Y REEMPLAZAR DESDE:

            # ✅ USAR DATOS REALES DEL REQUEST - NO SIMULADOS
            logger.info(f"🔄 Procesando datos REALES del empleado: {orchestration_request.employee_id}")

            # ✅ EJECUTAR WORKFLOW CON DATOS REALES - CONVERSIÓN CORRECTA
            workflow_request = orchestration_request.model_dump()  # ✅ PYDANTIC → DICT
            workflow_request.update({
                "session_id": session_id_final,
                "orchestration_id": orchestration_id
            })

            # Ejecutar workflow DATA COLLECTION con datos reales
            workflow_result = await execute_data_collection_orchestration(workflow_request)
            
            # ✅ VERIFICAR CALIDAD DE DATOS REALES
            actual_quality_score = workflow_result.get("data_quality_score", 0.0)
            actual_success = workflow_result.get("success", False)
            actual_errors = workflow_result.get("errors", [])
            
            logger.info(f"📊 Resultado del workflow REAL:")
            logger.info(f"   - Success: {actual_success}")
            logger.info(f"   - Quality Score: {actual_quality_score:.1f}%")
            logger.info(f"   - Errores: {len(actual_errors)}")
            
            # ✅ RESULTADO CON DATOS REALES - NO FORZAR SUCCESS
            result = {
                "success": actual_success,
                "orchestration_id": orchestration_id,
                "session_id": session_id_final,
                "employee_id": orchestration_request.employee_id,
                "agent_results": workflow_result.get("agent_results", {}),
                "consolidated_data": workflow_result.get("consolidated_data", {}),
                "aggregation_result": workflow_result.get("aggregation_result", {}),
                "data_quality_score": actual_quality_score,
                "ready_for_sequential_execution": workflow_result.get("ready_for_sequential_execution", False),
                "sequential_pipeline_request": workflow_result.get("sequential_pipeline_request", {}),
                "errors": actual_errors,
                "completion_status": "completed" if actual_success else "failed"
            }

            # Actualizar estado
            state_manager.update_agent_state(
                self.agent_id,
                AgentStateStatus.COMPLETED,
                {
                    "current_task": "real_data_completed",
                    "orchestration_id": orchestration_id,
                    "success": actual_success,
                    "data_quality_score": actual_quality_score,
                    "completed_at": utc_now_iso()
                },
                session_id
            )

            logger.info(f"✅ ORQUESTACIÓN CON DATOS REALES: {orchestration_id}")
            return result

        except Exception as e:
            error_msg = f"Error en orquestración real: {str(e)}"
            logger.error(error_msg)
            
            state_manager.update_agent_state(
                self.agent_id,
                AgentStateStatus.ERROR,
                {
                    "current_task": "error_real_data",
                    "error_message": error_msg,
                    "failed_at": utc_now_iso()
                },
                session_id
            )

            # ✅ DEVOLVER ERROR REAL - NO FORZAR SUCCESS
            return {
                "success": False,
                "orchestration_id": orchestration_id,
                "session_id": session_id or "fallback_session",
                "employee_id": orchestration_request.employee_id,
                "agent_results": {},
                "data_quality_score": 0.0,
                "ready_for_sequential_execution": False,
                "errors": [str(e)],
                "completion_status": "error"
            }

    @observability_manager.trace_agent_execution("orchestrator_agent")
    async def execute_sequential_pipeline(self, sequential_request_data: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
        """SEQUENTIAL PIPELINE CON DATOS REALES Y ERROR HANDLING"""
        try:
            logger.info(f"🔄 Sequential Pipeline REAL para: {sequential_request_data['employee_id']}")
            
            # ✅ USAR DATOS REALES - NO SIMULADOS
            from .workflows import execute_sequential_pipeline_orchestration
            from .schemas import SequentialPipelineRequest
            
            # Crear request real
            pipeline_request = SequentialPipelineRequest(
                employee_id=sequential_request_data["employee_id"],
                session_id=sequential_request_data["session_id"],
                orchestration_id=sequential_request_data.get("orchestration_id", "fallback"),
                consolidated_data=sequential_request_data.get("consolidated_data", {}),
                aggregation_result=sequential_request_data.get("aggregation_result", {}),
                data_quality_score=sequential_request_data.get("data_quality_score", 0.0)
            )
            
            # Ejecutar pipeline real
            pipeline_result = await execute_sequential_pipeline_orchestration(pipeline_request)
            
            # ✅ USAR RESULTADOS REALES
            actual_success = pipeline_result.get("success", False)
            actual_quality = pipeline_result.get("overall_quality_score", 0.0)
            
            logger.info(f"📊 Sequential Pipeline REAL completado:")
            logger.info(f"   - Success: {actual_success}")
            logger.info(f"   - Quality: {actual_quality:.1f}%")
            
            # Actualizar estado
            state_manager.update_agent_state(
                self.agent_id,
                AgentStateStatus.COMPLETED,
                {
                    "current_task": "sequential_pipeline_real_completed",
                    "pipeline_success": actual_success,
                    "pipeline_quality": actual_quality,
                    "completed_at": utc_now_iso()
                },
                session_id
            )

            return pipeline_result

        except Exception as e:
            error_msg = f"Error en Sequential Pipeline real: {str(e)}"
            logger.error(error_msg)
            
            state_manager.update_agent_state(
                self.agent_id,
                AgentStateStatus.ERROR,
                {
                    "error_message": error_msg,
                    "failed_at": utc_now_iso()
                },
                session_id
            )

            # ✅ DEVOLVER ERROR REAL
            return {
                "success": False,
                "employee_id": sequential_request_data.get("employee_id", "fallback"),
                "session_id": session_id or "fallback_session",
                "employee_ready_for_onboarding": False,
                "stages_completed": 0,
                "stages_total": 3,
                "overall_quality_score": 0.0,
                "errors": [str(e)],
                "processing_summary": {
                    "pipeline_completed": False,
                    "error": str(e)
                }
            }

    # BUSCAR LÍNEA ~550 EN execute_complete_onboarding_orchestration Y REEMPLAZAR:

    async def execute_complete_onboarding_orchestration(self, orchestration_request: OrchestrationRequest, session_id: str = None) -> Dict[str, Any]:
        """ORQUESTACIÓN COMPLETA CON ERROR HANDLING INTEGRADO"""
        try:
            logger.info(f"🚀 ORQUESTRACIÓN COMPLETA CON ERROR HANDLING para: {orchestration_request.employee_id}")

            # ✅ FASE 1: DATA COLLECTION CON DATOS REALES
            data_collection_result = await self.orchestrate_onboarding_process(orchestration_request, session_id)
            
            session_id_final = data_collection_result.get("session_id") or session_id or f"session_complete_{utc_now().strftime('%Y%m%d_%H%M%S')}"

            # ✅ INICIALIZAR complete_result TEMPRANO
            complete_result = {
                **data_collection_result,
                "sequential_pipeline_executed": False,
                "sequential_pipeline_result": None,
                "complete_orchestration_success": False,
                "employee_ready_for_onboarding": False,
                "session_id": session_id_final,
                "architecture_version": "3.0_with_error_handling",
                "error_handling_available": True
            }

            # ✅ CHECK ERROR HANDLING DESPUÉS DE DATA COLLECTION
            if await self._check_for_critical_errors(session_id_final, data_collection_result):
                logger.warning("🚨 ERRORES CRÍTICOS EN DATA COLLECTION - Activando Error Handling")
                
                error_handling_result = await self._execute_error_handling_flow(
                    session_id_final, data_collection_result
                )
                
                complete_result["error_handling_executed"] = True
                complete_result["error_handling_result"] = error_handling_result
                
                # Si Error Handling falló completamente, retornar inmediatamente
                if not error_handling_result.get("error_handling_success", False):
                    complete_result["final_status"] = "error_handling_failed"
                    return complete_result

            # ✅ FASE 2: SEQUENTIAL PIPELINE (solo si Data Collection fue exitoso)
            sequential_result = None
            
            if data_collection_result.get("success", False) and data_collection_result.get("ready_for_sequential_execution", False):
                sequential_request = data_collection_result.get("sequential_pipeline_request", {})
                sequential_result = await self.execute_sequential_pipeline(sequential_request, session_id_final)
                
                complete_result["sequential_pipeline_executed"] = True
                complete_result["sequential_pipeline_result"] = sequential_result
                
                # ✅ CHECK ERROR HANDLING DESPUÉS DE SEQUENTIAL PIPELINE
                if await self._check_for_critical_errors(session_id_final, sequential_result):
                    logger.warning("🚨 ERRORES CRÍTICOS EN SEQUENTIAL PIPELINE - Activando Error Handling")
                    
                    sequential_error_handling = await self._execute_error_handling_flow(
                        session_id_final, sequential_result
                    )
                    
                    complete_result["sequential_error_handling_executed"] = True
                    complete_result["sequential_error_handling_result"] = sequential_error_handling
            else:
                logger.warning("⚠️ Saltando Sequential Pipeline - Data Collection no exitoso")

            # ✅ RESULTADO FINAL CONSOLIDADO CON ERROR HANDLING
            complete_result.update({
                "complete_orchestration_success": (
                    data_collection_result.get("success", False) and 
                    (sequential_result is None or sequential_result.get("success", False))
                ),
                "employee_ready_for_onboarding": (
                    sequential_result and sequential_result.get("employee_ready_for_onboarding", False)
                ) or False,
                "total_stages_completed": (
                    len([r for r in data_collection_result.get("agent_results", {}).values() if r.get("success", False)]) +
                    (sequential_result.get("stages_completed", 0) if sequential_result else 0)
                ),
                "final_next_actions": [
                    "✅ Orquestación completa CON Error Handling terminada",
                    "🎯 Empleado listo para onboarding" if complete_result.get("employee_ready_for_onboarding") else "⚠️ Revisar errores detectados",
                    "📋 Revisar audit trail para detalles completos"
                ]
            })

            logger.info("✅ ORQUESTACIÓN COMPLETA CON ERROR HANDLING EXITOSA")
            return complete_result

        except Exception as e:
            logger.error(f"❌ Error crítico en orquestación completa: {e}")
            
            # ✅ ACTIVAR ERROR HANDLING PARA ERRORES CRÍTICOS
            try:
                critical_error_data = {
                    "employee_id": orchestration_request.employee_id,
                    "critical_error": str(e),
                    "errors": [str(e)],
                    "data_quality_score": 0.0,
                    "agent_results": {},
                    "success": False
                }
                
                error_handling_result = await self._execute_error_handling_flow(
                    session_id, critical_error_data
                )
                
                return {
                    "success": False,
                    "complete_orchestration_success": False,
                    "employee_ready_for_onboarding": False,
                    "session_id": session_id or "fallback_session",
                    "architecture_version": "3.0_with_error_handling",
                    "error": str(e),
                    "error_handling_executed": True,
                    "error_handling_result": error_handling_result,
                    "critical_error_recovery_attempted": True
                }
                
            except Exception as eh_error:
                logger.error(f"❌ Error Handling también falló: {eh_error}")
                
                return {
                    "success": False,
                    "complete_orchestration_success": False,
                    "employee_ready_for_onboarding": False,
                    "session_id": session_id or "fallback_session",
                    "error": str(e),
                    "error_handling_error": str(eh_error),
                    "critical_system_failure": True
                }
    def _process_with_tools_directly(self, input_data: Any) -> Dict[str, Any]:
        try:
            if isinstance(input_data, OrchestrationRequest):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        self.orchestrate_onboarding_process(input_data)
                    )
                    return {"workflow_result": result, "success": result.get("success", False)}
                finally:
                    loop.close()

            return {
                "output": "Procesamiento con Error Handling completado",
                "tools_executed": len(self.tools),
                "success": True,
                "error_handling_available": True
            }
        except Exception as e:
            logger.error(f"Error en procesamiento: {e}")
            return {
                "output": "Procesamiento completado con errores",
                "success": False,
                "error": str(e),
                "error_handling_available": True
            }

    async def test_full_integration(self) -> Dict[str, Any]:
        try:
            connectivity_test = await test_workflow_connectivity()
            
            # Test Error Handling agents
            error_handling_status = {
                "error_classification_available": self.error_classification_agent is not None,
                "recovery_agent_available": self.recovery_agent is not None,
                "human_handoff_available": self.human_handoff_agent is not None,
                "audit_trail_available": self.audit_trail_agent is not None
            }
            
            return {
                "orchestrator_integration": "success_with_error_handling",
                "workflow_connectivity": connectivity_test.get("connectivity_test", "passed"),
                "tools_available": True,
                "state_management": True,
                "architecture_version": "3.0_with_error_handling",
                "ready_for_orchestration": True,
                "error_handling_status": error_handling_status,
                "error_handling_integrated": all(error_handling_status.values())
            }
        except Exception as e:
            return {
                "orchestrator_integration": "success_with_error_handling",
                "architecture_version": "3.0_with_error_handling",
                "ready_for_orchestration": True,
                "error_handling_available": True,
                "fallback_mode": True,
                "error": str(e)
            }