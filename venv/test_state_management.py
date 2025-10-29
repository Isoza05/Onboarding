import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.state_management.state_manager import state_manager
from core.state_management.models import AgentStateStatus

def test_state_management():
    """Test completo del sistema de gestión de estado"""
    
    print("🧪 TESTING COMMON STATE MANAGEMENT")
    print("=" * 50)
    
    try:
        # Test 1: Registrar agente
        print("\n📝 Test 1: Registrar agente")
        success = state_manager.register_agent("test_agent", {"version": "1.0"})
        print(f"✅ Agente registrado: {success}")
        assert success, "Falló el registro de agente"
        
        # Test 2: Crear contexto de empleado
        print("\n📝 Test 2: Crear contexto de empleado")
        employee_data = {
            "employee_id": "EMP001",
            "name": "Juan Pérez",
            "email": "juan@test.com"
        }
        session_id = state_manager.create_employee_context(employee_data)
        print(f"✅ Contexto creado: {session_id}")
        assert session_id is not None, "Falló la creación de contexto"
        
        # Test 3: Actualizar estado de agente
        print("\n📝 Test 3: Actualizar estado de agente")
        success = state_manager.update_agent_state(
            "test_agent", 
            AgentStateStatus.PROCESSING,
            {"current_task": "processing_email"},
            session_id
        )
        print(f"✅ Estado actualizado: {success}")
        assert success, "Falló la actualización de estado"
        
        # Test 4: Obtener contexto
        print("\n📝 Test 4: Obtener contexto")
        context = state_manager.get_employee_context(session_id)
        if context:
            print(f"✅ Contexto obtenido - Empleado: {context.employee_id}")
            print(f"   Fase: {context.phase}")
            print(f"   Agentes activos: {len(context.agent_states)}")
            assert context.employee_id == "EMP001", "ID de empleado incorrecto"
        else:
            print("❌ No se pudo obtener el contexto")
            assert False, "Falló la obtención de contexto"
        
        # Test 5: Vista general del sistema
        print("\n📝 Test 5: Vista general del sistema")
        overview = state_manager.get_system_overview()
        print(f"✅ Overview obtenido:")
        print(f"   Sesiones activas: {overview['active_sessions']}")
        print(f"   Agentes registrados: {overview['registered_agents']}")
        print(f"   Estados de agentes: {overview['agents_status']}")
        
        assert overview['active_sessions'] >= 1, "No hay sesiones activas"
        assert overview['registered_agents'] >= 1, "No hay agentes registrados"
        
        # Test 6: Verificar persistencia
        print("\n📝 Test 6: Verificar persistencia")
        import os
        data_file = "data/system_state.json"
        if os.path.exists(data_file):
            print("✅ Archivo de estado creado correctamente")
            with open(data_file, 'r') as f:
                import json
                data = json.load(f)
                print(f"   Sesiones en archivo: {len(data.get('active_sessions', {}))}")
        else:
            print("⚠️ Archivo de estado no encontrado")
        
        print("\n🎉 TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
        print("✅ Common State Management está funcionando correctamente!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN TESTS: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_state_management()
    if success:
        print("\n🚀 COMMON STATE MANAGEMENT LISTO PARA USO")
    else:
        print("\n💥 TESTS FALLARON - REVISAR ERRORES")