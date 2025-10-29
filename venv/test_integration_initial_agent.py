import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.initial_data_collection.agent import InitialDataCollectionAgent
from core.state_management.state_manager import state_manager
from tests.mock_data import COMPLETE_ONBOARDING_EMAIL
from datetime import datetime

def test_integration():
    """Test de integración entre Initial Data Collection Agent y State Management"""
    
    print("🧪 TESTING INTEGRATION: INITIAL DATA COLLECTION + STATE MANAGEMENT")
    print("=" * 70)
    
    try:
        # Limpiar estado previo para test limpio
        print("\n📝 Preparando test...")
        
        # Crear agente (ya se registra automáticamente)
        agent = InitialDataCollectionAgent()
        print("✅ Agente creado e integrado")
        
        # Test 1: Verificar registro en State Management
        print("\n📝 Test 1: Verificar registro en State Management")
        overview = state_manager.get_system_overview()
        print(f"✅ Agentes registrados: {overview['registered_agents']}")
        print(f"✅ Estado del agente: {overview['agents_status'].get('initial_data_collection', 'no encontrado')}")
        
        # Test 2: Procesar email con integración
        print("\n📝 Test 2: Procesar email con integración completa")
        result = agent.process_onboarding_email(COMPLETE_ONBOARDING_EMAIL)
        
        print(f"✅ Procesamiento exitoso: {result['success']}")
        print(f"✅ Session ID generado: {result.get('session_id', 'No generado')}")
        print(f"✅ Calidad de datos: {result.get('data_quality_score', 0):.1f}%")
        
        session_id = result.get('session_id')
        
        # Test 3: Verificar estado en State Management
        print("\n📝 Test 3: Verificar estado actualizado")
        if session_id:
            context = state_manager.get_employee_context(session_id)
            if context:
                print(f"✅ Contexto encontrado para empleado: {context.employee_id}")
                print(f"✅ Fase actual: {context.phase}")
                print(f"✅ Datos procesados: {'Sí' if context.processed_data else 'No'}")
                print(f"✅ Agentes en contexto: {len(context.agent_states)}")
                
                if 'initial_data_collection' in context.agent_states:
                    agent_state = context.agent_states['initial_data_collection']
                    print(f"✅ Estado del agente en sesión: {agent_state.status}")
        
        # Test 4: Verificar estado de integración
        print("\n📝 Test 4: Estado de integración completo")
        integration_status = agent.get_integration_status(session_id)
        print(f"✅ Estado del agente: {integration_status['agent_state']['status']}")
        if integration_status.get('employee_context'):
            print(f"✅ Empleado ID: {integration_status['employee_context']['employee_id']}")
            print(f"✅ Fase: {integration_status['employee_context']['phase']}")
        
        # Test 5: Verificar persistencia
        print("\n📝 Test 5: Verificar persistencia del estado")
        overview_final = state_manager.get_system_overview()
        print(f"✅ Sesiones activas: {overview_final['active_sessions']}")
        print(f"✅ Última actualización: {overview_final['last_updated']}")
        
        print("\n🎉 INTEGRACIÓN COMPLETADA EXITOSAMENTE")
        print("✅ Initial Data Collection Agent está completamente integrado con State Management")
        
        return True, session_id
        
    except Exception as e:
        print(f"\n❌ ERROR EN INTEGRACIÓN: {e}")
        import traceback
        traceback.print_exc()
        return False, None

if __name__ == "__main__":
    success, session_id = test_integration()
    if success:
        print(f"\n🚀 INTEGRACIÓN EXITOSA - Session ID: {session_id}")
        print("🎯 LISTO PARA CREAR PRÓXIMOS AGENTES DEL DATA COLLECTION HUB")
    else:
        print("\n💥 INTEGRACIÓN FALLÓ - REVISAR ERRORES")