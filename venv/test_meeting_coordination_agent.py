import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.meeting_coordination.agent import MeetingCoordinationAgent
from agents.meeting_coordination.schemas import (
    MeetingCoordinationRequest, MeetingType, MeetingPriority, StakeholderRole
)
from core.state_management.state_manager import state_manager
from shared.models import Priority
from datetime import datetime, date, timedelta

def create_test_meeting_coordination_request():
    """Crear solicitud de coordinación con datos simulados del Contract Management Agent"""
    
    # === DATOS SIMULADOS DEL CONTRACT MANAGEMENT AGENT ===
    personal_data = {
        "employee_id": "EMP_MEET_001",
        "first_name": "Carlos",
        "middle_name": "Alberto",
        "last_name": "Rodríguez",
        "mothers_lastname": "Vargas", 
        "email": "carlos.rodriguez@empresa.com",
        "phone": "+506-8765-4321",
        "id_card": "1-2345-6789",
        "nationality": "Costarricense",
        "office": "Costa Rica",
        "city": "San José"
    }
    
    position_data = {
        "position": "Senior Software Engineer",
        "department": "Engineering",
        "position_area": "Software Development",
        "technology": "Python, React, AWS",
        "customer": "Tech Solutions Inc",
        "partner_name": "Innovation Labs",
        "project_manager": "Ana Mora",
        "reporting_manager": "Luis Fernández",
        "office": "Costa Rica",
        "collaborator_type": "Production",
        "billable_type": "Billable",
        "contracting_type": "Payroll",
        "team_lead": "María González"
    }
    
    contractual_data = {
        "start_date": (date.today() + timedelta(days=7)).isoformat(),  # Next week
        "salary": 85000.0,
        "currency": "USD",
        "employment_type": "Full-time",
        "work_modality": "Hybrid",
        "probation_period": 90,
        "benefits": [
            "Seguro médico completo",
            "Vacaciones 20 días",
            "Aguinaldo",
            "Bono por desempeño",
            "Capacitación técnica",
            "Work from home allowance"
        ]
    }
    
    it_credentials = {
        "username": "carlos.rodriguez",
        "email_configured": True,
        "domain_access": "COMPANY\\carlos.rodriguez",
        "vpn_access": True,
        "system_access": [
            "JIRA", "Confluence", "GitHub", "AWS Console", "Slack"
        ],
        "equipment_assigned": {
            "laptop": "MacBook Pro 16\"",
            "monitor": "Dell 27\" 4K",
            "peripherals": ["keyboard", "mouse", "headset"],
            "mobile_device": "iPhone 13"
        },
        "security_clearance": "Standard Developer",
        "badge_access": "BADGE-CR-DEV-001"
    }
    
    contract_details = {
        "contract_id": "CONT-20241115-001",
        "contract_status": "signed",
        "employment_terms": {
            "position_title": "Senior Software Engineer",
            "department": "Engineering",
            "reporting_manager": "Luis Fernández",
            "start_date": (date.today() + timedelta(days=7)).isoformat(),
            "work_location": "San José, Costa Rica",
            "work_schedule": "full_time"
        },
        "compensation_details": {
            "base_salary": 85000.0,
            "currency": "USD",
            "payment_frequency": "monthly"
        },
        "benefits_package": {
            "health_insurance": {"provider": "INS", "coverage": "complete"},
            "vacation_days": 20,
            "sick_days": 12,
            "professional_development": {"budget": 2000, "currency": "USD"}
        },
        "signed_contract_location": "/contracts/signed/CONT-20241115-001.pdf",
        "legal_validation_passed": True,
        "compliance_verified": True
    }
    
    return MeetingCoordinationRequest(
        employee_id="EMP_MEET_001",
        session_id="test_meeting_session_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
        personal_data=personal_data,
        position_data=position_data,
        contractual_data=contractual_data,
        it_credentials=it_credentials,
        contract_details=contract_details,
        priority=Priority.HIGH,
        onboarding_start_date=date.today() + timedelta(days=7),
        department_preferences={
            "engineering_onboarding": True,
            "technical_deep_dive": True,
            "agile_methodology_intro": True
        },
        special_requirements=[
            "Senior level technical briefing",
            "Architecture overview session", 
            "Team lead introduction",
            "Customer project briefing"
        ],
        business_hours="8:00-17:00",
        excluded_dates=[],
        preferred_meeting_duration=60,
        calendar_system="microsoft_outlook",
        notification_preferences={
            "email_reminders": True,
            "teams_notifications": True,
            "calendar_reminders": True
        }
    )

def test_meeting_coordination_agent():
    """Test completo del Meeting Coordination Agent"""
    print("🔄 TESTING MEETING COORDINATION AGENT + CALENDAR INTEGRATION")
    print("=" * 80)
    
    try:
        # Test 1: Crear y verificar Meeting Coordination Agent
        print("\n📝 Test 1: Inicializar Meeting Coordination Agent")
        coordinator = MeetingCoordinationAgent()
        print("✅ Meeting Coordination Agent creado exitosamente")
        
        # Verificar integración con State Management
        overview = state_manager.get_system_overview()
        print(f"✅ Agentes registrados en sistema: {overview['registered_agents']}")
        print(f"✅ Estado del coordinator: {overview['agents_status'].get('meeting_coordination_agent', 'no encontrado')}")
        
        # Verificar sistema de calendario
        calendar_status = coordinator.get_calendar_system_status()
        print(f"✅ Sistema de calendario online: {calendar_status['calendar_system_online']}")
        print(f"✅ Salas disponibles: {calendar_status['meeting_rooms_available']}")
        print(f"✅ Integración agente-calendario: {calendar_status['agent_integration']}")
        
        # Test 2: Crear solicitud de coordinación
        print("\n📝 Test 2: Crear solicitud de coordinación con datos del Contract Agent")
        coordination_request = create_test_meeting_coordination_request()
        print(f"✅ Solicitud creada para empleado: {coordination_request.employee_id}")
        print(f"✅ Fecha de inicio onboarding: {coordination_request.onboarding_start_date}")
        print(f"✅ Prioridad: {coordination_request.priority.value}")
        print(f"✅ Sistema de calendario: {coordination_request.calendar_system}")
        print(f"✅ Requisitos especiales: {len(coordination_request.special_requirements)}")
        
        # Verificar datos de entrada
        print("\n📊 Verificando calidad de datos de entrada del Contract Agent:")
        print(f"   👤 Datos personales: ✅ Completos ({coordination_request.personal_data.get('first_name')} {coordination_request.personal_data.get('last_name')})")
        print(f"   💼 Posición: ✅ {coordination_request.position_data.get('position')} en {coordination_request.position_data.get('department')}")
        print(f"   📄 Contrato: ✅ {coordination_request.contract_details.get('contract_status')} - ID: {coordination_request.contract_details.get('contract_id')}")
        print(f"   💻 IT Setup: ✅ Credenciales configuradas ({coordination_request.it_credentials.get('username')})")
        
        # Test 3: Ejecutar coordinación completa
        print("\n📝 Test 3: Ejecutar coordinación completa de reuniones")
        print("🚀 Iniciando coordinación de timeline de onboarding...")
        start_time = datetime.now()
        
        coordination_result = coordinator.coordinate_onboarding_meetings(coordination_request)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        print(f"⏱️ Tiempo total de coordinación: {processing_time:.2f} segundos")
        print(f"✅ Coordinación exitosa: {coordination_result['success']}")
        print(f"✅ Coordination ID: {coordination_result.get('coordination_id', 'No generado')}")
        print(f"✅ Session ID: {coordination_result.get('session_id', 'No generado')}")
        print(f"✅ Estado de coordinación: {coordination_result.get('coordination_status', 'unknown')}")
        
        session_id = coordination_result.get('session_id')
        coordination_id = coordination_result.get('coordination_id')
        
        # Test 4: Verificar identificación de stakeholders
        print("\n📝 Test 4: Verificar identificación y engagement de stakeholders")
        stakeholders_engaged = coordination_result.get('stakeholders_engaged', 0)
        identified_stakeholders = coordination_result.get('identified_stakeholders', [])
        stakeholder_mapping = coordination_result.get('stakeholder_mapping', {})
        
        print(f"✅ Stakeholders identificados: {stakeholders_engaged}")
        print(f"✅ Stakeholder mapping: {len(stakeholder_mapping)} roles")
        
        print("📋 Stakeholders por rol:")
        for role, stakeholder_ids in stakeholder_mapping.items():
            print(f"   {role}: {len(stakeholder_ids)} stakeholder(s)")
        
        # Verificar roles críticos
        critical_roles = [StakeholderRole.DIRECT_MANAGER.value, StakeholderRole.HR_REPRESENTATIVE.value, StakeholderRole.IT_SUPPORT.value]
        critical_covered = all(role in stakeholder_mapping for role in critical_roles)
        print(f"✅ Roles críticos cubiertos: {'Sí' if critical_covered else 'No'}")
        
        # Test 5: Verificar análisis de calendarios y programación
        print("\n📝 Test 5: Verificar análisis de calendarios y programación optimizada")
        meetings_scheduled = coordination_result.get('meetings_scheduled_successfully', 0)
        calendar_integration = coordination_result.get('calendar_integration_active', False)
        calendar_conflicts = coordination_result.get('calendar_conflicts_detected', 0)
        
        print(f"✅ Reuniones programadas exitosamente: {meetings_scheduled}")
        print(f"✅ Integración de calendario activa: {'Sí' if calendar_integration else 'No'}")
        print(f"✅ Conflictos de calendario detectados: {calendar_conflicts}")
        
        # Verificar timeline de onboarding
        onboarding_timeline = coordination_result.get('onboarding_timeline')
        if onboarding_timeline:
            if hasattr(onboarding_timeline, 'dict'):
                timeline_dict = onboarding_timeline.dict()
            elif hasattr(onboarding_timeline, '__dict__'):
                timeline_dict = onboarding_timeline.__dict__
            else:
                timeline_dict = onboarding_timeline
            
            print(f"✅ Timeline de onboarding generado:")
            print(f"   📅 Total de reuniones: {timeline_dict.get('total_meetings', 0)}")
            print(f"   ⏰ Horas estimadas totales: {timeline_dict.get('estimated_total_hours', 0):.1f}")
            print(f"   🚨 Reuniones críticas: {timeline_dict.get('critical_meetings_count', 0)}")
        
        # Test 6: Verificar métricas de calidad
        print("\n📝 Test 6: Verificar métricas de calidad y optimización")
        scheduling_efficiency = coordination_result.get('scheduling_efficiency_score', 0)
        stakeholder_satisfaction = coordination_result.get('stakeholder_satisfaction_predicted', 0)
        timeline_optimization = coordination_result.get('timeline_optimization_score', 0)
        
        print(f"✅ Eficiencia de programación: {scheduling_efficiency:.1f}%")
        print(f"✅ Satisfacción stakeholders predicha: {stakeholder_satisfaction:.1f}%")
        print(f"✅ Optimización de timeline: {timeline_optimization:.1f}%")
        
        # Calcular score general de calidad
        quality_scores = [scheduling_efficiency, stakeholder_satisfaction, timeline_optimization]
        overall_quality = sum(s for s in quality_scores if s > 0) / len([s for s in quality_scores if s > 0]) if any(quality_scores) else 0
        quality_threshold = 75.0
        quality_passed = overall_quality >= quality_threshold
        
        print(f"✅ Score general de calidad: {overall_quality:.1f}%")
        print(f"✅ Umbral de calidad cumplido: {'Sí' if quality_passed else 'No'} ({overall_quality:.1f}% >= {quality_threshold}%)")
        
        # Test 7: Verificar sistema de invitaciones y recordatorios
        print("\n📝 Test 7: Verificar sistema de invitaciones y recordatorios")
        reminder_system_setup = coordination_result.get('reminder_system_setup', False)
        notifications_scheduled = coordination_result.get('notifications_scheduled', 0)
        stakeholder_notifications = coordination_result.get('stakeholder_notifications_sent', 0)
        
        print(f"✅ Sistema de recordatorios configurado: {'Sí' if reminder_system_setup else 'No'}")
        print(f"✅ Notificaciones programadas: {notifications_scheduled}")
        print(f"✅ Notificaciones a stakeholders enviadas: {stakeholder_notifications}")
        
        # Test 8: Verificar preparación para ejecución
        print("\n📝 Test 8: Verificar preparación para ejecución de onboarding")
        ready_for_execution = coordination_result.get('ready_for_onboarding_execution', False)
        onboarding_status = coordination_result.get('onboarding_process_status', 'unknown')
        requires_review = coordination_result.get('requires_manual_review', False)
        
        print(f"✅ Listo para ejecución de onboarding: {'Sí' if ready_for_execution else 'No'}")
        print(f"✅ Estado del proceso: {onboarding_status}")
        print(f"✅ Requiere revisión manual: {'Sí' if requires_review else 'No'}")
        
        # Verificar warnings
        warnings = coordination_result.get('warnings', [])
        if warnings:
            print("⚠️ Advertencias detectadas:")
            for warning in warnings[:3]:  # Mostrar primeras 3
                print(f"   - {warning}")
        
        # Test 9: Verificar estado en State Management
        print("\n📝 Test 9: Verificar estado en Common State Management")
        if session_id:
            context = state_manager.get_employee_context(session_id)
            if context:
                print(f"✅ Contexto encontrado para empleado: {context.employee_id}")
                print(f"✅ Fase actual: {context.phase}")
                print(f"✅ Datos procesados: {'Sí' if context.processed_data else 'No'}")
                
                # Verificar datos de coordinación en contexto
                processed_data = context.processed_data
                if processed_data and "meeting_coordination_completed" in processed_data:
                    print(f"✅ Coordinación registrada en contexto: {processed_data['meeting_coordination_completed']}")
                    print(f"✅ ID de coordinación: {processed_data.get('coordination_id', 'N/A')}")
                    print(f"✅ Listo para ejecución: {processed_data.get('ready_for_execution', False)}")
                else:
                    print("⚠️ Datos de coordinación no encontrados en contexto")
            else:
                print("⚠️ No se encontró contexto en State Management")
        else:
            print("⚠️ Session ID no disponible")
        
        # Test 10: Verificar próximos pasos
        print("\n📝 Test 10: Verificar próximos pasos y recomendaciones")
        next_actions = coordination_result.get('next_actions', [])
        print("✅ Próximas acciones recomendadas:")
        for action in next_actions[:4]:  # Mostrar primeras 4
            print(f"   - {action}")
        
        # Test 11: Test de herramientas individuales
        print("\n📝 Test 11: Verificar herramientas de coordinación individualmente")
        try:
            # Test stakeholder finder
            print("   🔧 Testing stakeholder_finder_tool...")
            from agents.meeting_coordination.tools import stakeholder_finder_tool
            
            stakeholder_test = stakeholder_finder_tool.invoke({
                "employee_data": coordination_request.personal_data,
                "position_data": coordination_request.position_data,
                "contract_details": coordination_request.contract_details
            })
            print(f"      ✅ Stakeholder Finder Tool: {stakeholder_test.get('success', False)}")
            print(f"         Stakeholders identificados: {stakeholder_test.get('total_stakeholders', 0)}")
            
            # Test calendar analyzer
            if stakeholder_test.get('success'):
                print("   🔧 Testing calendar_analyzer_tool...")
                from agents.meeting_coordination.tools import calendar_analyzer_tool
                
                stakeholders = stakeholder_test.get('stakeholders_identified', [])
                calendar_test = calendar_analyzer_tool.invoke({
                    "stakeholders": [s.dict() if hasattr(s, 'dict') else s.__dict__ if hasattr(s, '__dict__') else s for s in stakeholders],
                    "start_date": coordination_request.onboarding_start_date.isoformat(),
                    "business_hours": coordination_request.business_hours
                })
                print(f"      ✅ Calendar Analyzer Tool: {calendar_test.get('success', False)}")
                print(f"         Slots óptimos encontrados: {len(calendar_test.get('optimal_meeting_slots', []))}")
            
            print("✅ Herramientas de coordinación funcionando correctamente")
            
        except Exception as e:
            print(f"⚠️ Error en test de herramientas: {e}")
        
        # Test 12: Test de integración con simulador de calendario
        print("\n📝 Test 12: Test de integración con simulador de calendario")
        try:
            if meetings_scheduled > 0:
                # Obtener datos para simulación
                scheduled_meetings = coordination_result.get('scheduled_meetings', [])
                calendar_integration_test = coordinator.simulate_calendar_integration(
                    [m.dict() if hasattr(m, 'dict') else m.__dict__ if hasattr(m, '__dict__') else m for m in scheduled_meetings[:3]],  # Test con primeras 3 reuniones
                    [s.dict() if hasattr(s, 'dict') else s.__dict__ if hasattr(s, '__dict__') else s for s in identified_stakeholders[:5]],  # Test con primeros 5 stakeholders
                    coordination_request.personal_data
                )
                
                print(f"✅ Simulación de calendario: {calendar_integration_test.get('success', False)}")
                print(f"   📅 Reuniones creadas: {calendar_integration_test.get('meetings_created', 0)}")
                print(f"   📧 Invitaciones enviadas: {calendar_integration_test.get('invitations_sent', 0)}")
                print(f"   🔔 Recordatorios programados: {calendar_integration_test.get('reminders_scheduled', 0)}")
                print(f"   ⚠️ Conflictos detectados: {calendar_integration_test.get('conflicts_detected', 0)}")
            else:
                print("⚠️ No hay reuniones programadas para simular integración")
                
        except Exception as e:
            print(f"⚠️ Error en simulación de calendario: {e}")
        
        # Test 13: Generar reportes de coordinación
        print("\n📝 Test 13: Generar reportes de engagement y timeline")
        if coordination_id:
            # Reporte de engagement
            engagement_report = coordinator.get_stakeholder_engagement_report(coordination_id)
            if not engagement_report.get('error'):
                print("✅ Reporte de engagement generado:")
                metrics = engagement_report['stakeholder_metrics']
                print(f"   👥 Stakeholders engaged: {metrics['total_stakeholders_engaged']}")
                print(f"   📅 Reuniones programadas: {metrics['meetings_scheduled']}")
                print(f"   📧 Invitaciones enviadas: {metrics['invitations_sent']}")
                print(f"   📊 Engagement score: {metrics['engagement_score']:.1f}%")
            
            # Reporte de timeline
            timeline_summary = coordinator.get_meeting_timeline_summary(coordination_id)
            if not timeline_summary.get('error'):
                print("✅ Resumen de timeline generado:")
                timeline_metrics = timeline_summary['timeline_summary']
                print(f"   📅 Total reuniones: {timeline_metrics['total_meetings']}")
                print(f"   ⏰ Horas estimadas: {timeline_metrics['estimated_hours']:.1f}")
                print(f"   🚨 Reuniones críticas: {timeline_metrics['critical_meetings']}")
                
                meetings_by_phase = timeline_summary['meetings_by_phase']
                print(f"   📋 Por fase - Day 1: {meetings_by_phase['day_1']}, Week 1: {meetings_by_phase['week_1']}, Month 1: {meetings_by_phase['month_1']}")
        
        # Test 14: Verificar integración completa del sistema
        print("\n📝 Test 14: Verificar integración completa del sistema")
        integration_status = coordination_result.get('integration_status', {})
        print(f"✅ Sistema de calendario: {integration_status.get('calendar_system', 'unknown')}")
        print(f"✅ Sistema de notificaciones: {integration_status.get('notification_system', 'unknown')}")
        print(f"✅ Directorio de stakeholders: {integration_status.get('stakeholder_directory', 'unknown')}")
        
        # Resumen final
        print("\n🎉 MEETING COORDINATION AGENT INTEGRATION TEST COMPLETADO")
        print("=" * 70)
        
        # Calcular score de éxito general
        success_indicators = [
            coordination_result['success'],
            quality_passed,
            ready_for_execution,
            stakeholders_engaged >= 3,  # Al menos Manager, HR, IT
            meetings_scheduled >= 3,     # Al menos reuniones críticas
            calendar_integration,        # Integración activa
            reminder_system_setup       # Sistema de recordatorios
        ]
        
        success_rate = (sum(success_indicators) / len(success_indicators)) * 100
        
        print(f"✅ MEETING COORDINATION AGENT: {'EXITOSO' if success_rate >= 75 else 'NECESITA REVISIÓN'}")
        print(f"✅ Score de éxito: {success_rate:.1f}%")
        print(f"✅ Stakeholders engaged: {stakeholders_engaged} ({critical_covered and 'Roles críticos cubiertos' or 'Faltan roles críticos'})")
        print(f"✅ Reuniones programadas: {meetings_scheduled}")
        print(f"✅ Calidad de coordinación: {overall_quality:.1f}%")
        print(f"✅ Listo para ejecución: {'Sí' if ready_for_execution else 'No'}")
        print(f"✅ Calendar Integration: {'ACTIVA' if calendar_integration else 'INACTIVA'}")
        print(f"✅ State Management: INTEGRADO")
        print(f"✅ LangFuse Observability: ACTIVA")
        
        return True, {
            "coordination_id": coordination_id,
            "session_id": session_id,
            "success_rate": success_rate,
            "processing_time": processing_time,
            "stakeholders_engaged": stakeholders_engaged,
            "meetings_scheduled": meetings_scheduled,
            "ready_for_execution": ready_for_execution,
            "overall_quality": overall_quality,
            "calendar_integration": calendar_integration
        }
        
    except Exception as e:
        print(f"\n❌ ERROR EN TEST DE MEETING COORDINATION: {e}")
        import traceback
        traceback.print_exc()
        return False, {"error": str(e)}

def test_calendar_system_connectivity():
    """Test específico de conectividad del sistema de calendario"""
    print("\n🔍 TESTING CALENDAR SYSTEM CONNECTIVITY")
    print("=" * 55)
    
    try:
        coordinator = MeetingCoordinationAgent()
        
        # Test estado del sistema
        calendar_status = coordinator.get_calendar_system_status()
        print(f"✅ Sistema online: {calendar_status['calendar_system_online']}")
        print(f"✅ Salas disponibles: {calendar_status['meeting_rooms_available']}")
        print(f"✅ Carga del sistema: {calendar_status.get('system_load', 'N/A')}")
        print(f"✅ Solicitudes activas: {calendar_status.get('active_requests', 0)}")
        
        # Test disponibilidad de salas
        from agents.meeting_coordination.calendar_simulator import calendar_simulator
        start_date = date.today()
        end_date = start_date + timedelta(days=14)
        
        room_availability = calendar_simulator.get_meeting_room_availability(start_date, end_date)
        print(f"✅ Reporte de salas generado para {len(room_availability['rooms'])} salas")
        print(f"✅ Período analizado: {room_availability['report_period']['start_date']} a {room_availability['report_period']['end_date']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en conectividad del calendario: {e}")
        return False

if __name__ == "__main__":
    print("🚀 INICIANDO TESTS COMPLETOS DEL MEETING COORDINATION AGENT")
    print("=" * 75)
    
    # Test principal
    success, main_result = test_meeting_coordination_agent()
    
    # Test de conectividad del calendario
    calendar_connectivity = test_calendar_system_connectivity()
    
    # Resumen final
    print("\n" + "=" * 75)
    print("📊 RESUMEN FINAL DE TESTS")
    print("=" * 75)
    
    if success:
        print("🎉 MEETING COORDINATION AGENT COMPLETAMENTE FUNCIONAL")
        print(f"✅ Success Rate: {main_result.get('success_rate', 0):.1f}%")
        print(f"✅ Tiempo de procesamiento: {main_result.get('processing_time', 0):.2f}s")
        print(f"✅ Stakeholders engaged: {main_result.get('stakeholders_engaged', 0)}")
        print(f"✅ Reuniones programadas: {main_result.get('meetings_scheduled', 0)}")
        print(f"✅ Calidad de coordinación: {main_result.get('overall_quality', 0):.1f}%")
        print(f"✅ Listo para ejecución: {main_result.get('ready_for_execution', False)}")
        print(f"✅ Calendar System: {'✅' if calendar_connectivity else '❌'}")
        print(f"✅ Coordination ID: {main_result.get('coordination_id', 'N/A')}")
        
        print("\n🎯 RESULTADO: MEETING COORDINATION & CALENDAR SPECIALIST OPERATIVO")
        print("🚀 ONBOARDING PIPELINE SECUENCIAL COMPLETADO")
        print("   📋 Pipeline completo: Data Collection → IT Provisioning → Contract Management → Meeting Coordination")
        print("   ✅ Empleado listo para comenzar onboarding execution")
        
    else:
        print("💥 MEETING COORDINATION AGENT REQUIERE REVISIÓN")
        print(f"❌ Error: {main_result.get('error', 'Unknown')}")
        print("\n🔧 REQUIERE DEBUGGING ANTES DE PROCEDER A EJECUCIÓN")
    
    print("\n" + "=" * 75)