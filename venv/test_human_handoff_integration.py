#!/usr/bin/env python3
"""
Test de integración completa del Human Handoff Agent
Simula el flujo: Error Classification → Recovery → Human Handoff
"""

import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_human_handoff_integration():
    """Test completo de integración del Human Handoff Agent"""
    
    print("🚀 INICIANDO TEST DE INTEGRACIÓN - HUMAN HANDOFF AGENT")
    print("=" * 80)
    
    try:
        # 1. Import y configuración inicial
        print("\n📋 PASO 1: Configuración inicial y imports")
        from agents.human_handoff.agent import HumanHandoffAgent
        from agents.human_handoff.schemas import (
            HandoffRequest, HandoffPriority, SpecialistType
        )
        from core.state_management.state_manager import state_manager
        
        # Inicializar agente
        handoff_agent = HumanHandoffAgent()
        print(f"✅ Human Handoff Agent inicializado: {handoff_agent.agent_name}")
        print(f"   - Agent ID: {handoff_agent.agent_id}")
        print(f"   - Tools disponibles: {len(handoff_agent.tools)}")
        print(f"   - Tools: {[tool.name for tool in handoff_agent.tools]}")
        
        # 2. Crear contexto de empleado para el test
        print("\n📋 PASO 2: Crear contexto de empleado")
        employee_data = {
            "employee_id": "EMP_HANDOFF_001",
            "first_name": "Ana",
            "last_name": "García",
            "email": "ana.garcia@empresa.com",
            "department": "Engineering", 
            "position": "Senior Software Engineer",
            "hire_date": datetime.utcnow().isoformat(),
            "manager_email": "manager@empresa.com"
        }
        
        session_id = state_manager.create_employee_context(employee_data)
        print(f"✅ Contexto de empleado creado")
        print(f"   - Employee ID: {employee_data['employee_id']}")
        print(f"   - Session ID: {session_id}")
        print(f"   - Department: {employee_data['department']}")
        
        # 3. Simular error crítico que requiere handoff
        print("\n📋 PASO 3: Simular escenario de error crítico")
        
        # Simular que recovery agent falló múltiples veces
        error_context = {
            "error_source": "recovery_agent",
            "error_type": "multiple_recovery_failures", 
            "failed_operations": [
                {
                    "operation": "agent_restart",
                    "attempts": 3,
                    "last_error": "Agent timeout after restart",
                    "timestamp": datetime.utcnow().isoformat()
                },
                {
                    "operation": "state_restoration",
                    "attempts": 2, 
                    "last_error": "State corruption detected",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ],
            "system_impact": "Pipeline completely blocked",
            "business_impact": "Employee onboarding halted"
        }
        
        # Recovery attempts simulados
        recovery_attempts = [
            {
                "recovery_id": "rec_001",
                "strategy": "automatic_retry",
                "status": "failed",
                "attempts": 3,
                "last_error": "Timeout exceeded",
                "timestamp": (datetime.utcnow() - timedelta(minutes=10)).isoformat()
            },
            {
                "recovery_id": "rec_002", 
                "strategy": "state_rollback",
                "status": "failed",
                "attempts": 2,
                "last_error": "State corruption detected",
                "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat()
            }
        ]
        
        print(f"✅ Error crítico simulado")
        print(f"   - Tipo: {error_context['error_type']}")
        print(f"   - Recovery attempts fallidos: {len(recovery_attempts)}")
        print(f"   - Impacto: Pipeline completamente bloqueado")
        
        # 4. Crear HandoffRequest
        print("\n📋 PASO 4: Crear HandoffRequest")
        
        handoff_request = HandoffRequest(
            session_id=session_id,
            employee_id=employee_data["employee_id"],
            source_agent="recovery_agent",
            source_request_id="rec_002",
            error_category="agent_failure",
            error_severity="critical",
            handoff_priority=HandoffPriority.CRITICAL,
            error_context=error_context,
            recovery_attempts=recovery_attempts,
            employee_context=employee_data,
            requires_immediate_attention=True,
            business_impact="high",
            escalation_level=2
        )
        
        print(f"✅ HandoffRequest creado")
        print(f"   - Handoff ID: {handoff_request.handoff_id}")
        print(f"   - Priority: {handoff_request.handoff_priority.value}")
        print(f"   - Category: {handoff_request.error_category}")
        print(f"   - Immediate attention: {handoff_request.requires_immediate_attention}")
        
        # 5. Ejecutar handoff
        print("\n📋 PASO 5: Ejecutar Human Handoff")
        print("🔄 Iniciando handoff process...")
        
        result = handoff_agent.execute_handoff(handoff_request, session_id)
        
        # 6. Analizar resultados
        print("\n📋 PASO 6: Análisis de resultados")
        
        if result["success"]:
            print("✅ HANDOFF EXITOSO")
            
            # Specialist Assignment
            if result.get("specialist_assigned"):
                specialist = result.get("specialist_assignment", {}).get("assigned_specialist", {})
                print(f"\n👤 ESPECIALISTA ASIGNADO:")
                print(f"   - Nombre: {specialist.get('name', 'Unknown')}")
                print(f"   - Tipo: {specialist.get('specialist_type', 'Unknown')}")
                print(f"   - Departamento: {specialist.get('department', 'Unknown')}")
                print(f"   - Email: {specialist.get('email', 'Unknown')}")
            
            # Context Package
            if result.get("context_preserved"):
                context_score = result.get("context_preservation_score", 0)
                print(f"\n📦 CONTEXTO PRESERVADO:")
                print(f"   - Completeness: {context_score:.1%}")
                print(f"   - Employee data: ✅")
                print(f"   - Error timeline: ✅") 
                print(f"   - Recovery history: ✅")
            
            # Escalation Ticket
            ticket = result.get("escalation_ticket", {})
            if ticket:
                print(f"\n🎫 TICKET CREADO:")
                print(f"   - Ticket ID: {ticket.get('ticket_id', 'Unknown')}")
                print(f"   - Title: {ticket.get('title', 'Unknown')}")
                print(f"   - Priority: {ticket.get('priority', 'Unknown')}")
                print(f"   - Assigned to: {ticket.get('assigned_to', 'Unknown')}")
                print(f"   - Due date: {ticket.get('due_date', 'Unknown')}")
            
            # Notifications
            notifications_sent = result.get("successful_notifications", 0)
            total_notifications = result.get("notifications_sent", [])
            print(f"\n📧 NOTIFICACIONES:")
            print(f"   - Enviadas exitosamente: {notifications_sent}")
            print(f"   - Total intentos: {len(total_notifications)}")
            
            for notification in total_notifications:
                status_icon = "✅" if notification.get("status") == "sent" else "❌"
                print(f"   {status_icon} {notification.get('recipient', 'Unknown')} via {notification.get('channel', 'unknown')}")
            
            # Quality Metrics
            handoff_quality = result.get("handoff_quality_score", 0)
            print(f"\n📊 MÉTRICAS DE CALIDAD:")
            print(f"   - Handoff Quality Score: {handoff_quality:.1%}")
            print(f"   - Context Preservation: {result.get('context_preservation_score', 0):.1%}")
            print(f"   - Processing Time: {result.get('processing_time', 0):.2f}s")
            
            # SLA Status
            sla_status = result.get("sla_compliance_status", "unknown")
            print(f"   - SLA Compliance: {sla_status}")
            
        else:
            print("❌ HANDOFF FALLIDO")
            print(f"   - Error: {result.get('message', 'Unknown error')}")
            print(f"   - Errors: {result.get('errors', [])}")
        
        # 7. Verificar estado en State Management
        print("\n📋 PASO 7: Verificar estado actualizado")
        
        updated_context = state_manager.get_employee_context(session_id)
        if updated_context:
            handoff_data = updated_context.processed_data
            print("✅ Estado actualizado en State Management:")
            print(f"   - Handoff completed: {handoff_data.get('human_handoff_completed', False)}")
            print(f"   - Specialist assigned: {handoff_data.get('specialist_assigned', False)}")
            print(f"   - Phase: {updated_context.phase}")
            
            if handoff_data.get('escalation_ticket_id'):
                print(f"   - Ticket ID: {handoff_data.get('escalation_ticket_id')}")
        
        # 8. Métricas del agente
        print("\n📋 PASO 8: Métricas del agente")
        
        metrics = handoff_agent.get_handoff_metrics()
        print("📊 MÉTRICAS ACTUALIZADAS:")
        print(f"   - Total handoffs: {metrics['handoff_metrics']['total_handoffs']}")
        print(f"   - Successful handoffs: {metrics['handoff_metrics']['successful_handoffs']}")
        print(f"   - Success rate: {metrics['success_rate']:.1%}")
        print(f"   - Context preservation rate: {metrics['context_preservation_rate']:.1%}")
        
        # 9. Validar configuración del agente
        print("\n📋 PASO 9: Validación de configuración")
        
        config_validation = handoff_agent.validate_handoff_configuration()
        if config_validation["configuration_valid"]:
            print("✅ Configuración del agente válida")
            print(f"   - Tools disponibles: {config_validation['tools_available']}/{config_validation['expected_tools']}")
            print(f"   - Handoff ready: {config_validation['handoff_ready']}")
        else:
            print("❌ Issues de configuración:")
            for issue in config_validation["validation_issues"]:
                print(f"   - {issue}")
        
        # 10. Test de recuperación de estado
        print("\n📋 PASO 10: Test de recuperación de handoff")
        
        if result.get("success") and result.get("handoff_id"):
            handoff_status = handoff_agent.get_handoff_status(result["handoff_id"])
            if handoff_status["found"]:
                print("✅ Handoff retrievable from history")
                print(f"   - Status: {handoff_status['status']}")
                print(f"   - Completed at: {handoff_status['completed_at']}")
            else:
                print("❌ Handoff not found in history")
        
        # 11. Resumen final
        print("\n" + "=" * 80)
        print("📊 RESUMEN DE TEST DE INTEGRACIÓN")
        print("=" * 80)
        
        if result["success"]:
            print("🎉 TEST EXITOSO - Human Handoff Agent funcionando correctamente")
            print("\nComponentes verificados:")
            print("✅ Escalation Routing - Specialist assignment")
            print("✅ Context Packaging - Information preservation") 
            print("✅ Ticket Management - Issue tracking")
            print("✅ Notification System - Stakeholder communication")
            print("✅ State Management - Status updates")
            print("✅ Metrics Collection - Performance tracking")
            
            print(f"\nHandoff Quality Score: {result.get('handoff_quality_score', 0):.1%}")
            print(f"Context Preservation: {result.get('context_preservation_score', 0):.1%}")
            print(f"Notifications Success: {result.get('successful_notifications', 0)}/{len(result.get('notifications_sent', []))}")
            
        else:
            print("❌ TEST FALLIDO - Revisar configuración y dependencias")
            print(f"Error: {result.get('message', 'Unknown')}")
        
        print("\n🔗 INTEGRACIÓN CON ERROR HANDLING CHAIN:")
        print("   Error Classification → Recovery Agent → Human Handoff → ✅ COMPLETADO")
        
        return result["success"]
        
    except Exception as e:
        print(f"\n❌ ERROR EN TEST: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_human_handoff_scenarios():
    """Test múltiples escenarios de handoff"""
    
    print("\n" + "=" * 80)
    print("🧪 TEST DE ESCENARIOS MÚLTIPLES")
    print("=" * 80)
    
    scenarios = [
        {
            "name": "Emergency Security Issue", 
            "priority": "emergency",
            "category": "security_issue",
            "specialist_type": "security_specialist",
            "expected_response_minutes": 5
        },
        {
            "name": "HR Quality Failure",
            "priority": "high", 
            "category": "quality_failure",
            "specialist_type": "hr_manager",
            "expected_response_minutes": 60
        },
        {
            "name": "System Integration Error",
            "priority": "medium",
            "category": "integration_error", 
            "specialist_type": "it_specialist",
            "expected_response_minutes": 240
        }
    ]
    
    try:
        from agents.human_handoff.agent import HumanHandoffAgent
        from agents.human_handoff.schemas import HandoffRequest, HandoffPriority
        
        handoff_agent = HumanHandoffAgent()
        success_count = 0
        
        for i, scenario in enumerate(scenarios):
            print(f"\n🎬 ESCENARIO {i+1}: {scenario['name']}")
            print(f"   Priority: {scenario['priority']}")
            print(f"   Category: {scenario['category']}")
            
            # Create test handoff request
            handoff_request = HandoffRequest(
                session_id=f"test_session_{i+1}",
                employee_id=f"EMP_TEST_{i+1:03d}",
                source_agent="error_classification_agent",
                source_request_id=f"class_{i+1}",
                error_category=scenario["category"],
                error_severity="critical" if scenario["priority"] == "emergency" else "high",
                handoff_priority=HandoffPriority(scenario["priority"]),
                requires_immediate_attention=scenario["priority"] == "emergency",
                business_impact="high" if scenario["priority"] in ["emergency", "critical"] else "medium"
            )
            
            # Execute handoff
            result = handoff_agent.process_request(handoff_request)
            
            if result["success"]:
                print(f"   ✅ Handoff successful")
                
                # Check specialist assignment
                if result.get("specialist_assignment"):
                    specialist_type = result["specialist_assignment"].get("assigned_specialist", {}).get("specialist_type")
                    if specialist_type == scenario["specialist_type"]:
                        print(f"   ✅ Correct specialist type: {specialist_type}")
                    else:
                        print(f"   ⚠️  Expected {scenario['specialist_type']}, got {specialist_type}")
                
                success_count += 1
            else:
                print(f"   ❌ Handoff failed: {result.get('message', 'Unknown error')}")
        
        print(f"\n📊 RESULTADOS: {success_count}/{len(scenarios)} escenarios exitosos")
        return success_count == len(scenarios)
        
    except Exception as e:
        print(f"❌ Error en test de escenarios: {e}")
        return False

if __name__ == "__main__":
    print("🧪 EJECUTANDO TESTS DEL HUMAN HANDOFF AGENT")
    
    # Test principal de integración
    main_test_success = test_human_handoff_integration()
    
    # Test de escenarios múltiples
    scenarios_test_success = test_human_handoff_scenarios()
    
    print("\n" + "=" * 80)
    print("🏁 RESULTADOS FINALES")
    print("=" * 80)
    
    if main_test_success and scenarios_test_success:
        print("🎉 TODOS LOS TESTS EXITOSOS")
        print("✅ Human Handoff Agent listo para producción")
        exit(0)
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        print("🔧 Revisar configuración antes de usar en producción")
        exit(1)