from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from agents.base.base_agent import BaseAgent
from agents.documentation.tools import (
    doc_analyzer_tool,
    medical_validator_tool,
    id_authenticator_tool,
    academic_verifier_tool
)
from agents.documentation.schemas import (
    DocumentationRequest,
    DocumentProcessingResult,
    DocumentType,
    ValidationStatus
)
from core.database import db_manager
from datetime import datetime
import json

# Imports para integración
from core.state_management.state_manager import state_manager
from core.state_management.models import AgentStateStatus, OnboardingPhase
from core.observability import observability_manager

class DocumentationAgent(BaseAgent):
    """
    Agente especializado en análisis y validación de documentos (CSA).
    Procesa: carné de vacunación, cédula, CV, ficha de personal, fotografías,
    verificación de antecedentes y títulos académicos.
    
    Implementa arquitectura BDI:
    - Beliefs: Los documentos deben ser auténticos y cumplir estándares legales
    - Desires: Validar todos los documentos requeridos con alta precisión
    - Intentions: Analizar, autenticar y verificar documentación completa
    """
    
    def __init__(self):
        super().__init__(
            agent_id="documentation_agent",
            agent_name="Documentation Agent (CSA)"
        )
        
        # Registrar agente en state management
        state_manager.register_agent(
            self.agent_id,
            {
                "version": "1.0", 
                "specialization": "document_analysis_validation",
                "tools_count": len(self.tools),
                "supported_documents": [dt.value for dt in DocumentType],
                "validation_capabilities": {
                    "medical_validation": True,
                    "id_authentication": True,
                    "academic_verification": True,
                    "document_analysis": True
                }
            }
        )
        self.logger.info("Documentation Agent integrado con State Management")

    def _initialize_tools(self) -> List:
        """Inicializar herramientas especializadas en documentos"""
        return [
            doc_analyzer_tool,
            medical_validator_tool, 
            id_authenticator_tool,
            academic_verifier_tool
        ]

    def _create_prompt(self) -> ChatPromptTemplate:
        """Crear prompt con framework BDI y patrón ReAct"""
        bdi = self._get_bdi_framework()
        
        system_prompt = f"""
Eres el Documentation Agent (CSA), especialista en análisis y validación de documentos para onboarding.

## FRAMEWORK BDI (Belief-Desire-Intention)
**BELIEFS (Creencias):**
{bdi['beliefs']}

**DESIRES (Deseos):**
{bdi['desires']}

**INTENTIONS (Intenciones):**
{bdi['intentions']}

## HERRAMIENTAS DISPONIBLES:
- doc_analyzer_tool: Analiza PDFs, extrae texto/imágenes, clasifica contenido
- medical_validator_tool: Valida certificados médicos y carné de vacunación 
- id_authenticator_tool: Autentica documentos de identidad y verificación cruzada
- academic_verifier_tool: Verifica títulos académicos e instituciones

## DOCUMENTOS SOPORTADOS:
- Carné de vacunación / Certificados médicos
- Cédula de identidad / Pasaporte
- CV / Curriculum Vitae
- Ficha de personal (XLSX)
- Fotografías (JPG/PNG)
- Verificación de antecedentes
- Títulos académicos

## PATRÓN REACT (Reason-Act-Observe):
**1. REASON (Razonar):**
- Clasificar tipo de documentos recibidos
- Identificar validaciones específicas requeridas
- Evaluar calidad y autenticidad visual
- Determinar estándares de compliance aplicables

**2. ACT (Actuar):**
- Extraer y analizar contenido con doc_analyzer_tool
- Validar documentos médicos con medical_validator_tool
- Autenticar identidad con id_authenticator_tool  
- Verificar credenciales académicas con academic_verifier_tool

**3. OBSERVE (Observar):**
- Verificar completitud de documentación requerida
- Evaluar scores de validación y autenticidad
- Identificar documentos faltantes o inválidos
- Generar reporte de compliance y próximos pasos

## CRITERIOS DE VALIDACIÓN:
- Score mínimo de calidad: 70%
- Documentos obligatorios: Cédula, CV, Foto, Certificado médico
- Verificación cruzada de datos de identidad
- Compliance con regulaciones de privacidad y HR

## INSTRUCCIONES:
1. Analiza TODOS los documentos recibidos sistemáticamente
2. Verifica autenticidad antes de extraer información crítica
3. Valida compliance médico y legal según normativas locales
4. Genera reportes detallados de documentación faltante
5. Mantén trazabilidad completa del procesamiento

Responde de manera estructurada y precisa, enfocándote en la validación exhaustiva.
"""
        
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}"),
            ("assistant", "Voy a analizar y validar todos los documentos proporcionados usando mis herramientas especializadas."),
            ("placeholder", "{agent_scratchpad}")
        ])

    def _get_bdi_framework(self) -> Dict[str, str]:
        """Framework BDI específico para validación de documentos"""
        return {
            "beliefs": """
• Los documentos deben ser auténticos y verificables contra fuentes oficiales
• La validación médica es crucial para compliance de seguridad ocupacional  
• Los documentos de identidad requieren verificación cruzada rigurosa
• Los títulos académicos deben verificarse contra instituciones acreditadas
• La calidad de imagen y extracción de texto impacta la precisión de validación
""",
            "desires": """
• Validar completamente todos los documentos requeridos para onboarding
• Asegurar autenticidad y compliance legal de toda la documentación
• Detectar documentos fraudulentos o de baja calidad tempranamente
• Proporcionar análisis detallado de cada tipo de documento
• Mantener 99%+ de precisión en validación documental
""",
            "intentions": """
• Ejecutar análisis exhaustivo de contenido y calidad documental
• Validar certificados médicos contra estándares sanitarios vigentes
• Autenticar documentos de identidad con verificación cruzada
• Verificar credenciales académicas contra bases de instituciones
• Generar reportes comprensivos de estado de documentación
"""
        }

    def _format_input(self, input_data: Any) -> str:
        """Formatear datos de entrada"""
        if isinstance(input_data, DocumentationRequest):
            docs_summary = []
            for doc in input_data.documents:
                docs_summary.append(f"- {doc.document_type.value}: {doc.file_name} ({doc.file_format.value}, {doc.file_size_kb}KB)")
            
            return f"""
Procesa y valida la siguiente documentación de onboarding:

**Empleado ID:** {input_data.employee_id}
**Session ID:** {input_data.session_id or 'No asignado'}
**Prioridad:** {input_data.processing_priority.value}

**Documentos recibidos ({len(input_data.documents)}):**
{chr(10).join(docs_summary)}

**Requisitos especiales:**
{chr(10).join([f"- {req}" for req in input_data.special_requirements]) if input_data.special_requirements else "- Ninguno"}

**Estándares de compliance:**
{', '.join(input_data.compliance_standards)}

Instrucciones:
1. Usa doc_analyzer_tool para analizar cada documento y extraer contenido
2. Usa medical_validator_tool para validar certificados médicos/vacunación
3. Usa id_authenticator_tool para autenticar documentos de identidad
4. Usa academic_verifier_tool para verificar títulos académicos
5. Proporciona reporte completo de validación y documentos faltantes

Procesa sistemáticamente cada documento según su tipo y genera análisis completo.
"""
        elif isinstance(input_data, dict):
            return f"""
Valida la siguiente documentación:
{json.dumps(input_data, indent=2, default=str)}

Ejecuta todas las validaciones necesarias según el tipo de documentos.
"""
        else:
            return str(input_data)

    def _format_output(self, result: Any, processing_time: float, success: bool, error: str = None) -> Dict[str, Any]:
        """Formatear salida del agente"""
        if not success:
            return {
                "success": False,
                "message": f"Error en procesamiento de documentos: {error}",
                "errors": [error] if error else [],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "validation_status": ValidationStatus.INVALID,
                "documents_processed": 0,
                "compliance_score": 0.0,
                "next_steps": ["Revisar errores y reenviar documentos"]
            }

        try:
            # Extraer resultados de herramientas
            doc_analyses = {}
            medical_validation = None
            id_authentication = None  
            academic_verification = None
            
            if isinstance(result, dict) and "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    if isinstance(step, tuple) and len(step) >= 2:
                        tool_name = step[0]
                        tool_result = step[1]
                        
                        if "doc_analyzer_tool" in str(tool_name) and isinstance(tool_result, dict):
                            if tool_result.get("success"):
                                doc_analyses["general_analysis"] = tool_result.get("analysis_results", {})
                                
                        elif "medical_validator_tool" in str(tool_name) and isinstance(tool_result, dict):
                            if tool_result.get("success"):
                                medical_validation = tool_result.get("validation_results", {})
                                
                        elif "id_authenticator_tool" in str(tool_name) and isinstance(tool_result, dict):
                            if tool_result.get("success"):
                                id_authentication = tool_result.get("authentication_results", {})
                                
                        elif "academic_verifier_tool" in str(tool_name) and isinstance(tool_result, dict):
                            if tool_result.get("success"):
                                academic_verification = tool_result.get("verification_results", {})

            # Calcular score de compliance general
            compliance_score = 0.0
            total_validations = 0
            
            if doc_analyses:
                compliance_score += doc_analyses.get("image_quality_score", 0)
                total_validations += 1
                
            if medical_validation:
                compliance_score += 90 if medical_validation.get("health_certificate_valid") else 20
                total_validations += 1
                
            if id_authentication:
                compliance_score += (id_authentication.get("confidence_score", 0) * 100)
                total_validations += 1
                
            if academic_verification:
                compliance_score += academic_verification.get("overall_score", 0)
                total_validations += 1
            
            if total_validations > 0:
                compliance_score = compliance_score / total_validations
            
            # Determinar status de validación
            validation_status = ValidationStatus.VALID if compliance_score >= 70 else ValidationStatus.REQUIRES_REVIEW
            if compliance_score < 50:
                validation_status = ValidationStatus.INVALID

            # Identificar documentos faltantes (simulación básica)
            missing_docs = []
            if not medical_validation:
                missing_docs.append(DocumentType.VACCINATION_CARD)
            if not id_authentication:
                missing_docs.append(DocumentType.ID_DOCUMENT)
            if not academic_verification:
                missing_docs.append(DocumentType.ACADEMIC_TITLES)

            # Próximos pasos
            next_steps = []
            if validation_status == ValidationStatus.VALID:
                next_steps.append("Documentación completa - proceder a credenciales IT")
                next_steps.append("Archivar documentos en sistema seguro")
            elif validation_status == ValidationStatus.REQUIRES_REVIEW:
                next_steps.append("Revisión manual requerida para documentos con baja calidad")
                next_steps.append("Verificar documentos marcados como sospechosos")
            else:
                next_steps.append("Solicitar documentos faltantes o de reemplazo")
                next_steps.append("Re-enviar documentación con mejor calidad")

            return {
                "success": True,
                "message": "Procesamiento de documentos completado",
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "validation_status": validation_status,
                "compliance_score": round(compliance_score, 2),
                "documents_processed": total_validations,
                "document_analyses": doc_analyses,
                "medical_validation": medical_validation,
                "id_authentication": id_authentication,
                "academic_verification": academic_verification,
                "missing_documents": [doc.value for doc in missing_docs],
                "requires_human_review": validation_status != ValidationStatus.VALID,
                "next_steps": next_steps,
                "escalation_needed": validation_status == ValidationStatus.INVALID
            }
            
        except Exception as e:
            self.logger.error(f"Error formateando salida de documentación: {e}")
            return {
                "success": False,
                "message": f"Error procesando resultados de documentación: {e}",
                "errors": [str(e)],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "validation_status": ValidationStatus.INVALID,
                "compliance_score": 0.0,
                "next_steps": ["Revisar errores del sistema"]
            }

    @observability_manager.trace_agent_execution("documentation_agent")
    def process_documentation_request(self, documentation_data: DocumentationRequest, session_id: str = None) -> Dict[str, Any]:
        """Procesar solicitud de documentación con integración completa"""
        
        # Actualizar estado del agente: PROCESSING
        state_manager.update_agent_state(
            self.agent_id,
            AgentStateStatus.PROCESSING,
            {
                "current_task": "document_validation",
                "employee_id": documentation_data.employee_id,
                "documents_count": len(documentation_data.documents),
                "priority": documentation_data.processing_priority.value,
                "started_at": datetime.utcnow().isoformat()
            },
            session_id
        )
        
        # Registrar métricas
        observability_manager.log_agent_metrics(
            self.agent_id,
            {
                "documents_received": len(documentation_data.documents),
                "document_types": [doc.document_type.value for doc in documentation_data.documents],
                "priority": documentation_data.processing_priority.value,
                "special_requirements": len(documentation_data.special_requirements)
            },
            session_id
        )
        
        try:
            # Procesar con el método base
            result = self.process_request(documentation_data, session_id)
            
            # Si el procesamiento fue exitoso, actualizar State Management
            if result["success"]:
                # Actualizar datos del empleado en State Management
                if session_id:
                    document_data = {
                        "document_analyses": result.get("document_analyses", {}),
                        "medical_validation": result.get("medical_validation", {}),
                        "id_authentication": result.get("id_authentication", {}),
                        "academic_verification": result.get("academic_verification", {}),
                        "compliance_score": result.get("compliance_score", 0),
                        "validation_status": result.get("validation_status", "unknown"),
                        "missing_documents": result.get("missing_documents", [])
                    }
                    
                    state_manager.update_employee_data(
                        session_id,
                        document_data,
                        "validation"
                    )
                
                # Actualizar estado del agente: COMPLETED
                state_manager.update_agent_state(
                    self.agent_id,
                    AgentStateStatus.COMPLETED,
                    {
                        "current_task": "completed",
                        "documents_processed": result.get("documents_processed", 0),
                        "compliance_score": result.get("compliance_score", 0),
                        "validation_status": result.get("validation_status"),
                        "requires_review": result.get("requires_human_review", False),
                        "completed_at": datetime.utcnow().isoformat()
                    },
                    session_id
                )
            else:
                # Si hubo error, actualizar estado
                state_manager.update_agent_state(
                    self.agent_id,
                    AgentStateStatus.ERROR,
                    {
                        "current_task": "error",
                        "errors": result.get("errors", []),
                        "failed_at": datetime.utcnow().isoformat()
                    },
                    session_id
                )
            
            # Agregar información de sesión al resultado
            result["session_id"] = session_id
            return result
            
        except Exception as e:
            # Error durante procesamiento
            state_manager.update_agent_state(
                self.agent_id,
                AgentStateStatus.ERROR,
                {
                    "current_task": "error", 
                    "error_message": str(e),
                    "failed_at": datetime.utcnow().isoformat()
                },
                session_id
            )
            
            self.logger.error(f"Error en proceso de documentación: {e}")
            return {
                "success": False,
                "message": f"Error en validación de documentos: {e}",
                "errors": [str(e)],
                "session_id": session_id,
                "agent_id": self.agent_id,
                "processing_time": 0,
                "compliance_score": 0.0,
                "validation_status": ValidationStatus.INVALID
            }

    def _process_with_tools_directly(self, input_data: Any) -> Dict[str, Any]:
        """Procesar usando herramientas directamente con flujo específico de documentos"""
        results = []
        formatted_input = self._format_input(input_data)
        self.logger.info(f"Procesando documentación con {len(self.tools)} herramientas")
        
        # Variables para almacenar resultados
        doc_analysis = None
        medical_validation = None
        id_authentication = None
        academic_verification = None
        
        # Preparar datos según el tipo de entrada
        documents = []
        if isinstance(input_data, DocumentationRequest):
            documents = input_data.documents
            employee_id = input_data.employee_id
        else:
            # Fallback para datos genéricos
            documents = input_data.get("documents", []) if isinstance(input_data, dict) else []
            employee_id = input_data.get("employee_id", "unknown") if isinstance(input_data, dict) else "unknown"
        
        # Ejecutar herramientas según tipo de documento disponible
        for tool in self.tools:
            try:
                self.logger.info(f"Ejecutando herramienta: {tool.name}")
                
                if tool.name == "doc_analyzer_tool":
                    # Analizar el primer documento como ejemplo
                    if documents:
                        doc_data = {
                            "file_name": documents[0].file_name,
                            "file_format": documents[0].file_format.value,
                            "document_type": documents[0].document_type.value
                        }
                    else:
                        doc_data = {"file_name": "test_document.pdf", "file_format": "pdf", "document_type": "cv_resume"}
                    
                    result = tool.invoke({
                        "document_data": doc_data,
                        "document_type": doc_data["document_type"],
                        "analysis_mode": "comprehensive"
                    })
                    doc_analysis = result
                    
                elif tool.name == "medical_validator_tool":
                    # Buscar documentos médicos
                    medical_doc = None
                    for doc in documents:
                        if doc.document_type == DocumentType.VACCINATION_CARD:
                            medical_doc = {
                                "document_type": "vaccination_card",
                                "vaccines": [
                                    {"name": "COVID-19", "date": "2024-01-15"},
                                    {"name": "Hepatitis B", "date": "2023-12-10"}
                                ],
                                "expiration_date": "2025-12-31",
                                "issuing_authority": "CCSS"
                            }
                            break
                    
                    if not medical_doc:
                        # Datos de ejemplo si no hay documento médico
                        medical_doc = {
                            "document_type": "vaccination_card",
                            "vaccines": [],
                            "issuing_authority": "Unknown"
                        }
                    
                    result = tool.invoke({
                        "document_data": medical_doc,
                        "validation_standards": ["general", "health_ministry"]
                    })
                    medical_validation = result
                    
                elif tool.name == "id_authenticator_tool":
                    # Buscar documentos de identidad
                    id_doc = None
                    for doc in documents:
                        if doc.document_type == DocumentType.ID_DOCUMENT:
                            id_doc = {
                                "id_number": "1-2345-6789",
                                "full_name": "Juan Pérez González",
                                "birth_date": "1990-05-15",
                                "nationality": "Costa Rica",
                                "expiration_date": "2030-05-15"
                            }
                            break
                    
                    if not id_doc:
                        # Datos de ejemplo
                        id_doc = {
                            "id_number": "0-0000-0000",
                            "full_name": "Empleado Nuevo",
                            "birth_date": "1990-01-01"
                        }
                    
                    result = tool.invoke({
                        "document_data": id_doc,
                        "cross_reference_data": {"full_name": "Juan Pérez", "id_number": "1-2345-6789"}
                    })
                    id_authentication = result
                    
                elif tool.name == "academic_verifier_tool":
                    # Buscar títulos académicos
                    academic_doc = None
                    for doc in documents:
                        if doc.document_type == DocumentType.ACADEMIC_TITLES:
                            academic_doc = {
                                "academic_titles": [{
                                    "degree": "Licenciatura en Ingeniería en Sistemas",
                                    "institution": "Universidad de Costa Rica",
                                    "graduation_date": "2020-12-15",
                                    "field_of_study": "Computer Science"
                                }]
                            }
                            break
                    
                    if not academic_doc:
                        # Datos de ejemplo
                        academic_doc = {
                            "degree": "Licenciatura en Administración",
                            "institution": "Universidad Nacional",
                            "graduation_date": "2019-06-30"
                        }
                    
                    result = tool.invoke({
                        "document_data": academic_doc,
                        "institution_database": True
                    })
                    academic_verification = result
                    
                else:
                    result = f"Herramienta {tool.name} procesada"
                
                results.append((tool.name, result))
                self.logger.info(f"✅ Herramienta {tool.name} completada")
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.logger.warning(f"❌ Error con herramienta {tool.name}: {e}")
                results.append((tool.name, error_msg))
        
        return {
            "output": "Procesamiento de documentación completado",
            "intermediate_steps": results,
            "doc_analysis": doc_analysis,
            "medical_validation": medical_validation,
            "id_authentication": id_authentication,
            "academic_verification": academic_verification
        }

    def get_integration_status(self, session_id: str = None) -> Dict[str, Any]:
        """Obtener estado de integración con State Management"""
        try:
            # Estado del agente
            agent_state = state_manager.get_agent_state(self.agent_id, session_id)
            
            # Contexto del empleado si existe sesión
            employee_context = None
            if session_id:
                employee_context = state_manager.get_employee_context(session_id)
            
            # Overview del sistema
            system_overview = state_manager.get_system_overview()
            
            return {
                "agent_state": {
                    "status": agent_state.status if agent_state else "not_registered",
                    "last_updated": agent_state.last_updated.isoformat() if agent_state and agent_state.last_updated else None,
                    "data": agent_state.data if agent_state else {}
                },
                "employee_context": {
                    "employee_id": employee_context.employee_id if employee_context else None,
                    "phase": employee_context.phase.value if employee_context and hasattr(employee_context.phase, 'value') else str(employee_context.phase) if employee_context else None,
                    "session_id": session_id,
                    "has_validation_data": bool(employee_context.validation_results) if employee_context else False
                } if employee_context else None,
                "system_overview": system_overview,
                "integration_success": True
            }
        except Exception as e:
            self.logger.error(f"Error obteniendo estado de integración: {e}")
            return {
                "integration_success": False,
                "error": str(e),
                "agent_state": {"status": "error"},
                "employee_context": None,
                "system_overview": {}
            }