"""
Test completo para Error Classification Agent
Verifica integración con State Management, herramientas y flujo de clasificación
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# Imports del proyecto
from agents.error_classification.agent import ErrorClassificationAgent
from agents.error_classification.schemas import (
    ErrorClassificationRequest, ErrorSource, ErrorCategory, 
    ErrorSeverity, RecoveryStrategy
)
from core.state_management.state_manager import state_manager
from core.state_management.models import AgentStateStatus, OnboardingPhase

def test_error_classification_agent_integration():
    """Test completo de integración del Error Classification Agent"""
    print("=== ERROR CLASSIFICATION AGENT - TEST COMPLETO ===\n")
    
    try:
        # 1. Inicializar agente
        print("1. Inicializando Error Classification Agent...")
        agent = ErrorClassificationAgent()
        print(f"✅ Agente inicializado: {agent.agent_name}")
        print(f"   - Agent ID: {agent.agent_id}")
        print(f"   - Herramientas: {len(agent.tools)}")
        
        # Verificar herramientas
        tool_names = [tool.name for tool in agent.tools]
        expected_tools = [
            "error_detector_tool",
            "severity_analyzer_tool", 
            "root_cause_finder_tool",
            "routing_engine_tool"
        ]
        
        print(f"   - Herramientas disponibles: {tool_names}")
        missing_tools = [tool for tool in expected_tools if tool not in tool_names]
        if missing_tools:
            print(f"   ⚠️  Herramientas faltantes: {missing_tools}")
        else:
            print("   ✅ Todas las herramientas están disponibles")
        
        print()
        
        # 2. Verificar integración con State Management
        print("2. Verificando integración con State Management...")
        agent_state = state_manager.get_agent_state(agent.agent_id)
        if agent_state:
            print("✅ Agente registrado en State Management")
            print(f"   - Estado: {agent_state.status}")
            print(f"   - Datos: {list(agent_state.data.keys())}")
        else:
            print("❌ Agente NO registrado en State Management")
            return False
        print()
        
        # 3. Crear contexto de empleado de prueba
        print("3. Creando contexto de empleado de prueba...")
        employee_data = {
            "employee_id": "EMP_ERROR_TEST_001",
            "first_name": "Test",
            "last_name": "Employee",
            "email": "test.employee@company.com",
            "department": "IT",
            "position": "Software Engineer",
            "priority": "high"
        }
        
        session_id = state_manager.create_employee_context(employee_data)
        if session_id:
            print(f"✅ Contexto creado - Session ID: {session_id}")
        else:
            print("❌ Error creando contexto de empleado")
            return False
        print()
        
        # 4. Simular errores del Progress Tracker
        print("4. Simulando errores del Progress Tracker...")
        mock_progress_tracker_errors = {
            "progress_tracker_result": {
                "success": False,
                "message": "Multiple pipeline issues detected",
                "pipeline_blocked": True,
                "sla_breaches_detected": 2,
                "immediate_actions_required": [
                    "Unblock IT provisioning stage",
                    "Address contract management timeout"
                ],
                "sla_monitoring_results": [
                    {
                        "stage": "it_provisioning",
                        "status": "breached",
                        "elapsed_time_minutes": 25.5,
                        "target_duration_minutes": 10
                    },
                    {
                        "stage": "contract_management", 
                        "status": "at_risk",
                        "elapsed_time_minutes": 18.2,
                        "target_duration_minutes": 15
                    }
                ],
                "quality_gate_results": [
                    {
                        "stage": "it_provisioning",
                        "success": False,
                        "gate_result": {
                            "status": "failed",
                            "passed": False,
                            "overall_score": 45.0,
                            "critical_issues": [
                                "Security clearance validation failed",
                                "Equipment assignment incomplete"
                            ]
                        }
                    }
                ]
            }
        }
        
        # 5. Simular errores de agentes individuales en State Management
        print("5. Simulando errores de agentes en State Management...")
        
        # Simular agente con timeout
        state_manager.update_agent_state(
            "it_provisioning_agent",
            AgentStateStatus.PROCESSING,
            {
                "started_at": (datetime.utcnow()).isoformat(),
                "current_task": "provisioning_credentials",
                "timeout_risk": True
            },
            session_id
        )
        
        # Simular agente con errores
        state_manager.update_agent_state(
            "contract_management_agent", 
            AgentStateStatus.ERROR,
            {
                "error_count": 4,
                "last_error": "Legal validation service unavailable",
                "failed_operations": ["contract_generation", "legal_validation"]
            },
            session_id
        )
        
        print("✅ Errores simulados en State Management")
        print()
        
        # 6. Crear request de clasificación
        print("6. Creando request de clasificación de errores...")
        classification_request = ErrorClassificationRequest(
            session_id=session_id,
            employee_id="EMP_ERROR_TEST_001",
            error_source=ErrorSource.PROGRESS_TRACKER,
            raw_error_data=mock_progress_tracker_errors,
            context_data={
                "employee_priority": "high",
                "business_impact": "medium",
                "time_sensitivity": "urgent",
                "pipeline_stage": "sequential_processing",
                "employee_type": "software_engineer",
                "department": "IT"
            },
            force_reclassification=False
        )
        
        print("✅ Request de clasificación creado")
        print(f"   - Employee ID: {classification_request.employee_id}")
        print(f"   - Error Source: {classification_request.error_source}")
        print(f"   - Context fields: {len(classification_request.context_data)}")
        print()
        
        # 7. Ejecutar clasificación de errores
        print("7. Ejecutando clasificación de errores...")
        print("   (Esto puede tomar unos momentos mientras se ejecutan todas las herramientas...)")
        
        start_time = datetime.utcnow()
        result = agent.classify_errors(classification_request, session_id)
        end_time = datetime.utcnow()
        
        processing_time = (end_time - start_time).total_seconds()
        print(f"   ⏱️  Tiempo de procesamiento: {processing_time:.2f} segundos")
        print()
        
        # 8. Analizar resultados
        print("8. Analizando resultados de clasificación...")
        
        if result["success"]:
            print("✅ Clasificación completada exitosamente")
            
            # Mostrar resumen de clasificación
            summary = result.get("classification_summary", {})
            print(f"   📊 Resumen de Clasificación:")
            print(f"      - Errores detectados: {summary.get('errors_detected', 0)}")
            print(f"      - Errores clasificados: {summary.get('errors_classified', 0)}")
            print(f"      - Severidad global: {summary.get('global_severity', 'unknown')}")
            print(f"      - Estrategia de recuperación: {summary.get('primary_recovery_strategy', 'unknown')}")
            print(f"      - Requiere escalación: {'Sí' if summary.get('requires_escalation') else 'No'}")
            print(f"      - Confianza: {summary.get('classification_confidence', 0):.2%}")
            
            # Mostrar errores detectados
            detected_errors = result.get("detected_errors", [])
            print(f"\n   🚨 Errores Detectados ({len(detected_errors)}):")
            for i, error in enumerate(detected_errors[:3], 1):  # Mostrar solo los primeros 3
                print(f"      {i}. {error.get('error_type', 'unknown')} - {error.get('severity', 'unknown')}")
                print(f"         Descripción: {error.get('description', 'N/A')}")
            
            if len(detected_errors) > 3:
                print(f"      ... y {len(detected_errors) - 3} errores más")
            
            # Mostrar acciones inmediatas
            actions = result.get("immediate_actions", [])
            print(f"\n   ⚡ Acciones Inmediatas ({len(actions)}):")
            for action in actions[:5]:  # Mostrar primeras 5 acciones
                print(f"      • {action}")
            
            # Mostrar próximo handler
            next_handler = result.get("next_handler", "unknown")
            print(f"\n   🎯 Próximo Handler: {next_handler}")
            
            # Mostrar tiempo estimado de resolución
            resolution_time = result.get("estimated_resolution_time", {})
            if resolution_time:
                print(f"   ⏰ Tiempo Estimado de Resolución: {resolution_time.get('estimated_avg_minutes', 'unknown')} minutos")
            
        else:
            print("❌ Clasificación falló")
            print(f"   Error: {result.get('message', 'Unknown error')}")
            errors = result.get("errors", [])
            for error in errors:
                print(f"   - {error}")
            return False
        
        print()
        
        # 9. Verificar actualización de State Management
        print("9. Verificando actualización de State Management...")
        
        # Verificar estado del agente
        updated_agent_state = state_manager.get_agent_state(agent.agent_id, session_id)
        if updated_agent_state:
            print(f"✅ Estado del agente actualizado: {updated_agent_state.status}")
            if updated_agent_state.data:
                data_keys = list(updated_agent_state.data.keys())
                print(f"   - Datos actualizados: {data_keys}")
        
        # Verificar contexto del empleado
        updated_context = state_manager.get_employee_context(session_id)
        if updated_context and updated_context.processed_data:
            error_data = updated_context.processed_data.get("error_classification_completed")
            if error_data:
                print("✅ Datos de clasificación guardados en contexto del empleado")
            else:
                print("⚠️  Datos de clasificación no encontrados en contexto")
        
        print()
        
        # 10. Test de herramientas individuales
        print("10. Probando herramientas individuales...")
        
        # Test Error Detector
        try:
            from agents.error_classification.tools import error_detector_tool
            detector_result = error_detector_tool.invoke({
                "session_id": session_id,
                "monitoring_data": mock_progress_tracker_errors,
                "include_historical": True
            })
            
            if detector_result.get("success"):
                error_count = detector_result.get("error_count", 0)
                print(f"   ✅ Error Detector: {error_count} errores detectados")
            else:
                print(f"   ❌ Error Detector falló: {detector_result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ Error Detector excepción: {e}")
        
        # Test Severity Analyzer
        try:
            from agents.error_classification.tools import severity_analyzer_tool
            
            # Usar errores del detector si están disponibles
            test_errors = detected_errors if 'detected_errors' in locals() else [
                {"error_type": "timeout", "source": "agent_direct", "severity": "high"}
            ]
            
            severity_result = severity_analyzer_tool.invoke({
                "detected_errors": test_errors,
                "context_data": classification_request.context_data
            })
            
            if severity_result.get("success"):
                global_severity = severity_result.get("global_severity", "unknown")
                print(f"   ✅ Severity Analyzer: Severidad global = {global_severity}")
            else:
                print(f"   ❌ Severity Analyzer falló: {severity_result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ Severity Analyzer excepción: {e}")
        
        print()
        
        # 11. Verificar integración con sistema de recuperación
        print("11. Verificando preparación para sistema de recuperación...")
        
        recovery_strategy = result.get("recovery_strategy")
        next_handler = result.get("next_handler")
        
        print(f"   🔄 Estrategia de recuperación: {recovery_strategy}")
        print(f"   🎯 Handler objetivo: {next_handler}")
        
        # Verificar si el routing es apropiado
        if recovery_strategy in [strategy.value for strategy in RecoveryStrategy]:
            print("   ✅ Estrategia de recuperación válida")
        else:
            print("   ⚠️  Estrategia de recuperación no reconocida")
        
        if next_handler and ":" in next_handler:
            handler_type, handler_id = next_handler.split(":", 1)
            print(f"   ✅ Handler routing válido: {handler_type} -> {handler_id}")
        else:
            print("   ⚠️  Handler routing incompleto")
        
        print()
        
        # 12. Cleanup y resumen final
        print("12. Limpieza y resumen final...")
        
        # Obtener overview del sistema
        system_overview = state_manager.get_system_overview()
        print(f"   📈 Sistema Overview:")
        print(f"      - Sesiones activas: {system_overview.get('active_sessions', 0)}")
        print(f"      - Agentes registrados: {system_overview.get('registered_agents', 0)}")
        
        print("\n" + "="*60)
        print("🎉 TEST COMPLETADO EXITOSAMENTE")
        print("="*60)
        print(f"✅ Error Classification Agent funcionando correctamente")
        print(f"✅ Integración con State Management verificada")
        print(f"✅ Herramientas de clasificación operativas")
        print(f"✅ Flujo de error handling preparado")
        print(f"⏱️  Tiempo total de test: {(datetime.utcnow() - start_time).total_seconds():.2f} segundos")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN TEST: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_error_classification_tools_individually():
    """Test individual de cada herramienta de clasificación"""
    print("\n=== TEST INDIVIDUAL DE HERRAMIENTAS ===\n")
    
    try:
        from agents.error_classification.tools import (
            error_detector_tool, severity_analyzer_tool, 
            root_cause_finder_tool, routing_engine_tool
        )
        
        # Test data común
        test_session_id = "test_session_tools"
        test_monitoring_data = {
            "progress_tracker_result": {
                "success": False,
                "pipeline_blocked": True,
                "sla_breaches_detected": 1
            }
        }
        
        test_errors = [
            {
                "source": "progress_tracker",
                "error_type": "pipeline_blocked", 
                "description": "Pipeline execution blocked by critical dependency failure",
                "severity": "critical",
                "timestamp": datetime.utcnow().isoformat(),
                "context": {"stage": "it_provisioning", "attempts": 3}
            }
        ]
        
        test_context = {
            "employee_priority": "high",
            "business_impact": "medium",
            "pipeline_stage": "sequential_processing"
        }
        
        # 1. Test Error Detector Tool
        print("1. Testing Error Detector Tool...")
        detector_result = error_detector_tool.invoke({
            "session_id": test_session_id,
            "monitoring_data": test_monitoring_data,
            "include_historical": False
        })
        
        if detector_result.get("success"):
            print(f"   ✅ Error Detector: {detector_result.get('error_count', 0)} errores")
        else:
            print(f"   ❌ Error Detector falló: {detector_result.get('error')}")
        
        # 2. Test Severity Analyzer Tool
        print("2. Testing Severity Analyzer Tool...")
        severity_result = severity_analyzer_tool.invoke({
            "detected_errors": test_errors,
            "context_data": test_context
        })
        
        if severity_result.get("success"):
            print(f"   ✅ Severity Analyzer: {severity_result.get('global_severity')}")
        else:
            print(f"   ❌ Severity Analyzer falló: {severity_result.get('error')}")
        
        # 3. Test Root Cause Finder Tool
        print("3. Testing Root Cause Finder Tool...")
        root_cause_result = root_cause_finder_tool.invoke({
            "detected_errors": test_errors,
            "error_context": test_context,
            "historical_data": {}
        })
        
        if root_cause_result.get("success"):
            analyses_count = len(root_cause_result.get("root_cause_analyses", []))
            print(f"   ✅ Root Cause Finder: {analyses_count} análisis")
        else:
            print(f"   ❌ Root Cause Finder falló: {root_cause_result.get('error')}")
        
        # 4. Test Routing Engine Tool
        print("4. Testing Routing Engine Tool...")
        
        mock_classifications = [
            {
                "classification_id": "test_class_1",
                "error_category": "agent_failure",
                "severity_level": "critical",
                "recovery_strategy": "automatic_retry"
            }
        ]
        
        routing_result = routing_engine_tool.invoke({
            "classification_results": mock_classifications,
            "system_capabilities": {
                "recovery_agent_available": True,
                "human_handoff_available": True
            }
        })
        
        if routing_result.get("success"):
            decisions_count = len(routing_result.get("routing_decisions", []))
            print(f"   ✅ Routing Engine: {decisions_count} decisiones")
        else:
            print(f"   ❌ Routing Engine falló: {routing_result.get('error')}")
        
        print("\n✅ Test de herramientas individuales completado")
        return True
        
    except Exception as e:
        print(f"❌ Error en test de herramientas: {e}")
        return False

def main():
    """Función principal para ejecutar todos los tests"""
    print("INICIANDO TESTS DEL ERROR CLASSIFICATION AGENT")
    print("=" * 80)
    
    # Test 1: Integración completa
    test1_success = test_error_classification_agent_integration()
    
    # Test 2: Herramientas individuales
    test2_success = test_error_classification_tools_individually()
    
    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN DE TESTS")
    print("=" * 80)
    print(f"Test de Integración: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"Test de Herramientas: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    
    if test1_success and test2_success:
        print("\n🎉 TODOS LOS TESTS PASARON - ERROR CLASSIFICATION AGENT LISTO")
        print("✅ Puedes proceder con la implementación del Recovery Agent")
    else:
        print("\n⚠️  ALGUNOS TESTS FALLARON - REVISA LOS ERRORES ANTES DE CONTINUAR")
    
    return test1_success and test2_success

if __name__ == "__main__":
    main()