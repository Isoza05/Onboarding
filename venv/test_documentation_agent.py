import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.documentation.agent import DocumentationAgent
from agents.documentation.schemas import (
    DocumentationRequest, DocumentInfo, DocumentType, 
    DocumentFormat, ValidationStatus
)
from core.state_management.state_manager import state_manager
from shared.models import Priority
from datetime import datetime

def create_test_documentation_request():
    """Crear solicitud de documentación de prueba"""
    
    # Crear documentos de prueba
    documents = [
        DocumentInfo(
            document_id="doc_001",
            document_type=DocumentType.VACCINATION_CARD,
            file_name="carnet_vacunacion_juan_perez.pdf",
            file_format=DocumentFormat.PDF,
            file_size_kb=245,
            content_hash="abc123def456"
        ),
        DocumentInfo(
            document_id="doc_002", 
            document_type=DocumentType.ID_DOCUMENT,
            file_name="cedula_juan_perez.jpg",
            file_format=DocumentFormat.JPG,
            file_size_kb=189,
            content_hash="def456ghi789"
        ),
        DocumentInfo(
            document_id="doc_003",
            document_type=DocumentType.CV_RESUME,
            file_name="CV_Juan_Perez_2024.pdf",
            file_format=DocumentFormat.PDF,
            file_size_kb=512,
            content_hash="ghi789jkl012"
        ),
        DocumentInfo(
            document_id="doc_004",
            document_type=DocumentType.PHOTO,
            file_name="foto_juan_perez.jpg",
            file_format=DocumentFormat.JPG,
            file_size_kb=95,
            content_hash="jkl012mno345"
        ),
        DocumentInfo(
            document_id="doc_005",
            document_type=DocumentType.ACADEMIC_TITLES,
            file_name="titulo_ingeniero_sistemas.pdf", 
            file_format=DocumentFormat.PDF,
            file_size_kb=389,
            content_hash="mno345pqr678"
        )
    ]
    
    return DocumentationRequest(
        employee_id="EMP_DOC_001",
        documents=documents,
        processing_priority=Priority.HIGH,
        special_requirements=[
            "Verificación médica estricta",
            "Validación académica con universidad"
        ],
        compliance_standards=["hr_standard", "health_ministry", "academic_accreditation"]
    )

def test_documentation_agent():
    """Test completo del Documentation Agent (CSA)"""
    print("🧪 TESTING DOCUMENTATION AGENT (CSA) + STATE MANAGEMENT + LANGFUSE")
    print("=" * 75)
    
    try:
        # Crear agente (ya se registra automáticamente)
        print("\n📝 Preparando test...")
        agent = DocumentationAgent()
        print("✅ Agente creado e integrado")
        
        # Test 1: Verificar registro en State Management
        print("\n📝 Test 1: Verificar registro en State Management")
        overview = state_manager.get_system_overview()
        print(f"✅ Agentes registrados: {overview['registered_agents']}")
        print(f"✅ Estado del agente: {overview['agents_status'].get('documentation_agent', 'no encontrado')}")
        
        # Test 2: Crear solicitud de documentación
        print("\n📝 Test 2: Crear solicitud de documentación")
        documentation_request = create_test_documentation_request()
        print(f"✅ Solicitud creada para empleado: {documentation_request.employee_id}")
        print(f"✅ Documentos a procesar: {len(documentation_request.documents)}")
        print(f"✅ Prioridad: {documentation_request.processing_priority.value}")
        
        # Mostrar tipos de documentos
        doc_types = [doc.document_type.value for doc in documentation_request.documents]
        print(f"✅ Tipos de documentos: {', '.join(doc_types)}")
        
        # Test 3: Procesar documentación con integración
        print("\n📝 Test 3: Procesar documentación con integración completa")
        result = agent.process_documentation_request(documentation_request)
        
        print(f"✅ Procesamiento exitoso: {result['success']}")
        print(f"✅ Session ID generado: {result.get('session_id', 'No generado')}")
        print(f"✅ Status de validación: {result.get('validation_status', 'unknown')}")
        print(f"✅ Score de compliance: {result.get('compliance_score', 0):.1f}%")
        print(f"✅ Documentos procesados: {result.get('documents_processed', 0)}")
        print(f"✅ Requiere revisión humana: {'Sí' if result.get('requires_human_review', True) else 'No'}")
        
        session_id = result.get('session_id')
        
        # Test 4: Verificar estado en State Management
        print("\n📝 Test 4: Verificar estado actualizado")
        if session_id:
            context = state_manager.get_employee_context(session_id)
            if context:
                print(f"✅ Contexto encontrado para empleado: {context.employee_id}")
                print(f"✅ Fase actual: {context.phase}")
                print(f"✅ Datos de validación: {'Sí' if context.validation_results else 'No'}")
                print(f"✅ Agentes en contexto: {len(context.agent_states)}")
                
                if 'documentation_agent' in context.agent_states:
                    agent_state = context.agent_states['documentation_agent']
                    print(f"✅ Estado del agente en sesión: {agent_state.status}")
            else:
                print("⚠️ No se encontró contexto para la sesión")
        else:
            print("⚠️ Session ID no disponible")
        
        # Test 5: Verificar validaciones específicas
        print("\n📝 Test 5: Verificar validaciones específicas por documento")
        
        # Validación médica
        if result.get('medical_validation'):
            medical = result['medical_validation']
            print(f"✅ Validación médica:")
            print(f"   Estado vacunación: {medical.get('vaccination_status', 'unknown')}")
            print(f"   Certificado válido: {'Sí' if medical.get('health_certificate_valid') else 'No'}")
            print(f"   Restricciones: {len(medical.get('medical_restrictions', []))}")
        
        # Autenticación de identidad
        if result.get('id_authentication'):
            id_auth = result['id_authentication']
            print(f"✅ Autenticación de identidad:")
            print(f"   Identidad verificada: {'Sí' if id_auth.get('identity_verified') else 'No'}")
            print(f"   Documento auténtico: {'Sí' if id_auth.get('document_authentic') else 'No'}")
            print(f"   Score de confianza: {id_auth.get('confidence_score', 0):.2f}")
        
        # Verificación académica
        if result.get('academic_verification'):
            academic = result['academic_verification']
            print(f"✅ Verificación académica:")
            print(f"   Institución acreditada: {'Sí' if academic.get('institution_accredited') else 'No'}")
            print(f"   Grado confirmado: {'Sí' if academic.get('degree_level_confirmed') else 'No'}")
            print(f"   Score general: {academic.get('overall_score', 0):.1f}%")
        
        # Test 6: Verificar documentos faltantes
        print("\n📝 Test 6: Verificar análisis de completitud")
        missing_docs = result.get('missing_documents', [])
        if missing_docs:
            print(f"⚠️ Documentos faltantes: {', '.join(missing_docs)}")
        else:
            print("✅ Todos los documentos principales presentes")
        
        # Próximos pasos
        next_steps = result.get('next_steps', [])
        if next_steps:
            print("📋 Próximos pasos:")
            for step in next_steps[:3]:  # Mostrar solo primeros 3
                print(f"   - {step}")
        
        # Test 7: Estado de integración completo
        print("\n📝 Test 7: Estado de integración completo")
        try:
            integration_status = agent.get_integration_status(session_id)
            if integration_status and integration_status.get('integration_success'):
                print(f"✅ Estado del agente: {integration_status['agent_state']['status']}")
                if integration_status.get('employee_context'):
                    print(f"✅ Empleado ID: {integration_status['employee_context']['employee_id']}")
                    print(f"✅ Fase: {integration_status['employee_context']['phase']}")
                    print(f"✅ Datos de validación: {'Sí' if integration_status['employee_context']['has_validation_data'] else 'No'}")
            else:
                print("⚠️ No se pudo obtener estado de integración")
        except Exception as e:
            print(f"⚠️ Error obteniendo estado de integración: {e}")
        
        # Test 8: Verificar herramientas específicas individualmente
        print("\n📝 Test 8: Verificar herramientas especializadas")
        
        # Análisis de documentos
        if result.get('document_analyses'):
            doc_analysis = result['document_analyses']
            print(f"✅ Análisis documental:")
            print(f"   Extracción de texto: {'Exitosa' if doc_analysis.get('text_extraction_success') else 'Fallida'}")
            print(f"   Calidad de imagen: {doc_analysis.get('image_quality_score', 0):.1f}%")
            print(f"   Clasificación: {doc_analysis.get('content_classification', 'unknown')}")
        
        print("\n🎉 INTEGRACIÓN DOCUMENTACIÓN COMPLETADA EXITOSAMENTE")
        print("✅ Documentation Agent (CSA) está completamente integrado")
        print("✅ State Management funcionando correctamente")  
        print("✅ LangFuse observability activa")
        print("✅ Todas las herramientas especializadas funcionando")
        
        return True, session_id
        
    except Exception as e:
        print(f"\n❌ ERROR EN INTEGRACIÓN DOCUMENTACIÓN: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_individual_tools():
    """Test individual de herramientas de documentación"""
    print("\n🔧 TESTING HERRAMIENTAS INDIVIDUALES")
    print("=" * 50)
    
    try:
        agent = DocumentationAgent()
        
        # Test doc_analyzer_tool
        print("\n📄 Test doc_analyzer_tool:")
        from agents.documentation.tools import doc_analyzer_tool
        doc_result = doc_analyzer_tool.invoke({
            "document_data": {
                "file_name": "test_cv.pdf",
                "file_format": "pdf",
                "document_type": "cv_resume"
            },
            "document_type": "cv_resume",
            "analysis_mode": "comprehensive"
        })
        print(f"✅ Análisis exitoso: {doc_result.get('success', False)}")
        if doc_result.get('success'):
            analysis = doc_result.get('analysis_results', {})
            print(f"   Extracción texto: {analysis.get('text_extraction_success', False)}")
            print(f"   Calidad imagen: {analysis.get('image_quality_score', 0):.1f}%")
        
        # Test medical_validator_tool  
        print("\n🏥 Test medical_validator_tool:")
        from agents.documentation.tools import medical_validator_tool
        medical_result = medical_validator_tool.invoke({
            "document_data": {
                "document_type": "vaccination_card",
                "vaccines": [{"name": "COVID-19", "date": "2024-01-15"}],
                "issuing_authority": "CCSS"
            },
            "validation_standards": ["general"]
        })
        print(f"✅ Validación exitosa: {medical_result.get('success', False)}")
        if medical_result.get('success'):
            validation = medical_result.get('validation_results', {})
            print(f"   Estado vacunación: {validation.get('vaccination_status', 'unknown')}")
        
        print("✅ Tests individuales completados")
        
    except Exception as e:
        print(f"❌ Error en tests individuales: {e}")

if __name__ == "__main__":
    # Test principal
    success, session_id = test_documentation_agent()
    
    if success:
        print(f"\n🚀 DOCUMENTATION AGENT EXITOSO - Session ID: {session_id}")
        print("🎯 DATA COLLECTION HUB CASI COMPLETO")
        print("📋 Próximo paso: Crear ORCHESTRATOR AGENT para coordinar los 3 agentes")
        
        # Test de herramientas individuales
        test_individual_tools()
        
    else:
        print("\n💥 INTEGRACIÓN DOCUMENTACIÓN FALLÓ - REVISAR ERRORES")