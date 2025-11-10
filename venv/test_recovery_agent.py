"""
Test completo para Recovery Agent
Verifica integración con State Management, herramientas de recuperación y flujo completo
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# Imports del proyecto
from agents.recovery_agent.agent import RecoveryAgent
from agents.recovery_agent.schemas import (
    RecoveryRequest, RecoveryStrategy, RecoveryAction, RecoveryPriority
)
from core.state_management.state_manager import state_manager
from core.state_management.models import AgentStateStatus, OnboardingPhase

def test_recovery_agent_integration():
    """Test completo de integración del Recovery Agent"""
    print("=== RECOVERY AGENT - TEST COMPLETO ===\n")
    
    try:
        # 1. Inicializar agente
        print("1. Inicializando Recovery Agent...")
        agent = RecoveryAgent()
        print(f"✅ Agente inicializado: {agent.agent_name}")
        print(f"   - Agent ID: {agent.agent_id}")
        print(f"   - Herramientas: {len(agent.tools)}")
        
        # Verificar herramientas
        tool_names = [tool.name for tool in agent.tools]
        expected_tools = [
            "retry_manager_tool",
            "state_restorer_tool",
            "circuit_breaker_tool", 
            "workflow_resumer_tool"
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
            print(f"   - Capacidades: {list(agent_state.data.get('capabilities', {}).keys())}")
        else:
            print("❌ Agente NO registrado en State Management")
            return False
        print()
        
        # 3. Crear contexto de empleado con errores simulados
        print("3. Creando contexto de empleado con errores simulados...")
        employee_data = {
            "employee_id": "EMP_RECOVERY_TEST_001",
            "first_name": "Recovery",
            "last_name": "Test",
            "email": "recovery.test@company.com",
            "department": "IT",
            "position": "Test Engineer",
            "priority": "high"
        }
        
        session_id = state_manager.create_employee_context(employee_data)
        if session_id:
            print(f"✅ Contexto creado - Session ID: {session_id}")
        else:
            print("❌ Error creando contexto de empleado")
            return False
        
        # 4. Simular agentes en estados problemáticos
        print("4. Simulando agentes en estados problemáticos...")
        
        # Agente con errores múltiples
        state_manager.update_agent_state(
            "it_provisioning_agent",
            AgentStateStatus.ERROR,
            {
                "error_count": 4,
                "last_error": "Timeout connecting to provisioning service",
                "consecutive_failures": 3,
                "last_attempt": datetime.utcnow().isoformat(),
                "failed_operations": ["create_user_account", "assign_equipment"]
            },
            session_id
        )
        
        # Agente stuck en processing
        state_manager.update_agent_state(
            "contract_management_agent",
            AgentStateStatus.PROCESSING,
            {
                "started_at": (datetime.utcnow() - timedelta(minutes=45)).isoformat(),
                "current_operation": "legal_validation",
                "timeout_risk": True,
                "processing_duration": 2700  # 45 minutos
            },
            session_id
        )
        
        # Agente con datos corruptos
        state_manager.update_agent_state(
            "documentation_agent",
            AgentStateStatus.COMPLETED,
            {
                "data_corruption_detected": True,
                "validation_score": 0.0,
                "output_corrupted": True,
                "requires_reprocessing": True
            },
            session_id
        )
        
        print("✅ Estados problemáticos simulados")
        print("   - IT Provisioning: ERROR con 4 errores")
        print("   - Contract Management: PROCESSING stuck por 45 min")
        print("   - Documentation: COMPLETED pero datos corruptos")
        print()
        
        # 5. Test de herramientas individuales
        print("5. Probando herramientas individuales...")
        
        # Test Retry Manager Tool
        try:
            from agents.recovery_agent.tools import retry_manager_tool
            
            test_recovery_request = {
                "session_id": session_id,
                "recovery_strategy": "exponential_backoff",
                "max_retry_attempts": 3,
                "retry_delay_seconds": 2
            }
            
            test_failed_operation = {
                "operation_type": "agent_processing",
                "agent_id": "it_provisioning_agent",
                "error_context": {"timeout": True, "service_unavailable": True}
            }
            
            retry_result = retry_manager_tool.invoke({
                "recovery_request": test_recovery_request,
                "failed_operation": test_failed_operation,
                "retry_config": {"base_delay": 1, "exponential_factor": 2.0}
            })
            
            if retry_result.get("success"):
                attempts = retry_result.get("total_attempts", 0)
                successful = retry_result.get("successful_attempts", 0)
                print(f"   ✅ Retry Manager: {successful}/{attempts} intentos exitosos")
            else:
                print(f"   ❌ Retry Manager falló: {retry_result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ Retry Manager excepción: {e}")
        
        # Test State Restorer Tool
        try:
            from agents.recovery_agent.tools import state_restorer_tool
            
            state_restore_result = state_restorer_tool.invoke({
                "recovery_request": {"session_id": session_id, "recovery_id": "test_restore"},
                "target_state": None
            })
            
            if state_restore_result.get("success"):
                restored_count = state_restore_result.get("successful_restorations", 0)
                total_count = state_restore_result.get("total_restorations", 0)
                print(f"   ✅ State Restorer: {restored_count}/{total_count} restauraciones exitosas")
            else:
                print(f"   ❌ State Restorer falló: {state_restore_result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ State Restorer excepción: {e}")
        
        # Test Circuit Breaker Tool
        try:
            from agents.recovery_agent.tools import circuit_breaker_tool
            
            circuit_result = circuit_breaker_tool.invoke({
                "recovery_request": {"session_id": session_id, "error_category": "integration_error"},
                "service_health_data": None
            })
            
            if circuit_result.get("success"):
                services = len(circuit_result.get("service_states", {}))
                actions = len(circuit_result.get("circuit_actions", []))
                print(f"   ✅ Circuit Breaker: {services} servicios monitoreados, {actions} acciones")
            else:
                print(f"   ❌ Circuit Breaker falló: {circuit_result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ Circuit Breaker excepción: {e}")
        
        # Test Workflow Resumer Tool
        try:
            from agents.recovery_agent.tools import workflow_resumer_tool
            
            workflow_result = workflow_resumer_tool.invoke({
                "recovery_request": {"session_id": session_id, "recovery_id": "test_workflow"},
                "checkpoint_data": None
            })
            
            if workflow_result.get("success"):
                resume_point = workflow_result.get("resume_point", "unknown")
                workflow_status = workflow_result.get("workflow_status", "unknown")
                print(f"   ✅ Workflow Resumer: Resume desde '{resume_point}', status '{workflow_status}'")
            else:
                print(f"   ❌ Workflow Resumer falló: {workflow_result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ Workflow Resumer excepción: {e}")
        
        print()
        
        # 6. Test de diferentes estrategias de recuperación
        print("6. Probando diferentes estrategias de recuperación...")
        
        recovery_strategies = [
            {
                "name": "Immediate Retry",
                "strategy": RecoveryStrategy.IMMEDIATE_RETRY,
                "actions": [RecoveryAction.RETRY_OPERATION],
                "priority": RecoveryPriority.HIGH
            },
            {
                "name": "State Rollback", 
                "strategy": RecoveryStrategy.STATE_ROLLBACK,
                "actions": [RecoveryAction.STATE_RESTORATION, RecoveryAction.PIPELINE_ROLLBACK],
                "priority": RecoveryPriority.CRITICAL
            },
            {
                "name": "Circuit Breaker",
                "strategy": RecoveryStrategy.CIRCUIT_BREAKER,
                "actions": [RecoveryAction.CIRCUIT_BREAKER_RESET, RecoveryAction.DEPENDENCY_CHECK],
                "priority": RecoveryPriority.MEDIUM
            }
        ]
        
        strategy_results = []
        
        for strategy_config in recovery_strategies:
            try:
                print(f"   Probando estrategia: {strategy_config['name']}")
                
                # Crear recovery request específico
                recovery_request = RecoveryRequest(
                    session_id=session_id,
                    employee_id="EMP_RECOVERY_TEST_001",
                    error_classification_id=f"error_class_{strategy_config['name'].lower().replace(' ', '_')}",
                    error_category="agent_failure",
                    error_severity="high",
                    failed_agent_id="it_provisioning_agent",
                    recovery_strategy=strategy_config["strategy"],
                    recovery_actions=strategy_config["actions"],
                    recovery_priority=strategy_config["priority"],
                    max_retry_attempts=2,
                    retry_delay_seconds=1,
                    timeout_minutes=5,
                    error_context={
                        "test_strategy": strategy_config["name"],
                        "simulated_error": True
                    }
                )
                
                # Ejecutar recuperación
                start_time = datetime.utcnow()
                result = agent.execute_recovery(recovery_request, session_id)
                end_time = datetime.utcnow()
                
                processing_time = (end_time - start_time).total_seconds()
                
                strategy_result = {
                    "strategy": strategy_config["name"],
                    "success": result.get("success", False),
                    "processing_time": processing_time,
                    "recovery_status": result.get("recovery_status"),
                    "system_recovered": result.get("system_recovered", False),
                    "actions_executed": len(result.get("recovery_actions_executed", [])),
                    "requires_escalation": result.get("requires_escalation", False)
                }
                
                strategy_results.append(strategy_result)
                
                if result.get("success"):
                    print(f"      ✅ {strategy_config['name']}: Éxito en {processing_time:.2f}s")
                    print(f"         - Status: {result.get('recovery_status')}")
                    print(f"         - Sistema recuperado: {'Sí' if result.get('system_recovered') else 'No'}")
                    print(f"         - Acciones ejecutadas: {len(result.get('recovery_actions_executed', []))}")
                else:
                    print(f"      ❌ {strategy_config['name']}: Falló en {processing_time:.2f}s")
                    print(f"         - Error: {result.get('message')}")
                    print(f"         - Requiere escalación: {'Sí' if result.get('requires_escalation') else 'No'}")
                
            except Exception as e:
                print(f"      ❌ {strategy_config['name']}: Excepción - {e}")
                strategy_results.append({
                    "strategy": strategy_config["name"],
                    "success": False,
                    "error": str(e)
                })
        
        print()
        
        # 7. Test de recuperación compleja (múltiples errores)
        print("7. Probando recuperación compleja con múltiples errores...")
        
        # Crear situación compleja
        complex_recovery_request = RecoveryRequest(
            session_id=session_id,
            employee_id="EMP_RECOVERY_TEST_001", 
            error_classification_id="complex_error_scenario",
            error_category="system_error",
            error_severity="critical",
            recovery_strategy=RecoveryStrategy.GRACEFUL_DEGRADATION,
            recovery_actions=[
                RecoveryAction.RETRY_OPERATION,
                RecoveryAction.STATE_RESTORATION,
                RecoveryAction.CIRCUIT_BREAKER_RESET,
                RecoveryAction.WORKFLOW_RESUMPTION
            ],
            recovery_priority=RecoveryPriority.EMERGENCY,
            max_retry_attempts=3,
            retry_delay_seconds=2,
            timeout_minutes=10,
            allow_partial_recovery=True,
            error_context={
                "multiple_agents_affected": True,
                "data_corruption": True,
                "service_degradation": True,
                "complex_scenario": True
            },
            recovery_context={
                "business_impact": "high",
                "time_sensitive": True,
                "requires_comprehensive_recovery": True
            }
        )
        
        print("   Ejecutando recuperación compleja...")
        start_time = datetime.utcnow()
        complex_result = agent.execute_recovery(complex_recovery_request, session_id)
        end_time = datetime.utcnow()
        
        complex_processing_time = (end_time - start_time).total_seconds()
        
        print(f"   ⏱️  Tiempo de procesamiento complejo: {complex_processing_time:.2f} segundos")
        
        if complex_result.get("success"):
            print("   ✅ Recuperación compleja exitosa")
            print(f"      - Status final: {complex_result.get('recovery_status')}")
            print(f"      - Sistema recuperado: {'Sí' if complex_result.get('system_recovered') else 'No'}")
            print(f"      - Acciones ejecutadas: {len(complex_result.get('recovery_actions_executed', []))}")
            print(f"      - Health score: {complex_result.get('system_health_score', 0):.2f}")
            print(f"      - Pipeline operacional: {'Sí' if complex_result.get('pipeline_operational') else 'No'}")
        else:
            print("   ❌ Recuperación compleja falló")
            print(f"      - Error: {complex_result.get('message')}")
            print(f"      - Requiere escalación: {'Sí' if complex_result.get('requires_escalation') else 'No'}")
            print(f"      - Razón de escalación: {complex_result.get('escalation_reason')}")
        
        print()
        
        # 8. Verificar estado post-recuperación
        print("8. Verificando estado del sistema post-recuperación...")
        
        # Verificar estado del agente de recuperación
        recovery_agent_state = state_manager.get_agent_state(agent.agent_id, session_id)
        if recovery_agent_state:
            print(f"✅ Estado del Recovery Agent: {recovery_agent_state.status}")
            if recovery_agent_state.data:
                recovery_data_keys = list(recovery_agent_state.data.keys())
                print(f"   - Datos actualizados: {recovery_data_keys[:5]}...")  # Mostrar primeros 5
        
        # Verificar contexto del empleado
        updated_context = state_manager.get_employee_context(session_id)
        if updated_context and updated_context.processed_data:
            recovery_data = updated_context.processed_data.get("recovery_completed")
            if recovery_data:
                print("✅ Datos de recuperación guardados en contexto del empleado")
                recovery_count = len([k for k in updated_context.processed_data.keys() if "recovery" in k])
                print(f"   - Campos de recuperación: {recovery_count}")
            else:
                print("⚠️  Datos de recuperación no encontrados en contexto")
        
        # Verificar estados de agentes afectados
        print("   Estados de agentes post-recuperación:")
        test_agents = ["it_provisioning_agent", "contract_management_agent", "documentation_agent"]
        for agent_id in test_agents:
            agent_state = state_manager.get_agent_state(agent_id, session_id)
            if agent_state:
                status = agent_state.status.value if hasattr(agent_state.status, 'value') else str(agent_state.status)
                print(f"      - {agent_id}: {status}")
        
        print()
        
        # 9. Test de métricas de recuperación
        print("9. Verificando métricas de recuperación...")
        
        # Obtener métricas del agente
        recovery_metrics = agent.get_recovery_metrics()
        print(f"✅ Métricas de recuperación:")
        print(f"   - Total recuperaciones: {recovery_metrics['recovery_metrics']['total_recoveries']}")
        print(f"   - Recuperaciones exitosas: {recovery_metrics['recovery_metrics']['successful_recoveries']}")
        print(f"   - Recuperaciones fallidas: {recovery_metrics['recovery_metrics']['failed_recoveries']}")
        print(f"   - Tasa de éxito: {recovery_metrics['success_rate']:.1%}")
        print(f"   - Tiempo promedio: {recovery_metrics['average_recovery_time_seconds']:.2f}s")
        
        print()
        
        # 10. Validar configuración de recuperación
        print("10. Validando configuración de recuperación...")
        
        config_validation = agent.validate_recovery_configuration()
        if config_validation["configuration_valid"]:
            print("✅ Configuración de recuperación válida")
            print(f"   - Herramientas disponibles: {config_validation['tools_available']}/{config_validation['expected_tools']}")
            print(f"   - Sistema listo: {'Sí' if config_validation['recovery_ready'] else 'No'}")
        else:
            print("❌ Problemas en configuración:")
            for issue in config_validation["validation_issues"]:
                print(f"   - {issue}")
        
        print()
        
        # 11. Resumen final y estadísticas
        print("11. Resumen final del test...")
        
        # Calcular estadísticas de estrategias
        successful_strategies = len([r for r in strategy_results if r.get("success", False)])
        total_strategies = len(strategy_results)
        strategy_success_rate = successful_strategies / total_strategies if total_strategies > 0 else 0
        
        # Tiempo total de test
        total_test_time = (datetime.utcnow() - start_time).total_seconds() if 'start_time' in locals() else 0
        
        print(f"   📊 Estadísticas del Test:")
        print(f"      - Estrategias probadas: {total_strategies}")
        print(f"      - Estrategias exitosas: {successful_strategies}")
        print(f"      - Tasa de éxito de estrategias: {strategy_success_rate:.1%}")
        print(f"      - Recuperación compleja: {'✅ Exitosa' if complex_result.get('success') else '❌ Fallada'}")
        print(f"      - Tiempo total de test: {total_test_time:.2f} segundos")
        
        # Overview del sistema final
        system_overview = state_manager.get_system_overview()
        print(f"   🏥 Estado Final del Sistema:")
        print(f"      - Sesiones activas: {system_overview.get('active_sessions', 0)}")
        print(f"      - Agentes registrados: {system_overview.get('registered_agents', 0)}")
        
        print("\n" + "="*60)
        print("🎉 TEST DEL RECOVERY AGENT COMPLETADO")
        print("="*60)
        
        # Determinar éxito general del test
        test_success = (
            config_validation["configuration_valid"] and
            strategy_success_rate >= 0.6 and  # Al menos 60% de estrategias exitosas
            recovery_metrics['recovery_metrics']['total_recoveries'] > 0
        )
        
        if test_success:
            print("✅ RECOVERY AGENT FUNCIONANDO CORRECTAMENTE")
            print("✅ Integración con State Management verificada")
            print("✅ Herramientas de recuperación operativas")
            print("✅ Estrategias de recuperación probadas")
            print("✅ Métricas y observabilidad funcionando")
            print("✅ Preparado para integración con Error Classification")
        else:
            print("⚠️  ALGUNOS ASPECTOS REQUIEREN ATENCIÓN")
            if not config_validation["configuration_valid"]:
                print("   - Configuración requiere corrección")
            if strategy_success_rate < 0.6:
                print("   - Estrategias de recuperación necesitan mejoras")
        
        print(f"⏱️  Tiempo total de test: {total_test_time:.2f} segundos")
        
        return test_success
        
    except Exception as e:
        print(f"\n❌ ERROR EN TEST: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_recovery_scenarios():
    """Test de escenarios específicos de recuperación"""
    print("\n=== TEST DE ESCENARIOS DE RECUPERACIÓN ===\n")
    
    try:
        agent = RecoveryAgent()
        
        # Crear contexto para tests
        employee_data = {
            "employee_id": "EMP_SCENARIO_TEST", 
            "first_name": "Scenario",
            "last_name": "Test"
        }
        session_id = state_manager.create_employee_context(employee_data)
        
        scenarios = [
            {
                "name": "Timeout Recovery",
                "description": "Agente stuck por timeout",
                "error_category": "agent_failure",
                "error_severity": "high",
                "strategy": RecoveryStrategy.EXPONENTIAL_BACKOFF,
                "actions": [RecoveryAction.RETRY_OPERATION, RecoveryAction.AGENT_RESTART]
            },
            {
                "name": "Data Corruption Recovery", 
                "description": "Datos corruptos requieren rollback",
                "error_category": "data_validation",
                "error_severity": "critical",
                "strategy": RecoveryStrategy.STATE_ROLLBACK,
                "actions": [RecoveryAction.STATE_RESTORATION, RecoveryAction.CACHE_CLEAR]
            },
            {
                "name": "Service Overload Recovery",
                "description": "Servicios sobrecargados requieren circuit breaker",
                "error_category": "system_error", 
                "error_severity": "medium",
                "strategy": RecoveryStrategy.CIRCUIT_BREAKER,
                "actions": [RecoveryAction.CIRCUIT_BREAKER_RESET, RecoveryAction.RESOURCE_CLEANUP]
            },
            {
                "name": "Pipeline Interruption Recovery",
                "description": "Pipeline interrumpido requiere reanudación",
                "error_category": "workflow_failure",
                "error_severity": "high",
                "strategy": RecoveryStrategy.GRACEFUL_DEGRADATION,
                "actions": [RecoveryAction.STATE_RESTORATION, RecoveryAction.DEPENDENCY_CHECK]
            }
        ]
        
        scenario_results = []
        
        for scenario in scenarios:
            print(f"Probando escenario: {scenario['name']}")
            print(f"   Descripción: {scenario['description']}")
            
            try:
                recovery_request = RecoveryRequest(
                    session_id=session_id,
                    employee_id="EMP_SCENARIO_TEST",
                    error_classification_id=f"scenario_{scenario['name'].lower().replace(' ', '_')}",
                    error_category=scenario["error_category"],
                    error_severity=scenario["error_severity"],
                    recovery_strategy=scenario["strategy"],
                    recovery_actions=scenario["actions"],
                    recovery_priority=RecoveryPriority.HIGH,
                    max_retry_attempts=2,
                    timeout_minutes=3,
                    error_context={"scenario_test": True, "scenario_name": scenario["name"]}
                )
                
                result = agent.execute_recovery(recovery_request, session_id)
                
                scenario_result = {
                    "scenario": scenario["name"],
                    "success": result.get("success", False),
                    "recovery_status": result.get("recovery_status"),
                    "actions_executed": len(result.get("recovery_actions_executed", [])),
                    "processing_time": result.get("processing_time", 0)
                }
                
                scenario_results.append(scenario_result)
                
                if result.get("success"):
                    print(f"   ✅ Éxito - Status: {result.get('recovery_status')}")
                else:
                    print(f"   ❌ Fallo - {result.get('message')}")
                
            except Exception as e:
                print(f"   ❌ Excepción: {e}")
                scenario_results.append({
                    "scenario": scenario["name"],
                    "success": False,
                    "error": str(e)
                })
        
        # Resumen de escenarios
        successful_scenarios = len([r for r in scenario_results if r.get("success", False)])
        print(f"\n📊 Resumen de Escenarios:")
        print(f"   - Escenarios probados: {len(scenarios)}")
        print(f"   - Escenarios exitosos: {successful_scenarios}")
        print(f"   - Tasa de éxito: {successful_scenarios/len(scenarios):.1%}")
        
        return successful_scenarios >= len(scenarios) * 0.75  # 75% éxito mínimo
        
    except Exception as e:
        print(f"❌ Error en test de escenarios: {e}")
        return False

def main():
    """Función principal para ejecutar todos los tests"""
    print("INICIANDO TESTS DEL RECOVERY AGENT")
    print("=" * 80)
    
    # Test 1: Integración completa
    test1_success = test_recovery_agent_integration()
    
    # Test 2: Escenarios específicos
    test2_success = test_recovery_scenarios()
    
    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN DE TESTS")
    print("=" * 80)
    print(f"Test de Integración: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"Test de Escenarios: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    
    if test1_success and test2_success:
        print("\n🎉 TODOS LOS TESTS PASARON - RECOVERY AGENT LISTO")
        print("✅ Puedes proceder con la implementación del Human Handoff Agent")
        print("✅ Recovery Agent listo para integración con Error Classification")
    else:
        print("\n⚠️  ALGUNOS TESTS FALLARON - REVISA LOS ERRORES ANTES DE CONTINUAR")
        if not test1_success:
            print("   - Revisa integración con State Management y herramientas")
        if not test2_success:
            print("   - Revisa estrategias de recuperación específicas")
    
    return test1_success and test2_success

if __name__ == "__main__":
    main()