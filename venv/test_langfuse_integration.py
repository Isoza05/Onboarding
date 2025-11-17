"""
Test usando LangGraph para generar la visualización de diagrama en Langfuse
"""
import os
from datetime import datetime
from dotenv import load_dotenv
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langfuse.langchain import CallbackHandler

load_dotenv()

# Definir el estado del grafo
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    email_data: dict
    parsed_data: dict
    structured_data: dict
    validation_results: dict
    quality_assessment: dict
    session_id: str
    current_step: str

def create_onboarding_graph():
    """Crear el grafo de LangGraph para visualización"""
    
    # Configurar LLM
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.1,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Configurar Langfuse
    os.environ["LANGFUSE_PUBLIC_KEY"] = os.getenv("LANGFUSE_PUBLIC_KEY")
    os.environ["LANGFUSE_SECRET_KEY"] = os.getenv("LANGFUSE_SECRET_KEY") 
    os.environ["LANGFUSE_BASE_URL"] = os.getenv("LANGFUSE_BASE_URL")
    
    langfuse_handler = CallbackHandler()
    
    # Definir nodos del grafo
    def agent_initialization(state: AgentState):
        """Inicializar el agente"""
        print("🔧 Ejecutando: agent_initialization")
        
        response = llm.invoke(
            state["messages"] + [HumanMessage(content="Inicializando Initial Data Collection Agent con arquitectura BDI y patrón ReAct. Configurando herramientas especializadas.")],
            config={
                "callbacks": [langfuse_handler],
                "tags": ["agent_initialization", "setup"],
                "metadata": {
                    "session_id": state["session_id"],
                    "step": "agent_initialization",
                    "component": "agent_setup"
                }
            }
        )
        
        return {
            "messages": [response],
            "current_step": "agent_initialization"
        }
    
    def email_reception(state: AgentState):
        """Procesar recepción del email"""
        print("📧 Ejecutando: email_reception")
        
        response = llm.invoke(
            [HumanMessage(content=f"Procesando email de onboarding: {state['email_data']['subject']}. Email recibido y validado para procesamiento.")],
            config={
                "callbacks": [langfuse_handler],
                "tags": ["email_reception", "input_processing"],
                "metadata": {
                    "session_id": state["session_id"],
                    "step": "email_reception",
                    "email_subject": state["email_data"]["subject"]
                }
            }
        )
        
        return {
            "messages": state["messages"] + [response],
            "current_step": "email_reception"
        }
    
    def email_parser_tool(state: AgentState):
        """Ejecutar herramienta de parseo"""
        print("🔍 Ejecutando: email_parser_tool")
        
        response = llm.invoke(
            [HumanMessage(content="Ejecutando email_parser_tool: Analizando estructura del email, identificando campos de datos, extrayendo información estructurada.")],
            config={
                "callbacks": [langfuse_handler],
                "tags": ["email_parser_tool", "tool_execution"],
                "metadata": {
                    "session_id": state["session_id"],
                    "step": "email_parser_tool",
                    "tool_order": 1
                }
            }
        )
        
        parsed_data = {
            "success": True,
            "fields_extracted": 9,
            "confidence": 0.92
        }
        
        return {
            "messages": state["messages"] + [response],
            "parsed_data": parsed_data,
            "current_step": "email_parser_tool"
        }
    
    def data_extractor_tool(state: AgentState):
        """Ejecutar herramienta de extracción"""
        print("📊 Ejecutando: data_extractor_tool")
        
        response = llm.invoke(
            [HumanMessage(content="Ejecutando data_extractor_tool: Estructurando datos según schema definido, normalizando campos, creando objeto EmployeeData.")],
            config={
                "callbacks": [langfuse_handler],
                "tags": ["data_extractor_tool", "tool_execution"],
                "metadata": {
                    "session_id": state["session_id"],
                    "step": "data_extractor_tool",
                    "tool_order": 2
                }
            }
        )
        
        structured_data = {
            "success": True,
            "employee_data": {
                "name": "Ana María González",
                "id_card": "98765432",
                "email": "ana.gonzalez@empresa.com"
            },
            "completeness": 0.85
        }
        
        return {
            "messages": state["messages"] + [response],
            "structured_data": structured_data,
            "current_step": "data_extractor_tool"
        }
    
    def format_validator_tool(state: AgentState):
        """Ejecutar herramienta de validación"""
        print("✅ Ejecutando: format_validator_tool")
        
        response = llm.invoke(
            [HumanMessage(content="Ejecutando format_validator_tool: Validando formatos de email, teléfono, cédula, fechas. Verificando consistencia de datos.")],
            config={
                "callbacks": [langfuse_handler],
                "tags": ["format_validator_tool", "tool_execution"],
                "metadata": {
                    "session_id": state["session_id"],
                    "step": "format_validator_tool",
                    "tool_order": 3
                }
            }
        )
        
        validation_results = {
            "is_valid": False,
            "errors": ["Phone format invalid", "Missing passport"],
            "validation_score": 0.78
        }
        
        return {
            "messages": state["messages"] + [response],
            "validation_results": validation_results,
            "current_step": "format_validator_tool"
        }
    
    def quality_assessor_tool(state: AgentState):
        """Ejecutar herramienta de evaluación de calidad"""
        print("⭐ Ejecutando: quality_assessor_tool")
        
        response = llm.invoke(
            [HumanMessage(content="Ejecutando quality_assessor_tool: Evaluando completitud de datos, calculando puntuación de calidad, identificando campos faltantes.")],
            config={
                "callbacks": [langfuse_handler],
                "tags": ["quality_assessor_tool", "tool_execution"],
                "metadata": {
                    "session_id": state["session_id"],
                    "step": "quality_assessor_tool",
                    "tool_order": 4
                }
            }
        )
        
        quality_assessment = {
            "quality_score": 7.41,
            "requires_manual_review": True,
            "missing_fields": ["passport", "emergency_contact"]
        }
        
        return {
            "messages": state["messages"] + [response],
            "quality_assessment": quality_assessment,
            "current_step": "quality_assessor_tool"
        }
    
    def results_integration(state: AgentState):
        """Integrar resultados"""
        print("🔗 Ejecutando: results_integration")
        
        response = llm.invoke(
            [HumanMessage(content="Integrando resultados de todas las herramientas: Parser exitoso, extractor completado, validator con advertencias, quality assessor indica revisión manual.")],
            config={
                "callbacks": [langfuse_handler],
                "tags": ["results_integration", "workflow_completion"],
                "metadata": {
                    "session_id": state["session_id"],
                    "step": "results_integration",
                    "tools_executed": 4
                }
            }
        )
        
        return {
            "messages": state["messages"] + [response],
            "current_step": "results_integration"
        }
    
    def agent_handoff(state: AgentState):
        """Preparar handoff al siguiente agente"""
        print("🤝 Ejecutando: agent_handoff")
        
        response = llm.invoke(
            [HumanMessage(content="Preparando handoff al siguiente agente: Datos procesados y validados, listo para confirmation_data_agent.")],
            config={
                "callbacks": [langfuse_handler],
                "tags": ["agent_handoff", "workflow_transition"],
                "metadata": {
                    "session_id": state["session_id"],
                    "step": "agent_handoff",
                    "next_agent": "confirmation_data_agent"
                }
            }
        )
        
        return {
            "messages": state["messages"] + [response],
            "current_step": "agent_handoff"
        }
    
    # Crear el grafo
    workflow = StateGraph(AgentState)
    
    # Agregar nodos
    workflow.add_node("agent_initialization", agent_initialization)
    workflow.add_node("email_reception", email_reception)
    workflow.add_node("email_parser_tool", email_parser_tool)
    workflow.add_node("data_extractor_tool", data_extractor_tool)
    workflow.add_node("format_validator_tool", format_validator_tool)
    workflow.add_node("quality_assessor_tool", quality_assessor_tool)
    workflow.add_node("results_integration", results_integration)
    workflow.add_node("agent_handoff", agent_handoff)
    
    # Definir el flujo
    workflow.add_edge(START, "agent_initialization")
    workflow.add_edge("agent_initialization", "email_reception")
    workflow.add_edge("email_reception", "email_parser_tool")
    workflow.add_edge("email_parser_tool", "data_extractor_tool")
    workflow.add_edge("data_extractor_tool", "format_validator_tool")
    workflow.add_edge("format_validator_tool", "quality_assessor_tool")
    workflow.add_edge("quality_assessor_tool", "results_integration")
    workflow.add_edge("results_integration", "agent_handoff")
    workflow.add_edge("agent_handoff", END)
    
    return workflow.compile()

def test_langgraph_visualization():
    """Test usando LangGraph para generar visualización de diagrama"""
    
    print("🚀 Test: LangGraph Visualization para Langfuse...")
    
    try:
        # Crear el grafo
        app = create_onboarding_graph()
        
        # Configurar Langfuse
        langfuse_handler = CallbackHandler()
        
        # Crear session_id único
        session_id = f"langgraph_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"🆔 Session ID: {session_id}")
        
        # Estado inicial
        initial_state = {
            "messages": [HumanMessage(content="Iniciando workflow de onboarding con LangGraph")],
            "email_data": {
                "subject": "Nuevo Colaborador - Ana María González",
                "sender": "rrhh@empresa.com",
                "body": "Información del nuevo colaborador..."
            },
            "parsed_data": {},
            "structured_data": {},
            "validation_results": {},
            "quality_assessment": {},
            "session_id": session_id,
            "current_step": "start"
        }
        
        # Ejecutar el grafo con Langfuse
        print("🔄 Ejecutando grafo completo...")
        
        final_state = app.invoke(
            initial_state,
            config={
                "callbacks": [langfuse_handler],
                "tags": ["langgraph", "complete_workflow", "onboarding"],
                "metadata": {
                    "session_id": session_id,
                    "workflow_type": "onboarding_agent",
                    "graph_structure": "sequential_pipeline"
                }
            }
        )
        
        print("✅ Grafo ejecutado completamente")
        print(f"📊 Session ID: {session_id}")
        print(f"📋 Último paso: {final_state['current_step']}")
        
        print("\n🎯 Ve la visualización del grafo en:")
        print(f"https://us.cloud.langfuse.com/project/cmhtk3pbw0042ad07aylg5bei/sessions")
        print(f"🔍 Busca Session ID: {session_id}")
        print("\n📊 También ve los traces individuales en:")
        print(f"https://us.cloud.langfuse.com/project/cmhtk3pbw0042ad07aylg5bei/traces")
        
        return session_id
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🚀 Iniciando test de LangGraph para visualización...")
    
    session_id = test_langgraph_visualization()
    
    if session_id:
        print(f"\n🎉 ¡Test exitoso!")
        print(f"📊 Session: {session_id}")
        print("\n💡 Ahora deberías ver:")
        print("1. 📈 El diagrama de flujo en la sección Sessions")
        print("2. 🔍 Los traces detallados en la sección Traces") 
        print("3. 📊 Métricas en el Dashboard")
    else:
        print("\n❌ Error en el test")