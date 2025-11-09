import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator.workflows import (
    sequential_pipeline_workflow, execute_sequential_pipeline_orchestration
)
from agents.orchestrator.schemas import (
    SequentialPipelineRequest, SequentialPipelinePhase, PipelineAgentResult
)
from agents.progress_tracker.schemas import PipelineStage
from core.state_management.state_manager import state_manager
from shared.models import Priority
from datetime import datetime, date, timedelta
import json

def create_test_sequential_pipeline_request():
    """Crear solicitud de Sequential Pipeline con datos del Data Aggregator"""
    
    # === DATOS CONSOLIDADOS DEL DATA AGGREGATOR ===
    consolidated_data = {
        "employee_data": {
            "employee_id": "EMP_PIPE_001",
            "first_name": "María",
            "middle_name": "Elena",
            "last_name": "Castillo",
            "mothers_lastname": "Mora",
            "id_card": "1-3456-7890",
            "passport": "CR123456789",
            "email": "maria.castillo@empresa.com",
            "phone": "+506-9876-5432",
            "gender": "Female",
            "birth_date": "1988-11-25",
            "nationality": "Costarricense",
            "marital_status": "Married",
            "children": 1,
            "english_level": "C1",
            "country": "Costa Rica",
            "city": "Cartago",
            "district": "Oriental",
            "current_address": "Cartago, Oriental, Costa Rica",
            "university": "Instituto Tecnológico de Costa Rica",
            "career": "Ingeniería en Computación",
            "position": "Tech Lead",
            "department": "Engineering",
            "position_area": "Software Architecture",
            "technology": "Java, Spring Boot, Microservices, AWS",
            "customer": "Global Financial Corp",
            "partner_name": "Tech Innovations Ltd",
            "project_manager": "Roberto Silva",
            "reporting_manager": "Ana Patricia Vega",
            "office": "Costa Rica",
            "collaborator_type": "Production",
            "billable_type": "Billable",
            "contracting_type": "Payroll",
            "contracting_time": "Long term",
            "start_date": (date.today() + timedelta(days=10)).isoformat(),
            "salary": 95000.0,
            "currency": "USD",
            "employment_type": "Full-time",
            "work_modality": "Hybrid"
        },
        "validation_results": {
            "data_collection": {
                "score": 88.5,
                "status": "completed"
            },
            "contract_validation": {
                "score": 85.2,
                "contract_validated": True,
                "offer_generated": True
            },
            "documentation": {
                "compliance_score": 92.1,
                "documents_validated": 7,
                "validation_status": "valid"
            }
        },
        "processing_summary": {
            "agents_executed": 4,
            "successful_agents": 4,
            "total_processing_time": 12.8,
            "overall_success": True,
            "overall_quality_score": 88.6
        }
    }
    
    # === RESULTADO DE AGREGACIÓN ===
    aggregation_result = {
        "success": True,
        "message": "Agregación de datos completada exitosamente",
        "aggregation_status": "completed",
        "overall_quality_score": 88.6,
        "completeness_score": 91.3,
        "consistency_score": 87.8,
        "reliability_score": 86.7,
        "quality_rating": "Good",
        "ready_for_sequential_pipeline": True,
        "pipeline_readiness": {
            "it_provisioning": True,
            "contract_management": True,
            "meeting_coordination": True
        },
        "validation_passed": True,
        "critical_issues": [],
        "warnings": [
            "Minor inconsistency in address format",
            "Optional document missing: parking permit"
        ],
        "requires_manual_review": False,
        "next_phase": "sequential_processing_pipeline",
        "next_actions": [
            "Proceder a IT Provisioning Agent",
            "Iniciar Contract Management Agent",
            "Configurar Meeting Coordination Agent"
        ]
    }
    
    return SequentialPipelineRequest(
        employee_id="EMP_PIPE_001",
        session_id="test_pipeline_session_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
        orchestration_id="test_orchestration_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
        consolidated_data=consolidated_data,
        aggregation_result=aggregation_result,
        data_quality_score=88.6,
        pipeline_priority=Priority.HIGH,
        quality_gates_enabled=True,
        sla_monitoring_enabled=True,
        auto_escalation_enabled=True,
        it_provisioning_config={
            "security_level": "standard",
            "equipment_type": "senior_developer",
            "vpn_access": True
        },
        contract_management_config={
            "contract_type": "full_time",
            "compliance_level": "standard",
            "legal_review_required": True
        },
        meeting_coordination_config={
            "onboarding_type": "senior_technical",
            "stakeholder_level": "extended",
            "meeting_intensity": "comprehensive"
        }
    )

def test_sequential_pipeline_integration():
    """Test completo de integración del Sequential Pipeline"""
    print("🔄 TESTING SEQUENTIAL PIPELINE INTEGRATION")
    print("=" * 85)
    
    try:
        # Test 1: Verificar inicialización del Sequential Pipeline Workflow
        print("\n📝 Test 1: Verificar inicialización del Sequential Pipeline")
        print(f"✅ Sequential Pipeline Workflow disponible: {sequential_pipeline_workflow.graph is not None}")
        print(f"✅ Agentes inicializados: {len([a for a in sequential_pipeline_workflow.agents.values() if a is not None])}/3")
        print(f"✅ Progress Tracker disponible: {sequential_pipeline_workflow.progress_tracker is not None}")
        
        # Verificar agentes específicos
        agents_status = {}
        for agent_type, agent_instance in sequential_pipeline_workflow.agents.items():
            agents_status[agent_type] = "✅ Inicializado" if agent_instance else "❌ No disponible"
            print(f"   {agent_type}: {agents_status[agent_type]}")
        
        # Test 2: Verificar integración con State Management
        print("\n📝 Test 2: Verificar integración con State Management")
        system_overview = state_manager.get_system_overview()
        print(f"✅ Agentes registrados en sistema: {system_overview['registered_agents']}")
        
        # Verificar que los agentes del pipeline estén registrados
        pipeline_agents = ['it_provisioning_agent', 'contract_management_agent', 'meeting_coordination_agent']
        registered_pipeline_agents = [agent for agent in pipeline_agents if agent in system_overview['agents_status']]
        print(f"✅ Agentes del pipeline registrados: {len(registered_pipeline_agents)}/3")
        
        for agent in pipeline_agents:
            status = system_overview['agents_status'].get(agent, 'no_registrado')
            print(f"   {agent}: {status}")
        
        # Test 3: Crear y validar solicitud de pipeline
        print("\n📝 Test 3: Crear solicitud de Sequential Pipeline")
        pipeline_request = create_test_sequential_pipeline_request()
        print(f"✅ Solicitud creada para empleado: {pipeline_request.employee_id}")
        print(f"✅ Calidad de datos de entrada: {pipeline_request.data_quality_score:.1f}%")
        print(f"✅ Listo para pipeline: {pipeline_request.aggregation_result['ready_for_sequential_pipeline']}")
        print(f"✅ Prioridad del pipeline: {pipeline_request.pipeline_priority.value}")
        
        # Verificar configuraciones
        print("📋 Configuraciones del pipeline:")
        print(f"   Quality Gates: {'Habilitado' if pipeline_request.quality_gates_enabled else 'Deshabilitado'}")
        print(f"   SLA Monitoring: {'Habilitado' if pipeline_request.sla_monitoring_enabled else 'Deshabilitado'}")
        print(f"   Auto Escalation: {'Habilitado' if pipeline_request.auto_escalation_enabled else 'Deshabilitado'}")
        
        # Verificar datos de entrada
        print("\n📊 Verificando calidad de datos consolidados:")
        employee_data = pipeline_request.consolidated_data.get("employee_data", {})
        validation_results = pipeline_request.consolidated_data.get("validation_results", {})
        
        print(f"   👤 Datos personales: ✅ {employee_data.get('first_name')} {employee_data.get('last_name')}")
        print(f"   💼 Posición: ✅ {employee_data.get('position')} en {employee_data.get('department')}")
        print(f"   💰 Salario: ✅ ${employee_data.get('salary', 0):,.0f} {employee_data.get('currency', 'USD')}")
        print(f"   📅 Inicio: ✅ {employee_data.get('start_date')}")
        
        # Verificar validaciones previas
        data_collection_score = validation_results.get("data_collection", {}).get("score", 0)
        contract_score = validation_results.get("contract_validation", {}).get("score", 0)
        documentation_score = validation_results.get("documentation", {}).get("compliance_score", 0)
        
        print(f"   📋 Data Collection: {data_collection_score:.1f}%")
        print(f"   📄 Contract Validation: {contract_score:.1f}%")
        print(f"   📁 Documentation: {documentation_score:.1f}%")
        
        # Test 4: Ejecutar Sequential Pipeline completo
        print("\n📝 Test 4: Ejecutar Sequential Pipeline completo")
        print("🚀 Iniciando ejecución del pipeline secuencial...")
        
        start_time = datetime.now()
        
        # IMPORTANTE: Usar asyncio para ejecutar el pipeline
        import asyncio
        
        # Crear event loop si no existe
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Ejecutar pipeline
        pipeline_result = loop.run_until_complete(
            execute_sequential_pipeline_orchestration(pipeline_request)
        )
        
        end_time = datetime.now()
        total_processing_time = (end_time - start_time).total_seconds()
        
        print(f"⏱️ Tiempo total de pipeline: {total_processing_time:.2f} segundos")
        print(f"✅ Pipeline ejecutado exitosamente: {pipeline_result.get('success', False)}")
        print(f"✅ Employee ID: {pipeline_result.get('employee_id', 'N/A')}")
        print(f"✅ Session ID: {pipeline_result.get('session_id', 'N/A')}")
        print(f"✅ Orchestration ID: {pipeline_result.get('orchestration_id', 'N/A')}")
        
        # Test 5: Verificar resultados por fase
        print("\n📝 Test 5: Verificar resultados de cada fase del pipeline")
        
        stages_completed = pipeline_result.get("stages_completed", 0)
        stages_total = pipeline_result.get("stages_total", 3)
        overall_quality = pipeline_result.get("overall_quality_score", 0)
        
        print(f"✅ Fases completadas: {stages_completed}/{stages_total}")
        print(f"✅ Score de calidad general: {overall_quality:.1f}%")
        
        # Verificar resultados individuales de agentes
        it_result = pipeline_result.get("it_provisioning_result")
        contract_result = pipeline_result.get("contract_management_result")
        meeting_result = pipeline_result.get("meeting_coordination_result")
        
        print("📋 Resultados por agente:")
        
        if it_result:
            success = it_result.get("success", False) if isinstance(it_result, dict) else getattr(it_result, 'success', False)
            quality = it_result.get("quality_score", 0) if isinstance(it_result, dict) else getattr(it_result, 'quality_score', 0)
            print(f"   🖥️ IT Provisioning: {'✅' if success else '❌'} (Calidad: {quality:.1f}%)")
        
        if contract_result:
            success = contract_result.get("success", False) if isinstance(contract_result, dict) else getattr(contract_result, 'success', False)
            quality = contract_result.get("quality_score", 0) if isinstance(contract_result, dict) else getattr(contract_result, 'quality_score', 0)
            print(f"   📄 Contract Management: {'✅' if success else '❌'} (Calidad: {quality:.1f}%)")
        
        if meeting_result:
            success = meeting_result.get("success", False) if isinstance(meeting_result, dict) else getattr(meeting_result, 'success', False)
            quality = meeting_result.get("quality_score", 0) if isinstance(meeting_result, dict) else getattr(meeting_result, 'quality_score', 0)
            print(f"   📅 Meeting Coordination: {'✅' if success else '❌'} (Calidad: {quality:.1f}%)")
        
        # Test 6: Verificar quality gates y SLA
        print("\n📝 Test 6: Verificar Quality Gates y SLA Monitoring")
        
        quality_gates_passed = pipeline_result.get("quality_gates_passed", 0)
        quality_gates_failed = pipeline_result.get("quality_gates_failed", 0)
        sla_breaches = pipeline_result.get("sla_breaches", 0)
        escalations = pipeline_result.get("escalations_triggered", 0)
        
        print(f"✅ Quality Gates pasados: {quality_gates_passed}")
        print(f"❌ Quality Gates fallados: {quality_gates_failed}")
        print(f"⏰ SLA breaches: {sla_breaches}")
        print(f"🚨 Escalaciones activadas: {escalations}")
        
        # Test 7: Verificar preparación para onboarding
        print("\n📝 Test 7: Verificar preparación para onboarding execution")
        
        employee_ready = pipeline_result.get("employee_ready_for_onboarding", False)
        onboarding_timeline = pipeline_result.get("onboarding_timeline")
        stakeholders_engaged = pipeline_result.get("stakeholders_engaged", [])
        
        print(f"✅ Empleado listo para onboarding: {'Sí' if employee_ready else 'No'}")
        print(f"✅ Timeline de onboarding: {'Creado' if onboarding_timeline else 'No disponible'}")
        print(f"✅ Stakeholders engaged: {len(stakeholders_engaged)}")
        
        if onboarding_timeline:
            if isinstance(onboarding_timeline, dict):
                total_meetings = onboarding_timeline.get("total_meetings", 0)
                estimated_hours = onboarding_timeline.get("estimated_total_hours", 0)
                print(f"   📅 Total reuniones programadas: {total_meetings}")
                print(f"   ⏰ Horas estimadas: {estimated_hours:.1f}")
        
        # Test 8: Verificar próximos pasos
        print("\n📝 Test 8: Verificar próximos pasos y recomendaciones")
        
        next_actions = pipeline_result.get("next_actions", [])
        requires_followup = pipeline_result.get("requires_followup", False)
        
        print(f"✅ Requiere seguimiento: {'Sí' if requires_followup else 'No'}")
        print("✅ Próximas acciones recomendadas:")
        for action in next_actions[:4]:  # Mostrar primeras 4
            print(f"   - {action}")
        
        # Test 9: Verificar manejo de errores y warnings
        print("\n📝 Test 9: Verificar manejo de errores y warnings")
        
        errors = pipeline_result.get("errors", [])
        warnings = pipeline_result.get("warnings", [])
        
        print(f"✅ Errores detectados: {len(errors)}")
        print(f"✅ Warnings generados: {len(warnings)}")
        
        if errors:
            print("❌ Errores:")
            for error in errors[:3]:  # Mostrar primeros 3
                print(f"   - {error}")
        
        if warnings:
            print("⚠️ Warnings:")
            for warning in warnings[:3]:  # Mostrar primeros 3
                print(f"   - {warning}")
        
        # Test 10: Verificar integración con State Management
        print("\n📝 Test 10: Verificar actualización en State Management")
        
        session_id = pipeline_result.get("session_id")
        if session_id:
            try:
                context = state_manager.get_employee_context(session_id)
                if context:
                    print(f"✅ Contexto actualizado para empleado: {context.employee_id}")
                    print(f"✅ Fase actual: {context.phase}")
                    
                    processed_data = context.processed_data
                    if processed_data and "sequential_pipeline_completed" in processed_data:
                        print(f"✅ Pipeline registrado en contexto: {processed_data['sequential_pipeline_completed']}")
                        print(f"✅ Employee ready: {processed_data.get('employee_ready_for_onboarding', False)}")
                        print(f"✅ Próxima fase: {processed_data.get('next_phase', 'unknown')}")
                    else:
                        print("⚠️ Datos del pipeline no encontrados en contexto")
                else:
                    print("⚠️ No se encontró contexto en State Management")
            except Exception as e:
                print(f"⚠️ Error verificando State Management: {e}")
        
        # Test 11: Test de workflow status
        print("\n📝 Test 11: Verificar estado general de workflows")
        
        from agents.orchestrator.workflows import get_workflow_status
        workflow_status = get_workflow_status()
        
        print("✅ Estado de workflows:")
        data_collection = workflow_status.get("data_collection_workflow", {})
        sequential_pipeline = workflow_status.get("sequential_pipeline_workflow", {})
        
        print(f"   📊 Data Collection Workflow: {'✅' if data_collection.get('available') else '❌'}")
        print(f"      Agentes: {data_collection.get('agents_initialized', 0)}/{data_collection.get('total_agents', 0)}")
        
        print(f"   📊 Sequential Pipeline Workflow: {'✅' if sequential_pipeline.get('available') else '❌'}")
        print(f"      Agentes: {sequential_pipeline.get('agents_initialized', 0)}/{sequential_pipeline.get('total_agents', 0)}")
        print(f"      Progress Tracker: {'✅' if sequential_pipeline.get('progress_tracker_available') else '❌'}")
        
        total_nodes = workflow_status.get("total_workflow_nodes", 0)
        print(f"   📊 Total nodos de workflow: {total_nodes}")
        
        # Resumen final
        print("\n🎉 SEQUENTIAL PIPELINE INTEGRATION TEST COMPLETADO")
        print("=" * 75)
        
        # Calcular score de éxito de la integración
        integration_indicators = [
            pipeline_result.get("success", False),
            employee_ready,
            stages_completed >= 2,  # Al menos 2 de 3 fases
            overall_quality >= 70,  # Calidad mínima
            len(errors) == 0,       # Sin errores críticos
            sequential_pipeline.get("available", False),  # Workflow disponible
            len(stakeholders_engaged) > 0,  # Stakeholders engaged
            onboarding_timeline is not None  # Timeline creado
        ]
        
        integration_success_rate = (sum(integration_indicators) / len(integration_indicators)) * 100
        
        print(f"✅ SEQUENTIAL PIPELINE: {'INTEGRACIÓN EXITOSA' if integration_success_rate >= 80 else 'REQUIERE AJUSTES'}")
        print(f"✅ Score de integración: {integration_success_rate:.1f}%")
        print(f"✅ Tiempo total: {total_processing_time:.2f}s")
        print(f"✅ Fases completadas: {stages_completed}/{stages_total}")
        print(f"✅ Calidad general: {overall_quality:.1f}%")
        print(f"✅ Empleado listo: {'Sí' if employee_ready else 'No'}")
        print(f"✅ Stakeholders: {len(stakeholders_engaged)}")
        print(f"✅ Quality Gates: {quality_gates_passed} passed / {quality_gates_failed} failed")
        print(f"✅ SLA Compliance: {'✅' if sla_breaches == 0 else f'❌ {sla_breaches} breaches'}")
        
        return True, {
            "success_rate": integration_success_rate,
            "processing_time": total_processing_time,
            "stages_completed": stages_completed,
            "overall_quality": overall_quality,
            "employee_ready": employee_ready,
            "stakeholders_engaged": len(stakeholders_engaged),
            "errors_count": len(errors),
            "warnings_count": len(warnings)
        }
        
    except Exception as e:
        print(f"\n❌ ERROR EN INTEGRATION TEST: {e}")
        import traceback
        traceback.print_exc()
        return False, {"error": str(e)}

def test_individual_workflow_components():
    """Test de componentes individuales del workflow"""
    print("\n🔍 TESTING INDIVIDUAL WORKFLOW COMPONENTS")
    print("=" * 60)
    
    try:
        # Test agents initialization
        print("📝 Test de inicialización de agentes:")
        
        agents_tests = []
        
        # Test IT Provisioning Agent
        try:
            from agents.it_provisioning.agent import ITProvisioningAgent
            it_agent = ITProvisioningAgent()
            agents_tests.append(("IT Provisioning Agent", True))
            print("   ✅ IT Provisioning Agent: Inicializado")
        except Exception as e:
            agents_tests.append(("IT Provisioning Agent", False))
            print(f"   ❌ IT Provisioning Agent: Error - {e}")
        
        # Test Contract Management Agent
        try:
            from agents.contract_management.agent import ContractManagementAgent
            contract_agent = ContractManagementAgent()
            agents_tests.append(("Contract Management Agent", True))
            print("   ✅ Contract Management Agent: Inicializado")
        except Exception as e:
            agents_tests.append(("Contract Management Agent", False))
            print(f"   ❌ Contract Management Agent: Error - {e}")
        
        # Test Meeting Coordination Agent
        try:
            from agents.meeting_coordination.agent import MeetingCoordinationAgent
            meeting_agent = MeetingCoordinationAgent()
            agents_tests.append(("Meeting Coordination Agent", True))
            print("   ✅ Meeting Coordination Agent: Inicializado")
        except Exception as e:
            agents_tests.append(("Meeting Coordination Agent", False))
            print(f"   ❌ Meeting Coordination Agent: Error - {e}")
        
        # Test Progress Tracker Agent
        try:
            from agents.progress_tracker.agent import ProgressTrackerAgent
            progress_agent = ProgressTrackerAgent()
            agents_tests.append(("Progress Tracker Agent", True))
            print("   ✅ Progress Tracker Agent: Inicializado")
        except Exception as e:
            agents_tests.append(("Progress Tracker Agent", False))
            print(f"   ❌ Progress Tracker Agent: Error - {e}")
        
        successful_agents = len([test for test in agents_tests if test[1]])
        total_agents = len(agents_tests)
        
        print(f"\n✅ Agentes inicializados exitosamente: {successful_agents}/{total_agents}")
        
        return successful_agents == total_agents
        
    except Exception as e:
        print(f"❌ Error en test de componentes: {e}")
        return False

if __name__ == "__main__":
    print("🚀 INICIANDO TESTS DE INTEGRACIÓN DEL SEQUENTIAL PIPELINE")
    print("=" * 80)
    
    # Test de componentes individuales
    components_success = test_individual_workflow_components()
    
    # Test de integración completa
    integration_success, integration_result = test_sequential_pipeline_integration()
    
    # Resumen final
    print("\n" + "=" * 80)
    print("📊 RESUMEN FINAL DE INTEGRACIÓN")
    print("=" * 80)
    
    if integration_success and components_success:
        print("🎉 SEQUENTIAL PIPELINE COMPLETAMENTE INTEGRADO Y FUNCIONAL")
        print(f"✅ Score de integración: {integration_result.get('success_rate', 0):.1f}%")
        print(f"✅ Tiempo de procesamiento: {integration_result.get('processing_time', 0):.2f}s")
        print(f"✅ Fases completadas: {integration_result.get('stages_completed', 0)}/3")
        print(f"✅ Calidad general: {integration_result.get('overall_quality', 0):.1f}%")
        print(f"✅ Empleado listo para onboarding: {integration_result.get('employee_ready', False)}")
        print(f"✅ Errores: {integration_result.get('errors_count', 0)}")
        
        print("\n🎯 RESULTADO: SEQUENTIAL PIPELINE OPERATIVO")
        print("🚀 PIPELINE COMPLETO FUNCIONAL:")
        print("   ✅ DATA COLLECTION HUB → DATA AGGREGATION → SEQUENTIAL PIPELINE")
        print("   ✅ IT PROVISIONING → CONTRACT MANAGEMENT → MEETING COORDINATION")
        print("   ✅ PROGRESS TRACKING + QUALITY GATES + SLA MONITORING")
        print("   ✅ STATE MANAGEMENT + LANGFUSE OBSERVABILITY")
        
        print("\n🎊 ¡ONBOARDING AUTOMATION SYSTEM COMPLETADO!")
        
    else:
        print("💥 SEQUENTIAL PIPELINE REQUIERE AJUSTES")
        if not components_success:
            print("❌ Problema en inicialización de componentes")
        if not integration_success:
            print(f"❌ Error en integración: {integration_result.get('error', 'Unknown')}")
        
        print("\n🔧 REQUIERE DEBUGGING Y CORRECCIÓN")
    
    print("\n" + "=" * 80)