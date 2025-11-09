from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from agents.base.base_agent import BaseAgent
from datetime import datetime, timedelta
import json

# Imports del progress tracker
from .tools import (
    step_completion_monitor_tool, quality_gate_validator_tool,
    sla_monitor_tool, escalation_trigger_tool
)
from .schemas import (
    ProgressTrackerRequest, ProgressTrackerResult, PipelineProgressSnapshot,
    PipelineStage, AgentStatus, QualityGateStatus, SLAStatus, EscalationLevel
)
from .monitoring_rules import monitoring_rules_engine

# Imports para integración
from core.state_management.state_manager import state_manager
from core.state_management.models import AgentStateStatus, OnboardingPhase
from core.observability import observability_manager
from core.database import db_manager

class ProgressTrackerAgent(BaseAgent):
    """
    Progress Tracker Agent - Pipeline Monitoring & Quality Assurance Specialist.
    Implementa arquitectura BDI:
    - Beliefs: El monitoreo continuo previene fallos y mejora la calidad del pipeline
    - Desires: Garantizar pipeline secuencial sin interrupciones con calidad óptima
    - Intentions: Monitorear progreso, validar quality gates, detectar SLAs, escalar proactivamente
    
    Supervisa: IT Provisioning → Contract Management → Meeting Coordination
    Produce: Métricas de progreso, alertas de calidad, escalaciones automáticas
    """
    
    def __init__(self):
        super().__init__(
            agent_id="progress_tracker_agent",
            agent_name="Progress Tracker & Quality Assurance Agent"
        )
        
        # Configuración específica del tracker
        self.monitoring_rules = monitoring_rules_engine
        self.active_monitoring_sessions = {}
        self.quality_history = {}
        self.sla_history = {}
        
        # Registrar agente en state management
        state_manager.register_agent(
            self.agent_id,
            {
                "version": "1.0",
                "specialization": "pipeline_monitoring_quality_assurance",
                "tools_count": len(self.tools),
                "capabilities": {
                    "step_completion_monitoring": True,
                    "quality_gate_validation": True,
                    "sla_monitoring": True,
                    "escalation_management": True,
                    "real_time_tracking": True,
                    "predictive_analytics": True
                },
                "monitoring_scope": ["sequential_pipeline", "quality_gates", "sla_compliance"],
                "escalation_levels": [level.value for level in EscalationLevel],
                "supported_stages": [stage.value for stage in PipelineStage if stage not in [PipelineStage.ONBOARDING_EXECUTION, PipelineStage.COMPLETED]],
                "integration_points": {
                    "state_management": "active",
                    "quality_gates": "enforced", 
                    "sla_monitoring": "real_time",
                    "escalation_system": "automated"
                }
            }
        )
        self.logger.info("Progress Tracker Agent integrado con State Management y Monitoring Rules")
    
    def _initialize_tools(self) -> List:
        """Inicializar herramientas de monitoreo y tracking"""
        return [
            step_completion_monitor_tool,
            quality_gate_validator_tool,
            sla_monitor_tool,
            escalation_trigger_tool
        ]
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Crear prompt con framework BDI y patrón ReAct para monitoreo de progreso"""
        bdi = self._get_bdi_framework()
        system_prompt = f"""
Eres el Progress Tracker & Quality Assurance Agent, especialista en monitoreo de pipeline y garantía de calidad.

## FRAMEWORK BDI (Belief-Desire-Intention)
**BELIEFS (Creencias):**
{bdi['beliefs']}

**DESIRES (Deseos):**
{bdi['desires']}

**INTENTIONS (Intenciones):**
{bdi['intentions']}

## HERRAMIENTAS DE MONITOREO:
- step_completion_monitor_tool: Monitorea estado y progreso de cada agente del pipeline secuencial
- quality_gate_validator_tool: Valida quality gates y criterios de calidad antes del siguiente paso
- sla_monitor_tool: Monitorea cumplimiento de SLAs y detecta riesgos en tiempo real
- escalation_trigger_tool: Detecta condiciones de escalación y ejecuta acciones automáticas

## PIPELINE SECUENCIAL SUPERVISADO:
1. **Data Aggregation** → Quality Gate → SLA Check
2. **IT Provisioning** → Quality Gate → SLA Check  
3. **Contract Management** → Quality Gate → SLA Check
4. **Meeting Coordination** → Quality Gate → SLA Check

## MÉTRICAS DE MONITOREO:
**Step Completion:**
- Progress percentage por agente
- Processing duration vs targets
- Success indicators y error counts
- Output validation y quality scores

**Quality Gates:**
- Required fields validation
- Quality thresholds compliance  
- Business rules evaluation
- Bypass authorization tracking

**SLA Monitoring:**
- Elapsed time vs targets
- Warning/Critical/Breach thresholds
- Predicted completion times
- Breach probability analysis

**Escalation Management:**
- Rule-based escalation triggers
- Dynamic escalation conditions
- Notification management
- Automatic action execution

## UMBRALES CRÍTICOS:
**Data Aggregation:** Target 5min, Breach 8min, Quality >70%
**IT Provisioning:** Target 10min, Breach 15min, Security >95%
**Contract Management:** Target 15min, Breach 20min, Compliance >90%
**Meeting Coordination:** Target 8min, Breach 12min, Engagement >80%

## PATRÓN REACT (Reason-Act-Observe):
**1. REASON (Razonar):**
- Evaluar progreso actual de cada agente del pipeline secuencial
- Analizar compliance con quality gates y umbrales de calidad
- Calcular tiempo transcurrido vs SLA targets y predecir completions
- Identificar patrones de riesgo y condiciones de escalación

**2. ACT (Actuar):**
- Ejecutar step_completion_monitor_tool para trackear progreso de agentes
- Usar quality_gate_validator_tool para validar criterios antes de proceder
- Aplicar sla_monitor_tool para detectar breaches y riesgos en tiempo real
- Implementar escalation_trigger_tool para escalaciones automáticas críticas

**3. OBSERVE (Observar):**
- Verificar que métricas de progreso sean consistentes y actualizadas
- Confirmar que quality gates pasen antes de permitir siguiente etapa
- Validar que SLAs estén dentro de rangos aceptables o escalados apropiadamente
- Asegurar que escalaciones se ejecuten correctamente con notificaciones enviadas

## CRITERIOS DE ESCALACIÓN AUTOMÁTICA:
- **CRITICAL:** SLA breach >5min, Quality failure después de 3 intentos
- **WARNING:** SLA at-risk, Quality score <70%, Agent errors >3
- **EMERGENCY:** Multiple failures simultáneos, System overload

## QUALITY GATES OBLIGATORIOS:
- **Data Aggregation:** Validation passed + Quality >70% + Ready for sequential
- **IT Provisioning:** Credentials created + Security compliance >95%
- **Contract Management:** Legal validation + Signatures complete + Compliance >90%
- **Meeting Coordination:** Stakeholders engaged + Meetings scheduled + Calendar active

## ACCIONES AUTOMÁTICAS:
- Pausar pipeline en breach crítico
- Crear tickets de incidente automáticamente
- Notificar stakeholders según severity
- Reiniciar agentes fallidos con recovery
- Extender SLAs bajo condiciones aprobadas

## INSTRUCCIONES CRÍTICAS:
1. SIEMPRE monitorea progreso antes de validar quality gates
2. Valida quality gates ANTES de permitir siguiente etapa del pipeline
3. Monitorea SLAs continuamente con predicciones de breach
4. Escala inmediatamente en condiciones críticas sin esperar confirmación
5. Mantén histórico de métricas para análisis de tendencias
6. Genera reportes detallados para auditoría y mejora continua

Monitorea con precisión técnica, valida con rigor científico y escala con inteligencia operacional.
"""

        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}"),
            ("assistant", "Voy a monitorear el progreso del pipeline secuencial y asegurar compliance con quality gates y SLAs."),
            ("placeholder", "{agent_scratchpad}")
        ])
    
    def _get_bdi_framework(self) -> Dict[str, str]:
        """Framework BDI específico para monitoreo de progreso"""
        return {
            "beliefs": """
• El monitoreo continuo del pipeline previene fallos críticos y mejora la calidad general
• Los quality gates rigurosos aseguran que solo datos de alta calidad procedan al siguiente paso
• El cumplimiento de SLAs es esencial para mantener la confianza del negocio en el sistema
• Las escalaciones automáticas tempranas previenen problemas mayores y reducen tiempo de resolución
• Las métricas históricas permiten optimización predictiva y mejora continua del pipeline
• La transparencia en el monitoreo facilita la toma de decisiones informadas por stakeholders
""",
            "desires": """
• Garantizar que el pipeline secuencial opere sin interrupciones con máxima calidad
• Asegurar que todos los quality gates se cumplan antes de proceder a la siguiente etapa
• Mantener cumplimiento de SLAs en >95% de los casos con escalación proactiva de riesgos
• Proporcionar visibilidad completa del progreso y métricas en tiempo real
• Minimizar intervención manual mediante automatización inteligente de monitoreo
• Optimizar continuamente el pipeline basado en análisis de patrones y tendencias
""",
            "intentions": """
• Monitorear activamente el progreso de cada agente con métricas detalladas y predictivas
• Validar rigurosamente quality gates con criterios específicos antes de permitir progression
• Detectar proactivamente riesgos de SLA y ejecutar escalaciones automáticas según severity
• Generar alertas inteligentes basadas en patrones históricos y umbrales dinámicos
• Mantener audit trail completo para compliance y análisis post-mortem de incidentes
• Proporcionar recomendaciones actionables para mejora continua del pipeline secuencial
"""
        }
    
    def _format_input(self, input_data: Any) -> str:
        """Formatear datos de entrada para monitoreo de progreso"""
        if isinstance(input_data, ProgressTrackerRequest):
            return f"""
Ejecuta monitoreo completo del pipeline secuencial para el siguiente empleado:

**INFORMACIÓN DEL MONITOREO:**
- Employee ID: {input_data.employee_id}
- Session ID: {input_data.session_id}
- Scope de monitoreo: {input_data.monitoring_scope}

**CONFIGURACIÓN DE MONITOREO:**
- Quality Gates: {'Habilitado' if input_data.include_quality_gates else 'Deshabilitado'}
- SLA Monitoring: {'Habilitado' if input_data.include_sla_monitoring else 'Deshabilitado'}
- Escalation Check: {'Habilitado' if input_data.include_escalation_check else 'Deshabilitado'}

**TARGETS DE MONITOREO:**
- Etapas objetivo: {input_data.target_stages if input_data.target_stages else 'Todas las etapas del pipeline secuencial'}
- Agentes objetivo: {input_data.target_agents if input_data.target_agents else 'Todos los agentes'}

**CONFIGURACIÓN DE REPORTES:**
- Métricas detalladas: {'Sí' if input_data.detailed_metrics else 'No'}
- Predicciones incluidas: {'Sí' if input_data.include_predictions else 'No'}
- Recomendaciones incluidas: {'Sí' if input_data.include_recommendations else 'No'}

**PIPELINE SECUENCIAL A MONITOREAR:**
1. Data Aggregation Agent → Quality Gate + SLA
2. IT Provisioning Agent → Quality Gate + SLA
3. Contract Management Agent → Quality Gate + SLA  
4. Meeting Coordination Agent → Quality Gate + SLA

**INSTRUCCIONES DE PROCESAMIENTO:**
1. Usa step_completion_monitor_tool para evaluar progreso de cada agente
2. Usa quality_gate_validator_tool para validar criterios de calidad por etapa
3. Usa sla_monitor_tool para detectar riesgos y breaches de SLA
4. Usa escalation_trigger_tool para procesar escalaciones automáticas

**OBJETIVO:** Asegurar pipeline secuencial operando dentro de parámetros de calidad y SLA con escalación proactiva de issues.
"""
        elif isinstance(input_data, dict):
            return f"""
Monitorea progreso del pipeline con los siguientes parámetros:
{json.dumps(input_data, indent=2, default=str)}

Ejecuta monitoreo completo: progreso + quality gates + SLA + escalaciones.
"""
        else:
            return str(input_data)
    
    # En agents/progress_tracker/agent.py - Reemplazar toda la función _format_output

    # En agents/progress_tracker/agent.py - Reemplazar TODA la función _format_output

    def _format_output(self, result: Any, processing_time: float, success: bool, error: str = None) -> Dict[str, Any]:
        """Formatear salida de monitoreo de progreso"""
        if not success:
            return {
                "success": False,
                "message": f"Error en monitoreo de progreso: {error}",
                "errors": [error] if error else [],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "tracking_status": "failed",
                "pipeline_health_score": 0.0,
                "requires_immediate_attention": True,
                "next_actions": ["Revisar errores de monitoreo", "Verificar conectividad con State Management"]
            }
        
        try:
            self.logger.info(f"Formateando output - result type: {type(result)}")
            
            # Inicializar todas las variables con valores por defecto
            step_monitoring_result = None
            quality_gate_results = []
            sla_monitoring_result = None
            escalation_result = None
            
            # Extraer resultados de herramientas con validación exhaustiva
            if result is not None and isinstance(result, dict):
                self.logger.info("Result es dict válido")
                intermediate_steps = result.get("intermediate_steps")
                
                if intermediate_steps is not None and isinstance(intermediate_steps, list):
                    self.logger.info(f"Processing {len(intermediate_steps)} intermediate steps")
                    
                    for i, step in enumerate(intermediate_steps):
                        try:
                            if step is not None and isinstance(step, tuple) and len(step) >= 2:
                                tool_name = step[0]
                                tool_result = step[1]
                                
                                self.logger.info(f"Step {i}: {tool_name} -> {type(tool_result)}")
                                
                                if tool_name is not None and "step_completion_monitor_tool" in str(tool_name):
                                    if tool_result is not None and isinstance(tool_result, dict):
                                        step_monitoring_result = tool_result
                                        self.logger.info("Step monitoring result assigned")
                                    
                                elif tool_name is not None and "quality_gate_validator_tool" in str(tool_name):
                                    if tool_result is not None:
                                        if isinstance(tool_result, list):
                                            quality_gate_results.extend(tool_result)
                                        elif isinstance(tool_result, dict):
                                            quality_gate_results.append(tool_result)
                                        self.logger.info(f"Quality gate results: {len(quality_gate_results)}")
                                    
                                elif tool_name is not None and "sla_monitor_tool" in str(tool_name):
                                    if tool_result is not None and isinstance(tool_result, dict):
                                        sla_monitoring_result = tool_result
                                        self.logger.info("SLA monitoring result assigned")
                                    
                                elif tool_name is not None and "escalation_trigger_tool" in str(tool_name):
                                    if tool_result is not None and isinstance(tool_result, dict):
                                        escalation_result = tool_result
                                        self.logger.info("Escalation result assigned")
                                        
                        except Exception as e:
                            self.logger.error(f"Error processing step {i}: {e}")
                            continue
            
            # Crear snapshot de progreso con validación
            progress_snapshot = None
            try:
                self.logger.info("Creating progress snapshot")
                progress_snapshot = self._create_progress_snapshot(
                    step_monitoring_result, quality_gate_results, sla_monitoring_result
                )
                self.logger.info(f"Progress snapshot created: {progress_snapshot is not None}")
            except Exception as e:
                self.logger.error(f"Error creating progress snapshot: {e}")
                progress_snapshot = None
            
            # Calcular métricas principales con manejo de errores
            pipeline_health_score = 0.0
            try:
                pipeline_health_score = self._calculate_pipeline_health_score(
                    step_monitoring_result, quality_gate_results, sla_monitoring_result
                )
            except Exception as e:
                self.logger.error(f"Error calculating pipeline health: {e}")
                pipeline_health_score = 0.0
            
            completion_confidence = 0.0
            try:
                completion_confidence = self._calculate_completion_confidence(
                    step_monitoring_result, sla_monitoring_result
                )
            except Exception as e:
                self.logger.error(f"Error calculating completion confidence: {e}")
                completion_confidence = 0.0
            
            estimated_time_remaining = None
            try:
                estimated_time_remaining = self._estimate_time_remaining(
                    step_monitoring_result, sla_monitoring_result
                )
            except Exception as e:
                self.logger.error(f"Error estimating time remaining: {e}")
                estimated_time_remaining = None
            
            # Determinar estado crítico con manejo de errores
            pipeline_blocked = False
            try:
                pipeline_blocked = self._is_pipeline_blocked(quality_gate_results, sla_monitoring_result)
            except Exception as e:
                self.logger.error(f"Error checking if pipeline blocked: {e}")
                pipeline_blocked = False
            
            requires_manual_intervention = False
            try:
                requires_manual_intervention = self._requires_manual_intervention(
                    step_monitoring_result, quality_gate_results, escalation_result
                )
            except Exception as e:
                self.logger.error(f"Error checking manual intervention: {e}")
                requires_manual_intervention = False
            
            escalation_required = False
            try:
                escalation_required = self._escalation_required(escalation_result)
            except Exception as e:
                self.logger.error(f"Error checking escalation required: {e}")
                escalation_required = False
            
            # Generar insights con manejo de errores
            immediate_actions = []
            try:
                immediate_actions = self._generate_immediate_actions(
                    step_monitoring_result, quality_gate_results, sla_monitoring_result, escalation_result
                )
            except Exception as e:
                self.logger.error(f"Error generating immediate actions: {e}")
                immediate_actions = []
            
            recommendations = []
            try:
                recommendations = self._generate_recommendations(
                    step_monitoring_result, quality_gate_results, sla_monitoring_result
                )
            except Exception as e:
                self.logger.error(f"Error generating recommendations: {e}")
                recommendations = []
            
            risk_mitigations = []
            try:
                risk_mitigations = self._generate_risk_mitigation_suggestions(
                    sla_monitoring_result, escalation_result
                )
            except Exception as e:
                self.logger.error(f"Error generating risk mitigations: {e}")
                risk_mitigations = []
            
            # Extraer métricas con validación exhaustiva
            stages_monitored = 0
            try:
                if step_monitoring_result is not None and isinstance(step_monitoring_result, dict):
                    step_metrics = step_monitoring_result.get("step_metrics")
                    if step_metrics is not None and isinstance(step_metrics, dict):
                        stages_monitored = len(step_metrics)
            except Exception as e:
                self.logger.error(f"Error extracting stages monitored: {e}")
                stages_monitored = 0
            
            quality_gates_evaluated = 0
            try:
                if quality_gate_results is not None and isinstance(quality_gate_results, list):
                    quality_gates_evaluated = len(quality_gate_results)
            except Exception as e:
                self.logger.error(f"Error counting quality gates: {e}")
                quality_gates_evaluated = 0
            
            sla_breaches_detected = 0
            try:
                if sla_monitoring_result is not None and isinstance(sla_monitoring_result, dict):
                    sla_results = sla_monitoring_result.get("sla_results")
                    if sla_results is not None and isinstance(sla_results, list):
                        sla_breaches_detected = len([
                            r for r in sla_results 
                            if r is not None and isinstance(r, dict) and r.get("status") == "breached"
                        ])
            except Exception as e:
                self.logger.error(f"Error counting SLA breaches: {e}")
                sla_breaches_detected = 0
            
            escalations_triggered = 0
            escalation_events = []
            try:
                if escalation_result is not None and isinstance(escalation_result, dict):
                    escalations_triggered = escalation_result.get("escalation_count", 0)
                    if escalations_triggered is None:
                        escalations_triggered = 0
                        
                    escalation_events = escalation_result.get("escalations_triggered", [])
                    if escalation_events is None:
                        escalation_events = []
            except Exception as e:
                self.logger.error(f"Error extracting escalations: {e}")
                escalations_triggered = 0
                escalation_events = []
            
            # Crear snapshot dict con validación
            snapshot_dict = {}
            try:
                if progress_snapshot is not None:
                    if hasattr(progress_snapshot, 'dict') and callable(progress_snapshot.dict):
                        snapshot_dict = progress_snapshot.dict()
                    else:
                        snapshot_dict = {
                            "employee_id": "unknown",
                            "session_id": "unknown", 
                            "current_stage": "data_aggregation",
                            "overall_progress_percentage": 0.0,
                            "pipeline_health_score": pipeline_health_score
                        }
                else:
                    snapshot_dict = {
                        "employee_id": "unknown",
                        "session_id": "unknown",
                        "current_stage": "data_aggregation", 
                        "overall_progress_percentage": 0.0,
                        "pipeline_health_score": pipeline_health_score
                    }
            except Exception as e:
                self.logger.error(f"Error creating snapshot dict: {e}")
                snapshot_dict = {
                    "employee_id": "unknown",
                    "session_id": "unknown",
                    "current_stage": "data_aggregation",
                    "overall_progress_percentage": 0.0,
                    "pipeline_health_score": pipeline_health_score
                }
            
            # Extraer warnings con validación
            warnings = []
            try:
                warnings = self._extract_warnings_from_results(step_monitoring_result, quality_gate_results, sla_monitoring_result)
                if warnings is None:
                    warnings = []
            except Exception as e:
                self.logger.error(f"Error extracting warnings: {e}")
                warnings = []
            
            # Extraer sla_results con validación
            sla_results = []
            try:
                if sla_monitoring_result is not None and isinstance(sla_monitoring_result, dict):
                    sla_results = sla_monitoring_result.get("sla_results", [])
                    if sla_results is None:
                        sla_results = []
            except Exception as e:
                self.logger.error(f"Error extracting SLA results: {e}")
                sla_results = []
            
            self.logger.info("Creating final output dict")
            
            return {
                "success": True,
                "message": "Monitoreo de progreso completado exitosamente",
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "tracking_status": "completed",
                
                # Snapshot principal
                "progress_snapshot": snapshot_dict,
                
                # Resultados detallados
                "quality_gate_results": quality_gate_results if quality_gate_results is not None else [],
                "sla_monitoring_results": sla_results,
                "escalation_events": escalation_events,
                
                # Métricas de salud del pipeline
                "pipeline_health_score": pipeline_health_score,
                "completion_confidence": completion_confidence,
                "estimated_time_remaining_minutes": estimated_time_remaining,
                
                # Indicadores de estado crítico
                "pipeline_blocked": pipeline_blocked,
                "requires_manual_intervention": requires_manual_intervention,
                "escalation_required": escalation_required,
                
                # Insights actionables
                "immediate_actions_required": immediate_actions,
                "recommendations": recommendations,
                "risk_mitigation_suggestions": risk_mitigations,
                
                # Métricas de monitoreo
                "monitoring_timestamp": datetime.utcnow().isoformat(),
                "monitoring_scope": "sequential_pipeline",
                "stages_monitored": stages_monitored,
                "quality_gates_evaluated": quality_gates_evaluated,
                "sla_breaches_detected": sla_breaches_detected,
                "escalations_triggered": escalations_triggered,
                
                # Error handling
                "errors": [],
                "warnings": warnings
            }
            
        except Exception as e:
            self.logger.error(f"Error formateando salida de monitoreo: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            
            return {
                "success": False,
                "message": f"Error procesando resultados de monitoreo: {e}",
                "errors": [str(e)],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "tracking_status": "error",
                "pipeline_health_score": 0.0,
                "stages_monitored": 0,
                "quality_gates_evaluated": 0,
                "sla_breaches_detected": 0,
                "escalations_triggered": 0,
                "progress_snapshot": {
                    "employee_id": "unknown",
                    "session_id": "unknown",
                    "current_stage": "data_aggregation",
                    "overall_progress_percentage": 0.0,
                    "pipeline_health_score": 0.0
                },
                "quality_gate_results": [],
                "sla_monitoring_results": [],
                "escalation_events": [],
                "immediate_actions_required": [],
                "recommendations": [],
                "risk_mitigation_suggestions": [],
                "warnings": []
            }
    # En agents/progress_tracker/agent.py - Reemplazar toda la función _create_progress_snapshot

    def _create_progress_snapshot(self, step_result: Dict, quality_results: List, 
                                sla_result: Dict) -> Optional[PipelineProgressSnapshot]:
        """Crear snapshot del progreso del pipeline"""
        try:
            # Verificar que tengamos datos válidos
            if not step_result or not isinstance(step_result, dict) or not step_result.get("success"):
                self.logger.warning("Step result no válido para crear snapshot")
                return None
            
            # Extraer datos básicos con valores por defecto
            employee_id = step_result.get("employee_id", "unknown")
            session_id = step_result.get("session_id", "unknown")
            current_stage = step_result.get("current_stage", "data_aggregation")
            overall_progress = step_result.get("overall_progress_percentage", 0.0)
            
            # Calcular métricas de quality gates
            quality_gates_total = len(quality_results) if quality_results else 0
            quality_gates_passed = 0
            overall_quality_score = 0.0
            
            if quality_results:
                for r in quality_results:
                    if isinstance(r, dict):
                        gate_result = r.get("gate_result", {})
                        if isinstance(gate_result, dict) and gate_result.get("passed", False):
                            quality_gates_passed += 1
                
                # Calcular score promedio de calidad
                quality_scores = []
                for r in quality_results:
                    if isinstance(r, dict):
                        gate_result = r.get("gate_result", {})
                        if isinstance(gate_result, dict):
                            score = gate_result.get("overall_score", 0)
                            if isinstance(score, (int, float)) and score > 0:
                                quality_scores.append(score)
                
                overall_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            
            # Calcular métricas de SLA
            sla_compliance_percentage = 100.0
            stages_on_time = 0
            stages_at_risk = 0
            stages_breached = 0
            
            if sla_result and isinstance(sla_result, dict) and sla_result.get("success"):
                sla_summary = sla_result.get("sla_summary", {})
                if isinstance(sla_summary, dict):
                    sla_compliance_percentage = sla_summary.get("compliance_percentage", 100.0)
                    stages_on_time = sla_summary.get("stages_on_time", 0)
                
                stages_at_risk = sla_result.get("at_risk_count", 0)
                stages_breached = sla_result.get("breach_count", 0)
            
            # Issues y escalaciones
            active_escalations = 0
            critical_issues = []
            warnings = []
            
            # Extraer blocking issues del step result
            blocking_issues = step_result.get("blocking_issues", [])
            if isinstance(blocking_issues, list):
                critical_issues.extend(blocking_issues)
            
            # Calcular probabilidad de éxito y factores de riesgo
            success_probability = self._calculate_success_probability(step_result, quality_results, sla_result)
            risk_factors = self._identify_risk_factors(step_result, quality_results, sla_result)
            
            # Estimar tiempo de finalización
            estimated_completion = None
            if sla_result and isinstance(sla_result, dict) and sla_result.get("success"):
                sla_results_list = sla_result.get("sla_results", [])
                if isinstance(sla_results_list, list):
                    remaining_times = []
                    for r in sla_results_list:
                        if isinstance(r, dict):
                            remaining = r.get("remaining_time_minutes", 0)
                            if isinstance(remaining, (int, float)) and remaining > 0:
                                remaining_times.append(remaining)
                    
                    if remaining_times:
                        max_remaining = max(remaining_times)
                        estimated_completion = datetime.utcnow() + timedelta(minutes=max_remaining)
            
            return PipelineProgressSnapshot(
                employee_id=employee_id,
                session_id=session_id,
                current_stage=PipelineStage(current_stage) if current_stage in PipelineStage.__members__.values() else PipelineStage.DATA_AGGREGATION,
                overall_progress_percentage=overall_progress,
                estimated_completion_time=estimated_completion,
                quality_gates_passed=quality_gates_passed,
                quality_gates_total=quality_gates_total,
                overall_quality_score=overall_quality_score,
                sla_compliance_percentage=sla_compliance_percentage,
                stages_on_time=stages_on_time,
                stages_at_risk=stages_at_risk,
                stages_breached=stages_breached,
                active_escalations=active_escalations,
                critical_issues=critical_issues,
                warnings=warnings,
                success_probability=success_probability,
                risk_factors=risk_factors
            )
            
        except Exception as e:
            self.logger.error(f"Error creando progress snapshot: {e}")
            return None
    
    def _calculate_pipeline_health_score(self, step_result: Dict, quality_results: List, 
                                       sla_result: Dict) -> float:
        """Calcular score de salud del pipeline (0-100)"""
        try:
            scores = []
            
            # Score de progreso (40% del total)
            if step_result and step_result.get("success"):
                progress_score = step_result.get("overall_progress_percentage", 0)
                performance_metrics = step_result.get("performance_metrics", {})
                error_penalty = min(20, performance_metrics.get("total_errors", 0) * 5)
                progress_score = max(0, progress_score - error_penalty)
                scores.append(("progress", progress_score, 0.4))
            
            # Score de calidad (30% del total)
            if quality_results:
                quality_scores = [r.get("gate_result", {}).get("overall_score", 0) for r in quality_results if r.get("gate_result")]
                avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
                scores.append(("quality", avg_quality, 0.3))
            
            # Score de SLA (30% del total)
            if sla_result and sla_result.get("success"):
                sla_compliance = sla_result.get("overall_sla_compliance", 100.0)
                scores.append(("sla", sla_compliance, 0.3))
            
            # Calcular weighted average
            if scores:
                weighted_sum = sum(score * weight for _, score, weight in scores)
                total_weight = sum(weight for _, _, weight in scores)
                return max(0.0, min(100.0, weighted_sum / total_weight))
            else:
                return 50.0  # Score neutral si no hay datos
                
        except Exception:
            return 50.0
    
    def _calculate_completion_confidence(self, step_result: Dict, sla_result: Dict) -> float:
        """Calcular confianza de completitud (0-1)"""
        try:
            confidence_factors = []
            
            # Factor de progreso
            if step_result and step_result.get("success"):
                progress = step_result.get("overall_progress_percentage", 0) / 100.0
                confidence_factors.append(progress)
                
                # Factor de errores
                performance_metrics = step_result.get("performance_metrics", {})
                error_count = performance_metrics.get("total_errors", 0)
                error_factor = max(0.0, 1.0 - (error_count * 0.1))
                confidence_factors.append(error_factor)
            
            # Factor de SLA
            if sla_result and sla_result.get("success"):
                breach_count = sla_result.get("breach_count", 0)
                at_risk_count = sla_result.get("at_risk_count", 0)
                sla_factor = max(0.0, 1.0 - (breach_count * 0.3) - (at_risk_count * 0.1))
                confidence_factors.append(sla_factor)
            
            return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
            
        except Exception:
            return 0.5
    
    def _estimate_time_remaining(self, step_result: Dict, sla_result: Dict) -> Optional[float]:
        """Estimar tiempo restante en minutos"""
        try:
            if not sla_result or not sla_result.get("success"):
                return None
            
            remaining_times = []
            sla_results = sla_result.get("sla_results", [])
            
            for result in sla_results:
                remaining = result.get("remaining_time_minutes", 0)
                if remaining > 0:
                    remaining_times.append(remaining)
            
            return max(remaining_times) if remaining_times else 0.0
            
        except Exception:
            return None
    
# Corregir los métodos helper en _format_output()

    # Corrección 1: Mejorar null-safety en _format_output()
    def _is_pipeline_blocked(self, quality_results: List, sla_result: Dict) -> bool:
        """Determinar si el pipeline está bloqueado"""
        try:
            # Verificar quality gates fallidos
            if quality_results:
                failed_gates = [r for r in quality_results if r and r.get("gate_result", {}).get("status") == "failed"]
                if failed_gates:
                    mandatory_failures = [r for r in failed_gates if not r.get("gate_result", {}).get("can_bypass", True)]
                    if mandatory_failures:
                        return True
            
            # Verificar SLA breaches críticos
            if sla_result and sla_result.get("success"):
                breach_count = sla_result.get("breach_count", 0)
                if breach_count >= 2:  # Múltiples breaches = bloqueo
                    return True
            
            return False
        except Exception as e:
            self.logger.warning(f"Error checking pipeline blocked: {e}")
            return False

    def _requires_manual_intervention(self, step_result: Dict, quality_results: List, 
                                escalation_result: Dict) -> bool:
        """Determinar si requiere intervención manual"""
        try:
            # Errores repetidos
            if step_result and step_result.get("success"):
                performance_metrics = step_result.get("performance_metrics", {})
                if performance_metrics.get("stages_with_errors", 0) >= 2:
                    return True
            
            # Quality gates que requieren revisión manual
            if quality_results:
                manual_review_gates = [r for r in quality_results if r.get("gate_result", {}).get("status") == "manual_review"]
                if manual_review_gates:
                    return True
            
            # Escalaciones críticas
            if escalation_result and escalation_result.get("success"):
                escalations = escalation_result.get("escalations_triggered", [])
                critical_escalations = [e for e in escalations if e.get("escalation_level") in ["critical", "emergency"]]
                if critical_escalations:
                    return True
            
            return False
        except Exception as e:
            self.logger.warning(f"Error checking manual intervention: {e}")
            return False
    
    def _escalation_required(self, escalation_result: Dict) -> bool:
        """Determinar si se requiere escalación"""
        if escalation_result and escalation_result.get("success"):
            return escalation_result.get("escalation_count", 0) > 0
        return False
    
    def _generate_immediate_actions(self, step_result: Dict, quality_results: List,
                                sla_result: Dict, escalation_result: Dict) -> List[str]:
        """Generar acciones inmediatas requeridas"""
        actions = []
        
        try:
            # Acciones por quality gates fallidos
            if quality_results:
                failed_gates = [r for r in quality_results if r.get("gate_result", {}).get("status") == "failed"]
                for gate in failed_gates:
                    gate_info = gate.get("gate_result", {})
                    actions.extend(gate.get("next_actions", []))
            
            # Acciones por SLA breaches
            if sla_result and sla_result.get("success"):
                breach_count = sla_result.get("breach_count", 0)
                if breach_count > 0:
                    actions.append("Address SLA breaches immediately")
                    actions.append("Notify management of timing issues")
            
            # Acciones por escalaciones
            if escalation_result and escalation_result.get("success"):
                escalations = escalation_result.get("escalations_triggered", [])
                if escalations:
                    actions.append("Review and acknowledge escalations")
                    actions.append("Execute escalation response procedures")
            
            # Acciones por bloqueos del pipeline
            if self._is_pipeline_blocked(quality_results, sla_result):
                actions.append("Resolve pipeline blocking issues")
                actions.append("Consider emergency bypass procedures")
            
            return list(set(actions))  # Remove duplicates
        except Exception as e:
            self.logger.warning(f"Error generating immediate actions: {e}")
            return ["Monitor pipeline for issues"]

    def _generate_recommendations(self, step_result: Dict, quality_results: List, 
                                sla_result: Dict) -> List[str]:
        """Generar recomendaciones de mejora"""
        recommendations = []
        
        try:
            # Recomendaciones por performance
            if step_result and step_result.get("success"):
                performance_metrics = step_result.get("performance_metrics", {})
                avg_processing_time = performance_metrics.get("average_processing_time", 0)
                
                if avg_processing_time > 600:  # Más de 10 minutos promedio
                    recommendations.append("Consider optimizing agent processing time")
                
                error_count = performance_metrics.get("total_errors", 0)
                if error_count > 5:
                    recommendations.append("Investigate root causes of recurring errors")
            
            # Recomendaciones por calidad
            if quality_results:
                low_quality_gates = [r for r in quality_results if r.get("gate_result", {}).get("overall_score", 100) < 80]
                if low_quality_gates:
                    recommendations.append("Review and strengthen quality validation processes")
            
            # Recomendaciones por SLA
            if sla_result and sla_result.get("success"):
                at_risk_count = sla_result.get("at_risk_count", 0)
                if at_risk_count > 1:
                    recommendations.append("Consider adjusting SLA thresholds based on historical data")
            
            # Recomendaciones por defecto
            if not recommendations:
                recommendations.append("Continue monitoring pipeline progress")
            
            return recommendations
        except Exception as e:
            self.logger.warning(f"Error generating recommendations: {e}")
            return ["Continue monitoring pipeline progress"]
    
    def _generate_risk_mitigation_suggestions(self, sla_result: Dict,
                                            escalation_result: Dict) -> List[str]:
        """Generar sugerencias de mitigación de riesgos"""
        mitigations = []
        
        # Mitigaciones por riesgos de SLA
        if sla_result and sla_result.get("success"):
            at_risk_stages = [r for r in sla_result.get("sla_results", []) if r.get("status") == "at_risk"]
            
            for stage_result in at_risk_stages:
                stage = stage_result.get("stage", "unknown")
                breach_probability = stage_result.get("breach_probability", 0)
                
                if breach_probability > 0.7:
                    mitigations.append(f"Consider immediate intervention for {stage} stage")
                elif breach_probability > 0.4:
                    mitigations.append(f"Monitor {stage} stage closely for potential delays")
        
        # Mitigaciones por patrones de escalación
        if escalation_result and escalation_result.get("success"):
            escalation_summary = escalation_result.get("escalation_summary", {})
            
            if escalation_summary.get("requires_immediate_action", False):
                mitigations.append("Activate incident response procedures")
                mitigations.append("Engage senior management for critical decision making")
            
            # Mitigaciones por tipos de escalación
            escalation_types = escalation_summary.get("by_type", {})
            if "sla_breach" in escalation_types:
                mitigations.append("Implement SLA extension procedures where appropriate")
            if "quality_failure" in escalation_types:
                mitigations.append("Engage quality assurance team for immediate review")
            if "agent_failure" in escalation_types:
                mitigations.append("Implement agent restart and recovery procedures")
        
        # Mitigaciones generales
        mitigations.extend([
            "Maintain continuous monitoring until pipeline completion",
            "Prepare rollback procedures in case of critical failures",
            "Document incidents for post-mortem analysis and improvement"
        ])
        
        return mitigations
    
    # En agents/progress_tracker/agent.py - Reemplazar toda la función _calculate_success_probability

    def _calculate_success_probability(self, step_result: Dict, quality_results: List, 
                                    sla_result: Dict) -> float:
        """Calcular probabilidad de éxito del pipeline (0-1)"""
        try:
            factors = []
            
            # Factor de progreso
            if step_result and isinstance(step_result, dict) and step_result.get("success"):
                progress = step_result.get("overall_progress_percentage", 0) / 100.0
                performance_metrics = step_result.get("performance_metrics", {})
                if isinstance(performance_metrics, dict):
                    error_penalty = min(0.3, performance_metrics.get("total_errors", 0) * 0.05)
                    progress_factor = max(0.0, progress - error_penalty)
                    factors.append(progress_factor)
            
            # Factor de calidad
            if quality_results and isinstance(quality_results, list):
                passed_gates = 0
                total_gates = len(quality_results)
                
                for r in quality_results:
                    if isinstance(r, dict):
                        gate_result = r.get("gate_result", {})
                        if isinstance(gate_result, dict) and gate_result.get("passed", False):
                            passed_gates += 1
                
                quality_factor = passed_gates / total_gates if total_gates > 0 else 1.0
                factors.append(quality_factor)
            
            # Factor de SLA
            if sla_result and isinstance(sla_result, dict) and sla_result.get("success"):
                compliance = sla_result.get("overall_sla_compliance", 100.0) / 100.0
                breach_count = sla_result.get("breach_count", 0)
                breach_penalty = breach_count * 0.2 if isinstance(breach_count, (int, float)) else 0
                sla_factor = max(0.0, compliance - breach_penalty)
                factors.append(sla_factor)
            
            return sum(factors) / len(factors) if factors else 0.5
            
        except Exception as e:
            self.logger.error(f"Error calculando probabilidad de éxito: {e}")
            return 0.5
    # En agents/progress_tracker/agent.py - Reemplazar toda la función _identify_risk_factors

    def _identify_risk_factors(self, step_result: Dict, quality_results: List, 
                            sla_result: Dict) -> List[str]:
        """Identificar factores de riesgo específicos"""
        risks = []
        
        try:
            # Riesgos por progreso lento
            if step_result and isinstance(step_result, dict) and step_result.get("success"):
                progress = step_result.get("overall_progress_percentage", 0)
                if isinstance(progress, (int, float)) and progress < 50:
                    risks.append("Below expected progress rate")
                
                performance_metrics = step_result.get("performance_metrics", {})
                if isinstance(performance_metrics, dict):
                    stages_with_errors = performance_metrics.get("stages_with_errors", 0)
                    avg_processing_time = performance_metrics.get("average_processing_time", 0)
                    
                    if isinstance(stages_with_errors, (int, float)) and stages_with_errors > 1:
                        risks.append("Multiple stages experiencing errors")
                    
                    if isinstance(avg_processing_time, (int, float)) and avg_processing_time > 900:  # 15 minutes
                        risks.append("Processing times exceeding normal ranges")
            
            # Riesgos por calidad
            if quality_results and isinstance(quality_results, list):
                failed_gates = 0
                manual_review_gates = 0
                
                for r in quality_results:
                    if isinstance(r, dict):
                        gate_result = r.get("gate_result", {})
                        if isinstance(gate_result, dict):
                            if gate_result.get("status") == "failed":
                                failed_gates += 1
                            elif gate_result.get("status") == "manual_review":
                                manual_review_gates += 1
                
                if failed_gates > 0:
                    risks.append(f"{failed_gates} quality gate(s) failed")
                
                if manual_review_gates > 0:
                    risks.append("Quality gates requiring manual intervention")
            
            # Riesgos por SLA
            if sla_result and isinstance(sla_result, dict) and sla_result.get("success"):
                at_risk_count = sla_result.get("at_risk_count", 0)
                breach_count = sla_result.get("breach_count", 0)
                
                if isinstance(breach_count, (int, float)) and breach_count > 0:
                    risks.append(f"SLA breaches detected ({breach_count} stages)")
                elif isinstance(at_risk_count, (int, float)) and at_risk_count > 1:
                    risks.append(f"Multiple stages at SLA risk ({at_risk_count} stages)")
            
        except Exception as e:
            self.logger.error(f"Error identificando factores de riesgo: {e}")
            risks.append("Error analyzing risk factors")
        
        return risks
    
    # En agents/progress_tracker/agent.py - Reemplazar toda la función _extract_warnings_from_results

    def _extract_warnings_from_results(self, step_result: Dict, quality_results: List, 
                                    sla_result: Dict) -> List[str]:
        """Extraer warnings de los resultados"""
        warnings = []
        
        try:
            # Warnings de progreso
            if step_result and isinstance(step_result, dict) and step_result.get("success"):
                blocking_issues = step_result.get("blocking_issues", [])
                if isinstance(blocking_issues, list):
                    warnings.extend(blocking_issues)
            
            # Warnings de calidad
            if quality_results and isinstance(quality_results, list):
                for quality_result in quality_results:
                    if isinstance(quality_result, dict):
                        gate_result = quality_result.get("gate_result", {})
                        if isinstance(gate_result, dict) and gate_result.get("warnings"):
                            gate_warnings = gate_result["warnings"]
                            if isinstance(gate_warnings, list):
                                warnings.extend(gate_warnings)
            
            # Warnings de SLA
            if sla_result and isinstance(sla_result, dict) and sla_result.get("success"):
                alerts = sla_result.get("alerts", [])
                if isinstance(alerts, list):
                    warning_alerts = [
                        alert["message"] for alert in alerts 
                        if isinstance(alert, dict) and alert.get("level") == "warning" and "message" in alert
                    ]
                    warnings.extend(warning_alerts)
            
        except Exception as e:
            self.logger.error(f"Error extrayendo warnings: {e}")
            warnings.append("Error extracting warnings from results")
        
        return warnings
    
    @observability_manager.trace_agent_execution("progress_tracker_agent")
    def track_pipeline_progress(self, tracking_request: ProgressTrackerRequest, 
                              session_id: str = None) -> Dict[str, Any]:
        """Ejecutar monitoreo completo del pipeline secuencial"""
        # Generar tracker_id
        tracker_id = f"track_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{tracking_request.employee_id}"
        
        # Actualizar estado: PROCESSING
        state_manager.update_agent_state(
            self.agent_id,
            AgentStateStatus.PROCESSING,
            {
                "current_task": "pipeline_tracking",
                "tracker_id": tracker_id,
                "employee_id": tracking_request.employee_id,
                "monitoring_scope": tracking_request.monitoring_scope,
                "started_at": datetime.utcnow().isoformat()
            },
            session_id
        )
        
        # Registrar métricas iniciales
        observability_manager.log_agent_metrics(
            self.agent_id,
            {
                "monitoring_scope": tracking_request.monitoring_scope,
                "quality_gates_enabled": tracking_request.include_quality_gates,
                "sla_monitoring_enabled": tracking_request.include_sla_monitoring,
                "escalation_check_enabled": tracking_request.include_escalation_check,
                "target_stages": len(tracking_request.target_stages),
                "detailed_metrics": tracking_request.detailed_metrics
            },
            session_id
        )
        
        try:
            # Procesar con el método base
            result = self.process_request(tracking_request, session_id)
            
            # Si el procesamiento fue exitoso, actualizar State Management
            if result["success"]:
                # Actualizar datos del empleado
                if session_id:
                    tracking_data = {
                        "progress_tracking_completed": True,
                        "tracker_id": tracker_id,
                        "pipeline_health_score": result.get("pipeline_health_score", 0),
                        "completion_confidence": result.get("completion_confidence", 0),
                        "pipeline_blocked": result.get("pipeline_blocked", False),
                        "escalation_required": result.get("escalation_required", False),
                        "estimated_completion": result.get("estimated_time_remaining_minutes", 0),
                        "monitoring_timestamp": datetime.utcnow().isoformat()
                    }
                    
                    state_manager.update_employee_data(
                        session_id,
                        tracking_data,
                        "monitored"
                    )
                
                # Actualizar estado: COMPLETED
                state_manager.update_agent_state(
                    self.agent_id,
                    AgentStateStatus.COMPLETED,
                    {
                        "current_task": "completed",
                        "tracker_id": tracker_id,
                        "pipeline_health_score": result.get("pipeline_health_score", 0),
                        "stages_monitored": result.get("stages_monitored", 0),
                        "quality_gates_evaluated": result.get("quality_gates_evaluated", 0),
                        "escalations_triggered": result.get("escalations_triggered", 0),
                        "tracking_status": result.get("tracking_status", "completed"),
                        "completed_at": datetime.utcnow().isoformat()
                    },
                    session_id
                )
                
                # Registrar en sesiones activas
                self.active_monitoring_sessions[tracker_id] = {
                    "status": "completed",
                    "result": result,
                    "completed_at": datetime.utcnow()
                }
                
            else:
                # Error en tracking
                state_manager.update_agent_state(
                    self.agent_id,
                    AgentStateStatus.ERROR,
                    {
                        "current_task": "error",
                        "tracker_id": tracker_id,
                        "errors": result.get("errors", []),
                        "failed_at": datetime.utcnow().isoformat()
                    },
                    session_id
                )
            
            # Agregar información de sesión al resultado
            result["tracker_id"] = tracker_id
            result["session_id"] = session_id
            return result
            
        except Exception as e:
            # Error durante tracking
            error_msg = f"Error ejecutando monitoreo de progreso: {str(e)}"
            state_manager.update_agent_state(
                self.agent_id,
                AgentStateStatus.ERROR,
                {
                    "current_task": "error",
                    "tracker_id": tracker_id,
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
                "tracker_id": tracker_id,
                "session_id": session_id,
                "agent_id": self.agent_id,
                "processing_time": 0,
                "tracking_status": "failed"
            }
    
    # En agents/progress_tracker/agent.py - Reemplazar toda la función _process_with_tools_directly

    # Corrección 2: Mejorar data handling en quality gate validator
    def _process_with_tools_directly(self, input_data: Any) -> Dict[str, Any]:
        """Procesar usando herramientas directamente con flujo específico de tracking"""
        results = []
        formatted_input = self._format_input(input_data)
        self.logger.info(f"Procesando tracking con {len(self.tools)} herramientas especializadas")
        
        # Variables para almacenar resultados
        step_monitoring_result = None
        quality_gate_results = []
        sla_monitoring_result = None
        escalation_result = None
        
        # Preparar datos según el tipo de entrada
        if isinstance(input_data, ProgressTrackerRequest):
            session_id = input_data.session_id
            employee_id = input_data.employee_id
            target_stages = input_data.target_stages or []
            include_quality_gates = input_data.include_quality_gates
            include_sla_monitoring = input_data.include_sla_monitoring
            include_escalation_check = input_data.include_escalation_check
        else:
            # Fallback para datos genéricos
            session_id = input_data.get("session_id", "") if isinstance(input_data, dict) else ""
            employee_id = input_data.get("employee_id", "unknown") if isinstance(input_data, dict) else "unknown"
            target_stages = input_data.get("target_stages", []) if isinstance(input_data, dict) else []
            include_quality_gates = True
            include_sla_monitoring = True
            include_escalation_check = True
        
        # 1. Ejecutar Step Completion Monitor (siempre primero)
        try:
            self.logger.info("Ejecutando step_completion_monitor_tool")
            step_monitoring_result = step_completion_monitor_tool.invoke({
                "session_id": session_id,
                "target_stages": target_stages,
                "detailed_analysis": True
            })
            results.append(("step_completion_monitor_tool", step_monitoring_result))
            self.logger.info("✅ Step completion monitoring completado")
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.logger.warning(f"❌ Error con step_completion_monitor_tool: {e}")
            results.append(("step_completion_monitor_tool", {"success": False, "error": error_msg}))
        
        # 2. Ejecutar Quality Gate Validator (si habilitado) - CORREGIDO
        if include_quality_gates and step_monitoring_result and step_monitoring_result.get("success"):
            try:
                self.logger.info("Ejecutando quality_gate_validator_tool para múltiples etapas")
                
                # Validar quality gates para cada etapa
                step_metrics = step_monitoring_result.get("step_metrics", {})
                
                for stage_name, stage_data in step_metrics.items():
                    if stage_data and stage_data.get("status") in ["completed", "processing"]:
                        try:
                            # Asegurar que stage_data tiene los campos necesarios - MEJORADO
                            enhanced_stage_data = {
                                **stage_data,
                                "agent_output_validated": True,
                                "stage_name": stage_name,
                                # Agregar campos por defecto si no existen
                                "overall_quality_score": stage_data.get("output_quality_score", 0),
                                "success": stage_data.get("status") == "completed"
                            }
                            
                            gate_result = quality_gate_validator_tool.invoke({
                                "session_id": session_id,
                                "stage": stage_name,
                                "agent_output": enhanced_stage_data
                            })
                            
                            # Validar que el resultado tenga la estructura correcta - NUEVO
                            if gate_result and gate_result.get("success"):
                                quality_gate_results.append(gate_result)
                            else:
                                self.logger.warning(f"Quality gate validation failed for {stage_name}: {gate_result.get('error', 'Unknown error')}")
                                # Agregar resultado de fallo estructurado - NUEVO
                                fallback_result = {
                                    "success": False,
                                    "stage": stage_name,
                                    "error": gate_result.get("error", "Validation failed"),
                                    "gate_result": {
                                        "passed": False,
                                        "status": "failed",
                                        "overall_score": 0.0,
                                        "gate_id": f"{stage_name}_gate",
                                        "critical_issues": ["Validation process failed"],
                                        "warnings": []
                                    }
                                }
                                quality_gate_results.append(fallback_result)
                                
                        except Exception as e:
                            self.logger.warning(f"Error validating quality gate for {stage_name}: {e}")
                            # Agregar resultado de error estructurado - NUEVO
                            error_result = {
                                "success": False,
                                "stage": stage_name,
                                "error": str(e),
                                "gate_result": {
                                    "passed": False,
                                    "status": "error",
                                    "overall_score": 0.0,
                                    "gate_id": f"{stage_name}_gate",
                                    "critical_issues": [f"Processing error: {str(e)}"],
                                    "warnings": []
                                }
                            }
                            quality_gate_results.append(error_result)
                
                results.append(("quality_gate_validator_tool", quality_gate_results))
                self.logger.info(f"✅ Quality gate validation completado para {len(quality_gate_results)} etapas")
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.logger.warning(f"❌ Error con quality_gate_validator_tool: {e}")
                # Estructura de error consistente - NUEVO
                results.append(("quality_gate_validator_tool", {
                    "success": False, 
                    "error": error_msg,
                    "quality_gate_results": []
                }))
        
        # 3. Ejecutar SLA Monitor (si habilitado)
        if include_sla_monitoring:
            try:
                self.logger.info("Ejecutando sla_monitor_tool")
                sla_monitoring_result = sla_monitor_tool.invoke({
                    "session_id": session_id,
                    "target_stages": target_stages,
                    "include_predictions": True
                })
                results.append(("sla_monitor_tool", sla_monitoring_result))
                self.logger.info("✅ SLA monitoring completado")
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.logger.warning(f"❌ Error con sla_monitor_tool: {e}")
                results.append(("sla_monitor_tool", {"success": False, "error": error_msg}))
        
        # 4. Ejecutar Escalation Trigger (si habilitado) - MEJORADO
        if include_escalation_check:
            try:
                self.logger.info("Ejecutando escalation_trigger_tool")
                
                # Preparar datos para escalación - MEJORADO
                sla_results_for_escalation = None
                quality_results_for_escalation = None
                
                if sla_monitoring_result and sla_monitoring_result.get("success"):
                    sla_results_for_escalation = sla_monitoring_result.get("sla_results", [])
                
                if quality_gate_results:
                    # Mejorar extracción de resultados de quality gates - CORREGIDO
                    quality_results_for_escalation = []
                    for qr in quality_gate_results:
                        if qr and qr.get("gate_result"):
                            quality_results_for_escalation.append(qr.get("gate_result", {}))
                        elif qr and qr.get("success") is False:
                            # Incluir fallos también
                            quality_results_for_escalation.append({
                                "status": "failed",
                                "passed": False,
                                "overall_score": 0.0
                            })
                
                escalation_result = escalation_trigger_tool.invoke({
                    "session_id": session_id,
                    "sla_results": sla_results_for_escalation,
                    "quality_results": quality_results_for_escalation,
                    "force_check": False
                })
                results.append(("escalation_trigger_tool", escalation_result))
                self.logger.info("✅ Escalation trigger completado")
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.logger.warning(f"❌ Error con escalation_trigger_tool: {e}")
                results.append(("escalation_trigger_tool", {"success": False, "error": error_msg}))
        
        # Evaluar éxito general - MEJORADO
        successful_tools = len([r for r in results if isinstance(r, tuple) and isinstance(r[1], dict) and r[1].get("success")])
        overall_success = successful_tools >= 2  # Al menos step monitoring y uno más
        
        return {
            "output": "Procesamiento de monitoreo de progreso completado",
            "intermediate_steps": results,
            "step_monitoring_result": step_monitoring_result,
            "quality_gate_results": quality_gate_results,
            "sla_monitoring_result": sla_monitoring_result,
            "escalation_result": escalation_result,
            "successful_tools": successful_tools,
            "overall_success": overall_success,
            "tools_executed": len(results)
        }

    # Métodos auxiliares para el agente
    def get_tracking_status(self, tracker_id: str) -> Dict[str, Any]:
        """Obtener estado de un tracking específico"""
        try:
            if tracker_id in self.active_monitoring_sessions:
                return {
                    "found": True,
                    "tracker_id": tracker_id,
                    **self.active_monitoring_sessions[tracker_id]
                }
            else:
                return {
                    "found": False,
                    "tracker_id": tracker_id,
                    "message": "Tracking no encontrado en registros activos"
                }
        except Exception as e:
            return {"found": False, "error": str(e)}
    
    def get_pipeline_health_report(self, session_id: str) -> Dict[str, Any]:
        """Generar reporte de salud del pipeline"""
        try:
            # Ejecutar monitoreo rápido
            quick_request = ProgressTrackerRequest(
                employee_id="health_check",
                session_id=session_id,
                monitoring_scope="pipeline_health",
                include_quality_gates=True,
                include_sla_monitoring=True,
                include_escalation_check=True,
                detailed_metrics=False
            )
            
            result = self.track_pipeline_progress(quick_request, session_id)
            
            if result["success"]:
                return {
                    "health_report_generated": True,
                    "pipeline_health_score": result.get("pipeline_health_score", 0),
                    "completion_confidence": result.get("completion_confidence", 0),
                    "pipeline_status": "healthy" if result.get("pipeline_health_score", 0) > 70 else "needs_attention",
                    "immediate_actions": result.get("immediate_actions_required", []),
                    "recommendations": result.get("recommendations", []),
                    "report_timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "health_report_generated": False,
                    "error": result.get("message", "Unknown error"),
                    "pipeline_status": "unknown"
                }
                
        except Exception as e:
            return {
                "health_report_generated": False,
                "error": str(e),
                "pipeline_status": "error"
            }
    
    def validate_monitoring_configuration(self) -> Dict[str, Any]:
        """Validar configuración de monitoreo"""
        try:
            from .monitoring_rules import validate_monitoring_configuration
            
            validation_issues = validate_monitoring_configuration()
            
            return {
                "configuration_valid": len(validation_issues) == 0,
                "validation_issues": validation_issues,
                "quality_gates_configured": len(self.monitoring_rules.quality_gates),
                "sla_configurations": len(self.monitoring_rules.sla_configurations),
                "escalation_rules": len(self.monitoring_rules.escalation_rules),
                "monitoring_ready": len(validation_issues) == 0
            }
            
        except Exception as e:
            return {
                "configuration_valid": False,
                "error": str(e),
                "monitoring_ready": False
            }