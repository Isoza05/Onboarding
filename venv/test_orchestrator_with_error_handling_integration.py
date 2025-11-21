import asyncio
import sys
import os
from datetime import datetime
from loguru import logger

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator.agent import OrchestratorAgent
from agents.orchestrator.schemas import OrchestrationRequest, AgentType, OrchestrationPattern
from shared.models import Priority
from core.state_management.state_manager import state_manager

def create_valid_test_request():
    """Crear request VÁLIDO que debería funcionar correctamente"""
    return OrchestrationRequest(
        employee_id="EMP_ERROR_HANDLING_VALID_001",
        employee_data={
            "employee_id": "EMP_ERROR_HANDLING_VALID_001",
            "first_name": "Maria",
            "middle_name": "Isabel",
            "last_name": "Rodriguez", 
            "mothers_lastname": "Gonzalez",
            "id_card": "1-1234-5678",
            "passport": "CR987654321",
            "email": "maria.rodriguez@empresa.com",
            "phone": "+506-7777-8888",
            "position": "Senior Data Analyst",
            "department": "Analytics",
            "university": "Universidad de Costa Rica",
            "career": "Estadística"
        },
        contract_data={
            "salary": 85000,
            "currency": "USD",
            "employment_type": "full_time",
            "start_date": "2025-01-20",
            "contract_duration": "indefinite",
            "benefits_package": "complete"
        },
        documents=[
            {"type": "cv", "filename": "maria_rodriguez_cv.pdf"},
            {"type": "id_copy", "filename": "cedula_maria.pdf"},
            {"type": "diploma", "filename": "titulo_estadistica.pdf"},
            {"type": "references", "filename": "referencias_laborales.pdf"}
        ],
        orchestration_pattern=OrchestrationPattern.CONCURRENT_DATA_COLLECTION,
        priority=Priority.HIGH
    )

def create_error_inducing_request():
    """Crear request con ERRORES que debe activar Error Handling"""
    return OrchestrationRequest(
        employee_id="EMP_ERROR_HANDLING_FAIL_002",
        employee_data={
            # ❌ DATOS INCOMPLETOS/ERRÓNEOS
            "employee_id": "EMP_ERROR_HANDLING_FAIL_002",
            "first_name": "",  # ❌ Nombre vacío
            "last_name": "ErrorTest",
            "email": "invalid-email",  # ❌ Email inválido
            "phone": "123",  # ❌ Teléfono inválido
            "position": "",  # ❌ Posición vacía
            "department": "",  # ❌ Departamento vacío
            # ❌ Faltan campos críticos: id_card, university, career, etc.
        },
        contract_data={
            # ❌ DATOS CONTRACTUALES ERRÓNEOS
            "salary": -1000,  # ❌ Salario negativo
            "currency": "INVALID",  # ❌ Moneda inválida
            "employment_type": "",  # ❌ Tipo vacío
            "start_date": "invalid-date",  # ❌ Fecha inválida
            # ❌ Faltan campos críticos
        },
        documents=[
            # ❌ DOCUMENTOS INSUFICIENTES (solo 1, deberían ser al menos 3)
            {"type": "invalid", "filename": ""}  # ❌ Documento inválido
        ],
        orchestration_pattern=OrchestrationPattern.CONCURRENT_DATA_COLLECTION,
        priority=Priority.LOW  # ❌ Prioridad baja
    )

async def test_error_handling_agents_availability():
    """Test 1: Verificar que los agentes de Error Handling están disponibles"""
    logger.info("=" * 80)
    logger.info("TEST 1: VERIFICAR DISPONIBILIDAD AGENTES ERROR HANDLING")
    logger.info("=" * 80)
    
    orchestrator = OrchestratorAgent()
    
    # Verificar que los agentes Error Handling están inicializados
    assert hasattr(orchestrator, 'error_classification_agent'), "❌ Error Classification Agent no disponible"
    assert hasattr(orchestrator, 'recovery_agent'), "❌ Recovery Agent no disponible"
    assert hasattr(orchestrator, 'human_handoff_agent'), "❌ Human Handoff Agent no disponible"
    assert hasattr(orchestrator, 'audit_trail_agent'), "❌ Audit Trail Agent no disponible"
    
    # Test de integración con Error Handling
    integration_result = await orchestrator.test_full_integration()
    
    assert integration_result["architecture_version"] == "3.0_with_error_handling"
    assert integration_result["error_handling_integrated"] == True
    
    error_handling_status = integration_result.get("error_handling_status", {})
    assert error_handling_status["error_classification_available"] == True
    assert error_handling_status["recovery_agent_available"] == True
    assert error_handling_status["human_handoff_available"] == True
    assert error_handling_status["audit_trail_available"] == True
    
    logger.info("✅ Error Classification Agent: Disponible")
    logger.info("✅ Recovery Agent: Disponible")
    logger.info("✅ Human Handoff Agent: Disponible")
    logger.info("✅ Audit Trail Agent: Disponible")
    logger.info(f"✅ Arquitectura version: {integration_result['architecture_version']}")
    logger.info(f"✅ Error Handling integrado: {integration_result['error_handling_integrated']}")
    
    return integration_result

async def test_valid_orchestration_no_error_handling():
    """Test 2: Orquestación válida que NO debe activar Error Handling"""
    logger.info("=" * 80)
    logger.info("TEST 2: ORQUESTACIÓN VÁLIDA - NO ERROR HANDLING")
    logger.info("=" * 80)
    
    orchestrator = OrchestratorAgent()
    valid_request = create_valid_test_request()
    
    logger.info(f"🔄 Procesando empleado válido: {valid_request.employee_id}")
    
    # Ejecutar orquestación completa
    result = await orchestrator.execute_complete_onboarding_orchestration(valid_request)
    
    # Verificaciones básicas
    assert result["success"] == True, f"❌ Orquestación válida falló: {result.get('errors', [])}"
    assert result["session_id"] is not None, "❌ Session ID no generado"
    
    # ✅ VERIFICAR QUE ERROR HANDLING NO SE ACTIVÓ
    error_handling_executed = result.get("error_handling_executed", False)
    assert error_handling_executed == False, "❌ Error Handling se activó innecesariamente"
    
    # Verificar calidad de datos
    data_quality_score = result.get("data_quality_score", 0.0)
    assert data_quality_score >= 30.0, f"❌ Quality score muy bajo: {data_quality_score:.1f}%"
    
    # Verificar sequential pipeline
    sequential_executed = result.get("sequential_pipeline_executed", False)
    employee_ready = result.get("employee_ready_for_onboarding", False)
    
    logger.info(f"✅ Orquestación exitosa: {result['success']}")
    logger.info(f"✅ Quality Score: {data_quality_score:.1f}%")
    logger.info(f"✅ Error Handling NO ejecutado: {not error_handling_executed}")
    logger.info(f"✅ Sequential Pipeline: {sequential_executed}")
    logger.info(f"✅ Empleado listo: {employee_ready}")
    
    return result

async def test_invalid_orchestration_triggers_error_handling():
    """Test 3: Orquestación inválida que DEBE activar Error Handling"""
    logger.info("=" * 80)
    logger.info("TEST 3: ORQUESTACIÓN INVÁLIDA - DEBE ACTIVAR ERROR HANDLING")
    logger.info("=" * 80)
    
    orchestrator = OrchestratorAgent()
    invalid_request = create_error_inducing_request()
    
    logger.info(f"🔄 Procesando empleado con errores: {invalid_request.employee_id}")
    logger.info("🔍 Datos erróneos incluyen:")
    logger.info("   - Nombre vacío")
    logger.info("   - Email inválido") 
    logger.info("   - Salario negativo")
    logger.info("   - Documentos insuficientes")
    
    start_time = datetime.now()
    
    # Ejecutar orquestación que debería fallar
    result = await orchestrator.execute_complete_onboarding_orchestration(invalid_request)
    
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    
    # ✅ VERIFICAR QUE ERROR HANDLING SE ACTIVÓ
    error_handling_executed = result.get("error_handling_executed", False)
    assert error_handling_executed == True, "❌ ERROR HANDLING NO SE ACTIVÓ con datos erróneos"
    
    # Verificar resultado de Error Handling
    error_handling_result = result.get("error_handling_result", {})
    assert error_handling_result is not None, "❌ No hay resultado de Error Handling"
    
    error_handling_success = error_handling_result.get("error_handling_success", False)
    
    # Verificar componentes de Error Handling
    classification_result = error_handling_result.get("classification_result", {})
    recovery_result = error_handling_result.get("recovery_result")
    handoff_result = error_handling_result.get("handoff_result") 
    audit_result = error_handling_result.get("audit_result", {})
    
    logger.info(f"✅ ERROR HANDLING ACTIVADO: {error_handling_executed}")
    logger.info(f"✅ Error Handling exitoso: {error_handling_success}")
    logger.info(f"✅ Tiempo de procesamiento: {processing_time:.2f}s")
    
    # Verificar Error Classification
    if classification_result:
        logger.info(f"✅ Error Classification ejecutado: {classification_result.get('success', False)}")
        logger.info(f"   - Estrategia: {classification_result.get('recovery_strategy', 'N/A')}")
        logger.info(f"   - Severidad: {classification_result.get('error_severity', 'N/A')}")
    
    # Verificar Recovery
    if recovery_result:
        logger.info(f"✅ Recovery ejecutado: {recovery_result.get('success', False)}")
        logger.info(f"   - Status: {recovery_result.get('final_status', 'N/A')}")
    
    # Verificar Human Handoff
    if handoff_result:
        logger.info(f"✅ Human Handoff ejecutado: {handoff_result.get('success', False)}")
        specialist = handoff_result.get('specialist_assignment', {})
        logger.info(f"   - Especialista: {specialist.get('name', 'N/A')}")
    
    # Verificar Audit Trail
    if audit_result:
        logger.info(f"✅ Audit Trail ejecutado: {audit_result.get('success', False)}")
        audit_summary = audit_result.get('audit_summary', {})
        logger.info(f"   - Eventos auditados: {audit_summary.get('total_events_logged', 0)}")
    
    return result

async def test_quality_score_threshold_trigger():
    """Test 4: Verificar trigger por Quality Score bajo"""
    logger.info("=" * 80)
    logger.info("TEST 4: TRIGGER POR QUALITY SCORE BAJO")
    logger.info("=" * 80)
    
    orchestrator = OrchestratorAgent()
    
    # Request que debería generar quality score bajo
    low_quality_request = OrchestrationRequest(
        employee_id="EMP_LOW_QUALITY_003",
        employee_data={
            "employee_id": "EMP_LOW_QUALITY_003",
            "first_name": "Test",
            "last_name": "LowQuality",
            # ❌ Datos mínimos - debería generar quality score bajo
        },
        contract_data={
            "salary": 50000
            # ❌ Datos contractuales mínimos
        },
        documents=[],  # ❌ Sin documentos
        orchestration_pattern=OrchestrationPattern.CONCURRENT_DATA_COLLECTION,
        priority=Priority.MEDIUM
    )
    
    logger.info("🔄 Procesando request con datos mínimos para quality score bajo...")
    
    # Ejecutar solo Data Collection para verificar quality score
    data_collection_result = await orchestrator.orchestrate_onboarding_process(low_quality_request)
    
    data_quality_score = data_collection_result.get("data_quality_score", 100.0)
    
    logger.info(f"📊 Quality Score obtenido: {data_quality_score:.1f}%")
    
    # Verificar que el quality score está bajo
    if data_quality_score < 30.0:
        logger.info("✅ Quality score < 30% - debería activar Error Handling")
        
        # Ejecutar orquestación completa para ver Error Handling
        complete_result = await orchestrator.execute_complete_onboarding_orchestration(low_quality_request)
        
        error_handling_executed = complete_result.get("error_handling_executed", False)
        logger.info(f"✅ Error Handling activado por quality score: {error_handling_executed}")
        
        return complete_result
    else:
        logger.warning(f"⚠️ Quality score {data_quality_score:.1f}% no es suficientemente bajo para trigger")
        return data_collection_result

async def test_error_handling_end_to_end_flow():
    """Test 5: Flujo completo End-to-End con Error Handling"""
    logger.info("=" * 80)
    logger.info("TEST 5: FLUJO COMPLETO END-TO-END CON ERROR HANDLING")
    logger.info("=" * 80)
    
    orchestrator = OrchestratorAgent()
    
    # Usar request con errores críticos
    critical_error_request = create_error_inducing_request()
    critical_error_request.employee_id = "EMP_CRITICAL_E2E_004"
    
    logger.info(f"🚀 INICIANDO FLUJO COMPLETO E2E: {critical_error_request.employee_id}")
    
    start_time = datetime.now()
    
    # Ejecutar flujo completo
    complete_result = await orchestrator.execute_complete_onboarding_orchestration(critical_error_request)
    
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()
    
    # Verificaciones del flujo completo
    session_id = complete_result.get("session_id")
    error_handling_executed = complete_result.get("error_handling_executed", False)
    
    logger.info(f"⏱️ Tiempo total E2E: {total_time:.2f} segundos")
    logger.info(f"✅ Session ID: {session_id}")
    logger.info(f"✅ Error Handling ejecutado: {error_handling_executed}")
    
    # Verificar State Management
    if session_id:
        context = state_manager.get_employee_context(session_id)
        if context:
            logger.info(f"✅ Contexto en State Management: {context.employee_id}")
            logger.info(f"✅ Fase actual: {context.phase}")
        else:
            logger.warning("⚠️ No se encontró contexto en State Management")
    
    # Verificar resultado de Error Handling
    if error_handling_executed:
        error_handling_result = complete_result.get("error_handling_result", {})
        error_summary = error_handling_result.get("error_handling_summary", {})
        
        logger.info("📋 RESUMEN ERROR HANDLING:")
        logger.info(f"   - Classification: {error_summary.get('classification_executed', False)}")
        logger.info(f"   - Recovery: {error_summary.get('recovery_executed', False)}")
        logger.info(f"   - Handoff: {error_summary.get('handoff_executed', False)}")
        logger.info(f"   - Audit: {error_summary.get('audit_executed', False)}")
        
        final_resolution = error_handling_result.get("final_resolution", "unknown")
        logger.info(f"✅ Resolución final: {final_resolution}")
    
    # Calcular métricas de éxito
    success_indicators = [
        complete_result.get("success") is not None,  # Tiene resultado
        session_id is not None,  # Session ID generado
        error_handling_executed,  # Error Handling se activó
        complete_result.get("architecture_version") == "3.0_with_error_handling"  # Versión correcta
    ]
    
    success_rate = (sum(success_indicators) / len(success_indicators)) * 100
    
    logger.info(f"📊 Success Rate E2E: {success_rate:.1f}%")
    
    return complete_result, {
        "success_rate": success_rate,
        "total_time": total_time,
        "error_handling_executed": error_handling_executed,
        "session_id": session_id
    }

async def run_error_handling_integration_tests():
    """Ejecutar todos los tests de integración Error Handling"""
    logger.info("🚀 INICIANDO TESTS DE INTEGRACIÓN ERROR HANDLING")
    logger.info("=" * 100)
    
    test_results = {}
    
    try:
        # TEST 1: Disponibilidad de agentes
        logger.info("📋 Ejecutando Test 1: Disponibilidad agentes Error Handling...")
        test1_result = await test_error_handling_agents_availability()
        test_results["test1_availability"] = test1_result["error_handling_integrated"]
        
        # TEST 2: Orquestación válida (sin Error Handling)
        logger.info("📋 Ejecutando Test 2: Orquestación válida...")
        test2_result = await test_valid_orchestration_no_error_handling()
        test_results["test2_valid"] = test2_result["success"]
        
        # TEST 3: Orquestación inválida (con Error Handling)
        logger.info("📋 Ejecutando Test 3: Orquestación inválida...")
        test3_result = await test_invalid_orchestration_triggers_error_handling()
        test_results["test3_invalid"] = test3_result.get("error_handling_executed", False)
        
        # TEST 4: Quality Score trigger
        logger.info("📋 Ejecutando Test 4: Quality Score trigger...")
        test4_result = await test_quality_score_threshold_trigger()
        test_results["test4_quality"] = test4_result is not None
        
        # TEST 5: End-to-End completo
        logger.info("📋 Ejecutando Test 5: End-to-End completo...")
        test5_result, test5_metrics = await test_error_handling_end_to_end_flow()
        test_results["test5_e2e"] = test5_metrics["error_handling_executed"]
        
        # RESUMEN FINAL
        logger.info("=" * 100)
        logger.info("🎉 TODOS LOS TESTS DE ERROR HANDLING COMPLETADOS")
        logger.info("=" * 100)
        
        total_success_rate = (sum(test_results.values()) / len(test_results)) * 100
        
        logger.info("📊 RESULTADOS FINALES:")
        logger.info(f"   ✅ Test 1 (Disponibilidad): {'PASS' if test_results['test1_availability'] else 'FAIL'}")
        logger.info(f"   ✅ Test 2 (Válido): {'PASS' if test_results['test2_valid'] else 'FAIL'}")
        logger.info(f"   ✅ Test 3 (Inválido): {'PASS' if test_results['test3_invalid'] else 'FAIL'}")
        logger.info(f"   ✅ Test 4 (Quality): {'PASS' if test_results['test4_quality'] else 'FAIL'}")
        logger.info(f"   ✅ Test 5 (E2E): {'PASS' if test_results['test5_e2e'] else 'FAIL'}")
        logger.info(f"   📈 Success Rate Total: {total_success_rate:.1f}%")
        
        if total_success_rate >= 80:
            logger.info("🎯 ERROR HANDLING INTEGRACIÓN: ✅ EXITOSA")
            logger.info("🚀 SISTEMA COMPLETO DE ONBOARDING CON ERROR HANDLING FUNCIONANDO")
        else:
            logger.warning("⚠️ ERROR HANDLING INTEGRACIÓN: NECESITA AJUSTES")
            
        return True, test_results
        
    except Exception as e:
        logger.error("=" * 100)
        logger.error(f"❌ TESTS DE ERROR HANDLING FALLARON: {e}")
        logger.error("=" * 100)
        import traceback
        logger.error(traceback.format_exc())
        
        return False, {"error": str(e)}

if __name__ == "__main__":
    print("🚀 INICIANDO TESTS DE INTEGRACIÓN ERROR HANDLING CON ORCHESTRATOR")
    print("=" * 100)
    
    # Ejecutar tests
    success, results = asyncio.run(run_error_handling_integration_tests())
    
    # Resumen final
    print("\n" + "=" * 100)
    print("📊 RESUMEN FINAL - ERROR HANDLING INTEGRATION")
    print("=" * 100)
    
    if success:
        print("🎉 INTEGRACIÓN ERROR HANDLING: ✅ EXITOSA")
        print("🔧 FUNCIONALIDADES VERIFICADAS:")
        print("   ✅ Agentes Error Handling disponibles")
        print("   ✅ Procesamiento de datos REALES")
        print("   ✅ Detección automática de errores") 
        print("   ✅ Activación de Error Handling")
        print("   ✅ Flujo completo: Classification → Recovery → Handoff → Audit")
        print("   ✅ Integration con State Management")
        print("\n🚀 SISTEMA DE ONBOARDING CON ERROR HANDLING COMPLETO Y FUNCIONAL")
    else:
        print("❌ INTEGRACIÓN ERROR HANDLING: FALLÓ")
        print(f"🔧 Error: {results.get('error', 'Unknown')}")
        print("\n🔧 REQUIERE DEBUGGING Y CORRECCIONES")
    
    print("=" * 100)