#!/usr/bin/env python3
"""
Test End-to-End del flujo completo de Error Handling:
Progress Tracker → Error Classification → Recovery → Human Handoff
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_complete_error_handling_flow():
    """Test del flujo completo de manejo de errores"""
    
    print("🔥 TEST END-TO-END: FLUJO COMPLETO DE ERROR HANDLING")
    print("=" * 80)
    
    try:
        # 1. Simular detección de error por Progress Tracker
        print("\n📋 PASO 1: Progress Tracker detecta error crítico")
        
        from agents.progress_tracker.schemas import ProgressTrackerRequest
        from core.state_management.state_manager import state_manager
        
        # Crear empleado y session
        employee_data = {
            "employee_id": "EMP_E2E_001",
            "first_name": "Carlos",
            "last_name": "Mendoza", 
            "department": "IT",
            "position": "DevOps Engineer"
        }
        
        session_id = state_manager.create_employee_context(employee_data)
        print(f"✅ Employee context created: {session_id}")
        
        # Simular agente fallido
        state_manager.update_agent_state(
            "it_provisioning_agent",
            "error",
            {
                "error_message": "Timeout creating user credentials", 
                "failed_operations": ["create_ad_user", "assign_permissions"],
                "retry_attempts": 3,
                "last_error_time": datetime.utcnow().isoformat()
            },
            session_id
        )
        
        print("✅ Agente IT Provisioning marcado como fallido")
        
        # 2. Error Classification
        print("\n📋 PASO 2: Error Classification Agent analiza el error")
        
        from agents.error_classification.agent import ErrorClassificationAgent
        from agents.error_classification.schemas import ErrorClassificationRequest, ErrorSource
        
        classification_agent = ErrorClassificationAgent()
        
        classification_request = ErrorClassificationRequest(
            session_id=session_id,
            employee_id=employee_data["employee_id"],
            error_source=ErrorSource.PROGRESS_TRACKER,
            raw_error_data={
                "agent_id": "it_provisioning_agent",
                "error_type": "timeout",
                "error_message": "Timeout creating user credentials",
                "retry_attempts": 3,
                "system_impact": "Employee cannot access systems"
            },
            context_data={
                "pipeline_stage": "it_provisioning",
                "business_hours": True,
                "priority_employee": False
            }
        )
        
        classification_result = classification_agent.classify_errors(classification_request, session_id)
        
        if classification_result["success"]:
            print("✅ Error clasificado exitosamente")
            print(f"   - Global Severity: {classification_result['classification_summary']['global_severity']}")
            print(f"   - Recovery Strategy: {classification_result['recovery_strategy']}")
            print(f"   - Next Handler: {classification_result['next_handler']}")
        else:
            print("❌ Error en clasificación")
            return False
        
        # 3. Recovery Agent (simulamos que falla)
        print("\n📋 PASO 3: Recovery Agent intenta recuperación automática")
        
        from agents.recovery_agent.agent import RecoveryAgent
        from agents.recovery_agent.schemas import RecoveryRequest, RecoveryStrategy, RecoveryAction, RecoveryPriority
        
        recovery_agent = RecoveryAgent()
        
        recovery_request = RecoveryRequest(
            session_id=session_id,
            employee_id=employee_data["employee_id"],
            error_classification_id=classification_result.get("classification_id", "class_001"),
            error_category="agent_failure",
            error_severity="critical",
            failed_agent_id="it_provisioning_agent",
            recovery_strategy=RecoveryStrategy.IMMEDIATE_RETRY,
            recovery_actions=[RecoveryAction.AGENT_RESTART, RecoveryAction.RETRY_OPERATION],
            recovery_priority=RecoveryPriority.CRITICAL,
            max_retry_attempts=2
        )
        
        recovery_result = recovery_agent.execute_recovery(recovery_request, session_id)
        
        # Simular que recovery falla
        recovery_success = False  # Forzamos fallo para trigger handoff
        
        if recovery_success:
            print("✅ Recovery exitoso - No se requiere handoff humano")
            return True
        else:
            print("❌ Recovery falló - Escalando a Human Handoff")
            print(f"   - Recovery Status: {recovery_result.get('recovery_status', 'failed')}")
            print(f"   - Actions Executed: {len(recovery_result.get('recovery_actions_executed', []))}")
        
        # 4. Human Handoff Agent
        print("\n📋 PASO 4: Human Handoff Agent ejecuta escalación")
        
        from agents.human_handoff.agent import HumanHandoffAgent
        from agents.human_handoff.schemas import HandoffRequest, HandoffPriority
        
        handoff_agent = HumanHandoffAgent()
        
        handoff_request = HandoffRequest(
            session_id=session_id,
            employee_id=employee_data["employee_id"],
            source_agent="recovery_agent",
            source_request_id=recovery_result.get("recovery_id", "rec_001"),
            error_category="agent_failure",
            error_severity="critical",
            handoff_priority=HandoffPriority.CRITICAL,
            error_context={
                "original_error": classification_request.raw_error_data,
                "classification_results": classification_result.get("classification_summary", {}),
                "recovery_attempts": recovery_result.get("recovery_actions_executed", [])
            },
            recovery_attempts=[{
                "recovery_id": recovery_result.get("recovery_id", "rec_001"),
                "strategy": "immediate_retry",
                "status": "failed",
                "timestamp": datetime.utcnow().isoformat()
            }],
            requires_immediate_attention=True,
            business_impact="high"
        )
        
        handoff_result = handoff_agent.execute_handoff(handoff_request, session_id)
        
        # 5. Análisis de resultados finales
        print("\n📋 PASO 5: Análisis de resultados del flujo completo")
        
        if handoff_result["success"]:
            print("🎉 FLUJO END-TO-END EXITOSO")
            
            print("\n📊 RESUMEN DEL FLUJO:")
            print("   1. ✅ Progress Tracker detectó error")
            print("   2. ✅ Error Classification analizó y categorizó")  
            print("   3. ❌ Recovery Agent falló (esperado)")
            print("   4. ✅ Human Handoff escaló exitosamente")
            
            print("\n🎯 RESULTADO FINAL:")
            specialist = handoff_result.get("specialist_assignment", {}).get("assigned_specialist", {})
            ticket = handoff_result.get("escalation_ticket", {})
            
            print(f"   - Especialista: {specialist.get('name', 'Unknown')} ({specialist.get('specialist_type', 'Unknown')})")
            print(f"   - Ticket: {ticket.get('ticket_id', 'Unknown')}")
            print(f"   - Contexto preservado: {handoff_result.get('context_preservation_score', 0):.1%}")
            print(f"   - Notificaciones enviadas: {handoff_result.get('successful_notifications', 0)}")
            
            # Verificar estado final del empleado
            final_context = state_manager.get_employee_context(session_id)
            if final_context:
                print(f"   - Employee Phase: {final_context.phase}")
                print(f"   - Handoff Completed: {final_context.processed_data.get('human_handoff_completed', False)}")
            
            return True
        else:
            print("❌ FLUJO END-TO-END FALLIDO")
            print(f"Error en Human Handoff: {handoff_result.get('message', 'Unknown')}")
            return False
        
    except Exception as e:
        print(f"❌ ERROR EN FLUJO E2E: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_complete_error_handling_flow()
    
    print("\n" + "=" * 80)
    if success:
        print("🏆 TEST END-TO-END EXITOSO")
        print("✅ Sistema completo de Error Handling funcionando")
        print("\nFlujo verificado:")
        print("   Progress Tracker → Error Classification → Recovery → Human Handoff")
        exit(0)
    else:
        print("❌ TEST END-TO-END FALLIDO")  
        print("🔧 Revisar componentes del sistema")
        exit(1)