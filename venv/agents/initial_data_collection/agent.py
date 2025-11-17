from core.state_management.state_manager import state_manager
from core.state_management.models import AgentStateStatus, OnboardingPhase
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from agents.base.base_agent import BaseAgent
from agents.initial_data_collection.tools import (
    email_parser_tool, 
    data_extractor_tool, 
    format_validator_tool, 
    quality_assessor_tool
)
from agents.initial_data_collection.schemas import (
    RawEmailData, 
    EmployeeData, 
    DataCollectionResult
)
from core.database import db_manager
from shared.models import OnboardingStatus
from datetime import datetime
import json

# NUEVOS IMPORTS PARA LANGFUSE
from langfuse.langchain import CallbackHandler
import os

class DataValidationConfig:
    """Configuración de validación simple"""
    def __init__(self):
        self.required_fields = [
            "basic_info.id_card",
            "basic_info.first_name", 
            "basic_info.last_name"
        ]
        self.minimum_quality_score = 0.8

class InitialDataCollectionAgent(BaseAgent):
    """
    Agente especializado en recolección y validación de datos iniciales de empleados.
    Implementa arquitectura BDI:
    - Beliefs: Los emails contienen datos estructurados que pueden ser extraídos
    - Desires: Extraer información completa y precisa del nuevo empleado
    - Intentions: Parsear, extraer, validar y estructurar datos de onboarding
    """
    
    def __init__(self):
        # IMPORTANTE: Inicializar validation_config ANTES de llamar super()
        self.validation_config = DataValidationConfig()
        
        # Configurar Langfuse ANTES de super()
        self._setup_langfuse()
        
        super().__init__(
            agent_id="initial_data_collection", 
            agent_name="Initial Data Collection Agent"
        )
        
        # Registrar agente en state management
        state_manager.register_agent(
            self.agent_id, 
            {
                "version": "1.0",
                "specialization": "data_extraction_validation",
                "tools_count": len(self.tools)
            }
        )
        self.logger.info("Initial Data Collection Agent integrado con State Management y Langfuse")

    def _setup_langfuse(self):
        """Configurar Langfuse para trazabilidad"""
        try:
            # Verificar variables de entorno
            public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
            secret_key = os.getenv("LANGFUSE_SECRET_KEY")
            base_url = os.getenv("LANGFUSE_BASE_URL")
            
            if not all([public_key, secret_key, base_url]):
                self.langfuse_handler = None
                print("⚠️ Langfuse no configurado - Variables de entorno faltantes")
                return
            
            # Configurar variables de entorno para el handler
            os.environ["LANGFUSE_PUBLIC_KEY"] = public_key
            os.environ["LANGFUSE_SECRET_KEY"] = secret_key
            os.environ["LANGFUSE_BASE_URL"] = base_url
            
            # Crear handler (lee automáticamente del entorno)
            self.langfuse_handler = CallbackHandler()
            
            print("✅ Langfuse handler configurado exitosamente")
            
        except Exception as e:
            print(f"❌ Error configurando Langfuse: {e}")
            self.langfuse_handler = None

    def process_onboarding_email(self, email_data: RawEmailData, session_id: str = None) -> Dict[str, Any]:
        """Procesar email de onboarding específico con integración de State Management y Langfuse Sessions"""
        
        # Crear o usar session_id
        if session_id is None:
            session_id = f"onboarding_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{email_data.subject[:20].replace(' ', '_')}"
        
        # Preparar configuración de trace para LangChain con Sessions
        if self.langfuse_handler:
            try:
                from langfuse import get_client, propagate_attributes
                
                langfuse = get_client()
                
                # Usar sessions de Langfuse con propagate_attributes
                with langfuse.start_as_current_observation(as_type="span", name="onboarding-email-processing"):
                    with propagate_attributes(session_id=session_id):
                        trace_config = {
                            "callbacks": [self.langfuse_handler],
                            "tags": ["onboarding", "data_collection", "email_processing"],
                            "metadata": {
                                "agent_id": self.agent_id,
                                "email_subject": email_data.subject,
                                "email_sender": email_data.sender,
                                "session_id": session_id
                            }
                        }
                        print(f"📊 Configuración de trace Langfuse con Session: {session_id}")
            except Exception as e:
                print(f"⚠️ Error configurando Langfuse sessions: {e}")
                trace_config = {
                    "callbacks": [self.langfuse_handler],
                    "tags": ["onboarding", "data_collection", "email_processing"],
                    "metadata": {
                        "agent_id": self.agent_id,
                        "email_subject": email_data.subject,
                        "session_id": session_id
                    }
                }
        else:
            trace_config = {}
        
        # Crear o usar contexto de empleado en State Management
        if session_id is None:
            session_id = state_manager.create_employee_context(
                {
                    "employee_id": f"temp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    "source": "email",
                    "raw_email_data": {
                        "subject": email_data.subject,
                        "sender": email_data.sender,
                        "received_at": email_data.received_at.isoformat()
                    }
                },
                session_id
            )

        # Actualizar estado del agente: PROCESSING
        state_manager.update_agent_state(
            self.agent_id,
            AgentStateStatus.PROCESSING,
            {
                "current_task": "email_processing",
                "email_subject": email_data.subject,
                "started_at": datetime.utcnow().isoformat()
            },
            session_id
        )

        try:
            # Procesar con trazabilidad de Langfuse
            result = self.process_request(email_data, session_id, trace_config)

            # Si el procesamiento fue exitoso, actualizar State Management
            if result["success"] and result.get("employee_data"):
                # Actualizar datos del empleado en State Management
                state_manager.update_employee_data(
                    session_id,
                    result["employee_data"],
                    "processed"
                )

                # Actualizar datos de validación
                if result.get("validation_summary"):
                    state_manager.update_employee_data(
                        session_id,
                        result["validation_summary"],
                        "validation"
                    )

                # Determinar ID real del empleado
                if isinstance(result["employee_data"], dict) and "basic_info" in result["employee_data"]:
                    employee_id = result["employee_data"]["basic_info"].get("id_card", "unknown")
                    
                    # Actualizar contexto con ID real
                    context = state_manager.get_employee_context(session_id)
                    if context:
                        context.employee_id = employee_id
                        context.phase = OnboardingPhase.DATA_COLLECTION

                # Intentar guardar en base de datos
                try:
                    employee_id = db_manager.save_employee_data(result["employee_data"])
                    result["employee_id"] = employee_id
                    # Actualizar estado
                    db_manager.update_employee_status(employee_id, OnboardingStatus.DATA_COLLECTED.value)
                    self.logger.info(f"Datos de empleado guardados con ID: {employee_id}")
                except Exception as e:
                    self.logger.error(f"Error guardando datos: {e}")
                    result["database_warning"] = f"Error guardando datos: {e}"

                # Actualizar estado del agente: COMPLETED
                state_manager.update_agent_state(
                    self.agent_id,
                    AgentStateStatus.COMPLETED,
                    {
                        "current_task": "completed",
                        "quality_score": result.get("data_quality_score", 0),
                        "requires_manual_review": result.get("requires_manual_review", True),
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
            self.logger.error(f"Error en proceso integrado: {e}")
            return {
                "success": False,
                "message": f"Error en procesamiento: {e}",
                "errors": [str(e)],
                "session_id": session_id,
                "agent_id": self.agent_id,
                "processing_time": 0
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
                    "has_processed_data": bool(employee_context.processed_data) if employee_context else False,
                    "has_validation_results": bool(employee_context.validation_results) if employee_context else False
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

    def _initialize_tools(self) -> List:
        """Inicializar herramientas especializadas"""
        return [
            email_parser_tool,
            data_extractor_tool, 
            format_validator_tool,
            quality_assessor_tool
        ]

    def _create_prompt(self) -> ChatPromptTemplate:
        """Crear prompt con framework BDI y patrón ReAct"""
        bdi = self._get_bdi_framework()
        system_prompt = f"""
Eres el Initial Data Collection Agent, especialista en extracción y validación de datos de onboarding.

## FRAMEWORK BDI (Belief-Desire-Intention)
**BELIEFS (Creencias):**
{bdi['beliefs']}

**DESIRES (Deseos):**
{bdi['desires']}

**INTENTIONS (Intenciones):**
{bdi['intentions']}

## HERRAMIENTAS DISPONIBLES:
- email_parser_tool: Parsea el contenido del email y extrae campos estructurados
- data_extractor_tool: Estructura los datos según el schema definido  
- format_validator_tool: Valida formatos y consistencia de datos
- quality_assessor_tool: Evalúa la calidad y completitud de los datos

## PATRÓN REACT (Reason-Act-Observe):
**1. REASON (Razonar):**
- Analiza el email recibido y su estructura
- Identifica patrones de datos y campos disponibles
- Planifica la estrategia de extracción más efectiva

**2. ACT (Actuar):**
- Ejecuta el parseo del email usando email_parser_tool
- Estructura los datos usando data_extractor_tool
- Valida formatos usando format_validator_tool
- Evalúa calidad usando quality_assessor_tool

**3. OBSERVE (Observar):**
- Verifica la calidad de los resultados obtenidos
- Identifica campos faltantes o con errores
- Determina si se requiere intervención manual
- Actualiza el contexto para futuras mejoras

## REQUERIMIENTOS DE CALIDAD:
- Puntuación mínima de calidad: {self.validation_config.minimum_quality_score * 100}%
- Campos requeridos: {', '.join(self.validation_config.required_fields)}
- Tiempo de respuesta objetivo: < 2 segundos

## INSTRUCCIONES:
1. Siempre usa las herramientas en el orden correcto
2. Valida que los datos cumplan estándares de calidad
3. Proporciona retroalimentación clara sobre cualquier problema
4. Mantén trazabilidad completa del proceso

Responde de manera profesional, clara y estructurada.
"""
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}"),
            ("assistant", "Voy a procesar la información del nuevo empleado paso a paso usando mis herramientas especializadas."),
            ("placeholder", "{agent_scratchpad}")
        ])

    def _get_bdi_framework(self) -> Dict[str, str]:
        """Framework BDI específico para recolección de datos"""
        return {
            "beliefs": """
• Los emails de onboarding contienen datos estructurados en formato de tabla
• La información puede estar en diferentes formatos pero sigue patrones consistentes  
• Los datos extraídos deben cumplir estándares de calidad para el procesamiento posterior
• La validación temprana previene errores en etapas subsecuentes del onboarding
""",
            "desires": """
• Extraer información completa y precisa del nuevo empleado
• Mantener alta calidad de datos (>80% completitud)
• Identificar automáticamente campos faltantes o incorrectos
• Proporcionar datos estructurados listos para el siguiente agente
""",
            "intentions": """
• Parsear el contenido del email de manera inteligente
• Extraer y normalizar todos los campos identificados
• Validar formatos de datos críticos (fechas, emails, números)
• Evaluar la calidad general y recomendar acciones
"""
        }

    def _format_input(self, input_data: Any) -> str:
        """Formatear datos de entrada"""
        if isinstance(input_data, RawEmailData):
            return f"""
Procesa la siguiente información de onboarding de un nuevo empleado:

**Asunto del Email:** {input_data.subject}
**Remitente:** {input_data.sender}
**Fecha de Recepción:** {input_data.received_at}

**Contenido del Email:**
{input_data.body}

Instrucciones:
1. Usa email_parser_tool para extraer los datos del contenido
2. Usa data_extractor_tool para estructurar la información
3. Usa format_validator_tool para validar los formatos
4. Usa quality_assessor_tool para evaluar la calidad

Proporciona un resumen completo del procesamiento y cualquier problema encontrado.
"""
        elif isinstance(input_data, dict):
            return f"""
Procesa los siguientes datos de empleado:
{json.dumps(input_data, indent=2, default=str)}

Valida la información y proporciona un análisis de calidad.
"""
        else:
            return str(input_data)

    def get_status(self) -> Dict[str, Any]:
        """Obtener estado del agente"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "status": "active",
            "tools_count": len(self.tools) if hasattr(self, 'tools') else 0,
            "memory_entries": len(self.memory.get("conversation_history", [])) if hasattr(self, 'memory') else 0,
            "session_id": self.memory.get("session_id") if hasattr(self, 'memory') else None,
            "last_activity": self.memory["conversation_history"][-1]["timestamp"] if hasattr(self, 'memory') and self.memory.get("conversation_history") else None,
            "validation_config": {
                "required_fields": len(self.validation_config.required_fields),
                "minimum_quality_score": self.validation_config.minimum_quality_score
            },
            "langfuse_enabled": self.langfuse_handler is not None,
            # AGREGADOS: Información del LLM
            "llm_type": self.llm.__class__.__name__ if hasattr(self, 'llm') else 'unknown',
            "llm_model": getattr(self.llm, 'model', 'unknown') if hasattr(self, 'llm') else 'unknown'
        }

    def _format_output(self, result: Any, processing_time: float, success: bool, error: str = None) -> Dict[str, Any]:
        """Formatear salida del agente"""
        if not success:
            return {
                "success": False,
                "message": f"Error en procesamiento: {error}",
                "errors": [error] if error else [],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "employee_data": None,
                "validation_summary": {},
                "missing_fields": [],
                "data_quality_score": None,
                "requires_manual_review": True
            }

        try:
            # Extraer resultados directos si están disponibles
            structured_data = None
            validation_results = {}
            quality_assessment = {}

            if isinstance(result, dict):
                structured_data = result.get("structured_data")
                validation_results = result.get("validation_results", {})
                quality_assessment = result.get("quality_assessment", {})

                # También buscar en intermediate_steps
                intermediate_steps = result.get("intermediate_steps", [])
                for step in intermediate_steps:
                    if isinstance(step, tuple) and len(step) >= 2:
                        tool_name = step[0]
                        tool_result = step[1]

                        if "data_extractor_tool" in str(tool_name) and isinstance(tool_result, dict):
                            if tool_result.get("success") and tool_result.get("structured_data"):
                                structured_data = tool_result["structured_data"]
                        elif "format_validator_tool" in str(tool_name):
                            validation_results = tool_result if isinstance(tool_result, dict) else {}
                        elif "quality_assessor_tool" in str(tool_name):
                            quality_assessment = tool_result if isinstance(tool_result, dict) else {}

            # Extraer métricas de calidad
            quality_score = quality_assessment.get("quality_score", 0.0)
            missing_fields = quality_assessment.get("missing_fields", [])
            requires_manual_review = quality_assessment.get("requires_manual_review", True)

            # Construir resultado final
            return {
                "success": True,
                "message": "Procesamiento completado exitosamente",
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "employee_data": structured_data,
                "validation_summary": validation_results,
                "missing_fields": missing_fields,
                "data_quality_score": quality_score,
                "requires_manual_review": requires_manual_review
            }

        except Exception as e:
            self.logger.error(f"Error formateando salida: {e}")
            return {
                "success": False,
                "message": f"Error formateando resultados: {e}",
                "errors": [str(e)],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "employee_data": None,
                "validation_summary": {},
                "missing_fields": [],
                "data_quality_score": 0.0,
                "requires_manual_review": True
            }

    def _process_with_tools_directly(self, input_data: Any) -> Dict[str, Any]:
        """Procesar usando herramientas directamente con flujo correcto"""
        results = []
        formatted_input = self._format_input(input_data)
        self.logger.info(f"Procesando con {len(self.tools)} herramientas")

        # Variables para almacenar resultados intermedios
        parsed_data = None
        structured_data = None
        validation_results = None
        quality_assessment = None

        for tool in self.tools:
            try:
                self.logger.info(f"Ejecutando herramienta: {tool.name}")
                
                # Preparar input específico para cada herramienta
                if tool.name == "email_parser_tool":
                    # Primera herramienta: usar el cuerpo del email
                    if hasattr(input_data, 'body'):
                        tool_input = input_data.body
                    else:
                        tool_input = str(input_data)
                    result = tool.invoke({"email_body": tool_input})
                    parsed_data = result

                elif tool.name == "data_extractor_tool":
                    # Segunda herramienta: usar resultado del parser
                    if parsed_data:
                        result = tool.invoke({"parsed_content": parsed_data})
                        structured_data = result
                    else:
                        result = {"success": False, "error": "No hay datos parseados disponibles"}

                elif tool.name == "format_validator_tool":
                    # Tercera herramienta: usar datos estructurados
                    if structured_data and structured_data.get("success") and structured_data.get("structured_data"):
                        result = tool.invoke({"employee_data": structured_data["structured_data"]})
                        validation_results = result
                    else:
                        result = {"is_valid": False, "errors": ["No hay datos estructurados disponibles"]}

                elif tool.name == "quality_assessor_tool":
                    # Cuarta herramienta: usar datos estructurados
                    if structured_data and structured_data.get("success") and structured_data.get("structured_data"):
                        result = tool.invoke({"employee_data": structured_data["structured_data"]})
                        quality_assessment = result
                    else:
                        result = {"quality_score": 0.0, "requires_manual_review": True}

                else:
                    # Herramienta genérica: usar input formateado
                    if hasattr(tool, 'invoke'):
                        result = tool.invoke({"input": formatted_input})
                    elif hasattr(tool, 'run'):
                        result = tool.run(formatted_input)
                    else:
                        result = f"Herramienta {tool.name} procesada"

                results.append((tool.name, result))
                self.logger.info(f"✅ Herramienta {tool.name} completada")

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.logger.warning(f"❌ Error con herramienta {tool.name}: {e}")
                results.append((tool.name, error_msg))

        return {
            "output": "Procesamiento completado con herramientas directas",
            "intermediate_steps": results,
            "parsed_data": parsed_data,
            "structured_data": structured_data,
            "validation_results": validation_results,
            "quality_assessment": quality_assessment
        }