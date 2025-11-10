from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from agents.base.base_agent import BaseAgent
from datetime import datetime
import json

# Imports del error classification
from .tools import (
    error_detector_tool, severity_analyzer_tool, 
    root_cause_finder_tool, routing_engine_tool
)
from .schemas import (
    ErrorClassificationRequest, ErrorClassificationResult, ErrorCategory, 
    ErrorType, ErrorSeverity, ErrorSource, RecoveryStrategy,
    RootCauseAnalysis, ErrorPattern
)

# Imports para integración
from core.state_management.state_manager import state_manager
from core.state_management.models import AgentStateStatus, OnboardingPhase
from core.observability import observability_manager
from core.database import db_manager

class ErrorClassificationAgent(BaseAgent):
    """
    Error Classification Agent - Especialista en análisis y clasificación de errores.
    
    Implementa arquitectura BDI:
    - Beliefs: La clasificación precisa de errores mejora la recuperación del sistema
    - Desires: Identificar y categorizar errores para optimizar la respuesta
    - Intentions: Detectar, analizar, clasificar y enrutar errores apropiadamente
    
    Recibe errores del Progress Tracker y otros agentes, los analiza y determina
    la estrategia de recuperación más apropiada.
    """

    def __init__(self):
        super().__init__(
            agent_id="error_classification_agent",
            agent_name="Error Classification & Analysis Agent"
        )
        
        # Configuración específica del clasificador
        self.classification_history = {}
        self.error_patterns_cache = {}
        self.confidence_threshold = 0.7
        
        # Registrar agente en state management
        state_manager.register_agent(
            self.agent_id,
            {
                "version": "1.0",
                "specialization": "error_analysis_classification",
                "tools_count": len(self.tools),
                "capabilities": {
                    "error_detection": True,
                    "severity_analysis": True,
                    "root_cause_analysis": True,
                    "pattern_recognition": True,
                    "recovery_routing": True,
                    "escalation_management": True
                },
                "error_categories": [category.value for category in ErrorCategory],
                "severity_levels": [severity.value for severity in ErrorSeverity],
                "recovery_strategies": [strategy.value for strategy in RecoveryStrategy],
                "integration_points": {
                    "progress_tracker": "active",
                    "recovery_agent": "target",
                    "human_handoff_agent": "target",
                    "state_management": "active",
                    "audit_trail": "active"
                }
            }
        )
        
        self.logger.info("Error Classification Agent integrado con State Management y Error Handling System")

    def _initialize_tools(self) -> List:
        """Inicializar herramientas de clasificación de errores"""
        return [
            error_detector_tool,
            severity_analyzer_tool,
            root_cause_finder_tool,
            routing_engine_tool
        ]

    def _create_prompt(self) -> ChatPromptTemplate:
        """Crear prompt con framework BDI y patrón ReAct para clasificación de errores"""
        bdi = self._get_bdi_framework()
        
        system_prompt = f"""
Eres el Error Classification Agent, especialista en análisis y clasificación de errores del sistema de onboarding.

## FRAMEWORK BDI (Belief-Desire-Intention)
**BELIEFS (Creencias):**
{bdi['beliefs']}

**DESIRES (Deseos):**
{bdi['desires']}

**INTENTIONS (Intenciones):**
{bdi['intentions']}

## HERRAMIENTAS DE CLASIFICACIÓN:
- error_detector_tool: Detecta errores de múltiples fuentes (Progress Tracker, agentes, SLA, Quality Gates)
- severity_analyzer_tool: Analiza severidad basada en contexto e impacto de negocio
- root_cause_finder_tool: Identifica causa raíz usando análisis de patrones y evidencia
- routing_engine_tool: Determina routing apropiado a Recovery Agent o Human Handoff Agent

## FUENTES DE ERRORES MONITOREADAS:
- **Progress Tracker**: Pipeline bloqueado, SLA breaches, escalaciones automáticas
- **Agentes Directos**: Timeouts, fallos de procesamiento, errores excesivos
- **Quality Gates**: Fallos de validación, revisión manual requerida
- **SLA Monitor**: Breaches críticos, etapas en riesgo
- **State Manager**: Inconsistencias de estado, pérdida de datos
- **Sistemas Externos**: Conectividad, autenticación, configuración

## CATEGORÍAS DE CLASIFICACIÓN:
- **AGENT_FAILURE**: Fallos directos de agentes individuales
- **SLA_BREACH**: Violaciones de acuerdos de nivel de servicio
- **QUALITY_FAILURE**: Fallos en quality gates y validaciones
- **SYSTEM_ERROR**: Errores del sistema subyacente
- **DATA_VALIDATION**: Problemas de validación de datos
- **INTEGRATION_ERROR**: Fallos de integración con sistemas externos
- **SECURITY_ISSUE**: Problemas de seguridad y autenticación
- **BUSINESS_RULE_VIOLATION**: Violaciones de reglas de negocio

## NIVELES DE SEVERIDAD:
- **EMERGENCY**: Fallos críticos del sistema que requieren respuesta inmediata
- **CRITICAL**: Errores que bloquean completamente el pipeline
- **HIGH**: Errores que impactan significativamente el proceso
- **MEDIUM**: Errores que causan retrasos menores
- **LOW**: Errores menores con impacto mínimo

## ESTRATEGIAS DE RECUPERACIÓN:
- **AUTOMATIC_RETRY**: Reintentos automáticos con backoff exponencial
- **MANUAL_INTERVENTION**: Requiere intervención humana especializada
- **ESCALATION_REQUIRED**: Escalación a management por criticidad
- **ROLLBACK_RECOVERY**: Rollback a estado anterior conocido
- **HUMAN_HANDOFF**: Handoff completo a especialista humano
- **SYSTEM_RESTART**: Reinicio de componentes del sistema

## PATRÓN REACT (Reason-Act-Observe):
**1. REASON (Razonar):**
- Analizar datos de error recibidos del Progress Tracker o agentes
- Evaluar contexto del empleado, pipeline stage y condiciones del sistema
- Identificar patrones de error y correlaciones históricas
- Determinar impacto en negocio y prioridad de resolución

**2. ACT (Actuar):**
- Ejecutar error_detector_tool para extraer y categorizar errores
- Usar severity_analyzer_tool para determinar severidad contextual
- Aplicar root_cause_finder_tool para análisis de causa raíz
- Implementar routing_engine_tool para determinar handler apropiado

**3. OBSERVE (Observar):**
- Verificar que clasificación sea consistente con patrones históricos
- Confirmar que severidad refleje apropiadamente el impacto del negocio
- Validar que causa raíz tenga evidencia suficiente y confianza alta
- Asegurar que routing dirija a handler más apropiado disponible

## CRITERIOS DE CLASIFICACIÓN:
- **Precisión**: Clasificación debe ser técnicamente correcta
- **Contexto**: Considerar impacto específico del empleado y negocio
- **Consistencia**: Mantener coherencia con clasificaciones históricas
- **Actionabilidad**: Routing debe resultar en acciones concretas de recuperación

## INTEGRACIÓN CON RECOVERY SYSTEM:
- **Recovery Agent**: Para errores con estrategia AUTOMATIC_RETRY, ROLLBACK_RECOVERY, SYSTEM_RESTART
- **Human Handoff Agent**: Para errores con MANUAL_INTERVENTION, ESCALATION_REQUIRED, HUMAN_HANDOFF
- **Progress Tracker**: Feedback loop para monitoreo continuo post-clasificación
- **State Management**: Actualización de estados de error y recovery

## INSTRUCCIONES CRÍTICAS:
1. SIEMPRE detecta errores de todas las fuentes disponibles antes de clasificar
2. Analiza severidad considerando contexto específico del empleado y negocio
3. Realiza análisis de causa raíz con evidencia concreta y confianza medible
4. Enruta errores al handler más apropiado basado en capacidades y disponibilidad
5. Mantén audit trail completo para análisis post-mortem y mejora continua
6. Proporciona clasificaciones actionables que resulten en recuperación efectiva

Clasifica con precisión forense, analiza con rigor científico y enruta con inteligencia estratégica.
"""

        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}"),
            ("assistant", "Voy a analizar y clasificar los errores del sistema para determinar la estrategia de recuperación más apropiada."),
            ("placeholder", "{agent_scratchpad}")
        ])

    def _get_bdi_framework(self) -> Dict[str, str]:
        """Framework BDI específico para clasificación de errores"""
        return {
            "beliefs": """
• La clasificación precisa de errores es fundamental para la recuperación efectiva del sistema
• Diferentes tipos de errores requieren estrategias de recuperación completamente diferentes
• El contexto del empleado y negocio influye significativamente en la severidad del error
• Los patrones de errores históricos proporcionan insights valiosos para clasificación futura
• La causa raíz debe identificarse con evidencia concreta para prevenir recurrencias
• El routing apropiado acelera la resolución y minimiza el impacto en el negocio
""",
            "desires": """
• Identificar y categorizar errores con máxima precisión y contexto apropiado
• Determinar severidad que refleje fielmente el impacto real en el negocio y empleado
• Realizar análisis de causa raíz que proporcione insights actionables para prevención
• Enrutar errores al handler más calificado para resolución rápida y efectiva
• Mantener base de conocimiento de patrones para mejorar clasificaciones futuras
• Proporcionar clasificaciones que resulten en recuperación exitosa del pipeline
""",
            "intentions": """
• Detectar errores proactivamente de todas las fuentes del sistema con cobertura completa
• Clasificar errores usando análisis contextual, patrones históricos y reglas de negocio
• Analizar severidad considerando impacto específico del empleado, pipeline y organización
• Identificar causa raíz usando metodologías forenses y evidencia correlacionada
• Determinar estrategia de recuperación óptima basada en tipo, severidad y recursos disponibles
• Enrutar errores al agente de recuperación más apropiado con contexto completo preservado
"""
        }

    def _format_input(self, input_data: Any) -> str:
        """Formatear datos de entrada para clasificación de errores"""
        if isinstance(input_data, ErrorClassificationRequest):
            return f"""
Ejecuta clasificación completa de errores para el siguiente caso:

**INFORMACIÓN DEL ERROR:**
- Employee ID: {input_data.employee_id}
- Session ID: {input_data.session_id}
- Fuente del Error: {input_data.error_source.value}
- Timestamp: {input_data.timestamp.isoformat()}

**DATOS DEL ERROR:**
{json.dumps(input_data.raw_error_data, indent=2, default=str)}

**CONTEXTO ADICIONAL:**
{json.dumps(input_data.context_data, indent=2, default=str) if input_data.context_data else "- Sin contexto adicional"}

**CONFIGURACIÓN DE PROCESAMIENTO:**
- Forzar reclasificación: {'Sí' if input_data.force_reclassification else 'No'}

**INSTRUCCIONES DE CLASIFICACIÓN:**
1. Usa error_detector_tool para detectar todos los errores del sistema
2. Usa severity_analyzer_tool para determinar severidad contextual
3. Usa root_cause_finder_tool para análisis de causa raíz con evidencia
4. Usa routing_engine_tool para determinar handler apropiado y escalation path

**OBJETIVO:** Clasificar error completamente y determinar estrategia de recuperación óptima.
"""

        elif isinstance(input_data, dict):
            return f"""
Clasifica el siguiente error del sistema:
{json.dumps(input_data, indent=2, default=str)}

Ejecuta análisis completo: detección + severidad + causa raíz + routing.
"""
        else:
            return str(input_data)

    def _format_output(self, result: Any, processing_time: float, success: bool, error: str = None) -> Dict[str, Any]:
        """Formatear salida de clasificación de errores"""
        if not success:
            return {
                "success": False,
                "message": f"Error en clasificación: {error}",
                "errors": [error] if error else [],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "classification_status": "failed",
                "errors_classified": 0,
                "recovery_strategy": RecoveryStrategy.MANUAL_INTERVENTION.value,
                "requires_escalation": True,
                "next_actions": ["Revisar errores de clasificación", "Escalación manual requerida"]
            }

        try:
            # Extraer resultados de herramientas
            detection_result = None
            severity_result = None
            root_cause_result = None
            routing_result = None

            if isinstance(result, dict) and "intermediate_steps" in result:
                for step_name, step_result in result["intermediate_steps"]:
                    if "error_detector_tool" in step_name and isinstance(step_result, dict):
                        detection_result = step_result
                    elif "severity_analyzer_tool" in step_name and isinstance(step_result, dict):
                        severity_result = step_result
                    elif "root_cause_finder_tool" in step_name and isinstance(step_result, dict):
                        root_cause_result = step_result
                    elif "routing_engine_tool" in step_name and isinstance(step_result, dict):
                        routing_result = step_result

            # Valores por defecto si no hay resultados
            detected_errors = detection_result.get("detected_errors", []) if detection_result else []
            error_count = len(detected_errors)
            
            # Determinar severidad global
            global_severity = ErrorSeverity.MEDIUM
            if severity_result and severity_result.get("success"):
                global_severity = severity_result.get("global_severity", ErrorSeverity.MEDIUM)

            # Extraer análisis de causa raíz
            root_cause_analyses = []
            if root_cause_result and root_cause_result.get("success"):
                root_cause_analyses = root_cause_result.get("root_cause_analyses", [])

            # Extraer decisiones de routing
            routing_decisions = []
            primary_handler = None
            if routing_result and routing_result.get("success"):
                routing_decisions = routing_result.get("routing_decisions", [])
                if routing_decisions:
                    primary_handler = routing_decisions[0].get("primary_handler")

            # Determinar estrategia de recuperación principal
            recovery_strategy = self._determine_primary_recovery_strategy(
                global_severity, detected_errors, primary_handler
            )

            # Determinar si requiere escalación
            requires_escalation = (
                global_severity in [ErrorSeverity.CRITICAL, ErrorSeverity.EMERGENCY] or
                error_count > 3 or
                any("escalation" in str(error).lower() for error in detected_errors)
            )

            # Generar clasificaciones de errores individuales
            error_classifications = self._generate_error_classifications(
                detected_errors, severity_result, root_cause_analyses, routing_decisions
            )

            # Generar acciones inmediatas
            immediate_actions = self._generate_immediate_actions(
                detected_errors, global_severity, recovery_strategy
            )

            # Generar recomendaciones preventivas
            preventive_measures = self._generate_preventive_measures(root_cause_analyses)

            return {
                "success": True,
                "message": "Clasificación de errores completada exitosamente",
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "classification_status": "completed",

                # Resumen de clasificación
                "classification_summary": {
                    "errors_detected": error_count,
                    "errors_classified": len(error_classifications),
                    "global_severity": global_severity.value if isinstance(global_severity, ErrorSeverity) else str(global_severity),
                    "primary_recovery_strategy": recovery_strategy.value if isinstance(recovery_strategy, RecoveryStrategy) else str(recovery_strategy),
                    "requires_escalation": requires_escalation,
                    "classification_confidence": self._calculate_overall_confidence(severity_result, root_cause_result)
                },

                # Resultados detallados
                "detected_errors": detected_errors,
                "error_classifications": error_classifications,
                "severity_analysis": severity_result.get("severity_analysis", {}) if severity_result else {},
                "root_cause_analyses": root_cause_analyses,
                "routing_decisions": routing_decisions,

                # Acciones y recuperación
                "recovery_strategy": recovery_strategy.value if isinstance(recovery_strategy, RecoveryStrategy) else str(recovery_strategy),
                "primary_handler": primary_handler,
                "immediate_actions": immediate_actions,
                "preventive_measures": preventive_measures,

                # Próximos pasos
                "next_handler": self._determine_next_handler(primary_handler, recovery_strategy),
                "escalation_required": requires_escalation,
                "estimated_resolution_time": self._estimate_classification_resolution_time(routing_decisions),

                # Metadatos
                "classification_timestamp": datetime.utcnow().isoformat(),
                "errors": [],
                "warnings": self._generate_classification_warnings(detected_errors, severity_result)
            }

        except Exception as e:
            self.logger.error(f"Error formateando salida de clasificación: {e}")
            return {
                "success": False,
                "message": f"Error procesando clasificación: {e}",
                "errors": [str(e)],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "classification_status": "error",
                "errors_classified": 0,
                "recovery_strategy": RecoveryStrategy.MANUAL_INTERVENTION.value,
                "requires_escalation": True
            }

    def _determine_primary_recovery_strategy(self, global_severity: ErrorSeverity, 
                                           detected_errors: List[Dict], 
                                           primary_handler: Optional[Dict]) -> RecoveryStrategy:
        """Determinar estrategia de recuperación principal"""
        try:
            # Estrategia basada en severidad
            if global_severity == ErrorSeverity.EMERGENCY:
                return RecoveryStrategy.ESCALATION_REQUIRED
            elif global_severity == ErrorSeverity.CRITICAL:
                return RecoveryStrategy.HUMAN_HANDOFF
            
            # Estrategia basada en tipo de errores
            error_types = [error.get("error_type", "") for error in detected_errors]
            
            if "timeout" in error_types or "agent_failure" in error_types:
                return RecoveryStrategy.AUTOMATIC_RETRY
            elif "sla_breach" in error_types:
                return RecoveryStrategy.ESCALATION_REQUIRED
            elif "quality_failure" in error_types:
                return RecoveryStrategy.MANUAL_INTERVENTION
            
            # Estrategia basada en handler
            if primary_handler:
                handler_type = primary_handler.get("handler_type", "")
                if handler_type == "recovery_agent":
                    return RecoveryStrategy.AUTOMATIC_RETRY
                elif handler_type == "human_handoff_agent":
                    return RecoveryStrategy.HUMAN_HANDOFF
            
            # Fallback
            return RecoveryStrategy.MANUAL_INTERVENTION
            
        except Exception:
            return RecoveryStrategy.MANUAL_INTERVENTION

    def _generate_error_classifications(self, detected_errors: List[Dict], 
                                      severity_result: Optional[Dict],
                                      root_cause_analyses: List,
                                      routing_decisions: List) -> List[Dict[str, Any]]:
        """Generar clasificaciones individuales de errores"""
        classifications = []
        
        for i, error in enumerate(detected_errors):
            try:
                # Mapear error a clasificación
                error_category = self._map_error_to_category(error)
                error_type = self._map_error_to_type(error)
                
                # Obtener severidad específica del error
                error_severity = ErrorSeverity.MEDIUM
                if severity_result and severity_result.get("severity_analysis"):
                    error_id = f"{error.get('source')}_{error.get('error_type')}"
                    if error_id in severity_result["severity_analysis"]:
                        error_severity = severity_result["severity_analysis"][error_id].get(
                            "final_severity", ErrorSeverity.MEDIUM
                        )

                # Obtener análisis de causa raíz correspondiente
                root_cause = None
                if i < len(root_cause_analyses):
                    root_cause = root_cause_analyses[i]

                # Obtener decisión de routing correspondiente
                routing_decision = None
                if i < len(routing_decisions):
                    routing_decision = routing_decisions[i]

                classification = {
                    "error_id": f"error_{i}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    "original_error": error,
                    "error_category": error_category.value if isinstance(error_category, ErrorCategory) else str(error_category),
                    "error_type": error_type.value if isinstance(error_type, ErrorType) else str(error_type),
                    "severity_level": error_severity.value if isinstance(error_severity, ErrorSeverity) else str(error_severity),
                    "root_cause_analysis": root_cause,
                    "routing_decision": routing_decision,
                    "recovery_strategy": self._determine_error_recovery_strategy(error_category, error_severity),
                    "classification_confidence": self._calculate_error_confidence(error, severity_result)
                }
                
                classifications.append(classification)
                
            except Exception as e:
                self.logger.warning(f"Error clasificando error individual {i}: {e}")
                continue
        
        return classifications

    def _map_error_to_category(self, error: Dict[str, Any]) -> ErrorCategory:
        """Mapear error a categoría"""
        source = error.get("source", "")
        error_type = error.get("error_type", "")
        
        # Mapeo basado en fuente
        if source == ErrorSource.AGENT_DIRECT:
            return ErrorCategory.AGENT_FAILURE
        elif source == ErrorSource.SLA_MONITOR:
            return ErrorCategory.SLA_BREACH
        elif source == ErrorSource.QUALITY_GATE:
            return ErrorCategory.QUALITY_FAILURE
        elif source == ErrorSource.STATE_MANAGER:
            return ErrorCategory.SYSTEM_ERROR
        elif source == ErrorSource.EXTERNAL_SYSTEM:
            return ErrorCategory.INTEGRATION_ERROR
        
        # Mapeo basado en tipo de error
        if "validation" in error_type:
            return ErrorCategory.DATA_VALIDATION
        elif "security" in error_type or "authentication" in error_type:
            return ErrorCategory.SECURITY_ISSUE
        elif "business" in error_type or "rule" in error_type:
            return ErrorCategory.BUSINESS_RULE_VIOLATION
        
        # Fallback
        return ErrorCategory.SYSTEM_ERROR

    def _map_error_to_type(self, error: Dict[str, Any]) -> ErrorType:
        """Mapear error a tipo específico"""
        error_type_str = error.get("error_type", "")
        
        # Mapeo directo si coincide con enum
        for error_type in ErrorType:
            if error_type.value == error_type_str:
                return error_type
        
        # Mapeo basado en palabras clave
        if "timeout" in error_type_str:
            return ErrorType.TIMEOUT
        elif "sla" in error_type_str and "breach" in error_type_str:
            return ErrorType.TIME_BREACH
        elif "quality" in error_type_str or "validation" in error_type_str:
            return ErrorType.VALIDATION_FAILURE
        elif "connectivity" in error_type_str or "connection" in error_type_str:
            return ErrorType.CONNECTIVITY_ERROR
        elif "authentication" in error_type_str or "auth" in error_type_str:
            return ErrorType.AUTHENTICATION_ERROR
        elif "configuration" in error_type_str or "config" in error_type_str:
            return ErrorType.CONFIGURATION_ERROR
        
        # Fallback
        return ErrorType.PROCESSING_ERROR

    def _determine_error_recovery_strategy(self, error_category: ErrorCategory, 
                                         error_severity: ErrorSeverity) -> str:
        """Determinar estrategia de recuperación para error específico"""
        if error_severity == ErrorSeverity.EMERGENCY:
            return RecoveryStrategy.ESCALATION_REQUIRED.value
        elif error_severity == ErrorSeverity.CRITICAL:
            if error_category in [ErrorCategory.AGENT_FAILURE, ErrorCategory.SYSTEM_ERROR]:
                return RecoveryStrategy.AUTOMATIC_RETRY.value
            else:
                return RecoveryStrategy.HUMAN_HANDOFF.value
        elif error_category == ErrorCategory.QUALITY_FAILURE:
            return RecoveryStrategy.MANUAL_INTERVENTION.value
        elif error_category == ErrorCategory.SLA_BREACH:
            return RecoveryStrategy.ESCALATION_REQUIRED.value
        else:
            return RecoveryStrategy.AUTOMATIC_RETRY.value

    def _calculate_error_confidence(self, error: Dict[str, Any], 
                                   severity_result: Optional[Dict]) -> float:
        """Calcular confianza en clasificación del error"""
        base_confidence = 0.7
        
        # Aumentar confianza si hay contexto rico
        if error.get("context") and len(error["context"]) > 3:
            base_confidence += 0.1
        
        # Aumentar confianza si hay análisis de severidad
        if severity_result and severity_result.get("success"):
            base_confidence += 0.1
        
        # Aumentar confianza para errores conocidos
        known_types = ["timeout", "sla_breach", "agent_failure", "quality_failure"]
        if error.get("error_type") in known_types:
            base_confidence += 0.1
        
        return min(1.0, base_confidence)

    def _calculate_overall_confidence(self, severity_result: Optional[Dict],
                                    root_cause_result: Optional[Dict]) -> float:
        """Calcular confianza general de la clasificación"""
        confidences = []
        
        if severity_result and severity_result.get("success"):
            # Promedio de confianza de análisis de severidad
            severity_analyses = severity_result.get("severity_analysis", {})
            if severity_analyses:
                severity_confidences = [
                    analysis.get("confidence", 0.5) 
                    for analysis in severity_analyses.values()
                ]
                confidences.append(sum(severity_confidences) / len(severity_confidences))
        
        if root_cause_result and root_cause_result.get("success"):
            # Promedio de confianza de análisis de causa raíz
            root_analyses = root_cause_result.get("root_cause_analyses", [])
            if root_analyses:
                root_confidences = [
                    analysis.get("confidence_level", 0.5) if isinstance(analysis, dict) else 0.5
                    for analysis in root_analyses
                ]
                confidences.append(sum(root_confidences) / len(root_confidences))
        
        return sum(confidences) / len(confidences) if confidences else 0.7

    def _generate_immediate_actions(self, detected_errors: List[Dict], 
                                   global_severity: ErrorSeverity,
                                   recovery_strategy: RecoveryStrategy) -> List[str]:
        """Generar acciones inmediatas basadas en clasificación"""
        actions = []
        
        # Acciones basadas en severidad
        if global_severity == ErrorSeverity.EMERGENCY:
            actions.extend([
                "Activate emergency incident response procedures",
                "Notify senior management immediately",
                "Prepare for potential system rollback"
            ])
        elif global_severity == ErrorSeverity.CRITICAL:
            actions.extend([
                "Escalate to technical leads",
                "Implement immediate containment measures",
                "Prepare stakeholder communications"
            ])
        
        # Acciones basadas en tipos específicos de errores
        error_types = [error.get("error_type", "") for error in detected_errors]
        
        if "pipeline_blocked" in error_types:
            actions.append("Unblock pipeline by addressing critical dependencies")
        
        if "timeout" in error_types:
            actions.append("Investigate and resolve timeout issues")
        
        if "sla_breach" in error_types:
            actions.extend([
                "Notify stakeholders of SLA breach",
                "Implement SLA recovery procedures"
            ])
        
        # Acciones basadas en estrategia de recuperación
        if recovery_strategy == RecoveryStrategy.AUTOMATIC_RETRY:
            actions.append("Initiate automatic retry procedures")
        elif recovery_strategy == RecoveryStrategy.HUMAN_HANDOFF:
            actions.append("Route to appropriate human specialist")
        elif recovery_strategy == RecoveryStrategy.ESCALATION_REQUIRED:
            actions.append("Execute escalation procedures immediately")
        
        return list(set(actions))  # Remove duplicates

    def _generate_preventive_measures(self, root_cause_analyses: List) -> List[str]:
        """Generar medidas preventivas basadas en análisis de causa raíz"""
        measures = []
        
        for analysis in root_cause_analyses:
            if isinstance(analysis, dict):
                # Extraer recomendaciones del análisis
                recommendations = analysis.get("recommendations", [])
                measures.extend(recommendations)
        
        # Medidas preventivas generales si no hay análisis específico
        if not measures:
            measures.extend([
                "Implement enhanced monitoring and alerting",
                "Review and update error handling procedures",
                "Conduct system health assessment",
                "Update incident response documentation"
            ])
        
        return list(set(measures))  # Remove duplicates

    def _determine_next_handler(self, primary_handler: Optional[Dict], 
                               recovery_strategy: RecoveryStrategy) -> str:
        """Determinar próximo handler en la cadena"""
        if primary_handler:
            handler_type = primary_handler.get("handler_type", "")
            handler_id = primary_handler.get("handler_id", "")
            return f"{handler_type}:{handler_id}"
        
        # Fallback basado en estrategia
        if recovery_strategy in [RecoveryStrategy.AUTOMATIC_RETRY, RecoveryStrategy.SYSTEM_RESTART]:
            return "recovery_agent:automatic_recovery_system"
        elif recovery_strategy in [RecoveryStrategy.HUMAN_HANDOFF, RecoveryStrategy.MANUAL_INTERVENTION]:
            return "human_handoff_agent:human_specialist_router"
        elif recovery_strategy == RecoveryStrategy.ESCALATION_REQUIRED:
            return "human_handoff_agent:escalation_handler"
        else:
            return "human_handoff_agent:general_escalation_handler"

    def _estimate_classification_resolution_time(self, routing_decisions: List) -> Dict[str, Any]:
        """Estimar tiempo de resolución basado en decisiones de routing"""
        if not routing_decisions:
            return {"estimated_minutes": 30, "confidence": 0.5}
        
        # Extraer estimaciones de tiempo de las decisiones
        estimated_times = []
        for decision in routing_decisions:
            est_time = decision.get("estimated_resolution_time", {})
            if est_time and "estimated_avg_minutes" in est_time:
                estimated_times.append(est_time["estimated_avg_minutes"])
        
        if estimated_times:
            avg_time = sum(estimated_times) / len(estimated_times)
            max_time = max(estimated_times)
            return {
                "estimated_avg_minutes": int(avg_time),
                "estimated_max_minutes": int(max_time),
                "confidence": 0.8
            }
        
        return {"estimated_minutes": 45, "confidence": 0.6}

    def _generate_classification_warnings(self, detected_errors: List[Dict],
                                        severity_result: Optional[Dict]) -> List[str]:
        """Generar warnings sobre la clasificación"""
        warnings = []
        
        # Warning si hay muchos errores
        if len(detected_errors) > 5:
            warnings.append(f"High error count detected: {len(detected_errors)} errors")
        
        # Warning si hay errores críticos
        critical_errors = [
            error for error in detected_errors 
            if error.get("severity") in ["critical", "emergency"]
        ]
        if critical_errors:
            warnings.append(f"{len(critical_errors)} critical/emergency errors require immediate attention")
        
        # Warning si la confianza es baja
        if severity_result:
            overall_confidence = self._calculate_overall_confidence(severity_result, None)
            if overall_confidence < 0.6:
                warnings.append(f"Low classification confidence ({overall_confidence:.1%}) - manual review recommended")
        
        return warnings

    @observability_manager.trace_agent_execution("error_classification_agent")
    def classify_errors(self, classification_request: ErrorClassificationRequest, 
                       session_id: str = None) -> Dict[str, Any]:
        """Ejecutar clasificación completa de errores"""
        # Generar classification_id
        classification_id = f"class_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{classification_request.employee_id}"
        
        # Actualizar estado: PROCESSING
        state_manager.update_agent_state(
            self.agent_id,
            AgentStateStatus.PROCESSING,
            {
                "current_task": "error_classification",
                "classification_id": classification_id,
                "employee_id": classification_request.employee_id,
                "error_source": classification_request.error_source.value,
                "started_at": datetime.utcnow().isoformat()
            },
            session_id
        )
        
        # Registrar métricas iniciales
        observability_manager.log_agent_metrics(
            self.agent_id,
            {
                "error_source": classification_request.error_source.value,
                "has_context_data": bool(classification_request.context_data),
                "force_reclassification": classification_request.force_reclassification,
                "raw_error_fields": len(classification_request.raw_error_data)
            },
            session_id
        )
        
        try:
            # Procesar con el método base
            result = self.process_request(classification_request, session_id)
            
            # Si la clasificación fue exitosa, actualizar State Management
            if result["success"]:
                # Actualizar datos del empleado con resultados de clasificación
                if session_id:
                    classification_data = {
                        "error_classification_completed": True,
                        "classification_id": classification_id,
                        "errors_classified": result.get("classification_summary", {}).get("errors_classified", 0),
                        "global_severity": result.get("classification_summary", {}).get("global_severity"),
                        "recovery_strategy": result.get("recovery_strategy"),
                        "requires_escalation": result.get("escalation_required", False),
                        "next_handler": result.get("next_handler"),
                        "classification_timestamp": datetime.utcnow().isoformat()
                    }
                    
                    # Actualizar phase si hay errores críticos
                    phase_update = None
                    if result.get("classification_summary", {}).get("global_severity") in ["critical", "emergency"]:
                        phase_update = "error_handling"
                    
                    state_manager.update_employee_data(
                        session_id,
                        classification_data,
                        "error_classified" if not phase_update else phase_update
                    )
                
                # Actualizar estado: COMPLETED
                state_manager.update_agent_state(
                    self.agent_id,
                    AgentStateStatus.COMPLETED,
                    {
                        "current_task": "completed",
                        "classification_id": classification_id,
                        "errors_classified": result.get("classification_summary", {}).get("errors_classified", 0),
                        "global_severity": result.get("classification_summary", {}).get("global_severity"),
                        "recovery_strategy": result.get("recovery_strategy"),
                        "next_handler": result.get("next_handler"),
                        "completed_at": datetime.utcnow().isoformat()
                    },
                    session_id
                )
                
                # Almacenar en historial de clasificaciones
                self.classification_history[classification_id] = {
                    "status": "completed",
                    "result": result,
                    "completed_at": datetime.utcnow()
                }
            else:
                # Error en clasificación
                state_manager.update_agent_state(
                    self.agent_id,
                    AgentStateStatus.ERROR,
                    {
                        "current_task": "error",
                        "classification_id": classification_id,
                        "errors": result.get("errors", []),
                        "failed_at": datetime.utcnow().isoformat()
                    },
                    session_id
                )
            
            # Agregar información de sesión al resultado
            result["classification_id"] = classification_id
            result["session_id"] = session_id
            
            return result
            
        except Exception as e:
            # Error durante clasificación
            error_msg = f"Error ejecutando clasificación de errores: {str(e)}"
            state_manager.update_agent_state(
                self.agent_id,
                AgentStateStatus.ERROR,
                {
                    "current_task": "error",
                    "classification_id": classification_id,
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
                "classification_id": classification_id,
                "session_id": session_id,
                "agent_id": self.agent_id,
                "processing_time": 0,
                "classification_status": "failed"
            }

    def _process_with_tools_directly(self, input_data: Any) -> Dict[str, Any]:
        """Procesar usando herramientas directamente con flujo específico de clasificación"""
        results = []
        formatted_input = self._format_input(input_data)
        self.logger.info(f"Procesando clasificación con {len(self.tools)} herramientas especializadas")
        
        # Variables para almacenar resultados
        detection_result = None
        severity_result = None
        root_cause_result = None
        routing_result = None
        
        # Preparar datos según el tipo de entrada
        if isinstance(input_data, ErrorClassificationRequest):
            session_id = input_data.session_id
            employee_id = input_data.employee_id
            raw_error_data = input_data.raw_error_data
            context_data = input_data.context_data or {}
        else:
            # Fallback para datos genéricos
            session_id = input_data.get("session_id", "") if isinstance(input_data, dict) else ""
            employee_id = input_data.get("employee_id", "unknown") if isinstance(input_data, dict) else "unknown"
            raw_error_data = input_data if isinstance(input_data, dict) else {"raw_data": str(input_data)}
            context_data = {}
        
        # 1. Ejecutar Error Detector (siempre primero)
        try:
            self.logger.info("Ejecutando error_detector_tool")
            detection_result = error_detector_tool.invoke({
                "session_id": session_id,
                "monitoring_data": raw_error_data,
                "include_historical": True
            })
            results.append(("error_detector_tool", detection_result))
            self.logger.info("✅ Error detection completado")
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.logger.warning(f"❌ Error con error_detector_tool: {e}")
            results.append(("error_detector_tool", {"success": False, "error": error_msg, "detected_errors": []}))
        
        # 2. Ejecutar Severity Analyzer (si hay errores detectados)
        if detection_result and detection_result.get("success") and detection_result.get("detected_errors"):
            try:
                self.logger.info("Ejecutando severity_analyzer_tool")
                severity_result = severity_analyzer_tool.invoke({
                    "detected_errors": detection_result["detected_errors"],
                    "context_data": context_data
                })
                results.append(("severity_analyzer_tool", severity_result))
                self.logger.info("✅ Severity analysis completado")
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.logger.warning(f"❌ Error con severity_analyzer_tool: {e}")
                results.append(("severity_analyzer_tool", {"success": False, "error": error_msg}))
        
        # 3. Ejecutar Root Cause Finder (si hay errores detectados)
        if detection_result and detection_result.get("success") and detection_result.get("detected_errors"):
            try:
                self.logger.info("Ejecutando root_cause_finder_tool")
                root_cause_result = root_cause_finder_tool.invoke({
                    "detected_errors": detection_result["detected_errors"],
                    "error_context": context_data,
                    "historical_data": self.classification_history
                })
                results.append(("root_cause_finder_tool", root_cause_result))
                self.logger.info("✅ Root cause analysis completado")
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.logger.warning(f"❌ Error con                root_cause_finder_tool: {e}")
                results.append(("root_cause_finder_tool", {"success": False, "error": error_msg}))
        
        # 4. Ejecutar Routing Engine (si hay resultados de clasificación)
        if (detection_result and detection_result.get("success") and 
            detection_result.get("detected_errors")):
            try:
                self.logger.info("Ejecutando routing_engine_tool")
                
                # Preparar classification results para routing
                classification_results = []
                detected_errors = detection_result.get("detected_errors", [])
                
                for i, error in enumerate(detected_errors):
                    # Crear resultado de clasificación simplificado para routing
                    classification_result = {
                        "classification_id": f"temp_class_{i}",
                        "error_category": self._map_error_to_category(error).value,
                        "severity_level": ErrorSeverity.MEDIUM.value,  # Default
                        "recovery_strategy": RecoveryStrategy.MANUAL_INTERVENTION.value,
                        "escalation_path": []
                    }
                    
                    # Actualizar con datos de severity si están disponibles
                    if severity_result and severity_result.get("success"):
                        severity_analysis = severity_result.get("severity_analysis", {})
                        error_id = f"{error.get('source')}_{error.get('error_type')}"
                        if error_id in severity_analysis:
                            classification_result["severity_level"] = severity_analysis[error_id].get(
                                "final_severity", ErrorSeverity.MEDIUM.value
                            )
                    
                    classification_results.append(classification_result)
                
                routing_result = routing_engine_tool.invoke({
                    "classification_results": classification_results,
                    "system_capabilities": {
                        "recovery_agent_available": True,
                        "human_handoff_available": True,
                        "escalation_system_active": True
                    }
                })
                results.append(("routing_engine_tool", routing_result))
                self.logger.info("✅ Error routing completado")
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.logger.warning(f"❌ Error con routing_engine_tool: {e}")
                results.append(("routing_engine_tool", {"success": False, "error": error_msg}))
        
        # Evaluar éxito general
        successful_tools = len([r for r in results if isinstance(r, tuple) and isinstance(r[1], dict) and r[1].get("success")])
        overall_success = successful_tools >= 1  # Al menos detection debe funcionar
        
        return {
            "output": "Clasificación de errores completada",
            "intermediate_steps": results,
            "detection_result": detection_result,
            "severity_result": severity_result,
            "root_cause_result": root_cause_result,
            "routing_result": routing_result,
            "successful_tools": successful_tools,
            "overall_success": overall_success,
            "tools_executed": len(results)
        }