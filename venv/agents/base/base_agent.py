from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from core.config import settings
from core.logging_config import get_audit_logger
from core.database import db_manager

# Import compatible de ChatOpenAI
try:
    from langchain_openai import ChatOpenAI
    print("✅ Usando langchain_openai")
except ImportError:
    try:
        from langchain.chat_models import ChatOpenAI
        print("✅ Usando langchain.chat_models")
    except ImportError:
        print("⚠️ ChatOpenAI no disponible, usando mock")
        # Mock simple para desarrollo
        class ChatOpenAI:
            def __init__(self, **kwargs):
                self.model = kwargs.get('model', 'gpt-4')
                self.temperature = kwargs.get('temperature', 0)
            
            def invoke(self, messages):
                return {"content": "Respuesta simulada del LLM"}

class BaseAgent(ABC):
    """Clase base para todos los agentes del sistema"""
    
    def __init__(self, agent_id: str, agent_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.logger = get_audit_logger(agent_id)
        
        # Configurar LLM
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            openai_api_key=settings.openai_api_key
        )
        
        # Memory para el agente
        self.memory = {
            "session_id": None,
            "conversation_history": [],
            "processing_context": {},
            "performance_metrics": {}
        }
        
        # Inicializar herramientas y agente
        self.tools = self._initialize_tools()
        self.prompt = self._create_prompt()
        
        # Simplificar creación de agente
        self.logger.info(f"Agente {self.agent_name} inicializado con {len(self.tools)} herramientas")
        
    @abstractmethod
    def _initialize_tools(self) -> List:
        """Inicializar herramientas específicas del agente"""
        pass
    
    @abstractmethod
    def _create_prompt(self) -> ChatPromptTemplate:
        """Crear prompt específico del agente"""
        pass
    
    @abstractmethod
    def _get_bdi_framework(self) -> Dict[str, str]:
        """Obtener framework BDI específico del agente"""
        pass
    
    def process_request(self, input_data: Any, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Procesar solicitud usando patrón ReAct simplificado"""
        start_time = datetime.utcnow()
        
        try:
            # Configurar sesión
            if session_id:
                self.memory["session_id"] = session_id
            
            # REASON: Analizar la solicitud
            self.logger.info(f"Iniciando procesamiento con {self.agent_name}")
            
            # ACT: Procesar con herramientas directamente
            result = self._process_with_tools_directly(input_data)
            
            # OBSERVE: Evaluar resultados
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Actualizar memoria
            self._update_memory(input_data, result, processing_time)
            
            # Crear audit trail
            try:
                db_manager.create_audit_entry(
                    agent_id=self.agent_id,
                    action=f"{self.agent_id}_processing_completed",
                    data={
                        "session_id": session_id,
                        "processing_time": processing_time,
                        "success": True
                    }
                )
            except Exception as e:
                self.logger.warning(f"Error creando audit trail: {e}")
            
            return self._format_output(result, processing_time, True)
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self.logger.error(f"Error en {self.agent_name}: {e}")
            
            return self._format_output(None, processing_time, False, str(e))
    
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
                tool_input = None
                
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
    @abstractmethod
    def _format_input(self, input_data: Any) -> str:
        """Formatear datos de entrada para el agente"""
        pass
    
    @abstractmethod
    def _format_output(self, result: Any, processing_time: float, success: bool, error: str = None) -> Dict[str, Any]:
        """Formatear datos de salida del agente"""
        pass
    
    def _update_memory(self, input_data: Any, result: Any, processing_time: float):
        """Actualizar memoria del agente"""
        self.memory["conversation_history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "input": str(input_data)[:200] + "..." if len(str(input_data)) > 200 else str(input_data),
            "result": str(result)[:200] + "..." if len(str(result)) > 200 else str(result),
            "processing_time": processing_time
        })
        
        # Mantener solo últimas 5 interacciones
        if len(self.memory["conversation_history"]) > 5:
            self.memory["conversation_history"] = self.memory["conversation_history"][-5:]
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado del agente"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "status": "active",
            "tools_count": len(self.tools),
            "memory_entries": len(self.memory["conversation_history"]),
            "session_id": self.memory.get("session_id"),
            "last_activity": self.memory["conversation_history"][-1]["timestamp"] if self.memory["conversation_history"] else None
        }