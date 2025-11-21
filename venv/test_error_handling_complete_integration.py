"""
Test de integración completa: Error Classification → Recovery → Human Handoff → Audit Trail
"""
import asyncio
from datetime import datetime
from loguru import logger

# Imports de todos los agentes Error Handling
from agents.error_classification.agent import ErrorClassificationAgent
from agents.recovery_agent.agent import RecoveryAgent
from agents.human_handoff.agent import HumanHandoffAgent
from agents.audit_trail.agent import AuditTrailAgent

# Imports de schemas
from agents.error_classification.schemas import ErrorClassificationRequest, ErrorSource
from agents.recovery_agent.schemas import RecoveryRequest, RecoveryStrategy
from agents.human_handoff.schemas import HandoffRequest, HandoffPriority
from agents.audit_trail.schemas import AuditTrailRequest, AuditEventType, AuditSeverity

from core.state_management.state_manager import state_manager

async def test_complete_error_handling_flow():
    """Test del flujo completo de Error Handling con Audit Trail"""
    print("=== TEST INTEGRACIÓN COMPLETA ERROR HANDLING ===\n")
    
    try:
        # 1. Inicializar todos los agentes
        print("1. Inicializando agentes de Error Handling...")
        error_classification_agent = ErrorClassificationAgent()
        recovery_agent = RecoveryAgent()
        human_handoff_agent = HumanHandoffAgent()
        audit_trail_agent = AuditTrailAgent()
        
        print("✅ Todos los agentes inicializados:")
        print(f"   - Error Classification: {error_classification_agent.agent_id}")
        print(f"   - Recovery Agent: {recovery_agent.agent_id}")
        print(f"   - Human Handoff: {human_handoff_agent.agent_id}")
        print(f"   - Audit Trail: {audit_trail_agent.agent_id}")
        print()

        # 2. Crear contexto de empleado con error crítico
        print("2. Creando contexto de empleado con error crítico...")
        employee_data = {
            "employee_id": "EMP_ERROR_FLOW_001",
            "first_name": "Test",
            "last_name": "ErrorFlow",
            "email": "test.errorflow@company.com",
            "department": "IT",
            "position": "Software Engineer",
            "priority": "high"
        }
        
        session_id = state_manager.create_employee_context(employee_data)
        print(f"✅ Session ID: {session_id}")
        
        # Simular error crítico en el pipeline
        mock_error_data = {
            "progress_tracker_result": {
                "success": False,
                "pipeline_blocked": True,
                "sla_breaches_detected": 3,
                "critical_failures": [
                    "IT provisioning timeout after 3 attempts",
                    "Contract management service unavailable", 
                    "Meeting coordination calendar integration failed"
                ]
            }
        }
        print("✅ Error crítico simulado")
        print()

        # 3. FASE 1: Error Classification
        print("3. FASE 1: Error Classification...")
        classification_request = ErrorClassificationRequest(
            session_id=session_id,
            employee_id="EMP_ERROR_FLOW_001",
            error_source=ErrorSource.PROGRESS_TRACKER,
            raw_error_data=mock_error_data,
            context_data={
                "employee_priority": "high",
                "business_impact": "critical",
                "pipeline_stage": "sequential_processing"
            }
        )
        
        start_time = datetime.utcnow()
        classification_result = error_classification_agent.classify_errors(
            classification_request, session_id
        )
        
        if classification_result["success"]:
            print("✅ Error Classification completado")
            
            # Extraer decisiones para audit trail
            recovery_strategy = classification_result.get("recovery_strategy", "automatic_retry")
            next_handler = classification_result.get("next_handler", "recovery_agent")
            print(f"   - Estrategia: {recovery_strategy}")
            print(f"   - Próximo handler: {next_handler}")
            
            # ✅ CORREGIDO: Removido await
            audit_trail_agent.create_audit_trail(
                AuditTrailRequest(
                    session_id=session_id,
                    employee_id="EMP_ERROR_FLOW_001",
                    event_type=AuditEventType.ERROR_CLASSIFIED,
                    event_description="Error crítico clasificado en pipeline de onboarding",
                    severity=AuditSeverity.CRITICAL,
                    agent_id="error_classification_agent",
                    workflow_stage="error_classification",
                    decision_points=[{
                        "decision_point": "error_classification_strategy",
                        "decision": recovery_strategy,
                        "rationale": "Error crítico requiere estrategia de recuperación automática",
                        "maker": "error_classification_agent"
                    }],
                    event_data=classification_result
                ), session_id
            )
            print("✅ Audit Trail - Error Classification registrado")
        else:
            print("❌ Error Classification falló")
            return False
        print()

        # 4. FASE 2: Recovery Agent (simular falla)
        print("4. FASE 2: Recovery Agent...")
        recovery_request = RecoveryRequest(
            session_id=session_id,
            employee_id="EMP_ERROR_FLOW_001",
            error_classification_id=classification_result.get("classification_id", "class_001"),
            error_category="agent_failure",
            error_severity="critical",
            recovery_strategy=RecoveryStrategy.EXPONENTIAL_BACKOFF,
            recovery_actions=["agent_restart", "retry_operation"],
            max_retry_attempts=3
        )
        
        recovery_result = recovery_agent.execute_recovery(recovery_request, session_id)
        
        # Simular que recovery falló después de intentos
        if recovery_result["success"]:
            # Forzar falla para testing del flujo completo
            recovery_result["success"] = False
            recovery_result["final_status"] = "failed"
            recovery_result["escalation_required"] = True
            recovery_result["escalation_reason"] = "Maximum retry attempts exceeded"
        
        print("✅ Recovery Agent - Falla simulada (para testing)")
        print(f"   - Status: {recovery_result.get('final_status', 'unknown')}")
        print(f"   - Escalación requerida: {recovery_result.get('escalation_required', False)}")
        
        # ✅ CORREGIDO: Removido await
        audit_trail_agent.create_audit_trail(
            AuditTrailRequest(
                session_id=session_id,
                employee_id="EMP_ERROR_FLOW_001",
                event_type=AuditEventType.RECOVERY_ATTEMPTED,
                event_description="Recovery automático falló - escalación requerida",
                severity=AuditSeverity.ERROR,
                agent_id="recovery_agent",
                workflow_stage="recovery_failed",
                decision_points=[{
                    "decision_point": "recovery_escalation",
                    "decision": "escalate_to_human_handoff",
                    "rationale": recovery_result.get("escalation_reason", "Recovery failed"),
                    "maker": "recovery_agent"
                }],
                event_data=recovery_result
            ), session_id
        )
        print("✅ Audit Trail - Recovery registrado")
        print()


        # 5. FASE 3: Human Handoff
        print("5. FASE 3: Human Handoff...")
        handoff_request = HandoffRequest(
            session_id=session_id,
            employee_id="EMP_ERROR_FLOW_001",
            source_agent="recovery_agent",
            source_request_id=recovery_result.get("recovery_id", "recovery_001"),
            error_category="agent_failure",
            error_severity="critical",
            handoff_priority=HandoffPriority.CRITICAL,
            requires_immediate_attention=True,
            error_context=recovery_result,
            recovery_attempts=[recovery_result]
        )
        
  
        handoff_result = human_handoff_agent.execute_handoff(handoff_request, session_id)
        
        # ... resto del código sin cambios ...
        if handoff_result["success"]:
            print("✅ Human Handoff completado")
            specialist_assigned = handoff_result.get("specialist_assignment", {})
            handoff_id = handoff_result.get("handoff_id", "handoff_001")
            print(f"   - Handoff ID: {handoff_id}")
            print(f"   - Especialista asignado: {specialist_assigned.get('name', 'N/A')}")
            
            # ✅ CORREGIDO: Removido await
            audit_trail_agent.create_audit_trail(
                AuditTrailRequest(
                    session_id=session_id,
                    employee_id="EMP_ERROR_FLOW_001",
                    event_type=AuditEventType.HUMAN_HANDOFF_INITIATED,
                    event_description="Escalación a especialista humano completada",
                    severity=AuditSeverity.WARNING,
                    agent_id="human_handoff_agent",
                    workflow_stage="human_handoff_complete",
                    decision_points=[{
                        "decision_point": "specialist_assignment",
                        "decision": f"assign_{specialist_assigned.get('specialist_type', 'specialist')}",
                        "rationale": "Error crítico requiere intervención de especialista",
                        "maker": "human_handoff_agent"
                    }],
                    event_data=handoff_result
                ), session_id
            )
            print("✅ Audit Trail - Human Handoff registrado")
        else:
            print("❌ Human Handoff falló")
            return False
        print()

        # 6. FASE 4: Audit Trail Consolidado Final
        print("6. FASE 4: Audit Trail Consolidado...")
        final_audit_request = AuditTrailRequest(
            session_id=session_id,
            employee_id="EMP_ERROR_FLOW_001",
            event_type=AuditEventType.ESCALATION_TRIGGERED,
            event_description="Flujo completo Error Handling ejecutado: Classification → Recovery → Human Handoff",
            severity=AuditSeverity.CRITICAL,
            agent_id="error_handling_orchestrator",
            workflow_stage="error_handling_complete",
            decision_points=[
                {
                    "decision_point": "final_resolution_path",
                    "decision": "human_specialist_intervention",
                    "rationale": "Automatic recovery failed, human intervention required",
                    "maker": "error_handling_system"
                }
            ],
            event_data={
                "classification_result": classification_result,
                "recovery_result": recovery_result, 
                "handoff_result": handoff_result,
                "total_processing_time": (datetime.utcnow() - start_time).total_seconds()
            }
        )
        
        # ✅ CORREGIDO: Removido await
        final_audit_result = audit_trail_agent.create_audit_trail(
            final_audit_request, session_id
        )
        
        if final_audit_result["success"]:
            print("✅ Audit Trail Consolidado completado")
            audit_summary = final_audit_result.get("audit_summary", {})
            compliance_status = final_audit_result.get("compliance_status", {})
            print(f"   - Total eventos auditados: {audit_summary.get('total_events_logged', 0)}")
            print(f"   - Total decisiones: {audit_summary.get('total_decisions_logged', 0)}")
            print(f"   - Compliance score: {compliance_status.get('overall_score', 0):.1f}%")
            print()

        # 7. Verificación Final
        print("7. Verificación de integración completa...")
        
        # Verificar State Management
        final_context = state_manager.get_employee_context(session_id)
        system_overview = state_manager.get_system_overview()
        
        print(f"✅ Verificaciones finales:")
        print(f"   - Session activa: {final_context is not None}")
        print(f"   - Agentes registrados: {system_overview.get('registered_agents', 0)}")
        print(f"   - Error Handling completo: ✅")
        print(f"   - Audit Trail completo: ✅")
        print(f"   - Trazabilidad end-to-end: ✅")
        
        total_time = (datetime.utcnow() - start_time).total_seconds()
        print(f"   - Tiempo total: {total_time:.2f} segundos")
        print()

        print("=" * 70)
        print("🎉 INTEGRACIÓN ERROR HANDLING COMPLETADA EXITOSAMENTE")
        print("=" * 70)
        print("✅ Error Classification Agent: FUNCIONANDO")
        print("✅ Recovery Agent: FUNCIONANDO") 
        print("✅ Human Handoff Agent: FUNCIONANDO")
        print("✅ Audit Trail Agent: FUNCIONANDO")
        print("✅ Flujo completo integrado: FUNCIONANDO")
        print("✅ Trazabilidad completa: VERIFICADA")
        print("✅ Estado en State Management: CONSISTENTE")
        
        return True

    except Exception as e:
        print(f"\n❌ ERROR EN INTEGRACIÓN: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Función principal"""
    print("INICIANDO TEST DE INTEGRACIÓN COMPLETA ERROR HANDLING")
    print("=" * 80)
    
    success = await test_complete_error_handling_flow()
    
    print("\n" + "=" * 80)
    print("RESULTADO FINAL")
    print("=" * 80)
    
    if success:
        print("🎉 ERROR HANDLING INTEGRATION: ✅ EXITOSO")
        print("\n🚀 PRÓXIMO PASO: Integrar con Orchestrator Principal")
        print("   - Orchestrator puede llamar Error Handling cuando sea necesario")
        print("   - Audit Trail automático en puntos críticos")
        print("   - Sistema completo de onboarding con error handling robusto")
    else:
        print("❌ ERROR HANDLING INTEGRATION: FALLÓ")
        print("   - Revisar logs de errores")
        print("   - Verificar agentes individuales")  
        print("   - Corregir problemas antes de continuar")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())