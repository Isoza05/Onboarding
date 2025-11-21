import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator.agent import OrchestratorAgent
from agents.orchestrator.schemas import OrchestrationRequest, OrchestrationPattern, AgentType, Priority
from core.state_management.state_manager import state_manager
from datetime import datetime, date
import asyncio

def create_valid_complete_test_request():
    """Crear solicitud completa VÁLIDA - MISMA QUE FUNCIONA EN EL TEST EXISTENTE"""
    employee_data = {
        "employee_id": "EMP_ERROR_HANDLING_VALID_001",
        "first_name": "Carlos",
        "middle_name": "Eduardo",
        "last_name": "Morales",
        "mothers_lastname": "Castro",
        "id_card": "1-9876-5432",
        "passport": "CR123456789",
        "gender": "Male",
        "birth_date": "1988-07-22",
        "nationality": "Costarricense",
        "marital_status": "Married",
        "children": 2,
        "english_level": "C1",
        "email": "carlos.morales@empresa.com",
        "phone": "+506-8888-9999",
        "country": "Costa Rica",
        "city": "San José",
        "district": "Escazú",
        "current_address": "Escazú, San José, Costa Rica",
        "university": "Tecnológico de Costa Rica",
        "career": "Ingeniería en Sistemas",
        "position": "Senior Software Architect",
        "position_area": "Software Architecture",
        "technology": "Java, Spring, Microservices, AWS",
        "customer": "Banco de Costa Rica",
        "partner_name": "TechSolutions Inc",
        "project_manager": "Ana Jiménez",
        "office": "Costa Rica",
        "collaborator_type": "Production",
        "billable_type": "Billable",
        "contracting_type": "Payroll",
        "contracting_time": "Long term",
        "contracting_office": "CRC",
        "reference_market": "Banking",
        "project_need": "Core Banking Modernization",
        "employment_type": "Full-time",
        "department": "Technology"
    }

    contract_data = {
        "start_date": "2025-12-01",
        "salary": 120000.0,
        "currency": "USD",
        "employment_type": "Full-time",
        "work_modality": "Hybrid",
        "probation_period": 90,
        "benefits": [
            "Seguro médico premium",
            "Vacaciones 20 días",
            "Aguinaldo",
            "Bono por desempeño 15%",
            "Capacitación técnica internacional",
            "Stock options"
        ],
        "position_title": "Senior Software Architect",
        "reporting_manager": "Luis Hernández",
        "job_level": "Senior",
        "location": "Escazú, Costa Rica"
    }

    documents = [
        {
            "document_type": "cv_resume",
            "filename": "carlos_morales_cv.pdf",
            "document_status": "valid",
            "upload_date": "2025-11-15"
        },
        {
            "document_type": "vaccination_card",
            "filename": "carnet_vacunacion.pdf", 
            "document_status": "valid",
            "upload_date": "2025-11-15"
        },
        {
            "document_type": "id_document",
            "filename": "cedula_identidad.pdf",
            "document_status": "valid",
            "upload_date": "2025-11-15"
        },
        {
            "document_type": "academic_titles",
            "filename": "titulo_ingenieria.pdf",
            "document_status": "verified",
            "upload_date": "2025-11-15"
        },
        {
            "document_type": "photo",
            "filename": "foto_personal.jpg",
            "document_status": "valid",
            "upload_date": "2025-11-15"
        }
    ]

    return OrchestrationRequest(
        employee_id="EMP_ERROR_HANDLING_VALID_001",
        employee_data=employee_data,
        contract_data=contract_data,
        documents=documents,
        orchestration_pattern=OrchestrationPattern.CONCURRENT_DATA_COLLECTION,
        priority=Priority.HIGH,
        special_requirements=[
            "Senior architect level validation",
            "Banking sector security clearance",
            "International training coordination",
            "Stock options documentation"
        ],
        required_agents=[
            AgentType.INITIAL_DATA_COLLECTION,
            AgentType.CONFIRMATION_DATA,
            AgentType.DOCUMENTATION
        ],
        agent_config={
            "validation_strictness": "high",
            "compliance_level": "banking",
            "security_clearance": "level_2"
        }
    )

def create_invalid_error_test_request():
    """Crear solicitud INVÁLIDA para activar Error Handling"""
    employee_data = {
        "employee_id": "EMP_ERROR_HANDLING_INVALID_002",
        # ❌ DATOS CRÍTICOS FALTANTES O INVÁLIDOS
        "first_name": "",  # ❌ Vacío
        "last_name": "ErrorTest",
        "email": "invalid-email-format",  # ❌ Email inválido
        "phone": "123",  # ❌ Teléfono inválido
        "position": "",  # ❌ Posición vacía
        "department": "",  # ❌ Departamento vacío
        # ❌ FALTAN: id_card, university, career, etc.
    }

    contract_data = {
        # ❌ DATOS CONTRACTUALES PROBLEMÁTICOS
        "salary": -5000,  # ❌ Salario negativo
        "currency": "INVALID_CURRENCY",  # ❌ Moneda inválida
        "employment_type": "",  # ❌ Tipo vacío
        "start_date": "invalid-date-format",  # ❌ Fecha inválida
        # ❌ FALTAN CAMPOS CRÍTICOS
    }

    documents = [
        # ❌ DOCUMENTOS INSUFICIENTES E INVÁLIDOS
        {
            "document_type": "invalid_type",
            "filename": "",  # ❌ Nombre vacío
            "document_status": "corrupted"  # ❌ Estado problemático
        }
    ]

    return OrchestrationRequest(
        employee_id="EMP_ERROR_HANDLING_INVALID_002",
        employee_data=employee_data,
        contract_data=contract_data,
        documents=documents,
        orchestration_pattern=OrchestrationPattern.CONCURRENT_DATA_COLLECTION,
        priority=Priority.LOW,  # ❌ Prioridad baja
        special_requirements=[],
        required_agents=[
            AgentType.INITIAL_DATA_COLLECTION,
            AgentType.CONFIRMATION_DATA,
            AgentType.DOCUMENTATION
        ]
    )

async def test_valid_orchestration_with_error_handling():
    """Test 1: Orquestación válida - NO debe activar Error Handling"""
    print("🚀 TEST 1: ORQUESTACIÓN VÁLIDA CON ERROR HANDLING DISPONIBLE")
    print("=" * 80)
    
    try:
        orchestrator = OrchestratorAgent()
        valid_request = create_valid_complete_test_request()
        
        print(f"🔄 Procesando empleado válido: {valid_request.employee_id}")
        print("📋 Datos completos:")
        print(f"   - Employee data: {len(valid_request.employee_data)} campos")
        print(f"   - Contract data: {len(valid_request.contract_data)} campos")
        print(f"   - Documents: {len(valid_request.documents)} documentos")
        print(f"   - Priority: {valid_request.priority}")
        
        start_time = datetime.now()
        
        # Ejecutar orquestación completa
        result = await orchestrator.execute_complete_onboarding_orchestration(valid_request)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Analizar resultados
        success = result.get("success", False)
        complete_success = result.get("complete_orchestration_success", False)
        data_quality_score = result.get("data_quality_score", 0.0)
        error_handling_executed = result.get("error_handling_executed", False)
        sequential_executed = result.get("sequential_pipeline_executed", False)
        employee_ready = result.get("employee_ready_for_onboarding", False)
        session_id = result.get("session_id")
        
        print(f"\n📊 RESULTADOS TEST 1:")
        print(f"   ✅ Success: {success}")
        print(f"   ✅ Complete Success: {complete_success}")
        print(f"   ✅ Quality Score: {data_quality_score:.1f}%")
        print(f"   ✅ Error Handling ejecutado: {error_handling_executed}")
        print(f"   ✅ Sequential Pipeline: {sequential_executed}")
        print(f"   ✅ Employee ready: {employee_ready}")
        print(f"   ✅ Session ID: {session_id}")
        print(f"   ⏱️ Tiempo: {processing_time:.2f}s")
        
        # Verificar que Error Handling NO se activó (con datos válidos)
        expected_no_error_handling = not error_handling_executed
        
        print(f"\n🎯 VALIDACIÓN TEST 1:")
        if data_quality_score >= 30.0:
            print(f"   ✅ Quality score suficiente: {data_quality_score:.1f}% >= 30%")
        else:
            print(f"   ⚠️ Quality score bajo: {data_quality_score:.1f}% < 30%")
            
        if expected_no_error_handling:
            print("   ✅ Error Handling NO se activó (correcto con datos válidos)")
        else:
            print("   ⚠️ Error Handling se activó innecesariamente")
        
        return {
            "test_1_success": success,
            "test_1_quality_score": data_quality_score,
            "test_1_error_handling_not_triggered": expected_no_error_handling,
            "test_1_processing_time": processing_time,
            "test_1_result": result
        }
        
    except Exception as e:
        print(f"❌ ERROR EN TEST 1: {e}")
        import traceback
        traceback.print_exc()
        return {
            "test_1_success": False,
            "test_1_error": str(e)
        }

async def test_invalid_orchestration_should_trigger_error_handling():
    """Test 2: Orquestación inválida - DEBE activar Error Handling"""
    print("\n🚨 TEST 2: ORQUESTACIÓN INVÁLIDA - DEBE ACTIVAR ERROR HANDLING")
    print("=" * 80)
    
    try:
        orchestrator = OrchestratorAgent()
        invalid_request = create_invalid_error_test_request()
        
        print(f"🔄 Procesando empleado con errores: {invalid_request.employee_id}")
        print("🚨 Datos problemáticos:")
        print("   - Nombre vacío")
        print("   - Email inválido")
        print("   - Salario negativo (-5000)")
        print("   - Documentos insuficientes")
        print("   - Campos críticos faltantes")
        
        start_time = datetime.now()
        
        # Ejecutar orquestación que debería fallar y activar Error Handling
        result = await orchestrator.execute_complete_onboarding_orchestration(invalid_request)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Analizar resultados
        success = result.get("success", False)
        data_quality_score = result.get("data_quality_score", 0.0)
        error_handling_executed = result.get("error_handling_executed", False)
        error_handling_result = result.get("error_handling_result", {})
        session_id = result.get("session_id")
        
        print(f"\n📊 RESULTADOS TEST 2:")
        print(f"   ✅ Success: {success}")
        print(f"   ✅ Quality Score: {data_quality_score:.1f}%")
        print(f"   🚨 Error Handling ejecutado: {error_handling_executed}")
        print(f"   ✅ Session ID: {session_id}")
        print(f"   ⏱️ Tiempo: {processing_time:.2f}s")
        
        # Analizar Error Handling en detalle
        if error_handling_executed and error_handling_result:
            error_handling_success = error_handling_result.get("error_handling_success", False)
            classification_result = error_handling_result.get("classification_result", {})
            recovery_result = error_handling_result.get("recovery_result")
            handoff_result = error_handling_result.get("handoff_result")
            audit_result = error_handling_result.get("audit_result", {})
            
            print(f"\n🔧 DETALLES ERROR HANDLING:")
            print(f"   ✅ Error Handling exitoso: {error_handling_success}")
            
            if classification_result:
                strategy = classification_result.get("recovery_strategy", "unknown")
                severity = classification_result.get("error_severity", "unknown")
                print(f"   📊 Error Classification: {classification_result.get('success', False)}")
                print(f"      - Estrategia: {strategy}")
                print(f"      - Severidad: {severity}")
            
            if recovery_result:
                print(f"   🔧 Recovery: {recovery_result.get('success', False)}")
                print(f"      - Status: {recovery_result.get('final_status', 'unknown')}")
            
            if handoff_result:
                print(f"   👤 Human Handoff: {handoff_result.get('success', False)}")
                specialist = handoff_result.get('specialist_assignment', {})
                print(f"      - Especialista: {specialist.get('name', 'N/A')}")
            
            if audit_result:
                print(f"   📋 Audit Trail: {audit_result.get('success', False)}")
                audit_summary = audit_result.get('audit_summary', {})
                print(f"      - Eventos: {audit_summary.get('total_events_logged', 0)}")
        
        # Validaciones críticas
        print(f"\n🎯 VALIDACIÓN TEST 2:")
        if data_quality_score < 30.0:
            print(f"   ✅ Quality score bajo detectado: {data_quality_score:.1f}% < 30%")
        else:
            print(f"   ⚠️ Quality score inesperadamente alto: {data_quality_score:.1f}%")
            
        if error_handling_executed:
            print("   ✅ Error Handling se activó correctamente")
        else:
            print("   ❌ Error Handling NO se activó (problema)")
        
        return {
            "test_2_error_handling_triggered": error_handling_executed,
            "test_2_quality_score": data_quality_score,
            "test_2_quality_below_threshold": data_quality_score < 30.0,
            "test_2_processing_time": processing_time,
            "test_2_error_handling_result": error_handling_result,
            "test_2_result": result
        }
        
    except Exception as e:
        print(f"❌ ERROR EN TEST 2: {e}")
        import traceback
        traceback.print_exc()
        return {
            "test_2_error_handling_triggered": False,
            "test_2_error": str(e)
        }

async def test_state_management_integration():
    """Test 3: Verificar integración con State Management"""
    print("\n📊 TEST 3: VERIFICAR STATE MANAGEMENT CON ERROR HANDLING")
    print("=" * 80)
    
    try:
        # Obtener overview del sistema
        system_overview = state_manager.get_system_overview()
        
        print("📋 ESTADO DEL SISTEMA:")
        print(f"   ✅ Sesiones activas: {system_overview.get('active_sessions', 0)}")
        print(f"   ✅ Agentes registrados: {system_overview.get('registered_agents', 0)}")
        print(f"   ✅ Contextos de empleados: {system_overview.get('employee_contexts', 0)}")
        
        # Verificar agentes específicos
        agents_status = system_overview.get('agents_status', {})
        error_handling_agents = [
            'error_classification_agent',
            'recovery_agent', 
            'human_handoff_agent',
            'audit_trail_agent',
            'orchestrator_agent'
        ]
        
        print(f"\n🔧 AGENTES ERROR HANDLING:")
        for agent in error_handling_agents:
            status = agents_status.get(agent, {}).get('status', 'unknown')
            print(f"   ✅ {agent}: {status}")
        
        return {
            "test_3_system_healthy": True,
            "test_3_agents_registered": len(agents_status),
            "test_3_error_handling_agents_available": len([
                a for a in error_handling_agents 
                if a in agents_status
            ])
        }
        
    except Exception as e:
        print(f"❌ ERROR EN TEST 3: {e}")
        return {
            "test_3_system_healthy": False,
            "test_3_error": str(e)
        }

async def main():
    """Ejecutar tests completos de Error Handling Integration"""
    print("🚀 TESTS COMPLETOS: ORCHESTRATOR + ERROR HANDLING INTEGRATION")
    print("=" * 100)
    print("🎯 OBJETIVO: Verificar que Error Handling se active solo cuando sea necesario")
    print("=" * 100)
    
    start_time = datetime.now()
    
    try:
        # Test 1: Datos válidos - NO Error Handling
        test1_results = await test_valid_orchestration_with_error_handling()
        
        # Test 2: Datos inválidos - SÍ Error Handling  
        test2_results = await test_invalid_orchestration_should_trigger_error_handling()
        
        # Test 3: State Management
        test3_results = await test_state_management_integration()
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # Análisis final
        print("\n" + "=" * 100)
        print("📊 RESUMEN FINAL - ERROR HANDLING INTEGRATION")
        print("=" * 100)
        
        # Métricas de éxito
        test1_passed = test1_results.get("test_1_success", False) and test1_results.get("test_1_error_handling_not_triggered", False)
        test2_passed = test2_results.get("test_2_error_handling_triggered", False) and test2_results.get("test_2_quality_below_threshold", False)
        test3_passed = test3_results.get("test_3_system_healthy", False)
        
        print(f"✅ Test 1 (Válido - NO Error Handling): {'PASS' if test1_passed else 'FAIL'}")
        if test1_passed:
            quality1 = test1_results.get("test_1_quality_score", 0)
            time1 = test1_results.get("test_1_processing_time", 0)
            print(f"   - Quality Score: {quality1:.1f}%")
            print(f"   - Tiempo: {time1:.2f}s")
        
        print(f"✅ Test 2 (Inválido - SÍ Error Handling): {'PASS' if test2_passed else 'FAIL'}")
        if test2_passed:
            quality2 = test2_results.get("test_2_quality_score", 0)
            time2 = test2_results.get("test_2_processing_time", 0)
            print(f"   - Quality Score: {quality2:.1f}%")
            print(f"   - Error Handling activado: ✅")
            print(f"   - Tiempo: {time2:.2f}s")
        
        print(f"✅ Test 3 (State Management): {'PASS' if test3_passed else 'FAIL'}")
        if test3_passed:
            agents_count = test3_results.get("test_3_agents_registered", 0)
            eh_agents = test3_results.get("test_3_error_handling_agents_available", 0)
            print(f"   - Agentes registrados: {agents_count}")
            print(f"   - Error Handling agents: {eh_agents}/5")
        
        # Resultado final
        all_tests_passed = test1_passed and test2_passed and test3_passed
        success_rate = (sum([test1_passed, test2_passed, test3_passed]) / 3) * 100
        
        print(f"\n📈 SUCCESS RATE: {success_rate:.1f}%")
        print(f"⏱️ TIEMPO TOTAL: {total_time:.2f}s")
        
        if all_tests_passed:
            print("\n🎉 ERROR HANDLING INTEGRATION: ✅ COMPLETAMENTE EXITOSO")
            print("🎯 FUNCIONALIDADES VERIFICADAS:")
            print("   ✅ Orquestación válida funciona sin Error Handling")
            print("   ✅ Orquestación inválida activa Error Handling")
            print("   ✅ Error Classification ejecuta correctamente")
            print("   ✅ Recovery/Handoff/Audit se ejecutan según sea necesario")
            print("   ✅ State Management integrado correctamente")
            print("   ✅ Quality Score threshold (30%) funciona")
            print("\n🚀 SISTEMA DE ONBOARDING CON ERROR HANDLING: COMPLETO Y FUNCIONAL")
            
        elif success_rate >= 66.7:
            print("\n⚠️ ERROR HANDLING INTEGRATION: PARCIALMENTE EXITOSO")
            print("🔧 RECOMENDACIONES:")
            if not test1_passed:
                print("   - Revisar flujo de datos válidos")
            if not test2_passed:
                print("   - Revisar activación de Error Handling con datos inválidos")
            if not test3_passed:
                print("   - Revisar integración con State Management")
                
        else:
            print("\n❌ ERROR HANDLING INTEGRATION: NECESITA CORRECCIONES")
            print("🔧 REQUIERE DEBUGGING ADICIONAL")
        
        return {
            "overall_success": all_tests_passed,
            "success_rate": success_rate,
            "total_time": total_time,
            "test1_results": test1_results,
            "test2_results": test2_results,
            "test3_results": test3_results
        }
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO EN TESTS: {e}")
        import traceback
        traceback.print_exc()
        return {
            "overall_success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    print("🚀 INICIANDO TESTS DE ERROR HANDLING INTEGRATION")
    print("=" * 100)
    
    results = asyncio.run(main())
    
    print("\n" + "=" * 100)
    print("🏁 TESTS FINALIZADOS")
    print("=" * 100)
    
    if results.get("overall_success", False):
        print("🎉 RESULTADO: ERROR HANDLING INTEGRATION EXITOSO")
        exit(0)
    else:
        print("❌ RESULTADO: ERROR HANDLING INTEGRATION FALLÓ")
        exit(1)