import asyncio
from datetime import datetime
from loguru import logger

# Imports del sistema refactorizado
from agents.orchestrator.agent import OrchestratorAgent
from agents.orchestrator.schemas import OrchestrationRequest, AgentType, OrchestrationPattern
from shared.models import Priority

def create_sample_orchestration_request():
    """Crear request de prueba sin pytest fixture"""
    return OrchestrationRequest(
        employee_id="EMP_REFACT_001",
        session_id=None,  # Que se auto-genere
        employee_data={
            "employee_id": "EMP_REFACT_001",
            "first_name": "Carlos",
            "middle_name": "Eduardo", 
            "last_name": "Morales",
            "mothers_lastname": "Castro",
            "id_card": "1-9876-5432",
            "email": "carlos.morales@empresa.com",
            "phone": "+506-8888-9999",
            "position": "Senior Software Architect",
            "department": "Technology",
            "university": "Tecnológico de Costa Rica",
            "career": "Ingeniería en Sistemas"
        },
        contract_data={
            "salary": 75000,
            "currency": "USD",
            "employment_type": "full_time",
            "start_date": "2025-01-15",
            "contract_duration": "indefinite",
            "benefits_package": "complete"
        },
        documents=[
            {"type": "cv", "filename": "carlos_morales_cv.pdf"},
            {"type": "id_copy", "filename": "cedula_carlos.pdf"},
            {"type": "diploma", "filename": "titulo_ingenieria.pdf"}
        ],
        orchestration_pattern=OrchestrationPattern.CONCURRENT_DATA_COLLECTION,
        priority=Priority.HIGH,
        special_requirements=["security_clearance", "equipment_laptop"],
        required_agents=[
            AgentType.INITIAL_DATA_COLLECTION,
            AgentType.CONFIRMATION_DATA,
            AgentType.DOCUMENTATION
        ]
    )

async def test_simplified_architecture_status():
    """Test 1: Verificar que la arquitectura simplificada está funcionando"""
    logger.info("=" * 60)
    logger.info("TEST 1: ARQUITECTURA SIMPLIFICADA STATUS")
    logger.info("=" * 60)
    
    orchestrator_agent = OrchestratorAgent()
    
    # Test de integración simplificado
    integration_result = await orchestrator_agent.test_full_integration()
    
    assert integration_result["orchestrator_integration"] == "success_simplified"
    assert integration_result["architecture_version"] == "simplified_2.0"
    assert integration_result["ready_for_orchestration"] is True
    
    logger.info(f"✅ Arquitectura simplificada funcionando: {integration_result['ready_for_orchestration']}")
    logger.info(f"✅ Workflow connectivity: {integration_result['workflow_connectivity']}")
    logger.info(f"✅ Tools available: {integration_result['tools_available']}")
    
    return integration_result

async def test_data_collection_workflow_simplified():
    """Test 2: Data Collection Workflow con arquitectura simplificada"""
    logger.info("=" * 60)
    logger.info("TEST 2: DATA COLLECTION WORKFLOW SIMPLIFICADO")  
    logger.info("=" * 60)
    
    orchestrator_agent = OrchestratorAgent()
    sample_orchestration_request = create_sample_orchestration_request()
    
    # Ejecutar Data Collection simplificado
    result = await orchestrator_agent.orchestrate_onboarding_process(
        sample_orchestration_request
    )
    
    # Verificaciones críticas de la refactorización
    assert result["success"] is True, f"Data Collection falló: {result.get('errors', [])}"
    assert result["session_id"] is not None, "❌ PROBLEMA #1: Session ID se perdió"
    assert result["session_id"] != "", "❌ Session ID vacío"
    
    # Verificar que tenemos resultados de agentes
    agent_results = result.get("agent_results", {})
    assert len(agent_results) >= 3, f"❌ Esperaba 3 agentes, obtuve {len(agent_results)}"
    
    # Verificar agregación
    aggregation_result = result.get("aggregation_result", {})
    assert aggregation_result.get("success", False), "❌ Agregación falló"
    
    # Verificar quality score
    data_quality_score = result.get("data_quality_score", 0.0)
    assert data_quality_score > 0, f"❌ Quality score es 0: {data_quality_score}"
    
    # Verificar preparación para Sequential Pipeline
    sequential_ready = result.get("ready_for_sequential_execution", False)
    
    logger.info(f"✅ Session ID creado y preservado: {result['session_id']}")
    logger.info(f"✅ Agentes ejecutados: {len(agent_results)}/3")
    logger.info(f"✅ Score de calidad: {data_quality_score:.1f}%")
    logger.info(f"✅ Sequential Pipeline ready: {sequential_ready}")
    
    return result

async def test_sequential_pipeline_simplified():
    """Test 3: Sequential Pipeline con arquitectura simplificada"""
    logger.info("=" * 60)
    logger.info("TEST 3: SEQUENTIAL PIPELINE SIMPLIFICADO")
    logger.info("=" * 60)
    
    orchestrator_agent = OrchestratorAgent()
    
    # Datos de prueba para Sequential Pipeline
    sequential_request_data = {
        "employee_id": "EMP_REFACT_001",
        "session_id": "session_test_refact_001", 
        "orchestration_id": "orch_simple_test_001",
        "consolidated_data": {
            "aggregated_employee_data": {
                "employee_id": "EMP_REFACT_001",
                "first_name": "Carlos",
                "last_name": "Morales",
                "email": "carlos.morales@empresa.com",
                "position": "Senior Software Architect"
            },
            "data_quality_metrics": {
                "overall_quality": 61.1,
                "aggregation_success": True
            }
        },
        "aggregation_result": {
            "success": True,
            "overall_quality_score": 61.1,
            "ready_for_sequential_pipeline": True
        },
        "data_quality_score": 61.1
    }
    
    # Ejecutar Sequential Pipeline simplificado
    pipeline_result = await orchestrator_agent.execute_sequential_pipeline(
        sequential_request_data
    )
    
    # Verificaciones críticas
    assert pipeline_result["success"] is True, f"❌ PROBLEMA #2: Sequential Pipeline falló: {pipeline_result.get('errors', [])}"
    assert pipeline_result["session_id"] == "session_test_refact_001", "❌ Session ID se perdió en Sequential Pipeline"
    
    # Verificar stages completadas
    stages_completed = pipeline_result.get("stages_completed", 0)
    assert stages_completed >= 2, f"❌ PROBLEMA #3: Solo {stages_completed}/3 stages completadas"
    
    # Verificar employee ready
    employee_ready = pipeline_result.get("employee_ready_for_onboarding", False)
    
    logger.info(f"✅ Sequential Pipeline ejecutado: {pipeline_result['success']}")
    logger.info(f"✅ Session ID preservado: {pipeline_result['session_id']}")
    logger.info(f"✅ Etapas completadas: {stages_completed}/3")
    logger.info(f"✅ Empleado listo para onboarding: {employee_ready}")
    
    return pipeline_result

async def test_complete_orchestration_flow_simplified():
    """Test 4: Flujo completo con arquitectura simplificada"""
    logger.info("=" * 60)
    logger.info("TEST 4: FLUJO COMPLETO SIMPLIFICADO")
    logger.info("=" * 60)
    
    orchestrator_agent = OrchestratorAgent()
    sample_orchestration_request = create_sample_orchestration_request()
    
    # Ejecutar orquestación completa
    complete_result = await orchestrator_agent.execute_complete_onboarding_orchestration(
        sample_orchestration_request
    )
    
    # Verificaciones del flujo completo
    assert complete_result["success"] is True, f"Orquestación completa falló: {complete_result.get('errors', [])}"
    assert complete_result["session_id"] is not None, "Session ID se perdió en flujo completo"
    assert complete_result["architecture_version"] == "simplified_2.0", "Arquitectura no es la simplificada"
    
    # Verificar que ambas fases se ejecutaron
    assert complete_result.get("sequential_pipeline_executed", False), "Sequential Pipeline no se ejecutó"
    assert complete_result.get("complete_orchestration_success", False), "Orquestación completa no fue exitosa"
    
    # Verificar employee ready
    employee_ready = complete_result.get("employee_ready_for_onboarding", False)
    total_stages = complete_result.get("total_stages_completed", 0)
    
    logger.info(f"✅ Orquestación completa exitosa: {complete_result['complete_orchestration_success']}")
    logger.info(f"✅ Sequential Pipeline ejecutado: {complete_result['sequential_pipeline_executed']}")
    logger.info(f"✅ Total de stages completadas: {total_stages}")
    logger.info(f"✅ Empleado listo para onboarding: {employee_ready}")
    logger.info(f"✅ Arquitectura version: {complete_result['architecture_version']}")
    
    return complete_result

async def run_refactoring_tests():
    """Ejecutar todos los tests de refactorización"""
    logger.info("🚀 INICIANDO TESTS DE ARQUITECTURA REFACTORIZADA")
    logger.info("=" * 80)
    
    try:
        # TEST 1: Arquitectura simplificada
        test1_result = await test_simplified_architecture_status()
        
        # TEST 2: Data Collection simplificado
        test2_result = await test_data_collection_workflow_simplified()
        
        # TEST 3: Sequential Pipeline simplificado
        test3_result = await test_sequential_pipeline_simplified()
        
        # TEST 4: Flujo completo simplificado
        test4_result = await test_complete_orchestration_flow_simplified()
        
        logger.info("=" * 80)
        logger.info("🎉 TODOS LOS TESTS DE REFACTORIZACIÓN COMPLETADOS EXITOSAMENTE")
        logger.info("=" * 80)
        logger.info("✅ PROBLEMAS RESUELTOS:")
        logger.info("   - Session ID se preserva correctamente")
        logger.info("   - Sequential Pipeline se ejecuta exitosamente")
        logger.info("   - Datos se propagan correctamente")
        logger.info("   - Arquitectura simplificada funciona")
        logger.info("=" * 80)
        
        # Resumen final
        logger.info("📊 RESUMEN DE RESULTADOS:")
        logger.info(f"   - Test 1 (Arquitectura): {'✅ PASS' if test1_result['ready_for_orchestration'] else '❌ FAIL'}")
        logger.info(f"   - Test 2 (Data Collection): {'✅ PASS' if test2_result['success'] else '❌ FAIL'}")
        logger.info(f"   - Test 3 (Sequential Pipeline): {'✅ PASS' if test3_result['success'] else '❌ FAIL'}")
        logger.info(f"   - Test 4 (Flujo Completo): {'✅ PASS' if test4_result['success'] else '❌ FAIL'}")
        
        return True
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ TEST DE REFACTORIZACIÓN FALLÓ: {e}")
        logger.error("=" * 80)
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Ejecutar tests
    success = asyncio.run(run_refactoring_tests())
    
    if success:
        print("🎉 REFACTORIZACIÓN EXITOSA - TODOS LOS TESTS PASARON")
    else:
        print("❌ REFACTORIZACIÓN FALLÓ - REVISAR LOGS")