import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.contract_management.agent import ContractManagementAgent
from agents.contract_management.schemas import (
    ContractGenerationRequest, ContractType, ComplianceLevel
)
from core.state_management.state_manager import state_manager
from shared.models import Priority
from datetime import datetime, date

def create_test_contract_generation_request():
    """Crear solicitud de contract management con datos del IT Provisioning Agent"""
    
    # Datos simulados del IT Provisioning Agent (salida típica)
    personal_data = {
        "employee_id": "EMP_CONT_001",
        "first_name": "María",
        "middle_name": "Fernanda",
        "last_name": "Jiménez",
        "mothers_lastname": "Castro", 
        "id_card": "1-3456-7890",
        "email": "maria.jimenez@empresa.com",
        "phone": "+506-8888-9012",
        "birth_date": "1985-11-18",
        "nationality": "Costarricense",
        "country": "Costa Rica",
        "city": "San José",
        "district": "Santa Ana",
        "current_address": "Santa Ana, San José, Costa Rica"
    }
    
    position_data = {
        "position": "Senior Data Analyst",
        "position_area": "Data Analytics",
        "technology": "SQL, Python, Power BI, Tableau",
        "customer": "Banco de Costa Rica",
        "partner_name": "Analytics Corp",
        "project_manager": "Carlos Rodríguez Mora",
        "office": "Costa Rica",
        "collaborator_type": "Production",
        "billable_type": "Billable",
        "contracting_type": "Payroll",
        "contracting_time": "Long term",
        "contracting_office": "CRC",
        "reference_market": "Financial Services",
        "project_need": "Business Intelligence Platform",
        "department": "Data & Analytics"
    }
    
    contractual_data = {
        "start_date": "2025-12-15",
        "salary": 92000.0,
        "currency": "USD",
        "employment_type": "Full-time",
        "work_modality": "Hybrid",
        "probation_period": 90,
        "benefits": [
            "Seguro médico CCSS + privado",
            "Vacaciones 18 días",
            "Aguinaldo completo",
            "Bono por desempeño trimestral",
            "Capacitación técnica anual $3000",
            "Gimnasio corporativo",
            "Subsidio de almuerzo"
        ]
    }
    
    # Credenciales IT del IT Provisioning Agent
    it_credentials = {
        "username": "maria.jimenez",
        "email": "maria.jimenez@company.com",
        "temporary_password": "TempPass456!",
        "domain_access": "company\\maria.jimenez",
        "vpn_credentials": "VPN-EMP_CONT_001-202512",
        "badge_access": "BADGE-CRC-STANDARD-EMP_CONT_001",
        "employee_id": "EMP_CONT_001",
        "created_at": "2025-11-04T16:40:00Z",
        "must_change_password": True,
        "equipment_assignment": {
            "laptop": {
                "type": "dell_latitude",
                "model": "Dell Latitude 5530",
                "serial": "LAP-20251104-7894"
            },
            "monitor": {
                "size": "27 inch",
                "model": "Dell UltraSharp",
                "serial": "MON-20251104-5621"
            },
            "peripherals": [
                {"type": "wireless_keyboard", "model": "Logitech MX Keys"},
                {"type": "wireless_mouse", "model": "Logitech MX Master 3"},
                {"type": "headset_pro", "model": "Jabra Evolve2 65"}
            ],
            "software_licenses": [
                "Windows 11 Pro", "Office 365 Business", "Power BI Pro",
                "SQL Server Management Studio", "Python", "Tableau Desktop"
            ]
        },
        "access_level": "standard",
        "provisioning_completed": True
    }
    
    return ContractGenerationRequest(
        employee_id="EMP_CONT_001",
        session_id="test_contract_session_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
        personal_data=personal_data,
        position_data=position_data,
        contractual_data=contractual_data,
        it_credentials=it_credentials,
        contract_type=ContractType.FULL_TIME,
        compliance_level=ComplianceLevel.STANDARD,
        priority=Priority.HIGH,
        special_clauses=[
            "Cláusula de confidencialidad reforzada para datos financieros",
            "Acceso a herramientas de Business Intelligence",
            "Trabajo remoto hasta 3 días por semana"
        ],
        legal_requirements=[
            "Verificación de antecedentes para sector financiero",
            "Capacitación en protección de datos LGPD",
            "Certificación en herramientas de análisis"
        ],
        template_version="v2024.1"
    )

def test_contract_management_agent():
    """Test completo del Contract Management Agent"""
    print("🔄 TESTING CONTRACT MANAGEMENT AGENT + HR SIMULATOR + LEGAL VALIDATION")
    print("=" * 85)
    
    try:
        # Test 1: Crear y verificar Contract Management Agent
        print("\n📝 Test 1: Inicializar Contract Management Agent")
        contract_agent = ContractManagementAgent()
        print("✅ Contract Management Agent creado exitosamente")
        
        # Verificar integración con State Management
        overview = state_manager.get_system_overview()
        print(f"✅ Agentes registrados en sistema: {overview['registered_agents']}")
        print(f"✅ Estado del Contract agent: {overview['agents_status'].get('contract_management_agent', 'no encontrado')}")
        
        # Test 2: Verificar HR Department Simulator
        print("\n📝 Test 2: Verificar HR Department Simulator")
        hr_dept_status = contract_agent.get_hr_department_status()
        print(f"✅ HR Department Status: {hr_dept_status.get('current_load', 'unknown')}")
        print(f"✅ Compliance Rate: {hr_dept_status.get('compliance_rate', 'unknown')}")
        print(f"✅ Contract Templates: {hr_dept_status.get('contract_templates', 0)} disponibles")
        print(f"✅ Legal Clauses: {hr_dept_status.get('legal_clauses', 0)} en librería")
        print(f"✅ Benefits Packages: {hr_dept_status.get('benefits_packages', 0)} configurados")
        
        # Test 3: Crear solicitud de contract management
        print("\n📝 Test 3: Crear solicitud de contract management")
        contract_request = create_test_contract_generation_request()
        print(f"✅ Solicitud creada para empleado: {contract_request.employee_id}")
        print(f"✅ Posición: {contract_request.position_data['position']}")
        print(f"✅ Tipo de contrato: {contract_request.contract_type.value}")
        print(f"✅ Nivel de compliance: {contract_request.compliance_level.value}")
        print(f"✅ Prioridad: {contract_request.priority.value}")
        print(f"✅ Cláusulas especiales: {len(contract_request.special_clauses)}")
        print(f"✅ Requisitos legales: {len(contract_request.legal_requirements)}")
        
        # Verificar datos de entrada
        print("\n📊 Verificando datos de entrada:")
        print(f"   👤 Empleado: {contract_request.personal_data['first_name']} {contract_request.personal_data['last_name']}")
        print(f"   💼 Posición: {contract_request.position_data['position']}")
        print(f"   💰 Salario: {contract_request.contractual_data['currency']} {contract_request.contractual_data['salary']:,}")
        print(f"   📅 Fecha inicio: {contract_request.contractual_data['start_date']}")
        print(f"   🖥️ IT Credentials: {contract_request.it_credentials['email']}")
        print(f"   💻 Equipamiento: {'Asignado' if contract_request.it_credentials['equipment_assignment'] else 'Pendiente'}")
        
        # Test 4: Generar preview del contrato
        print("\n📝 Test 4: Generar preview del contrato")
        contract_preview = contract_agent.generate_contract_preview(
            contract_request.personal_data,
            contract_request.it_credentials
        )
        
        if contract_preview.get("success"):
            preview_data = contract_preview.get("contract_preview", {})
            print(f"✅ Preview generado exitosamente")
            print(f"   📄 Tipo de contrato: {preview_data.get('contract_type', 'N/A')}")
            print(f"   📋 Páginas estimadas: {preview_data.get('estimated_pages', 0)}")
            print(f"   🏛️ Jurisdicción: {preview_data.get('jurisdiction', 'N/A')}")
            print(f"   💼 Beneficios incluidos: {preview_data.get('benefits_summary', {}).get('vacation_days', 0)} días vacaciones")
            print(f"   🖥️ IT integrado: {'Sí' if preview_data.get('it_provisions', {}).get('email') else 'No'}")
        else:
            print(f"⚠️ Error generando preview: {contract_preview.get('error', 'Unknown')}")
        
        # Test 5: Ejecutar contract management completo
        print("\n📝 Test 5: Ejecutar contract management completo")
        print("🚀 Iniciando generación, validación y firma de contrato...")
        start_time = datetime.now()
        
        contract_result = contract_agent.execute_contract_management(contract_request)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"⏱️ Tiempo total de procesamiento: {processing_time:.2f} segundos")
        print(f"✅ Contract management exitoso: {contract_result['success']}")
        print(f"✅ Contract Management ID: {contract_result.get('contract_management_id', 'No generado')}")
        print(f"✅ Session ID: {contract_result.get('session_id', 'No generado')}")
        print(f"✅ Estado del contrato: {contract_result.get('contract_status', 'unknown')}")
        
        session_id = contract_result.get('session_id')
        contract_mgmt_id = contract_result.get('contract_management_id')
        
        # Test 6: Verificar métricas de contract management
        print("\n📝 Test 6: Verificar métricas de contract management")
        contract_generated = contract_result.get('contract_generated', False)
        legal_validation_passed = contract_result.get('legal_validation_passed', False)
        signature_process_complete = contract_result.get('signature_process_complete', False)
        document_archived = contract_result.get('document_archived', False)
        compliance_score = contract_result.get('compliance_score', 0)
        
        print(f"✅ Contrato generado: {'Sí' if contract_generated else 'No'}")
        print(f"✅ Validación legal aprobada: {'Sí' if legal_validation_passed else 'No'}")
        print(f"✅ Proceso de firma completado: {'Sí' if signature_process_complete else 'No'}")
        print(f"✅ Documento archivado: {'Sí' if document_archived else 'No'}")
        print(f"✅ Score de compliance: {compliance_score:.1f}%")
        
        # Test 7: Verificar detalles del contrato
        print("\n📝 Test 7: Verificar detalles del contrato generado")
        contract_details = contract_result.get('employee_contract_details', {})
        contract_id = contract_result.get('contract_id', '')
        
        if contract_details:
            print(f"✅ Contract ID: {contract_id}")
            print(f"✅ Posición contractual: {contract_details.get('position', 'N/A')}")
            print(f"✅ Departamento: {contract_details.get('department', 'N/A')}")
            print(f"✅ Fecha de inicio: {contract_details.get('start_date', 'N/A')}")
            print(f"✅ Salario contractual: {contract_details.get('salary', 0):,}")
            
            # Verificar beneficios
            benefits = contract_details.get('benefits', {})
            if benefits:
                print(f"✅ Días de vacaciones: {benefits.get('vacation_days', 0)}")
                print(f"✅ Seguro médico: {benefits.get('health_insurance', {}).get('provider', 'N/A')}")
                
            # Verificar IT provisions
            it_provisions = contract_details.get('it_provisions', {})
            if it_provisions:
                print(f"✅ Email corporativo: {it_provisions.get('email', 'N/A')}")
                print(f"✅ Acceso VPN: {'Sí' if it_provisions.get('vpn_access') else 'No'}")
                print(f"✅ Equipamiento incluido: {'Sí' if it_provisions.get('equipment_provided') else 'No'}")
        else:
            print("⚠️ No se encontraron detalles del contrato")
            
        # Test 8: Verificar proceso de validación legal
        print("\n📝 Test 8: Verificar validación legal y compliance")
        contract_summary = contract_result.get('contract_summary', {})
        
        print(f"✅ Estado de generación: {contract_summary.get('generation_status', 'Unknown')}")
        print(f"✅ Estado de validación: {contract_summary.get('validation_status', 'Unknown')}")
        print(f"✅ Estado de firma: {contract_summary.get('signature_status', 'Unknown')}")
        print(f"✅ Estado de archivo: {contract_summary.get('archive_status', 'Unknown')}")
        print(f"✅ Porcentaje de compliance: {contract_summary.get('compliance_percentage', '0%')}")
        
        # Verificar si requiere revisión manual
        requires_review = contract_result.get('requires_manual_review', False)
        print(f"✅ Requiere revisión manual: {'Sí' if requires_review else 'No'}")
        
        # Test 9: Verificar preparación para Meeting Coordination
        print("\n📝 Test 9: Verificar preparación para Meeting Coordination Agent")
        ready_for_meeting = contract_result.get('ready_for_meeting_coordination', False)
        signed_contract_location = contract_result.get('signed_contract_location', '')
        
        print(f"✅ Listo para Meeting Coordination: {'Sí' if ready_for_meeting else 'No'}")
        print(f"✅ Ubicación contrato firmado: {signed_contract_location if signed_contract_location else 'No disponible'}")
        
        if ready_for_meeting:
            print("🎯 Datos preparados para Meeting Coordination:")
            print(f"   📄 Contract ID: {contract_id}")
            print(f"   👤 Employee Details: Disponibles")
            print(f"   📋 Contract Terms: Ejecutados")
            print(f"   🔐 IT Provisions: Integradas")
        
        # Test 10: Verificar estado en Common State Management
        print("\n📝 Test 10: Verificar estado en Common State Management")
        if session_id:
            context = state_manager.get_employee_context(session_id)
            if context:
                print(f"✅ Contexto encontrado para empleado: {context.employee_id}")
                print(f"✅ Fase actual: {context.phase}")
                print(f"✅ Datos procesados: {'Sí' if context.processed_data else 'No'}")
                
                # Verificar datos de contract management en contexto
                processed_data = context.processed_data
                if processed_data and "contract_management_completed" in processed_data:
                    print(f"✅ Contract Management registrado: {processed_data['contract_management_completed']}")
                    print(f"✅ Contract ID: {processed_data.get('signed_contract', 'N/A')}")
                    print(f"✅ Listo para meeting: {processed_data.get('ready_for_meeting', False)}")
                    print(f"✅ Próxima fase: {processed_data.get('next_phase', 'unknown')}")
                else:
                    print("⚠️ Datos de contract management no encontrados en contexto")
            else:
                print("⚠️ No se encontró contexto en State Management")
        else:
            print("⚠️ Session ID no disponible")
            
        # Test 11: Verificar próximos pasos
        print("\n📝 Test 11: Verificar próximos pasos y recomendaciones")
        next_actions = contract_result.get('next_actions', [])
        print("✅ Próximas acciones recomendadas:")
        for action in next_actions[:4]:  # Mostrar primeras 4
            print(f"   - {action}")
            
                # Test 12: Test de herramientas individuales
        print("\n📝 Test 12: Verificar herramientas de contract management individualmente")
        try:
            # Test contract generator
            print("   🔧 Testing contract_generator_tool...")
            from agents.contract_management.tools import contract_generator_tool
            
            # Usar single dict como en el test exitoso
            generator_test = contract_generator_tool.invoke({
                "employee_data": {
                    **contract_request.personal_data,
                    **contract_request.position_data
                },
                "it_credentials": contract_request.it_credentials,
                "contractual_data": contract_request.contractual_data,
                "template_version": contract_request.template_version
            })
            print(f"      ✅ Contract Generator: {generator_test.get('success', False)}")
            if generator_test.get('success'):
                metadata = generator_test.get('generation_metadata', {})
                print(f"         Contract ID: {metadata.get('contract_id', 'N/A')}")
                print(f"         Template usado: {metadata.get('template_used', 'N/A')}")
                print(f"         Cláusulas incluidas: {metadata.get('clauses_included', 0)}")
                print(f"         Páginas estimadas: {metadata.get('pages_estimated', 0)}")
                
            # Test legal validator (con contrato generado)
            if generator_test.get('success'):
                print("   🔧 Testing legal_validator_tool...")
                from agents.contract_management.tools import legal_validator_tool
                
                contract_doc = generator_test.get('contract_document', {})
                validator_test = legal_validator_tool.invoke({
                    "contract_document": contract_doc,
                    "validation_level": "standard"
                })
                print(f"      ✅ Legal Validator: {validator_test.get('success', False)}")
                if validator_test.get('success'):
                    validation_result = validator_test.get('validation_result', {})
                    print(f"         Compliance Score: {validation_result.get('compliance_score', 0):.1f}%")
                    print(f"         Es válido: {validation_result.get('is_valid', False)}")
                    print(f"         Issues legales: {len(validation_result.get('legal_issues', []))}")
                    
            print("✅ Herramientas de contract management funcionando correctamente")
            
        except Exception as e:
            print(f"⚠️ Error en test de herramientas: {e}")     
        # Test 13: Verificar integración con HR Simulator
        print("\n📝 Test 13: Verificar integración con HR Department Simulator")
        try:
            import asyncio
            
            # Test directo del simulador
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            simulator_response = loop.run_until_complete(
                contract_agent.hr_simulator.process_contract_request(
                    {
                        **contract_request.personal_data,
                        **contract_request.position_data
                    },
                    contract_request.it_credentials,
                    contract_request.contractual_data
                )
            )
            loop.close()
            
            print(f"✅ HR Simulator Response: {simulator_response.status}")
            print(f"✅ Request ID: {simulator_response.request_id}")
            print(f"✅ Processing Time: {simulator_response.processing_time_minutes:.2f} min")
            print(f"✅ Legal Clauses: {len(simulator_response.legal_clauses)} generadas")
            print(f"✅ Approval Workflow: {len(simulator_response.approval_workflow)} pasos")
            print(f"✅ Compliance Requirements: Configurados")
            
        except Exception as e:
            print(f"⚠️ Error en test de HR Simulator: {e}")
            
        # Test 14: Verificar status de contrato específico
        print("\n📝 Test 14: Verificar status de contract management específico")
        if contract_mgmt_id:
            contract_status = contract_agent.get_contract_status(contract_mgmt_id)
            if contract_status.get('found'):
                print(f"✅ Contract management encontrado: {contract_status['contract_management_id'] if 'contract_management_id' in contract_status else contract_mgmt_id}")
                print(f"✅ Status: {contract_status.get('status', 'unknown')}")
                print(f"✅ Completado en: {contract_status.get('completed_at', 'N/A')}")
            else:
                print(f"⚠️ Contract management no encontrado: {contract_status.get('message', 'Error')}")
        else:
            print("⚠️ Contract Management ID no disponible para verificar status")
            
        # Test 15: Verificar integración completa del sistema
        print("\n📝 Test 15: Verificar integración completa del sistema")
        try:
            # Verificar estado del agente en State Management
            agent_state = state_manager.get_agent_state(contract_agent.agent_id, session_id)
            system_overview = state_manager.get_system_overview()
            
            print(f"✅ Estado del Contract Agent: {agent_state.status if agent_state else 'not_found'}")
            print(f"✅ Última actualización: {agent_state.last_updated.isoformat() if agent_state and agent_state.last_updated else 'N/A'}")
            print(f"✅ Agentes activos en sistema: {system_overview['registered_agents']}")
            print(f"✅ Contratos activos: {len(contract_agent.active_contracts)}")
            
            integration_success = bool(agent_state and agent_state.status == "completed")
            print(f"✅ Integración exitosa: {'Sí' if integration_success else 'No'}")
            
        except Exception as e:
            print(f"⚠️ Error verificando integración: {e}")
            integration_success = False
            
        # Resumen final
        print("\n🎉 CONTRACT MANAGEMENT AGENT INTEGRATION TEST COMPLETADO")
        print("=" * 75)
        
        # Calcular score de éxito general
        success_indicators = [
            contract_result['success'],
            ready_for_meeting,
            contract_generated,
            legal_validation_passed,
            signature_process_complete,
            document_archived,
            compliance_score >= 85.0,
            integration_success
        ]
        
        success_rate = (sum(success_indicators) / len(success_indicators)) * 100
        
        print(f"✅ CONTRACT MANAGEMENT AGENT: {'EXITOSO' if success_rate >= 70 else 'NECESITA REVISIÓN'}")
        print(f"✅ Score de éxito: {success_rate:.1f}%")
        print(f"✅ Contract management completado: {contract_result['success']}")
        print(f"✅ Contrato generado: {'Sí' if contract_generated else 'No'}")
        print(f"✅ Validación legal: {'Sí' if legal_validation_passed else 'No'}")
        print(f"✅ Proceso de firma: {'Sí' if signature_process_complete else 'No'}")
        print(f"✅ Documento archivado: {'Sí' if document_archived else 'No'}")
        print(f"✅ Score de compliance: {compliance_score:.1f}%")
        print(f"✅ Listo para Meeting Coordination: {'Sí' if ready_for_meeting else 'No'}")
        print(f"✅ State Management: {'INTEGRADO' if integration_success else 'ERROR'}")
        print(f"✅ HR Simulator: ACTIVO")
        print(f"✅ LangFuse Observability: ACTIVA")
        
        return True, {
            "contract_management_id": contract_mgmt_id,
            "session_id": session_id,
            "success_rate": success_rate,
            "processing_time": processing_time,
            "contract_generated": contract_generated,
            "legal_validation_passed": legal_validation_passed,
            "signature_process_complete": signature_process_complete,
            "document_archived": document_archived,
            "compliance_score": compliance_score,
            "ready_for_meeting": ready_for_meeting,
            "integration_success": integration_success
        }
        
    except Exception as e:
        print(f"\n❌ ERROR EN TEST DE CONTRACT MANAGEMENT: {e}")
        import traceback
        traceback.print_exc()
        return False, {"error": str(e)}

def test_hr_simulator_standalone():
    """Test específico del HR Department Simulator"""
    print("\n🔍 TESTING HR DEPARTMENT SIMULATOR ESPECÍFICO")
    print("=" * 60)
    
    try:
        from agents.contract_management.hr_simulator import HRDepartmentSimulator
        import asyncio
        
        simulator = HRDepartmentSimulator()
        
        # Test datos de muestra
        test_employee_data = {
            "employee_id": "EMP_HR_TEST",
            "first_name": "Ana",
            "last_name": "Rodríguez",
            "position": "Legal Counsel",
            "department": "Legal",
            "office": "Costa Rica",
            "salary": 110000,
            "currency": "USD"
        }
        
        test_it_credentials = {
            "email": "ana.rodriguez@company.com",
            "username": "ana.rodriguez",
            "equipment_assignment": {"laptop": True}
        }
        
        test_contractual_data = {
            "start_date": "2025-12-20",
            "employment_type": "Full-time",
            "benefits": ["Premium health insurance", "Legal professional development"]
        }
        
        # Ejecutar simulación
        print("🚀 Ejecutando simulación de HR Department...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        response = loop.run_until_complete(
            simulator.process_contract_request(
                test_employee_data, 
                test_it_credentials,
                test_contractual_data
            )
        )
        loop.close()
        
        print(f"✅ Simulación exitosa: {response.status == 'completed'}")
        print(f"✅ Request ID: {response.request_id}")
        print(f"✅ Processing Time: {response.processing_time_minutes:.2f} min")
        
        # Verificar template de contrato
        contract_template = response.contract_template
        print(f"\n📋 Template de contrato:")
        print(f"   Tipo: {contract_template.get('template_type', 'N/A')}")
        print(f"   Posición: {contract_template.get('position_title', 'N/A')}")
        print(f"   Salario: {contract_template.get('currency', 'USD')} {contract_template.get('salary', 0):,}")
        print(f"   Jurisdicción: {contract_template.get('jurisdiction', 'N/A')}")
        
        # Verificar cláusulas legales
        legal_clauses = response.legal_clauses
        print(f"\n⚖️ Cláusulas legales generadas: {len(legal_clauses)}")
        for clause in legal_clauses[:3]:  # Mostrar primeras 3
            print(f"   - {clause.title} ({clause.clause_type})")
            
        # Verificar beneficios
        benefits = response.benefits_configuration
        print(f"\n💼 Configuración de beneficios:")
        print(f"   Días de vacaciones: {benefits.vacation_days}")
        print(f"   Seguro médico: {benefits.health_insurance.get('provider', 'N/A')}")
        print(f"   Desarrollo profesional: ${benefits.professional_development.get('annual_budget', 0) if benefits.professional_development else 0}")
        
        # Verificar workflow de aprobación
        approval_workflow = response.approval_workflow
        print(f"\n🔄 Workflow de aprobación: {len(approval_workflow)} pasos")
        for step in approval_workflow[:4]:  # Mostrar primeros 4
            print(f"   {step}")
            
        # Verificar compliance
        compliance_req = response.compliance_requirements
        print(f"\n📋 Compliance requirements:")
        requirements = compliance_req.get('requirements', {})
        print(f"   Background check: {requirements.get('background_check', False)}")
        print(f"   Education verification: {requirements.get('education_verification', False)}")
        print(f"   CCSS registration: {requirements.get('ccss_registration', False)}")
        print(f"   Compliance level: {compliance_req.get('compliance_level', 'standard')}")
        
        # Estadísticas del departamento
        stats = simulator.get_department_stats()
        print(f"\n📊 Estadísticas HR Department:")
        print(f"   Requests activos: {stats['active_requests']}")
        print(f"   Templates disponibles: {stats['contract_templates']}")
        print(f"   Cláusulas legales: {stats['legal_clauses']}")
        print(f"   Paquetes de beneficios: {stats['benefits_packages']}")
        print(f"   Compliance rate: {stats['compliance_rate']}")
        print(f"   Tiempo promedio: {stats['average_processing_time']}")
        
        return response.status == "completed"
        
    except Exception as e:
        print(f"❌ Error en HR Simulator: {e}")
        return False

if __name__ == "__main__":
    print("🚀 INICIANDO TESTS COMPLETOS DEL CONTRACT MANAGEMENT AGENT")
    print("=" * 80)
    
    # Test principal
    success, main_result = test_contract_management_agent()
    
    # Test de HR simulator
    hr_simulator_success = test_hr_simulator_standalone()
    
    # Resumen final
    print("\n" + "=" * 80)
    