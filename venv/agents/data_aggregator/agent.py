from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from agents.base.base_agent import BaseAgent
from datetime import datetime
import json

# Imports del data aggregator
from .tools import (
    data_consolidator_tool, cross_validator_tool,
    readiness_assessor_tool, quality_calculator_tool
)
from .schemas import (
    AggregationRequest, AggregationResult, ConsolidatedEmployeeData,
    ProcessingReadinessAssessment, ValidationLevel, AggregationConfig
)
from .validators import ValidationEngine, FieldValidationStatus

# Imports para integración
from core.state_management.state_manager import state_manager
from core.state_management.models import AgentStateStatus, OnboardingPhase
from core.observability import observability_manager
from core.database import db_manager

class DataAggregatorAgent(BaseAgent):
    """
    Data Aggregator Agent - Consolida y valida datos del DATA COLLECTION HUB.
    
    Implementa arquitectura BDI:
    - Beliefs: Los datos consolidados y validados cruzadamente son más confiables
    - Desires: Proporcionar datos de alta calidad para el pipeline secuencial
    - Intentions: Consolidar, validar, evaluar calidad y preparar datos
    
    Recibe resultados de: Initial Data + Confirmation Data + Documentation
    Produce: Datos consolidados, validados y listos para IT + Contract + Meeting
    """
    
    def __init__(self):
        super().__init__(
            agent_id="data_aggregator_agent",
            agent_name="Data Aggregator & Validation Agent"
        )
        
        # Configuración del agregador
        self.aggregation_config = AggregationConfig.get_default_config()
        self.validation_engine = ValidationEngine(ValidationLevel.STANDARD)
        self.active_aggregations = {}
        
        # Registrar agente en state management
        state_manager.register_agent(
            self.agent_id,
            {
                "version": "1.0",
                "specialization": "data_aggregation_cross_validation",
                "tools_count": len(self.tools),
                "capabilities": {
                    "data_consolidation": True,
                    "cross_validation": True,
                    "quality_assessment": True,
                    "readiness_evaluation": True,
                    "field_validation": True
                },
                "validation_levels": [level.value for level in ValidationLevel],
                "aggregation_config": {
                    "default_validation_level": ValidationLevel.STANDARD.value,
                    "supported_sources": ["initial_data_collection_agent", "confirmation_data_agent", "documentation_agent"]
                }
            }
        )
        self.logger.info("Data Aggregator Agent integrado con State Management")

    def _initialize_tools(self) -> List:
        """Inicializar herramientas de agregación"""
        return [
            data_consolidator_tool,
            cross_validator_tool,
            readiness_assessor_tool,
            quality_calculator_tool
        ]

    def _create_prompt(self) -> ChatPromptTemplate:
        """Crear prompt con framework BDI y patrón ReAct para agregación"""
        bdi = self._get_bdi_framework()
        
        system_prompt = f"""
Eres el Data Aggregator & Validation Agent, especialista en consolidación y validación de datos.

## FRAMEWORK BDI (Belief-Desire-Intention)
**BELIEFS (Creencias):**
{bdi['beliefs']}

**DESIRES (Deseos):**
{bdi['desires']}

**INTENTIONS (Intenciones):**
{bdi['intentions']}

## HERRAMIENTAS DE AGREGACIÓN:
- data_consolidator_tool: Consolida datos de múltiples agentes en estructura unificada
- cross_validator_tool: Realiza validación cruzada y detecta inconsistencias
- readiness_assessor_tool: Evalúa preparación para IT provisioning, contract management, meeting coordination
- quality_calculator_tool: Calcula métricas completas de calidad de datos

## DATOS DE ENTRADA (DATA COLLECTION HUB):
1. **Initial Data Collection Agent**: Datos básicos del empleado, información personal, posición
2. **Confirmation Data Agent**: Términos contractuales validados, salario, beneficios
3. **Documentation Agent**: Estado de documentación, validaciones médicas, académicas, identidad

## DATOS DE SALIDA (PARA SEQUENTIAL PIPELINE):
1. **IT Provisioning Data**: Employee ID, nombres, email, posición, departamento, oficina
2. **Contract Management Data**: Datos contractuales completos, salario, términos, fechas
3. **Meeting Coordination Data**: Información para calendario, project manager, participantes

## VALIDACIONES CRÍTICAS:
- **Identidad**: Consistencia de nombres entre cédula y datos iniciales
- **Contractuales**: Coherencia de salario, fechas, términos de empleo
- **Académicas**: Verificación de títulos y certificaciones
- **Documentales**: Completitud y autenticidad de documentación requerida

## PATRÓN REACT (Reason-Act-Observe):
**1. REASON (Razonar):**
- Analizar calidad y completitud de datos de cada agente fuente
- Identificar inconsistencias y conflictos entre fuentes
- Evaluar nivel de confianza y reliability por fuente
- Determinar campos críticos faltantes o problemáticos

**2. ACT (Actuar):**
- Consolidar datos usando data_consolidator_tool priorizando fuentes más confiables
- Ejecutar validación cruzada con cross_validator_tool para detectar discrepancias
- Calcular métricas de calidad con quality_calculator_tool (completeness, consistency, accuracy)
- Evaluar preparación con readiness_assessor_tool para cada fase del pipeline

**3. OBSERVE (Observar):**
- Verificar que datos consolidados mantengan integridad y consistencia
- Confirmar que métricas de calidad cumplan umbrales mínimos (>70%)
- Validar que datos estén listos para IT provisioning, contract management, meeting coordination
- Generar alertas para datos que requieren intervención manual

## CRITERIOS DE CALIDAD:
- **Completeness Score**: >80% para datos críticos, >70% para datos opcionales
- **Consistency Score**: >90% entre fuentes para campos de identidad
- **Reliability Score**: Basado en success rate de agentes fuente
- **Overall Quality**: >75% para proceder al pipeline secuencial

## UMBRALES DE ESCALACIÓN:
- Quality Score < 60%: Escalación inmediata
- Inconsistencias críticas en identidad: Revisión manual
- Documentación faltante: Solicitar documentos adicionales
- Datos contractuales incompletos: Contactar HR/Legal

## INSTRUCCIONES CRÍTICAS:
1. SIEMPRE consolida datos de los 3 agentes antes de validar
2. Ejecuta validación cruzada exhaustiva para detectar inconsistencias
3. Calcula métricas de calidad completas antes de evaluar preparación
4. Evalúa preparación específica para cada fase del pipeline secuencial
5. Genera reportes detallados de calidad y preparación
6. Escala inmediatamente si detectas problemas críticos de calidad

Procesa con precisión científica, valida con rigor forense y consolida con excelencia técnica.
"""
        
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}"),
            ("assistant", "Voy a consolidar y validar los datos del DATA COLLECTION HUB para preparar el pipeline secuencial."),
            ("placeholder", "{agent_scratchpad}")
        ])

    def _get_bdi_framework(self) -> Dict[str, str]:
        """Framework BDI específico para agregación de datos"""
        return {
            "beliefs": """
• Los datos consolidados de múltiples fuentes son más confiables que datos individuales
• La validación cruzada detecta errores e inconsistencias que pasarían desapercibidas
• La calidad de datos de entrada determina directamente la calidad del pipeline completo
• Los umbrales de calidad deben ser estrictos para evitar problemas downstream
• La preparación adecuada de datos acelera significativamente el pipeline secuencial
• Las inconsistencias en identidad son críticas y requieren resolución inmediata
""",
            "desires": """
• Proporcionar datos consolidados de máxima calidad al pipeline secuencial
• Detectar y resolver todas las inconsistencias entre fuentes de datos
• Asegurar que datos críticos estén completos y validados antes de proceder
• Optimizar la preparación de datos para cada fase específica del pipeline
• Mantener trazabilidad completa de origen y transformaciones de datos
• Minimizar intervención manual mediante validación automatizada exhaustiva
""",
            "intentions": """
• Consolidar inteligentemente datos priorizando fuentes más confiables
• Ejecutar validación cruzada rigurosa para garantizar consistencia
• Calcular métricas de calidad multidimensionales (completeness, consistency, accuracy, reliability)
• Evaluar preparación específica para IT provisioning, contract management, meeting coordination
• Generar reportes detallados de calidad y recomendaciones de mejora
• Escalar proactivamente cuando datos no cumplan estándares de calidad mínimos
"""
        }

    def _format_input(self, input_data: Any) -> str:
        """Formatear datos de entrada para agregación"""
        if isinstance(input_data, AggregationRequest):
            return f"""
Procesa y agrega los siguientes datos del DATA COLLECTION HUB:

**IDENTIFICACIÓN:**
- Employee ID: {input_data.employee_id}
- Session ID: {input_data.session_id}
- Nivel de validación: {input_data.validation_level.value}
- Prioridad: {input_data.priority.value}

**RESULTADOS DE AGENTES FUENTE:**

**1. INITIAL DATA COLLECTION AGENT:**
{self._format_agent_results(input_data.initial_data_results)}

**2. CONFIRMATION DATA AGENT:**
{self._format_agent_results(input_data.confirmation_data_results)}

**3. DOCUMENTATION AGENT:**
{self._format_agent_results(input_data.documentation_results)}

**CONFIGURACIÓN DE AGREGACIÓN:**
- Validación estricta en campos: {', '.join(input_data.strict_validation_fields) if input_data.strict_validation_fields else 'Ninguno'}
- Contexto de orquestación: {'Disponible' if input_data.orchestration_context else 'No disponible'}
- Requisitos especiales: {len(input_data.special_requirements)} elementos

**INSTRUCCIONES DE PROCESAMIENTO:**
1. Usa data_consolidator_tool para unificar datos de los 3 agentes
2. Usa cross_validator_tool para detectar inconsistencias entre fuentes
3. Usa quality_calculator_tool para métricas de calidad completas
4. Usa readiness_assessor_tool para evaluar preparación del pipeline secuencial

**OBJETIVO:** Generar datos consolidados de alta calidad listos para IT Provisioning, Contract Management y Meeting Coordination.
"""
        elif isinstance(input_data, dict):
            return f"""
Agrega y valida los siguientes datos:
{json.dumps(input_data, indent=2, default=str)}

Ejecuta consolidación, validación cruzada y evaluación de calidad completa.
"""
        else:
            return str(input_data)

    def _format_agent_results(self, results: Dict[str, Any]) -> str:
        """Formatear resultados de un agente específico"""
        if not results:
            return "- No hay resultados disponibles"
            
        lines = []
        lines.append(f"- Éxito: {'Sí' if results.get('success') else 'No'}")
        
        if results.get('validation_score'):
            lines.append(f"- Score de validación: {results['validation_score']:.1f}%")
        elif results.get('compliance_score'):
            lines.append(f"- Score de compliance: {results['compliance_score']:.1f}%")
            
        if results.get('processing_time'):
            lines.append(f"- Tiempo de procesamiento: {results['processing_time']:.2f}s")
            
        if results.get('errors'):
            lines.append(f"- Errores: {len(results['errors'])}")
            
        return '\n'.join(lines)

    def _format_output(self, result: Any, processing_time: float, success: bool, error: str = None) -> Dict[str, Any]:
        """Formatear salida de agregación"""
        if not success:
            return {
                "success": False,
                "message": f"Error en agregación de datos: {error}",
                "errors": [error] if error else [],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "aggregation_status": "failed",
                "overall_quality_score": 0.0,
                "ready_for_sequential_pipeline": False,
                "next_actions": ["Revisar errores de agregación", "Verificar calidad de datos fuente"]
            }

        try:
            # Extraer resultado de agregación
            aggregation_result = None
            
            if isinstance(result, dict) and "intermediate_steps" in result:
                # Buscar resultado final de agregación
                consolidated_data = None
                validation_results = None
                quality_metrics = None
                readiness_assessment = None
                
                for step in result["intermediate_steps"]:
                    if isinstance(step, tuple) and len(step) >= 2:
                        tool_name = step[0]
                        tool_result = step[1]
                        
                        if "data_consolidator_tool" in str(tool_name):
                            consolidated_data = tool_result
                        elif "cross_validator_tool" in str(tool_name):
                            validation_results = tool_result
                        elif "quality_calculator_tool" in str(tool_name):
                            quality_metrics = tool_result
                        elif "readiness_assessor_tool" in str(tool_name):
                            readiness_assessment = tool_result

                # Construir resultado agregado
                overall_quality_score = quality_metrics.get("overall_quality_score", 0.0) if quality_metrics else 0.0
                consistency_score = validation_results.get("consistency_score", 100.0) if validation_results else 100.0
                
                # Determinar preparación para pipeline
                ready_for_it = readiness_assessment.get("ready_for_it_provisioning", False) if readiness_assessment else False
                ready_for_contract = readiness_assessment.get("ready_for_contract_management", False) if readiness_assessment else False
                ready_for_meeting = readiness_assessment.get("ready_for_meeting_coordination", False) if readiness_assessment else False
                
                overall_readiness = ready_for_it and ready_for_contract and ready_for_meeting
                
                # Identificar issues críticos
                critical_issues = []
                warnings = []
                
                if validation_results:
                    critical_issues.extend(validation_results.get("critical_issues", []))
                    warnings.extend(validation_results.get("warnings", []))
                    
                if readiness_assessment:
                    critical_issues.extend(readiness_assessment.get("blocking_issues", []))
                
                # Próximas acciones
                next_actions = []
                if overall_readiness and overall_quality_score >= 70:
                    next_actions.extend([
                        "Proceder a IT Provisioning Agent",
                        "Iniciar Contract Management Agent", 
                        "Configurar Meeting Coordination Agent"
                    ])
                else:
                    if readiness_assessment:
                        next_actions.extend(readiness_assessment.get("recommended_actions", []))
                    if overall_quality_score < 70:
                        next_actions.append("Mejorar calidad de datos antes de proceder")
                    if critical_issues:
                        next_actions.append("Resolver issues críticos identificados")

                return {
                    "success": True,
                    "message": "Agregación de datos completada",
                    "agent_id": self.agent_id,
                    "processing_time": processing_time,
                    "aggregation_status": "completed",
                    
                    # Métricas de calidad
                    "overall_quality_score": overall_quality_score,
                    "completeness_score": quality_metrics.get("completeness_score", 0.0) if quality_metrics else 0.0,
                    "consistency_score": consistency_score,
                    "reliability_score": quality_metrics.get("reliability_score", 0.0) if quality_metrics else 0.0,
                    "quality_rating": quality_metrics.get("quality_rating", "Unknown") if quality_metrics else "Unknown",
                    
                    # Preparación para pipeline
                    "ready_for_sequential_pipeline": overall_readiness,
                    "pipeline_readiness": {
                        "it_provisioning": ready_for_it,
                        "contract_management": ready_for_contract,
                        "meeting_coordination": ready_for_meeting
                    },
                    
                    # Datos consolidados
                    "consolidated_data": consolidated_data.get("personal_data", {}) if consolidated_data else {},
                    "data_completeness_percentage": consolidated_data.get("data_completeness_percentage", 0.0) if consolidated_data else 0.0,
                    
                    # Control de calidad
                    "validation_passed": overall_quality_score >= 70 and consistency_score >= 85,
                    "critical_issues": critical_issues,
                    "warnings": warnings,
                    "requires_manual_review": len(critical_issues) > 0 or overall_quality_score < 60,
                    
                    # Próximos pasos
                    "next_phase": "sequential_processing_pipeline" if overall_readiness else "data_quality_improvement",
                    "next_actions": next_actions,
                    
                    # Resultados detallados
                    "aggregation_details": {
                        "consolidation_result": consolidated_data,
                        "validation_result": validation_results,
                        "quality_metrics": quality_metrics,
                        "readiness_assessment": readiness_assessment
                    }
                }

            # Fallback si no hay resultados estructurados
            return {
                "success": True,
                "message": "Procesamiento de agregación completado",
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "aggregation_status": "completed",
                "overall_quality_score": 0.0,
                "ready_for_sequential_pipeline": False,
                "next_actions": ["Verificar resultados de herramientas de agregación"]
            }

        except Exception as e:
            self.logger.error(f"Error formateando salida de agregación: {e}")
            return {
                "success": False,
                "message": f"Error procesando resultados de agregación: {e}",
                "errors": [str(e)],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "aggregation_status": "error"
            }

    @observability_manager.trace_agent_execution("data_aggregator_agent")
    def aggregate_data_collection_results(self, aggregation_request: AggregationRequest, session_id: str = None) -> Dict[str, Any]:
        """Agregar resultados del DATA COLLECTION HUB con validación completa"""
        
        # Generar aggregation_id
        aggregation_id = f"agg_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{aggregation_request.employee_id}"
        
        # Actualizar estado del agregador: PROCESSING
        state_manager.update_agent_state(
            self.agent_id,
            AgentStateStatus.PROCESSING,
            {
                "current_task": "data_aggregation",
                "aggregation_id": aggregation_id,
                "employee_id": aggregation_request.employee_id,
                "validation_level": aggregation_request.validation_level.value,
                "sources_count": 3,  # Initial + Confirmation + Documentation
                "started_at": datetime.utcnow().isoformat()
            },
            session_id
        )

        # Registrar métricas
        observability_manager.log_agent_metrics(
            self.agent_id,
            {
                "validation_level": aggregation_request.validation_level.value,
                "priority": aggregation_request.priority.value,
                "sources_available": len([
                    r for r in [
                        aggregation_request.initial_data_results,
                        aggregation_request.confirmation_data_results,
                        aggregation_request.documentation_results
                    ] if r
                ]),
                "strict_validation_fields": len(aggregation_request.strict_validation_fields),
                "special_requirements": len(aggregation_request.special_requirements)
            },
            session_id
        )

        try:
            # Procesar con el método base
            result = self.process_request(aggregation_request, session_id)

            # Si el procesamiento fue exitoso, actualizar State Management
            if result["success"]:
                # Actualizar datos del empleado en State Management
                if session_id:
                    aggregated_data = {
                        "aggregation_completed": True,
                        "aggregation_id": aggregation_id,
                        "consolidated_data": result.get("consolidated_data", {}),
                        "quality_metrics": {
                            "overall_quality_score": result.get("overall_quality_score", 0),
                            "completeness_score": result.get("completeness_score", 0),
                            "consistency_score": result.get("consistency_score", 0)
                        },
                        "pipeline_readiness": result.get("pipeline_readiness", {}),
                        "ready_for_sequential": result.get("ready_for_sequential_pipeline", False),
                        "next_phase": result.get("next_phase", "sequential_processing_pipeline")
                    }
                    
                    state_manager.update_employee_data(
                        session_id,
                        aggregated_data,
                        "processed"
                    )

                # Actualizar estado del agregador: COMPLETED
                state_manager.update_agent_state(
                    self.agent_id,
                    AgentStateStatus.COMPLETED,
                    {
                        "current_task": "completed",
                        "aggregation_id": aggregation_id,
                        "quality_score": result.get("overall_quality_score", 0),
                        "ready_for_pipeline": result.get("ready_for_sequential_pipeline", False),
                        "validation_passed": result.get("validation_passed", False),
                        "requires_review": result.get("requires_manual_review", False),
                        "completed_at": datetime.utcnow().isoformat()
                    },
                    session_id
                )
                
                # Registrar en agregaciones activas
                self.active_aggregations[aggregation_id] = {
                    "status": "completed",
                    "result": result,
                    "completed_at": datetime.utcnow()
                }

            else:
                # Error en agregación
                state_manager.update_agent_state(
                    self.agent_id,
                    AgentStateStatus.ERROR,
                    {
                        "current_task": "error",
                        "aggregation_id": aggregation_id,
                        "errors": result.get("errors", []),
                        "failed_at": datetime.utcnow().isoformat()
                    },
                    session_id
                )

            # Agregar información de sesión al resultado
            result["aggregation_id"] = aggregation_id
            result["session_id"] = session_id
            return result

        except Exception as e:
            # Error durante agregación
            error_msg = f"Error ejecutando agregación: {str(e)}"
            
            state_manager.update_agent_state(
                self.agent_id,
                AgentStateStatus.ERROR,
                {
                    "current_task": "error",
                    "aggregation_id": aggregation_id,
                    "error_message": error_msg,
                    "failed_at": datetime.utcnow().isoformat()
                },
                session_id
            )

            self.logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "errors": [str(e)],
                "aggregation_id": aggregation_id,
                "session_id": session_id,
                "agent_id": self.agent_id,
                "processing_time": 0,
                "aggregation_status": "failed"
            }

    def _process_with_tools_directly(self, input_data: Any) -> Dict[str, Any]:
        """Procesar usando herramientas directamente con flujo específico de agregación"""
        results = []
        formatted_input = self._format_input(input_data)
        self.logger.info(f"Procesando agregación con {len(self.tools)} herramientas especializadas")
        
        # Variables para almacenar resultados
        consolidation_result = None
        validation_result = None
        quality_result = None
        readiness_result = None
        
        # Preparar datos según el tipo de entrada
        if isinstance(input_data, AggregationRequest):
            agent_results = {
                "initial_data_collection_agent": input_data.initial_data_results,
                "confirmation_data_agent": input_data.confirmation_data_results,
                "documentation_agent": input_data.documentation_results
            }
            employee_id = input_data.employee_id
            validation_level = input_data.validation_level.value
        else:
            # Fallback para datos genéricos
            agent_results = input_data.get("agent_results", {}) if isinstance(input_data, dict) else {}
            employee_id = input_data.get("employee_id", "unknown") if isinstance(input_data, dict) else "unknown"
            validation_level = "standard"

        # Ejecutar herramientas en orden secuencial
        for tool in self.tools:
            try:
                self.logger.info(f"Ejecutando herramienta: {tool.name}")
                
                if tool.name == "data_consolidator_tool":
                    result = tool.invoke({
                        "agent_results": agent_results,
                        "employee_id": employee_id,
                        "validation_level": validation_level
                    })
                    consolidation_result = result
                    
                elif tool.name == "cross_validator_tool":
                    if consolidation_result and consolidation_result.get("success"):
                        result = tool.invoke({
                            "consolidated_data": {
                                "personal_data": consolidation_result.get("personal_data", {}),
                                "academic_data": consolidation_result.get("academic_data", {}),
                                "position_data": consolidation_result.get("position_data", {}),
                                "contractual_data": consolidation_result.get("contractual_data", {}),
                                "documentation_status": consolidation_result.get("documentation_status", {})
                            },
                            "source_data": agent_results,
                            "validation_rules": []
                        })
                        validation_result = result
                    else:
                        result = {"success": False, "error": "No hay datos consolidados para validar"}
                    
                elif tool.name == "quality_calculator_tool":
                    if consolidation_result and validation_result:
                        source_quality_scores = consolidation_result.get("source_data_quality", {})
                        result = tool.invoke({
                            "consolidated_data": {
                                "personal_data": consolidation_result.get("personal_data", {}),
                                "documentation_status": consolidation_result.get("documentation_status", {}),
                                "data_completeness_percentage": consolidation_result.get("data_completeness_percentage", 0)
                            },
                            "validation_results": validation_result,
                            "source_quality_scores": source_quality_scores
                        })
                        quality_result = result
                    else:
                        result = {"success": False, "error": "Faltan datos de consolidación o validación"}
                        
                elif tool.name == "readiness_assessor_tool":
                    if consolidation_result:
                        completeness_requirements = self.aggregation_config.completeness_requirements
                        result = tool.invoke({
                            "consolidated_data": {
                                "personal_data": consolidation_result.get("personal_data", {}),
                                "academic_data": consolidation_result.get("academic_data", {}),
                                "position_data": consolidation_result.get("position_data", {}),
                                "contractual_data": consolidation_result.get("contractual_data", {})
                            },
                            "completeness_requirements": completeness_requirements
                        })
                        readiness_result = result
                    else:
                        result = {"success": False, "error": "No hay datos consolidados para evaluar preparación"}
                        
                else:
                    result = f"Herramienta {tool.name} procesada"

                results.append((tool.name, result))
                self.logger.info(f"✅ Herramienta {tool.name} completada")

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.logger.warning(f"❌ Error con herramienta {tool.name}: {e}")
                results.append((tool.name, error_msg))

        # Evaluar éxito general
        successful_tools = len([r for r in results if isinstance(r, tuple) and isinstance(r[1], dict) and r[1].get("success")])
        overall_success = successful_tools >= 3  # Al menos consolidation, validation, y uno más

        return {
            "output": "Procesamiento de agregación de datos completado",
            "intermediate_steps": results,
            "consolidation_result": consolidation_result,
            "validation_result": validation_result,
            "quality_result": quality_result,
            "readiness_result": readiness_result,
            "successful_tools": successful_tools,
            "overall_success": overall_success,
            "tools_executed": len(results)
        }

    def get_aggregation_status(self, aggregation_id: str) -> Dict[str, Any]:
        """Obtener estado de una agregación específica"""
        try:
            if aggregation_id in self.active_aggregations:
                return {
                    "found": True,
                    "aggregation_id": aggregation_id,
                    **self.active_aggregations[aggregation_id]
                }
            else:
                return {
                    "found": False,
                    "aggregation_id": aggregation_id,
                    "message": "Agregación no encontrada en registros activos"
                }
        except Exception as e:
            return {"found": False, "error": str(e)}

    def get_integration_status(self, session_id: str = None) -> Dict[str, Any]:
        """Obtener estado de integración completo"""
        try:
            # Estado del agregador
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
                "active_aggregations": len(self.active_aggregations),
                "validation_engine": {
                    "validation_level": self.validation_engine.validation_level.value,
                    "validators_count": len(self.validation_engine.validators)
                },
                "employee_context": {
                    "employee_id": employee_context.employee_id if employee_context else None,
                    "phase": employee_context.phase.value if employee_context and hasattr(employee_context.phase, 'value') else str(employee_context.phase) if employee_context else None,
                    "session_id": session_id,
                    "has_processed_data": bool(employee_context.processed_data) if employee_context else False
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
                "validation_engine": {"status": "error"}
            }

    def validate_data_quality(self, consolidated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validar calidad de datos usando validation engine"""
        try:
            validation_result = self.validation_engine.validate_consolidated_data(consolidated_data)
            
            return {
                "success": True,
                "validation_engine_result": validation_result,
                "overall_validation_score": validation_result["overall_score"],
                "field_validations": validation_result["validation_results"],
                "validation_summary": {
                    "total_validations": validation_result["total_validations"],
                    "valid_count": validation_result["valid_count"],
                    "warning_count": validation_result["warning_count"],
                    "error_count": validation_result["error_count"]
                }
            }
        except Exception as e:
            self.logger.error(f"Error en validación de calidad: {e}")
            return {
                "success": False,
                "error": str(e),
                "overall_validation_score": 0.0
            }

    def get_quality_report(self, aggregation_id: str) -> Dict[str, Any]:
        """Generar reporte de calidad para una agregación específica"""
        try:
            if aggregation_id not in self.active_aggregations:
                return {"error": "Agregación no found"}
                
            aggregation_data = self.active_aggregations[aggregation_id]
            result = aggregation_data["result"]
            
            quality_report = {
                "aggregation_id": aggregation_id,
                "employee_id": result.get("employee_id", "unknown"),
                "report_timestamp": datetime.utcnow().isoformat(),
                "quality_metrics": {
                    "overall_quality_score": result.get("overall_quality_score", 0),
                    "completeness_score": result.get("completeness_score", 0),
                    "consistency_score": result.get("consistency_score", 0),
                    "reliability_score": result.get("reliability_score", 0),
                    "quality_rating": result.get("quality_rating", "Unknown")
                },
                "validation_status": {
                    "validation_passed": result.get("validation_passed", False),
                    "critical_issues": result.get("critical_issues", []),
                    "warnings": result.get("warnings", []),
                    "requires_manual_review": result.get("requires_manual_review", False)
                },
                "pipeline_readiness": result.get("pipeline_readiness", {}),
                "recommendations": result.get("next_actions", [])
            }
            
            return quality_report
            
        except Exception as e:
            return {"error": str(e)}