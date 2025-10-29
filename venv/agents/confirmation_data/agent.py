from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from agents.base.base_agent import BaseAgent
from agents.confirmation_data.tools import (
    salary_validator_tool,
    contract_validator_tool, 
    offer_generator_tool,
    compliance_checker_tool
)
from agents.confirmation_data.schemas import (
    ConfirmationRequest,
    ConfirmationResult,
    ValidationConfig
)
from core.database import db_manager
from shared.models import OnboardingStatus
from datetime import datetime
import json

# Imports para integración
from core.state_management.state_manager import state_manager
from core.state_management.models import AgentStateStatus, OnboardingPhase
from core.observability import observability_manager

class ConfirmationDataAgent(BaseAgent):
    """
    Agente especializado en validación de términos contractuales y generación de documentos de oferta.
    
    Implementa arquitectura BDI:
    - Beliefs: Los términos contractuales siguen políticas organizacionales
    - Desires: Validar términos y generar documentos precisos
    - Intentions: Validar salarios, verificar compliance, generar ofertas
    """
    
    def __init__(self):
        # Inicializar configuración de validación
        self.validation_config = ValidationConfig()
        
        super().__init__(
            agent_id="confirmation_data_agent", 
            agent_name="Confirmation Data Agent"
        )
        
        # Registrar agente en state management
        state_manager.register_agent(
            self.agent_id, 
            {
                "version": "1.0",
                "specialization": "contract_validation_offer_generation",
                "tools_count": len(self.tools),
                "validation_config": {
                    "salary_validation": self.validation_config.salary_validation,
                    "policy_compliance": self.validation_config.policy_compliance,
                    "minimum_score": self.validation_config.minimum_validation_score
                }
            }
        )
        
        self.logger.info("Confirmation Data Agent integrado con State Management")
    
    def _initialize_tools(self) -> List:
        """Inicializar herramientas especializadas"""
        return [
            salary_validator_tool,
            contract_validator_tool,
            offer_generator_tool,
            compliance_checker_tool
        ]
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Crear prompt con framework BDI y patrón ReAct"""
        bdi = self._get_bdi_framework()
        
        system_prompt = f"""
        Eres el Confirmation Data Agent, especialista en validación contractual y generación de ofertas.

        ## FRAMEWORK BDI (Belief-Desire-Intention)
        
        **BELIEFS (Creencias):**
        {bdi['beliefs']}
        
        **DESIRES (Deseos):**
        {bdi['desires']}
        
        **INTENTIONS (Intenciones):**
        {bdi['intentions']}
        
        ## HERRAMIENTAS DISPONIBLES:
        - salary_validator_tool: Valida rangos salariales contra políticas empresariales
        - contract_validator_tool: Verifica términos contractuales y fechas
        - offer_generator_tool: Genera cartas de oferta digitales profesionales
        - compliance_checker_tool: Verifica compliance con regulaciones locales
        
        ## PATRÓN REACT (Reason-Act-Observe):
        
        **1. REASON (Razonar):**
        - Analiza los términos contractuales propuestos
        - Evalúa riesgos legales y de compliance
        - Identifica validaciones necesarias según la posición
        
        **2. ACT (Actuar):**
        - Ejecuta validación salarial usando salary_validator_tool
        - Verifica términos usando contract_validator_tool
        - Genera documentos usando offer_generator_tool
        - Verifica compliance usando compliance_checker_tool
        
        **3. OBSERVE (Observar):**
        - Verifica que todas las validaciones sean exitosas
        - Confirma que los documentos cumplan estándares
        - Evalúa la puntuación general de validación
        - Identifica elementos que requieren aprobación adicional
        
        ## CRITERIOS DE VALIDACIÓN:
        - Puntuación mínima de validación: {self.validation_config.minimum_validation_score * 100}%
        - Validación salarial: {'Habilitada' if self.validation_config.salary_validation else 'Deshabilitada'}
        - Compliance obligatorio: {'Sí' if self.validation_config.policy_compliance else 'No'}
        - Tiempo de respuesta objetivo: < 2 segundos
        
        ## INSTRUCCIONES:
        1. Valida SIEMPRE los términos antes de generar documentos
        2. Asegúrate de que el salario esté dentro de las bandas aprobadas
        3. Verifica compliance antes de aprobar cualquier contrato
        4. Genera documentos solo si todas las validaciones pasan
        5. Mantén trazabilidad completa del proceso de validación
        
        Responde de manera profesional y estructurada, enfocándote en precisión legal y contractual.
        """
        
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}"),
            ("assistant", "Voy a procesar y validar los términos contractuales paso a paso usando mis herramientas especializadas."),
            ("placeholder", "{agent_scratchpad}")
        ])
    
    def _get_bdi_framework(self) -> Dict[str, str]:
        """Framework BDI específico para validación contractual"""
        return {
            "beliefs": """
            • Los términos contractuales deben cumplir políticas organizacionales establecidas
            • Los salarios deben estar dentro de las bandas aprobadas para cada posición
            • El compliance legal es obligatorio antes de generar cualquier documento
            • La validación temprana previene problemas legales y de recursos humanos
            • Los documentos generados deben ser profesionales y legalmente sólidos
            """,
            "desires": """
            • Validar exhaustivamente todos los términos contractuales
            • Asegurar que los salarios sean competitivos y estén en banda
            • Generar documentos de oferta de alta calidad y profesionales
            • Mantener 100% de compliance con regulaciones aplicables
            • Proporcionar validaciones precisas para el equipo de contratación
            """,
            "intentions": """
            • Ejecutar validación salarial completa contra bandas establecidas
            • Verificar todos los términos contractuales por consistencia y validez
            • Generar cartas de oferta personalizadas y profesionales
            • Validar compliance con regulaciones locales e internacionales
            • Proporcionar recomendaciones claras para términos no conformes
            """
        }
    
    def _format_input(self, input_data: Any) -> str:
        """Formatear datos de entrada"""
        if isinstance(input_data, ConfirmationRequest):
            return f"""
            Procesa y valida la siguiente solicitud de confirmación contractual:
            
            **Empleado ID:** {input_data.employee_id}
            **Prioridad:** {input_data.priority}
            
            **Términos Contractuales:**
            - Fecha de inicio: {input_data.contract_terms.start_date}
            - Salario: ${input_data.contract_terms.salary:,} {input_data.contract_terms.currency}
            - Tipo de empleo: {input_data.contract_terms.employment_type}
            - Modalidad: {input_data.contract_terms.work_modality}
            - Período de prueba: {input_data.contract_terms.probation_period} días
            - Beneficios: {', '.join(input_data.contract_terms.benefits) if input_data.contract_terms.benefits else 'Estándar'}
            
            **Información de Posición:**
            - Título: {input_data.position_info.position_title}
            - Departamento: {input_data.position_info.department}
            - Manager: {input_data.position_info.reporting_manager}
            - Ubicación: {input_data.position_info.location}
            
            **Notas adicionales:** {input_data.additional_notes or 'Ninguna'}
            
            Instrucciones:
            1. Usa salary_validator_tool para validar el salario propuesto
            2. Usa contract_validator_tool para verificar términos contractuales
            3. Usa compliance_checker_tool para verificar regulaciones
            4. Usa offer_generator_tool para generar la carta de oferta si todo es válido
            
            Proporciona un análisis completo de la validación y documentos generados.
            """
        elif isinstance(input_data, dict):
            return f"""
            Valida los siguientes datos contractuales:
            {json.dumps(input_data, indent=2, default=str)}
            
            Ejecuta todas las validaciones necesarias y genera documentos apropiados.
            """
        else:
            return str(input_data)
    
    def _format_output(self, result: Any, processing_time: float, success: bool, error: str = None) -> Dict[str, Any]:
        """Formatear salida del agente"""
        if not success:
            return {
                "success": False,
                "message": f"Error en procesamiento: {error}",
                "errors": [error] if error else [],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "confirmed_terms": None,
                "validation_score": 0.0,
                "offer_letter_generated": False,
                "compliance_check": {},
                "next_actions": ["Revisar errores y reintentar"]
            }
        
        try:
            # Extraer resultados de herramientas
            salary_validation = None
            contract_validation = None
            compliance_results = None
            offer_letter = None
            
            if isinstance(result, dict) and "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    if isinstance(step, tuple) and len(step) >= 2:
                        tool_name = step[0]
                        tool_result = step[1]
                        
                        if "salary_validator_tool" in str(tool_name) and isinstance(tool_result, dict):
                            salary_validation = tool_result.get("validation_results", {})
                        
                        elif "contract_validator_tool" in str(tool_name) and isinstance(tool_result, dict):
                            contract_validation = tool_result.get("validation_results", {})
                        
                        elif "compliance_checker_tool" in str(tool_name) and isinstance(tool_result, dict):
                            compliance_results = tool_result.get("compliance_results", {})
                        
                        elif "offer_generator_tool" in str(tool_name) and isinstance(tool_result, dict):
                            offer_letter = tool_result.get("offer_letter")
            
            # Calcular puntuación general de validación
            validation_score = 0.0
            score_components = 0
            
            if salary_validation:
                if salary_validation.get("is_valid", False):
                    validation_score += 25
                score_components += 1
            
            if contract_validation:
                if contract_validation.get("is_valid", False):
                    validation_score += 25
                score_components += 1
            
            if compliance_results:
                validation_score += (compliance_results.get("compliance_score", 0) / 100) * 50
                score_components += 1
            
            if score_components > 0:
                validation_score = validation_score / score_components if score_components < 3 else validation_score
            
            # Determinar próximas acciones
            next_actions = []
            if validation_score >= (self.validation_config.minimum_validation_score * 100):
                next_actions.append("Proceder con firma de contrato")
                next_actions.append("Enviar carta de oferta al candidato")
            else:
                next_actions.append("Revisar términos contractuales")
                next_actions.append("Obtener aprobaciones adicionales si es necesario")
            
            if compliance_results and not compliance_results.get("is_compliant", True):
                next_actions.append("Consultar con departamento legal")
            
            return {
                "success": True,
                "message": "Validación contractual completada exitosamente",
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "confirmed_terms": {
                    "salary_validation": salary_validation,
                    "contract_validation": contract_validation,
                    "compliance_results": compliance_results
                },
                "validated_position": True,
                "offer_letter_generated": offer_letter is not None,
                "offer_letter": offer_letter,
                "validation_score": round(validation_score, 2),
                "compliance_check": compliance_results or {},
                "next_actions": next_actions,
                "requires_manual_review": validation_score < (self.validation_config.minimum_validation_score * 100)
            }
            
        except Exception as e:
            self.logger.error(f"Error formateando salida: {e}")
            return {
                "success": False,
                "message": f"Error procesando resultados: {e}",
                "errors": [str(e)],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "confirmed_terms": None,
                "validation_score": 0.0,
                "offer_letter_generated": False,
                "next_actions": ["Revisar errores del sistema"]
            }
    
    @observability_manager.trace_agent_execution("confirmation_data_agent")
    def process_confirmation_request(self, confirmation_data: ConfirmationRequest, session_id: str = None) -> Dict[str, Any]:
        """Procesar solicitud de confirmación con integración completa"""
        
        # Actualizar estado del agente: PROCESSING
        state_manager.update_agent_state(
            self.agent_id,
            AgentStateStatus.PROCESSING,
            {
                "current_task": "contract_validation",
                "employee_id": confirmation_data.employee_id,
                "priority": confirmation_data.priority.value,
                "started_at": datetime.utcnow().isoformat()
            },
            session_id
        )
        
        # Registrar métricas
        observability_manager.log_agent_metrics(
            self.agent_id,
            {
                "request_priority": confirmation_data.priority.value,
                "salary_amount": confirmation_data.contract_terms.salary,
                "position_title": confirmation_data.position_info.position_title
            },
            session_id
        )
        
        try:
            # Procesar con el método base
            result = self.process_request(confirmation_data, session_id)
            
            # Si el procesamiento fue exitoso, actualizar State Management
            if result["success"]:
                
                # Actualizar datos del empleado en State Management
                if session_id:
                    contract_data = {
                        "confirmed_terms": result.get("confirmed_terms", {}),
                        "validation_score": result.get("validation_score", 0),
                        "offer_letter_generated": result.get("offer_letter_generated", False),
                        "compliance_status": result.get("compliance_check", {}).get("is_compliant", False)
                    }
                    
                    state_manager.update_employee_data(
                        session_id,
                        contract_data,
                        "validation"
                    )
                
                # Actualizar estado del agente: COMPLETED
                state_manager.update_agent_state(
                    self.agent_id,
                    AgentStateStatus.COMPLETED,
                    {
                        "current_task": "completed",
                        "validation_score": result.get("validation_score", 0),
                        "offer_generated": result.get("offer_letter_generated", False),
                        "requires_review": result.get("requires_manual_review", False),
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
            
            self.logger.error(f"Error en proceso de confirmación: {e}")
            return {
                "success": False,
                "message": f"Error en validación contractual: {e}",
                "errors": [str(e)],
                "session_id": session_id,
                "agent_id": self.agent_id,
                "processing_time": 0,
                "validation_score": 0.0
            }
    
    def _process_with_tools_directly(self, input_data: Any) -> Dict[str, Any]:
        """Procesar usando herramientas directamente con flujo específico"""
        results = []
        formatted_input = self._format_input(input_data)
        
        self.logger.info(f"Procesando validación contractual con {len(self.tools)} herramientas")
        
        # Variables para almacenar resultados
        salary_validation = None
        contract_validation = None
        compliance_results = None
        offer_letter = None
        
        # Extraer datos según el tipo de entrada
        if isinstance(input_data, ConfirmationRequest):
            salary_data = {
                "position": input_data.position_info.position_title,
                "salary": input_data.contract_terms.salary,
                "currency": input_data.contract_terms.currency,
                "location": input_data.position_info.location or ""
            }
            
            contract_data = input_data.contract_terms.dict()
            contract_data.update(input_data.position_info.dict())
            
        else:
            # Fallback para datos genéricos
            salary_data = input_data if isinstance(input_data, dict) else {}
            contract_data = input_data if isinstance(input_data, dict) else {}
        
        # Ejecutar herramientas en orden lógico
        for tool in self.tools:
            try:
                self.logger.info(f"Ejecutando herramienta: {tool.name}")
                
                if tool.name == "salary_validator_tool":
                    result = tool.invoke({"salary_data": salary_data})
                    salary_validation = result
                    
                elif tool.name == "contract_validator_tool":
                    result = tool.invoke({"contract_data": contract_data})
                    contract_validation = result
                    
                elif tool.name == "compliance_checker_tool":
                    result = tool.invoke({"contract_terms": contract_data})
                    compliance_results = result
                    
                elif tool.name == "offer_generator_tool":
                    # Solo generar oferta si las validaciones anteriores son exitosas
                    should_generate = True
                    
                    if salary_validation and not salary_validation.get("validation_results", {}).get("is_valid", True):
                        should_generate = False
                    
                    if contract_validation and not contract_validation.get("validation_results", {}).get("is_valid", True):
                        should_generate = False
                    
                    if should_generate:
                        employee_data = {
                            "basic_info": {"first_name": "Empleado", "last_name": "Nuevo"},  # Placeholder
                            "contract_terms": contract_data,
                            "position_info": contract_data,
                            "employee_id": getattr(input_data, 'employee_id', 'unknown') if hasattr(input_data, 'employee_id') else 'unknown'
                        }
                        result = tool.invoke({"employee_data": employee_data})
                        offer_letter = result
                    else:
                        result = {"success": False, "message": "Validaciones previas fallaron, no se genera oferta"}
                
                else:
                    result = f"Herramienta {tool.name} procesada"
                
                results.append((tool.name, result))
                self.logger.info(f"✅ Herramienta {tool.name} completada")
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.logger.warning(f"❌ Error con herramienta {tool.name}: {e}")
                results.append((tool.name, error_msg))
        
        return {
            "output": "Validación contractual completada",
            "intermediate_steps": results,
            "salary_validation": salary_validation,
            "contract_validation": contract_validation,
            "compliance_results": compliance_results,
            "offer_letter": offer_letter
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
                "required_validations": ["salary", "contract", "compliance"],
                "minimum_validation_score": self.validation_config.minimum_validation_score,
                "salary_validation_enabled": self.validation_config.salary_validation
            }
        }