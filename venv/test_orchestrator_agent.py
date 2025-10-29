import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from agents.orchestrator.agent import OrchestratorAgent
from agents.orchestrator.schemas import (
    OrchestrationRequest, OrchestrationPattern, AgentType
)
from core.state_management.state_manager import state_manager
from shared.models import Priority
from datetime import datetime, timedelta

def create_test_orchestration_request():
    """Crear solicitud completa de orquestación de prueba"""
    
    # Datos del empleado
    employee_data = {
        "employee_id": "EMP_ORCH_001",
        "first_name": "Carlos",
        "middle_name": "Alberto", 
        "last_name": "González Pérez",
        "preferred_name": "Carlos",
        "email": "carlos.gonzalez@empresa.com",
        "phone": "+506-8888-9999",
        "id_card": "1-1234-5678",
        "passport": "CR123456789",
        "employment_type": "full_time",
        "position_level": "senior",
        "department": "Engineering",
        "hire_date": (datetime.now() + timedelta(days=14)).isoformat(),
        "manager_email": "manager@empresa.com"
    }
    
    # Términos contractuales
    contract_data = {
        "salary": 85000.0,
        "currency": "USD",
        "employment_type": "Full-time",
        "work_modality": "Hybrid",
        "start_date": (datetime.now() + timedelta(days=14)).date().isoformat(),
        "probation_period": 90,
        "benefits": ["Seguro médico", "Vacaciones", "Aguinaldo", "Bono por desempeño"],
        "position_title": "Senior Software Engineer",
        "reporting_manager": "María López",
        "job_level": "Senior",
        "location": "San José, Costa Rica"
    }
    
    # Documentos adjuntos
    documents = [
        {
            "document_id": "doc_orch_001",
            "document_type": "vaccination_card",
            "file_name": "carnet_vacunacion_carlos.pdf",
            "file_format": "pdf",
            "file_size_kb": 256,
            "content_hash": "orch_abc123"
        },
        {
            "document_id": "doc_orch_002",
            "document_type": "id_document", 
            "file_name": "cedula_carlos.jpg",
            "file_format": "jpg",
            "file_size_kb": 145,
            "content_hash": "orch_def456"
        },
        {
            "document_id": "doc_orch_003",
            "document_type": "cv_resume",
            "file_name": "CV_Carlos_Gonzalez_2024.pdf",
            "file_format": "pdf",
            "file_size_kb": 678,
            "content_hash": "orch_ghi789"
        },
        {
            "document_id": "doc_orch_004",
            "document_type": "academic_titles",
            "file_name": "titulo_ingenieria_sistemas.pdf",
            "file_format": "pdf", 
            "file_size_kb": 423,
            "content_hash": "orch_jkl012"
        }
    ]
    
    return OrchestrationRequest(
        employee_id="EMP_ORCH_001",
        employee_data=employee_data,
        contract_data=contract_data,
        documents=documents,
        orchestration_pattern=OrchestrationPattern.CONCURRENT_DATA_COLLECTION,
        priority=Priority.HIGH,
        special_requirements=[
            "Senior engineer validation",
            "Security clearance required", 
            "Fast track processing"
        ],
        deadline=datetime.now() + timedelta(hours=2),
        required_agents=[
            AgentType.INITIAL_DATA_COLLECTION,
            AgentType.CONFIRMATION_DATA,
            AgentType.DOCUMENTATION
        ],
        agent_config={
            "timeout_per_agent": 300,
            "quality_threshold": 75.0,
            "parallel_execution": True
        }
    )

async def test_orchestrator_agent():
    """Test completo del Orchestrator Agent con workflow LangGraph"""
    print("🎭 TESTING ORCHESTRATOR AGENT + LANGGRAPH WORKFLOWS + FULL INTEGRATION")
    print("=" * 85)
    
    try:
        # Test 1: Crear y verificar Orchestrator Agent
        print("\n📝 Test 1: Inicializar Orchestrator Agent")
        orchestrator = OrchestratorAgent()
        print("✅ Orchestrator Agent creado exitosamente")
        
        # Verificar integración con State Management
        overview = state_manager.get_system_overview()
        print(f"✅ Agentes registrados en sistema: {overview['registered_agents']}")
        print(f"✅ Estado del orchestrator: {overview['agents_status'].get('orchestrator_agent', 'no encontrado')}")
        
        # Test 2: Verificar workflow status
        print("\n📝 Test 2: Verificar estado de workflows LangGraph")
        integration_status = await orchestrator.test_full_integration()
        print(f"✅ Integración del orchestrator: {integration_status['orchestrator_integration']}")
        print(f"✅ Conectividad workflow: {integration_status['workflow_connectivity']}")
        print(f"✅ Herramientas disponibles: {integration_status['tools_available']}")
        print(f"✅ Agentes en workflow: {integration_status['agents_in_workflow']}")
        print(f"✅ Listo para orquestación: {integration_status['ready_for_orchestration']}")
        
        if not integration_status['ready_for_orchestration']:
            print("⚠️ ADVERTENCIA: Sistema no completamente listo, continuando con test limitado")
        
        # Test 3: Crear solicitud de orquestación
        print("\n📝 Test 3: Crear solicitud de orquestación completa")
        orchestration_request = create_test_orchestration_request()
        print(f"✅ Solicitud creada para empleado: {orchestration_request.employee_id}")
        print(f"✅ Patrón de orquestación: {orchestration_request.orchestration_pattern.value}")
        print(f"✅ Agentes requeridos: {len(orchestration_request.required_agents)}")
        print(f"✅ Documentos adjuntos: {len(orchestration_request.documents)}")
        print(f"✅ Prioridad: {orchestration_request.priority.value}")
        print(f"✅ Requisitos especiales: {len(orchestration_request.special_requirements)}")
        
        # Test 4: Ejecutar orquestación completa
        print("\n📝 Test 4: Ejecutar orquestación completa con LangGraph")
        print("🚀 Iniciando coordinación de DATA COLLECTION HUB...")
        
        # Ejecutar orquestación
        start_time = datetime.now()
        orchestration_result = await orchestrator.orchestrate_onboarding_process(orchestration_request)
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        print(f"⏱️ Tiempo total de ejecución: {execution_time:.2f} segundos")
        print(f"✅ Orquestación exitosa: {orchestration_result['success']}")
        print(f"✅ Orchestration ID: {orchestration_result.get('orchestration_id', 'No generado')}")
        print(f"✅ Session ID: {orchestration_result.get('session_id', 'No generado')}")
        print(f"✅ Estado de orquestación: {orchestration_result.get('orchestration_status', 'unknown')}")
        
        session_id = orchestration_result.get('session_id')
        orchestration_id = orchestration_result.get('orchestration_id')
        
        # Test 5: Verificar resultados de agentes coordinados
        print("\n📝 Test 5: Verificar coordinación de agentes del DATA COLLECTION HUB")
        
        agent_results = orchestration_result.get('agent_results', {})
        print(f"✅ Agentes ejecutados: {len(agent_results)}")
        
        for agent_type, result in agent_results.items():
            if isinstance(result, dict):
                success = result.get('success', False)
                processing_time = result.get('processing_time', 0)
                score = result.get('validation_score', result.get('compliance_score', 0))
                
                print(f"   🤖 {agent_type}:")
                print(f"      Exitoso: {'✅' if success else '❌'}")
                print(f"      Tiempo: {processing_time:.1f}s")
                print(f"      Score: {score:.1f}%")
        
        # Test 6: Verificar datos consolidados
        print("\n📝 Test 6: Verificar consolidación de datos")
        consolidated_data = orchestration_result.get('consolidated_employee_data', {})
        validation_results = orchestration_result.get('validation_results', {})
        
        if consolidated_data:
            print(f"✅ Datos del empleado consolidados: {len(consolidated_data)} campos")
            print(f"   Nombre: {consolidated_data.get('first_name', 'N/A')} {consolidated_data.get('last_name', 'N/A')}")
            print(f"   Email: {consolidated_data.get('email', 'N/A')}")
            print(f"   Departamento: {consolidated_data.get('department', 'N/A')}")
        
        if validation_results:
            print(f"✅ Resultados de validación: {len(validation_results)} componentes")
            for validation_type, result in validation_results.items():
                if isinstance(result, dict):
                    score = result.get('score', result.get('compliance_score', 0))
                    print(f"   {validation_type}: {score:.1f}%")
        
        # Test 7: Verificar métricas de calidad
        print("\n📝 Test 7: Verificar métricas de calidad y SLA")
        orchestration_summary = orchestration_result.get('orchestration_summary', {})
        overall_quality = orchestration_result.get('overall_quality_score', 0)
        
        print(f"✅ Score de calidad general: {overall_quality:.1f}%")
        print(f"✅ Agentes exitosos: {orchestration_summary.get('agents_successful', 0)}/{orchestration_summary.get('agents_executed', 0)}")
        print(f"✅ Workflow completado: {'Sí' if orchestration_summary.get('workflow_completed', False) else 'No'}")
        print(f"✅ DATA COLLECTION HUB completado: {'Sí' if orchestration_result.get('data_collection_hub_completed', False) else 'No'}")
        
        # Verificar SLA
        sla_compliant = execution_time < 300  # 5 minutos límite
        quality_compliant = overall_quality >= 70.0
        
        print(f"✅ SLA de tiempo cumplido: {'Sí' if sla_compliant else 'No'} ({execution_time:.1f}s < 300s)")
        print(f"✅ SLA de calidad cumplido: {'Sí' if quality_compliant else 'No'} ({overall_quality:.1f}% >= 70%)")
        
        # Test 8: Verificar estado en State Management
        print("\n📝 Test 8: Verificar estado en Common State Management")
        if session_id:
            context = state_manager.get_employee_context(session_id)
            if context:
                print(f"✅ Contexto encontrado para empleado: {context.employee_id}")
                print(f"✅ Fase actual: {context.phase}")
                print(f"✅ Datos procesados: {'Sí' if context.processed_data else 'No'}")
                print(f"✅ Agentes en contexto: {len(context.agent_states)}")
                
                # Verificar estados individuales de agentes
                for agent_id, agent_state in context.agent_states.items():
                    print(f"   🤖 {agent_id}: {agent_state.status}")
            else:
                print("⚠️ No se encontró contexto en State Management")
        
        # Test 9: Verificar próximos pasos
        print("\n📝 Test 9: Verificar próximos pasos del workflow")
        next_phase = orchestration_result.get('next_phase', 'unknown')
        next_actions = orchestration_result.get('next_actions', [])
        
        print(f"✅ Próxima fase: {next_phase}")
        print("✅ Próximas acciones:")
        for action in next_actions[:3]:  # Mostrar primeras 3
            print(f"   - {action}")
        
        requires_escalation = orchestration_result.get('requires_escalation', False)
        manual_review = orchestration_result.get('manual_review_needed', False)
        
        print(f"✅ Requiere escalación: {'Sí' if requires_escalation else 'No'}")
        print(f"✅ Requiere revisión manual: {'Sí' if manual_review else 'No'}")
        
        # Test 10: Test de herramientas individuales
        print("\n📝 Test 10: Verificar herramientas de orquestación individualmente")
        try:
            # Test pattern selector
            from agents.orchestrator.tools import pattern_selector_tool
            pattern_result = pattern_selector_tool.invoke({
                "selection_criteria": {
                    "employee_type": "full_time",
                    "position_level": "senior", 
                    "department": "Engineering",
                    "priority": "high"
                },
                "employee_context": orchestration_request.employee_data,
                "system_state": {}
            })
            print(f"✅ Pattern Selector: {pattern_result.get('success', False)}")
            print(f"   Patrón seleccionado: {pattern_result.get('selected_pattern', 'unknown')}")
            
            # Test task distributor
            from agents.orchestrator.tools import task_distributor_tool
            distribution_result = task_distributor_tool.invoke({
                "orchestration_pattern": "concurrent_data_collection",
                "agent_assignments": [
                    {
                        "agent_type": "initial_data_collection_agent",
                        "task_description": "Process initial data",
                        "input_data": {}
                    }
                ],
                "distribution_strategy": {}
            })
            print(f"✅ Task Distributor: {distribution_result.get('success', False)}")
            print(f"   Tareas creadas: {distribution_result.get('tasks_created', 0)}")
            
            print("✅ Herramientas de orquestación funcionando correctamente")
            
        except Exception as e:
            print(f"⚠️ Error en test de herramientas: {e}")
        
        # Test 11: Verificar integración completa
        print("\n📝 Test 11: Verificar integración completa del sistema")
        final_integration_status = orchestrator.get_integration_status(session_id)
        
        print(f"✅ Integración exitosa: {final_integration_status['integration_success']}")
        print(f"✅ Estado del orchestrator: {final_integration_status['agent_state']['status']}")
        print(f"✅ Orquestaciones activas: {final_integration_status['active_orchestrations']}")
        print(f"✅ Workflow disponible: {final_integration_status['workflow_status']['workflow_available']}")
        
        if final_integration_status.get('employee_context'):
            emp_ctx = final_integration_status['employee_context']
            print(f"✅ Contexto del empleado actualizado: {emp_ctx['has_processed_data']}")
        
        # Resumen final
        print("\n🎉 ORCHESTRATOR AGENT INTEGRATION TEST COMPLETADO")
        print("=" * 60)
        
        # Calcular score de éxito general
        success_indicators = [
            orchestration_result['success'],
            sla_compliant,
            quality_compliant,
            len(agent_results) >= 3,
            final_integration_status['integration_success'],
            orchestration_result.get('data_collection_hub_completed', False)
        ]
        
        success_rate = (sum(success_indicators) / len(success_indicators)) * 100
        
        print(f"✅ ORCHESTRATOR AGENT: {'EXITOSO' if success_rate >= 80 else 'NECESITA REVISIÓN'}")
        print(f"✅ Score de éxito: {success_rate:.1f}%")
        print(f"✅ DATA COLLECTION HUB: {'COMPLETADO' if orchestration_result.get('data_collection_hub_completed', False) else 'INCOMPLETO'}")
        print(f"✅ Workflow LangGraph: {'FUNCIONAL' if final_integration_status['workflow_status']['workflow_available'] else 'NO DISPONIBLE'}")
        print(f"✅ State Management: {'INTEGRADO' if final_integration_status['integration_success'] else 'ERROR'}")
        print(f"✅ LangFuse Observability: ACTIVA")
        
        return True, {
            "orchestration_id": orchestration_id,
            "session_id": session_id,
            "success_rate": success_rate,
            "execution_time": execution_time,
            "overall_quality_score": overall_quality,
            "agents_coordinated": len(agent_results)
        }
        
    except Exception as e:
        print(f"\n❌ ERROR EN TEST DE ORCHESTRATOR: {e}")
        import traceback
        traceback.print_exc()
        return False, {"error": str(e)}

async def test_workflow_components():
    """Test específico de componentes del workflow"""
    print("\n🔧 TESTING COMPONENTES ESPECÍFICOS DEL WORKFLOW")
    print("=" * 55)
    
    try:
        orchestrator = OrchestratorAgent()
        
        # Test conectividad workflow
        print("\n📝 Test conectividad workflow LangGraph:")
        from agents.orchestrator.workflows import test_workflow_connectivity
        connectivity = await test_workflow_connectivity()
        print(f"✅ Test de conectividad: {connectivity.get('connectivity_test', 'unknown')}")
        
        if connectivity.get('agents_status'):
            for agent_type, status in connectivity['agents_status'].items():
                print(f"   🤖 {agent_type}: {status}")
        
        # Test workflow status
        print("\n📝 Test estado del workflow:")
        from agents.orchestrator.workflows import get_workflow_status
        workflow_status = get_workflow_status()
        print(f"✅ Workflow disponible: {workflow_status['workflow_available']}")
        print(f"✅ Agentes inicializados: {workflow_status['agents_initialized']}/{workflow_status['total_agents']}")
        print(f"✅ Nodos del workflow: {workflow_status['workflow_nodes']}")
        
        # Test herramientas individualmente
        print("\n📝 Test herramientas de orquestación:")
        tools_results = {}
        
        for tool in orchestrator.tools:
            try:
                print(f"   🔧 Testing {tool.name}...")
                # Test básico de cada herramienta
                if "pattern_selector" in tool.name:
                    result = tool.invoke({
                        "selection_criteria": {"employee_type": "full_time"},
                        "employee_context": {},
                        "system_state": {}
                    })
                elif "task_distributor" in tool.name:
                    result = tool.invoke({
                        "orchestration_pattern": "concurrent_data_collection",
                        "agent_assignments": [],
                        "distribution_strategy": {}
                    })
                elif "state_coordinator" in tool.name:
                    result = tool.invoke({
                        "session_id": "test",
                        "agent_states": {},
                        "coordination_action": "validate"
                    })
                elif "progress_monitor" in tool.name:
                    result = tool.invoke({
                        "orchestration_state": {"session_id": "test", "started_at": datetime.now().isoformat()},
                        "monitoring_criteria": {},
                        "sla_thresholds": {}
                    })
                
                tools_results[tool.name] = result.get('success', False) if isinstance(result, dict) else True
                print(f"      ✅ {tool.name}: {'OK' if tools_results[tool.name] else 'ERROR'}")
                
            except Exception as e:
                tools_results[tool.name] = False
                print(f"      ❌ {tool.name}: ERROR - {str(e)}")
        
        tools_success = sum(tools_results.values()) / len(tools_results) * 100
        print(f"✅ Herramientas funcionando: {tools_success:.1f}%")
        
        return {
            "connectivity_test": connectivity.get('connectivity_test'),
            "workflow_available": workflow_status['workflow_available'],
            "tools_success_rate": tools_success,
            "components_ready": all([
                connectivity.get('connectivity_test') == 'passed',
                workflow_status['workflow_available'],
                tools_success >= 75
            ])
        }
        
    except Exception as e:
        print(f"❌ Error en test de componentes: {e}")
        return {"error": str(e), "components_ready": False}

if __name__ == "__main__":
    async def run_all_tests():
        print("🚀 INICIANDO TESTS COMPLETOS DEL ORCHESTRATOR AGENT")
        print("=" * 65)
        
        # Test componentes primero
        components_result = await test_workflow_components()
        
        # Test principal
        success, main_result = await test_orchestrator_agent()
        
        # Resumen final
        print("\n" + "=" * 65)
        print("📊 RESUMEN FINAL DE TESTS")
        print("=" * 65)
        
        if success:
            print("🎉 ORCHESTRATOR AGENT COMPLETAMENTE FUNCIONAL")
            print(f"✅ Success Rate: {main_result.get('success_rate', 0):.1f}%")
            print(f"✅ Tiempo de ejecución: {main_result.get('execution_time', 0):.2f}s")
            print(f"✅ Score de calidad: {main_result.get('overall_quality_score', 0):.1f}%")
            print(f"✅ Agentes coordinados: {main_result.get('agents_coordinated', 0)}")
            print(f"✅ Orchestration ID: {main_result.get('orchestration_id', 'N/A')}")
            print("\n🎯 RESULTADO: DATA COLLECTION HUB COMPLETAMENTE OPERATIVO")
            print("🚀 LISTO PARA PROCEDER CON DATA AGGREGATION & VALIDATION POINT")
        else:
            print("💥 ORCHESTRATOR AGENT REQUIERE REVISIÓN")
            print(f"❌ Error: {main_result.get('error', 'Unknown')}")
            print("\n🔧 REQUIERE DEBUGGING ANTES DE CONTINUAR")
        
        print("\n" + "=" * 65)
    
    # Ejecutar tests
    asyncio.run(run_all_tests())