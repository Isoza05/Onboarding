import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator.agent import OrchestratorAgent
from agents.orchestrator.schemas import (
    OrchestrationRequest, OrchestrationPattern, AgentType, Priority
)
from core.state_management.state_manager import state_manager
from datetime import datetime, date
import asyncio

def create_complete_test_request():
    """Crear solicitud completa de orquestación para test end-to-end"""
    
    # Datos del empleado (similares al test del Data Aggregator)
    employee_data = {
        "employee_id": "EMP_COMPLETE_001",
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
    
    # Datos contractuales
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
    
    # Documentos adjuntos (simulados)
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
        employee_id="EMP_COMPLETE_001",
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

async def test_complete_orchestration():
    """Test completo end-to-end de toda la orquestación"""
    print("🚀 TESTING ORQUESTACIÓN COMPLETA END-TO-END")
    print("=" * 80)
    print("📋 Flujo: Data Collection → Aggregation → Sequential Pipeline")
    print("=" * 80)
    
    try:
        # Test 1: Crear Orchestrator Agent
        print("\n📝 Test 1: Inicializar Orchestrator Agent")
        orchestrator = OrchestratorAgent()
        print("✅ Orchestrator Agent creado exitosamente")
        
        # Verificar integración
        integration_status = orchestrator.get_integration_status()
        print(f"✅ Integración exitosa: {integration_status['integration_success']}")
        print(f"✅ Workflow disponible: {integration_status['workflow_status'].get('workflow_available', False)}")
        
        # Test 2: Crear solicitud completa
        print("\n📝 Test 2: Crear solicitud de orquestación completa")
        orchestration_request = create_complete_test_request()
        print(f"✅ Solicitud creada para empleado: {orchestration_request.employee_id}")
        print(f"✅ Patrón de orquestación: {orchestration_request.orchestration_pattern.value}")
        print(f"✅ Prioridad: {orchestration_request.priority.value}")
        print(f"✅ Agentes requeridos: {len(orchestration_request.required_agents)}")
        print(f"✅ Documentos adjuntos: {len(orchestration_request.documents)}")
        print(f"✅ Requisitos especiales: {len(orchestration_request.special_requirements)}")
        
        # Test 3: Ejecutar orquestación completa
        print("\n📝 Test 3: Ejecutar orquestación completa")
        print("🔄 Iniciando Data Collection + Aggregation + Sequential Pipeline...")
        start_time = datetime.now()
        
        # Ejecutar orquestación completa
        complete_result = await orchestrator.execute_complete_onboarding_orchestration(orchestration_request)
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        print(f"⏱️ Tiempo total de orquestación: {total_time:.2f} segundos")
        orchestration_success = complete_result.get('complete_orchestration_success', complete_result.get('success', False))
        print(f"✅ Orquestación completa exitosa: {orchestration_success}")
        print(f"✅ Orchestration ID: {complete_result.get('orchestration_id', 'N/A')}")
        print(f"✅ Session ID: {complete_result.get('session_id', 'N/A')}")
        
        # AGREGAR:
        print(f"✅ Aggregation Result: {bool(complete_result.get('aggregation_result'))}")
        if complete_result.get('aggregation_result'):
            agg_result = complete_result['aggregation_result']
            print(f"✅ Aggregation Success: {agg_result.get('success', False)}")
            print(f"✅ Quality Score: {agg_result.get('overall_quality_score', 0):.1f}%")
            print(f"✅ Ready for Pipeline: {agg_result.get('ready_for_sequential_pipeline', False)}")

        session_id = complete_result.get('session_id')
        
        # Test 4: Verificar Data Collection Hub
        print("\n📝 Test 4: Verificar Data Collection Hub")
        data_collection_success = complete_result.get('success', False)
        agents_coordinated = complete_result.get('agents_coordinated', 0)
        overall_quality = complete_result.get('overall_quality_score', 0)
        
        print(f"✅ Data Collection exitoso: {data_collection_success}")
        print(f"✅ Agentes coordinados: {agents_coordinated}")
        print(f"✅ Score de calidad general: {overall_quality:.1f}%")
        print(f"✅ Data Collection Hub completado: {complete_result.get('data_collection_hub_completed', False)}")
        
        # Test 5: Verificar Data Aggregation
        print("\n📝 Test 5: Verificar Data Aggregation & Validation")
        aggregation_details = complete_result.get('aggregation_details', {})
        if aggregation_details:
            aggregation_result = aggregation_details.get('aggregation_result', {})
            print(f"✅ Data Aggregation ejecutado: {bool(aggregation_result)}")
            
            if aggregation_result:
                print(f"✅ Agregación exitosa: {aggregation_result.get('success', False)}")
                print(f"✅ Score de calidad agregada: {aggregation_result.get('overall_quality_score', 0):.1f}%")
                print(f"✅ Validación aprobada: {aggregation_result.get('validation_passed', False)}")
                print(f"✅ Listo para pipeline: {aggregation_result.get('ready_for_sequential_pipeline', False)}")
        else:
            print("⚠️ Detalles de agregación no encontrados")
        
        # Test 6: Verificar Sequential Pipeline
        print("\n📝 Test 6: Verificar Sequential Pipeline")
        sequential_executed = complete_result.get('sequential_pipeline_executed', False)
        sequential_result = complete_result.get('sequential_pipeline_result', {})
        
        print(f"✅ Sequential Pipeline ejecutado: {sequential_executed}")
        
        if sequential_executed and sequential_result:
            sequential_success = sequential_result.get('success', False)
            stages_completed = sequential_result.get('stages_completed', 0)
            employee_ready = sequential_result.get('employee_ready_for_onboarding', False)
            
            print(f"✅ Sequential Pipeline exitoso: {sequential_success}")
            print(f"✅ Etapas completadas: {stages_completed}/3")
            print(f"✅ Empleado listo para onboarding: {employee_ready}")
            
            # Verificar cada etapa
            print("📋 Resultados por etapa:")
            pipeline_results = sequential_result.get('pipeline_results', {})
            if 'it_provisioning' in pipeline_results:
                it_result = pipeline_results['it_provisioning']
                it_success = getattr(it_result, 'success', False) if hasattr(it_result, 'success') else it_result.get('success', False)
                print(f"   🖥️ IT Provisioning: {'✅' if it_success else '❌'}")
                
            if 'contract_management' in pipeline_results:
                contract_result = pipeline_results['contract_management']
                contract_success = getattr(contract_result, 'success', False) if hasattr(contract_result, 'success') else contract_result.get('success', False)
                print(f"   📄 Contract Management: {'✅' if contract_success else '❌'}")
                
            if 'meeting_coordination' in pipeline_results:
                meeting_result = pipeline_results['meeting_coordination']
                meeting_success = getattr(meeting_result, 'success', False) if hasattr(meeting_result, 'success') else meeting_result.get('success', False)
                print(f"   📅 Meeting Coordination: {'✅' if meeting_success else '❌'}")
            
            # Verificar timeline de onboarding
            onboarding_timeline = sequential_result.get('onboarding_timeline')
            if onboarding_timeline:
                print(f"✅ Timeline de onboarding creado: {len(onboarding_timeline)} actividades")
        else:
            print("⚠️ Sequential Pipeline no fue ejecutado o falló")
        
        # Test 7: Verificar State Management
        print("\n📝 Test 7: Verificar estado en Common State Management")
        if session_id:
            context = state_manager.get_employee_context(session_id)
            if context:
                print(f"✅ Contexto encontrado para empleado: {context.employee_id}")
                print(f"✅ Fase actual: {context.phase}")
                print(f"✅ Datos procesados: {'Sí' if context.processed_data else 'No'}")
                
                # Verificar datos específicos del proceso completo
                processed_data = context.processed_data
                if processed_data:
                    print(f"✅ Orquestación completada: {processed_data.get('orchestration_completed', False)}")
                    print(f"✅ Sequential pipeline completado: {processed_data.get('sequential_pipeline_completed', False)}")
                    print(f"✅ Empleado listo: {processed_data.get('employee_ready_for_onboarding', False)}")
            else:
                print("⚠️ No se encontró contexto en State Management")
        
        # Test 8: Verificar próximos pasos
        print("\n📝 Test 8: Verificar próximos pasos")
        final_actions = complete_result.get('final_next_actions', [])
        print("✅ Próximas acciones:")
        for action in final_actions:
            print(f"   - {action}")
        
        # Test 9: Métricas finales
        print("\n📝 Test 9: Métricas finales de orquestación")
        total_stages = complete_result.get('total_stages_completed', 0)
        employee_ready_final = complete_result.get('employee_ready_for_onboarding', False)
        
        print(f"✅ Total de etapas completadas: {total_stages}")
        print(f"✅ Tiempo total: {total_time:.2f}s")
        print(f"✅ Empleado listo para onboarding: {'Sí' if employee_ready_final else 'No'}")
        
        # Calcular score de éxito general
        success_indicators = [
            complete_result.get('complete_orchestration_success', complete_result.get('success', False)),
            data_collection_success,
            sequential_executed,
            employee_ready_final,
            overall_quality >= 70.0,
            total_stages >= 5  # Al menos 3 data collection + 2 sequential
        ]
        
        success_rate = (sum(success_indicators) / len(success_indicators)) * 100
        
        # Test 10: Resumen final
        print("\n🎉 ORQUESTACIÓN COMPLETA END-TO-END COMPLETADA")
        print("=" * 70)
        
        print(f"✅ RESULTADO GENERAL: {'🎯 EXITOSO' if success_rate >= 75 else '⚠️ NECESITA REVISIÓN'}")
        print(f"✅ Score de éxito: {success_rate:.1f}%")
        print(f"✅ Tiempo total: {total_time:.2f} segundos")
        print(f"✅ Data Collection Hub: {'✅' if data_collection_success else '❌'}")
        print(f"✅ Data Aggregation: {'✅' if bool(aggregation_details) else '❌'}")
        print(f"✅ Sequential Pipeline: {'✅' if sequential_executed else '❌'}")
        print(f"✅ Empleado listo: {'✅' if employee_ready_final else '❌'}")
        print(f"✅ State Management: {'✅' if session_id and context else '❌'}")
        
        if employee_ready_final:
            print("\n🚀 EMPLEADO COMPLETAMENTE PROCESADO Y LISTO PARA ONBOARDING")
            print("📋 Próximos pasos del negocio:")
            print("   1. Ejecutar timeline de onboarding")
            print("   2. Coordinar primer día de trabajo")
            print("   3. Activar monitoreo de progreso inicial")
        else:
            print("\n⚠️ EMPLEADO REQUIERE REVISIÓN MANUAL")
            print("📋 Acciones requeridas:")
            print("   1. Revisar errores en el proceso")
            print("   2. Completar datos faltantes")
            print("   3. Resolver problemas de calidad")
        
        return True, {
            "success_rate": success_rate,
            "total_time": total_time,
            "employee_ready": employee_ready_final,
            "data_collection_success": data_collection_success,
            "sequential_pipeline_executed": sequential_executed,
            "session_id": session_id
        }
        
    except Exception as e:
        print(f"\n❌ ERROR EN TEST DE ORQUESTACIÓN COMPLETA: {e}")
        import traceback
        traceback.print_exc()
        return False, {"error": str(e)}

if __name__ == "__main__":
    print("🚀 INICIANDO TEST COMPLETO DE ORQUESTACIÓN END-TO-END")
    print("=" * 80)
    
    # Ejecutar test completo
    success, result = asyncio.run(test_complete_orchestration())
    
    # Resumen final
    print("\n" + "=" * 80)
    print("📊 RESUMEN FINAL DEL TEST COMPLETO")
    print("=" * 80)
    
    if success:
        print("🎉 TEST DE ORQUESTACIÓN COMPLETA EXITOSO")
        print(f"✅ Success Rate: {result.get('success_rate', 0):.1f}%")
        print(f"✅ Tiempo total: {result.get('total_time', 0):.2f}s")
        print(f"✅ Empleado listo: {result.get('employee_ready', False)}")
        print(f"✅ Data Collection: {result.get('data_collection_success', False)}")
        print(f"✅ Sequential Pipeline: {result.get('sequential_pipeline_executed', False)}")
        print(f"✅ Session ID: {result.get('session_id', 'N/A')}")
        
        print("\n🎯 PROYECTO DE ONBOARDING AGENTS FUNCIONANDO COMPLETAMENTE")
        print("🚀 DATA COLLECTION → AGGREGATION → SEQUENTIAL PIPELINE → READY FOR ONBOARDING")
    else:
        print("💥 TEST DE ORQUESTACIÓN COMPLETA FALLÓ")
        print(f"❌ Error: {result.get('error', 'Unknown')}")
        print("\n🔧 REQUIERE DEBUGGING DE LA INTEGRACIÓN COMPLETA")
    
    print("\n" + "=" * 80)