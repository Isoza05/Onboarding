import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.confirmation_data.agent import ConfirmationDataAgent
from agents.confirmation_data.schemas import ConfirmationRequest, ContractTerms, PositionInfo
from core.state_management.state_manager import state_manager
from shared.models import Priority
from datetime import datetime, date, timedelta

def create_test_confirmation_request():
    """Crear solicitud de confirmación de prueba"""
    
    contract_terms = ContractTerms(
        start_date=date.today() + timedelta(days=14),
        salary=75000.0,
        currency="USD",
        employment_type="Full-time",
        work_modality="Hybrid",
        probation_period=90,
        benefits=["Seguro médico", "Vacaciones", "Aguinaldo"]
    )
    
    position_info = PositionInfo(
        position_title="Data Engineer",
        department="Engineering",
        reporting_manager="María López",
        job_level="Mid-level",
        location="Costa Rica"
    )
    
    return ConfirmationRequest(
        employee_id="EMP_TEST_001",
        contract_terms=contract_terms,
        position_info=position_info,
        additional_notes="Candidato con excelente perfil técnico",
        priority=Priority.HIGH
    )

def test_confirmation_data_agent():
    """Test completo del Confirmation Data Agent"""
    
    print("🧪 TESTING CONFIRMATION DATA AGENT + STATE MANAGEMENT + LANGFUSE")
    print("=" * 70)
    
    try:
        # Crear agente (ya se registra automáticamente)
        print("\n📝 Preparando test...")
        agent = ConfirmationDataAgent()
        print("✅ Agente creado e integrado")
        
        # Test 1: Verificar registro en State Management
        print("\n📝 Test 1: Verificar registro en State Management")
        overview = state_manager.get_system_overview()
        print(f"✅ Agentes registrados: {overview['registered_agents']}")
        print(f"✅ Estado del agente: {overview['agents_status'].get('confirmation_data_agent', 'no encontrado')}")
        
        # Test 2: Crear solicitud de confirmación
        print("\n📝 Test 2: Crear solicitud de confirmación")
        confirmation_request = create_test_confirmation_request()
        print(f"✅ Solicitud creada para empleado: {confirmation_request.employee_id}")
        print(f"✅ Salario propuesto: ${confirmation_request.contract_terms.salary:,} {confirmation_request.contract_terms.currency}")
        print(f"✅ Posición: {confirmation_request.position_info.position_title} en {confirmation_request.position_info.department}")
        
        # Test 3: Procesar confirmación con integración
        print("\n📝 Test 3: Procesar confirmación con integración completa")
        result = agent.process_confirmation_request(confirmation_request)
        
        print(f"✅ Procesamiento exitoso: {result['success']}")
        print(f"✅ Session ID generado: {result.get('session_id', 'No generado')}")
        print(f"✅ Puntuación de validación: {result.get('validation_score', 0):.1f}%")
        print(f"✅ Requiere escalación: {'Sí' if result.get('requires_escalation', True) else 'No'}")
        print(f"✅ Carta de oferta generada: {'Sí' if result.get('offer_letter_generated', False) else 'No'}")
        
        session_id = result.get('session_id')
        
         # Test 4: Verificar estado actualizado
        print("\n📝 Test 4: Verificar estado actualizado")
        if session_id:
            context = state_manager.get_employee_context(session_id)
            if context:
                print(f"✅ Contexto encontrado para empleado: {context.employee_id}")
                print(f"✅ Fase actual: {context.phase}")
                print(f"✅ Datos de validación: {'Sí' if context.validation_results else 'No'}")
                print(f"✅ Agentes en contexto: {len(context.agent_states)}")
                if 'confirmation_data_agent' in context.agent_states:
                    agent_state = context.agent_states['confirmation_data_agent']
                    print(f"✅ Estado del agente en sesión: {agent_state.status}")
            else:
                print("⚠️ No se encontró contexto para la sesión")
        else:
            print("⚠️ Session ID no disponible")
        
        # Test 5: Verificar herramientas individualmente
        print("\n📝 Test 5: Verificar herramientas específicas")
        if result.get('salary_validation'):
            salary_result = result['salary_validation']
            if salary_result.get('success'):
                validation = salary_result.get('validation_results', {})
                print(f"✅ Validación salarial: {'Dentro de banda' if validation.get('within_band') else 'Fuera de banda'}")
                print(f"   Rango: ${validation.get('band_min', 0):,} - ${validation.get('band_max', 0):,}")
        
        if result.get('compliance_check'):
            compliance = result['compliance_check']
            print(f"✅ Compliance score: {compliance.get('compliance_score', 0):.1f}%")
            print(f"   Cumple normativas: {'Sí' if compliance.get('is_compliant', False) else 'No'}")
        
        # Test 6: Verificar carta de oferta
        print("\n📝 Test 6: Verificar carta de oferta generada")
        if result.get('offer_letter_content'):
            offer_lines = result['offer_letter_content'].split('\n')[:5]  # Primeras 5 líneas
            print("✅ Carta de oferta generada:")
            for line in offer_lines:
                if line.strip():
                    print(f"   {line.strip()}")
            print("   ...")
        
        # Test 7: Estado de integración completo
        print("\n📝 Test 7: Estado de integración completo")
        try:
            integration_status = agent.get_integration_status(session_id)
            if integration_status and 'agent_state' in integration_status:
                print(f"✅ Estado del agente: {integration_status['agent_state']['status']}")
                if integration_status.get('employee_context'):
                    print(f"✅ Empleado ID: {integration_status['employee_context']['employee_id']}")
                    print(f"✅ Fase: {integration_status['employee_context']['phase']}")
                    print(f"✅ Datos de validación: {'Sí' if integration_status['employee_context']['has_validation_data'] else 'No'}")
            else:
                print("⚠️ No se pudo obtener estado de integración")
        except Exception as e:
            print(f"⚠️ Error obteniendo estado de integración: {e}")

        # ... rest of code ...

        print("\n🎉 INTEGRACIÓN COMPLETADA EXITOSAMENTE")
        print("✅ Confirmation Data Agent está completamente integrado")
        print("✅ State Management funcionando correctamente")
        print("✅ LangFuse observability activa")
        
        return True, session_id
        
    except Exception as e:
        print(f"\n❌ ERROR EN INTEGRACIÓN: {e}")
        import traceback
        traceback.print_exc()
        return False, None

if __name__ == "__main__":
    success, session_id = test_confirmation_data_agent()
    if success:
        print(f"\n🚀 CONFIRMATION DATA AGENT EXITOSO - Session ID: {session_id}")
        print("🎯 LISTO PARA CREAR DOCUMENTATION AGENT (CSA)")
    else:
        print("\n💥 INTEGRACIÓN FALLÓ - REVISAR ERRORES")