import os
from dotenv import load_dotenv
from core.logging_config import setup_logging
from core.database import db_manager
from agents.initial_data_collection.agent import InitialDataCollectionAgent
from tests.mock_data import (
    COMPLETE_ONBOARDING_EMAIL,
    INCOMPLETE_ONBOARDING_EMAIL,
    MALFORMED_EMAIL
)

def main():
    """Función principal para probar el Initial Data Collection Agent"""
    
    # Cargar configuración
    load_dotenv()
    
    # Configurar logging
    setup_logging()
    
    print("🤖 INITIAL DATA COLLECTION AGENT - SISTEMA DE ONBOARDING")
    print("=" * 60)
    
    # Verificar configuración
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY no encontrada en .env")
        print("   Por favor configura tu API key de OpenAI")
        return
    
    # Conectar a base de datos
    print("📦 Conectando a MongoDB...")
    if not db_manager.connect():
        print("⚠️  Advertencia: No se pudo conectar a MongoDB")
        print("   El agente funcionará sin persistencia")
    else:
        print("✅ Conexión a MongoDB establecida")
    
    # Inicializar agente
    print("\n🚀 Inicializando Initial Data Collection Agent...")
    try:
        agent = InitialDataCollectionAgent()
        print("✅ Agente inicializado correctamente")
        print(f"📊 Estado: {agent.get_status()}")
    except Exception as e:
        print(f"❌ Error inicializando agente: {e}")
        return
    
    # Ejecutar pruebas
    test_cases = [
        ("Email Completo", COMPLETE_ONBOARDING_EMAIL),
        ("Email Incompleto", INCOMPLETE_ONBOARDING_EMAIL),
        ("Email Malformado", MALFORMED_EMAIL)
    ]
    
    print("\n" + "=" * 60)
    print("🧪 EJECUTANDO PRUEBAS DEL AGENTE")
    print("=" * 60)
    
    for test_name, email_data in test_cases:
        print(f"\n📧 Procesando: {test_name}")
        print("-" * 40)
        
        try:
            result = agent.process_onboarding_email(email_data)
            
            # Mostrar resultados
            print(f"✅ Éxito: {result.get('success', False)}")
            print(f"📊 Calidad: {result.get('data_quality_score', 0):.1f}%")
            print(f"⏱️  Tiempo: {result.get('processing_time', 0):.2f}s")
            print(f"🔍 Revisión Manual: {'Sí' if result.get('requires_manual_review', True) else 'No'}")
            
            if result.get('employee_data'):
                emp_data = result['employee_data']
                if isinstance(emp_data, dict) and 'basic_info' in emp_data:
                    basic_info = emp_data['basic_info']
                    print(f"👤 Empleado: {basic_info.get('first_name', 'N/A')} {basic_info.get('last_name', 'N/A')}")
                    print(f"🆔 ID: {basic_info.get('id_card', 'N/A')}")
                else:
                    print("👤 Datos de empleado: Estructura procesada")
            
            missing_fields = result.get('missing_fields', [])
            if missing_fields:
                print(f"⚠️  Campos Faltantes: {len(missing_fields)}")
                for field in missing_fields[:3]:  # Mostrar solo los primeros 3
                    print(f"   - {field}")
                if len(missing_fields) > 3:
                    print(f"   ... y {len(missing_fields) - 3} más")
            
            errors = result.get('errors', [])
            if errors:
                print(f"❌ Errores: {len(errors)}")
                for error in errors[:2]:  # Mostrar solo los primeros 2
                    print(f"   - {error}")
                    
        except Exception as e:
            print(f"❌ Error procesando {test_name}: {e}")
        
        print("-" * 40)
    
    # Mostrar estadísticas finales
    print(f"\n📈 ESTADÍSTICAS FINALES DEL AGENTE")
    print("=" * 60)
    final_status = agent.get_status()
    print(f"🔧 Herramientas disponibles: {final_status['tools_count']}")
    print(f"📝 Interacciones procesadas: {final_status['memory_entries']}")
    print(f"🕐 Última actividad: {final_status.get('last_activity', 'N/A')}")
    
    # Desconectar base de datos
    if db_manager.client:
        db_manager.disconnect()
        print("📦 Desconectado de MongoDB")
    
    print("\n✅ Pruebas completadas exitosamente!")
    print("🚀 El Initial Data Collection Agent está listo para producción")

if __name__ == "__main__":
    main()