from typing import Dict, Any, List, Optional
from langchain.tools import BaseTool
from datetime import datetime, timedelta
import json
from .schemas import (
    ErrorCategory, ErrorType, ErrorSeverity, ErrorSource, RecoveryStrategy,
    ErrorPattern, RootCauseAnalysis, ErrorClassificationResult
)

class ErrorDetectorTool(BaseTool):
    """Herramienta para detectar errores del sistema"""
    name: str = "error_detector_tool"
    description: str = "Detecta y extrae errores de múltiples fuentes del sistema"

    def _run(self, session_id: str, monitoring_data: Dict[str, Any], 
             include_historical: bool = True) -> Dict[str, Any]:
        """Detectar errores en el sistema"""
        try:
            from core.state_management.state_manager import state_manager
            
            detected_errors = []
            error_count = 0
            
            # Obtener contexto del empleado
            employee_context = state_manager.get_employee_context(session_id)
            if not employee_context:
                return {
                    "success": False,
                    "error": "Employee context not found",
                    "detected_errors": [],
                    "error_count": 0
                }

            # 1. Detectar errores del Progress Tracker
            progress_errors = self._detect_progress_tracker_errors(monitoring_data, employee_context)
            detected_errors.extend(progress_errors)

            # 2. Detectar errores de agentes individuales
            agent_errors = self._detect_agent_errors(employee_context)
            detected_errors.extend(agent_errors)

            # 3. Detectar errores de SLA
            sla_errors = self._detect_sla_errors(monitoring_data)
            detected_errors.extend(sla_errors)

            # 4. Detectar errores de Quality Gates
            quality_errors = self._detect_quality_gate_errors(monitoring_data)
            detected_errors.extend(quality_errors)

            return {
                "success": True,
                "session_id": session_id,
                "employee_id": employee_context.employee_id,
                "detection_timestamp": datetime.utcnow().isoformat(),
                "detected_errors": detected_errors,
                "error_count": len(detected_errors),
                "error_summary": self._summarize_errors(detected_errors),
                "detection_scope": "system_wide",
                "historical_included": include_historical
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error detecting system errors: {str(e)}",
                "detected_errors": [],
                "error_count": 0
            }

    def _detect_progress_tracker_errors(self, monitoring_data: Dict[str, Any], 
                                       employee_context) -> List[Dict[str, Any]]:
        """Detectar errores del Progress Tracker"""
        errors = []
        
        # Extraer datos del progress tracker
        progress_data = monitoring_data.get("progress_tracker_result", {})
        if not progress_data.get("success", True):
            errors.append({
                "source": ErrorSource.PROGRESS_TRACKER,
                "error_type": "monitoring_failure",
                "description": progress_data.get("message", "Progress tracking failed"),
                "severity": "high",
                "timestamp": datetime.utcnow().isoformat(),
                "context": progress_data
            })

        # Detectar errores de pipeline bloqueado
        if progress_data.get("pipeline_blocked", False):
            errors.append({
                "source": ErrorSource.PROGRESS_TRACKER,
                "error_type": "pipeline_blocked",
                "description": "Pipeline execution is blocked",
                "severity": "critical",
                "timestamp": datetime.utcnow().isoformat(),
                "context": {
                    "blocking_issues": progress_data.get("immediate_actions_required", [])
                }
            })

        # Detectar SLA breaches del progress tracker
        sla_breaches = progress_data.get("sla_breaches_detected", 0)
        if sla_breaches > 0:
            errors.append({
                "source": ErrorSource.PROGRESS_TRACKER,
                "error_type": "sla_breach_detected",
                "description": f"{sla_breaches} SLA breaches detected",
                "severity": "high" if sla_breaches < 2 else "critical",
                "timestamp": datetime.utcnow().isoformat(),
                "context": {
                    "breach_count": sla_breaches,
                    "sla_results": progress_data.get("sla_monitoring_results", [])
                }
            })

        return errors

    def _detect_agent_errors(self, employee_context) -> List[Dict[str, Any]]:
        """Detectar errores de agentes individuales"""
        errors = []
        
        for agent_id, agent_state in employee_context.agent_states.items():
            # Detectar agentes con estado de error
            if agent_state.status.value == "error":
                errors.append({
                    "source": ErrorSource.AGENT_DIRECT,
                    "error_type": "agent_failure",
                    "description": f"Agent {agent_id} is in error state",
                    "severity": "high",
                    "timestamp": datetime.utcnow().isoformat(),
                    "context": {
                        "agent_id": agent_id,
                        "agent_errors": agent_state.errors,
                        "agent_data": agent_state.data
                    }
                })

            # Detectar agentes con muchos errores
            if len(agent_state.errors) > 3:
                errors.append({
                    "source": ErrorSource.AGENT_DIRECT,
                    "error_type": "excessive_errors",
                    "description": f"Agent {agent_id} has excessive errors ({len(agent_state.errors)})",
                    "severity": "medium",
                    "timestamp": datetime.utcnow().isoformat(),
                    "context": {
                        "agent_id": agent_id,
                        "error_count": len(agent_state.errors),
                        "recent_errors": agent_state.errors[-3:]
                    }
                })

            # Detectar timeouts (agente processing por mucho tiempo)
            if (agent_state.status.value == "processing" and 
                agent_state.last_updated and 
                (datetime.utcnow() - agent_state.last_updated).total_seconds() > 1800):  # 30 minutos
                
                errors.append({
                    "source": ErrorSource.AGENT_DIRECT,
                    "error_type": "timeout",
                    "description": f"Agent {agent_id} appears to be stuck in processing",
                    "severity": "high",
                    "timestamp": datetime.utcnow().isoformat(),
                    "context": {
                        "agent_id": agent_id,
                        "processing_duration": (datetime.utcnow() - agent_state.last_updated).total_seconds(),
                        "last_updated": agent_state.last_updated.isoformat()
                    }
                })

        return errors

    def _detect_sla_errors(self, monitoring_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detectar errores de SLA"""
        errors = []
        
        sla_results = monitoring_data.get("sla_monitoring_results", [])
        for sla_result in sla_results:
            if isinstance(sla_result, dict):
                # SLA breach
                if sla_result.get("status") == "breached":
                    errors.append({
                        "source": ErrorSource.SLA_MONITOR,
                        "error_type": "sla_breach",
                        "description": f"SLA breach in stage {sla_result.get('stage')}",
                        "severity": "critical",
                        "timestamp": datetime.utcnow().isoformat(),
                        "context": sla_result
                    })
                
                # SLA at risk
                elif sla_result.get("status") == "at_risk":
                    errors.append({
                        "source": ErrorSource.SLA_MONITOR,
                        "error_type": "sla_at_risk",
                        "description": f"SLA at risk in stage {sla_result.get('stage')}",
                        "severity": "medium",
                        "timestamp": datetime.utcnow().isoformat(),
                        "context": sla_result
                    })

        return errors

    def _detect_quality_gate_errors(self, monitoring_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detectar errores de Quality Gates"""
        errors = []
        
        quality_results = monitoring_data.get("quality_gate_results", [])
        for quality_result in quality_results:
            if isinstance(quality_result, dict):
                gate_result = quality_result.get("gate_result", {})
                
                # Quality gate failed
                if gate_result.get("status") == "failed":
                    errors.append({
                        "source": ErrorSource.QUALITY_GATE,
                        "error_type": "quality_failure",
                        "description": f"Quality gate failed for stage {quality_result.get('stage')}",
                        "severity": "high",
                        "timestamp": datetime.utcnow().isoformat(),
                        "context": {
                            "stage": quality_result.get("stage"),
                            "gate_result": gate_result,
                            "critical_issues": gate_result.get("critical_issues", [])
                        }
                    })
                
                # Quality gate requires manual review
                elif gate_result.get("status") == "manual_review":
                    errors.append({
                        "source": ErrorSource.QUALITY_GATE,
                        "error_type": "manual_review_required",
                        "description": f"Quality gate requires manual review for stage {quality_result.get('stage')}",
                        "severity": "medium",
                        "timestamp": datetime.utcnow().isoformat(),
                        "context": {
                            "stage": quality_result.get("stage"),
                            "gate_result": gate_result
                        }
                    })

        return errors

    def _summarize_errors(self, detected_errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Crear resumen de errores detectados"""
        if not detected_errors:
            return {"total": 0}
        
        summary = {
            "total": len(detected_errors),
            "by_source": {},
            "by_severity": {},
            "by_type": {},
            "critical_count": 0
        }
        
        for error in detected_errors:
            source = error.get("source", "unknown")
            severity = error.get("severity", "unknown")
            error_type = error.get("error_type", "unknown")
            
            summary["by_source"][source] = summary["by_source"].get(source, 0) + 1
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
            summary["by_type"][error_type] = summary["by_type"].get(error_type, 0) + 1
            
            if severity in ["critical", "emergency"]:
                summary["critical_count"] += 1
        
        return summary

class SeverityAnalyzerTool(BaseTool):
    """Herramienta para analizar severidad de errores"""
    name: str = "severity_analyzer_tool"
    description: str = "Analiza y determina la severidad de errores detectados"

    def _run(self, detected_errors: List[Dict[str, Any]], 
             context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analizar severidad de errores"""
        try:
            severity_analysis = {}
            
            for error in detected_errors:
                error_id = f"{error.get('source')}_{error.get('error_type')}"
                
                # Análisis base de severidad
                base_severity = self._calculate_base_severity(error)
                
                # Ajustar severidad por contexto
                contextual_severity = self._adjust_severity_by_context(
                    base_severity, error, context_data
                )
                
                # Calcular impacto
                impact_analysis = self._analyze_impact(error, context_data)
                
                severity_analysis[error_id] = {
                    "base_severity": base_severity,
                    "contextual_severity": contextual_severity,
                    "final_severity": contextual_severity,
                    "impact_analysis": impact_analysis,
                    "confidence": self._calculate_confidence(error, context_data)
                }
            
            # Determinar severidad global
            global_severity = self._determine_global_severity(severity_analysis)
            
            return {
                "success": True,
                "severity_analysis": severity_analysis,
                "global_severity": global_severity,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "recommendations": self._generate_severity_recommendations(severity_analysis)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error analyzing severity: {str(e)}",
                "severity_analysis": {}
            }

    def _calculate_base_severity(self, error: Dict[str, Any]) -> ErrorSeverity:
        """Calcular severidad base del error"""
        error_type = error.get("error_type", "")
        source = error.get("source", "")
        
        # Mapeo de tipos de error a severidad
        critical_types = ["pipeline_blocked", "agent_failure", "sla_breach", "system_error"]
        high_types = ["timeout", "quality_failure", "excessive_errors"]
        medium_types = ["sla_at_risk", "manual_review_required", "validation_failure"]
        
        if error_type in critical_types:
            return ErrorSeverity.CRITICAL
        elif error_type in high_types:
            return ErrorSeverity.HIGH
        elif error_type in medium_types:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    def _adjust_severity_by_context(self, base_severity: ErrorSeverity, 
                                   error: Dict[str, Any], 
                                   context_data: Dict[str, Any]) -> ErrorSeverity:
        """Ajustar severidad basada en contexto"""
        # Factores que pueden elevar severidad
        employee_priority = context_data.get("employee_priority", "normal")
        business_impact = context_data.get("business_impact", "low")
        time_sensitivity = context_data.get("time_sensitivity", "normal")
        
        severity_score = self._severity_to_score(base_severity)
        
        # Ajustes por prioridad del empleado
        if employee_priority == "executive":
            severity_score += 1
        elif employee_priority == "high":
            severity_score += 0.5
        
        # Ajustes por impacto de negocio
        if business_impact == "high":
            severity_score += 1
        elif business_impact == "critical":
            severity_score += 2
        
        # Ajustes por sensibilidad temporal
        if time_sensitivity == "urgent":
            severity_score += 0.5
        elif time_sensitivity == "critical":
            severity_score += 1
        
        return self._score_to_severity(severity_score)

    def _severity_to_score(self, severity: ErrorSeverity) -> float:
        """Convertir severidad a score numérico"""
        mapping = {
            ErrorSeverity.LOW: 1.0,
            ErrorSeverity.MEDIUM: 2.0,
            ErrorSeverity.HIGH: 3.0,
            ErrorSeverity.CRITICAL: 4.0,
            ErrorSeverity.EMERGENCY: 5.0
        }
        return mapping.get(severity, 1.0)

    def _score_to_severity(self, score: float) -> ErrorSeverity:
        """Convertir score numérico a severidad"""
        if score >= 5.0:
            return ErrorSeverity.EMERGENCY
        elif score >= 4.0:
            return ErrorSeverity.CRITICAL
        elif score >= 3.0:
            return ErrorSeverity.HIGH
        elif score >= 2.0:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    def _analyze_impact(self, error: Dict[str, Any], 
                       context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analizar impacto del error"""
        return {
            "pipeline_impact": self._assess_pipeline_impact(error),
            "business_impact": self._assess_business_impact(error, context_data),
            "user_impact": self._assess_user_impact(error, context_data),
            "system_impact": self._assess_system_impact(error)
        }

    def _assess_pipeline_impact(self, error: Dict[str, Any]) -> str:
        """Evaluar impacto en el pipeline"""
        error_type = error.get("error_type", "")
        
        if error_type in ["pipeline_blocked", "agent_failure"]:
            return "pipeline_stopped"
        elif error_type in ["sla_breach", "timeout"]:
            return "pipeline_delayed"
        elif error_type in ["quality_failure"]:
            return "pipeline_quality_compromised"
        else:
            return "pipeline_minimal_impact"

    def _assess_business_impact(self, error: Dict[str, Any], 
                               context_data: Dict[str, Any]) -> str:
        """Evaluar impacto en el negocio"""
        employee_type = context_data.get("employee_type", "standard")
        department = context_data.get("department", "general")
        
        if employee_type == "executive":
            return "high_business_impact"
        elif department in ["IT", "Security", "Legal"]:
            return "medium_business_impact"
        else:
            return "low_business_impact"

    def _assess_user_impact(self, error: Dict[str, Any], 
                           context_data: Dict[str, Any]) -> str:
        """Evaluar impacto en el usuario"""
        error_type = error.get("error_type", "")
        
        if error_type in ["pipeline_blocked", "agent_failure"]:
            return "user_experience_blocked"
        elif error_type in ["sla_breach", "timeout"]:
            return "user_experience_delayed"
        else:
            return "user_experience_minimal"

    def _assess_system_impact(self, error: Dict[str, Any]) -> str:
        """Evaluar impacto en el sistema"""
        source = error.get("source", "")
        error_type = error.get("error_type", "")
        
        if error_type in ["system_error", "connectivity_error"]:
            return "system_wide_impact"
        elif source == ErrorSource.STATE_MANAGER:
            return "data_consistency_impact"
        else:
            return "localized_impact"

    def _calculate_confidence(self, error: Dict[str, Any], 
                             context_data: Dict[str, Any]) -> float:
        """Calcular confianza en el análisis"""
        base_confidence = 0.8
        
        # Reducir confianza si faltan datos de contexto
        if not context_data:
            base_confidence -= 0.2
        
        # Aumentar confianza para errores bien definidos
        if error.get("error_type") in ["sla_breach", "quality_failure", "agent_failure"]:
            base_confidence += 0.1
        
        return min(1.0, max(0.0, base_confidence))

    def _determine_global_severity(self, severity_analysis: Dict[str, Any]) -> ErrorSeverity:
        """Determinar severidad global del conjunto de errores"""
        if not severity_analysis:
            return ErrorSeverity.LOW
        
        severities = [analysis["final_severity"] for analysis in severity_analysis.values()]
        
        # Si hay algún error EMERGENCY o CRITICAL, la severidad global es CRITICAL
        if any(s == ErrorSeverity.EMERGENCY for s in severities):
            return ErrorSeverity.EMERGENCY
        elif any(s == ErrorSeverity.CRITICAL for s in severities):
            return ErrorSeverity.CRITICAL
        elif any(s == ErrorSeverity.HIGH for s in severities):
            return ErrorSeverity.HIGH
        elif any(s == ErrorSeverity.MEDIUM for s in severities):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    def _generate_severity_recommendations(self, severity_analysis: Dict[str, Any]) -> List[str]:
        """Generar recomendaciones basadas en análisis de severidad"""
        recommendations = []
        
        critical_count = sum(1 for analysis in severity_analysis.values() 
                           if analysis["final_severity"] in [ErrorSeverity.CRITICAL, ErrorSeverity.EMERGENCY])
        
        if critical_count > 0:
            recommendations.append("Activate immediate incident response procedures")
            recommendations.append("Notify senior management and stakeholders")
        
        high_count = sum(1 for analysis in severity_analysis.values() 
                        if analysis["final_severity"] == ErrorSeverity.HIGH)
        
        if high_count > 1:
            recommendations.append("Escalate to technical team leads")
            recommendations.append("Implement parallel recovery procedures")
        
        return recommendations

class RootCauseFinderTool(BaseTool):
    """Herramienta para encontrar causa raíz de errores"""
    name: str = "root_cause_finder_tool"
    description: str = "Analiza y determina la causa raíz de errores del sistema"

    def _run(self, detected_errors: List[Dict[str, Any]], 
             error_context: Dict[str, Any],
             historical_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Encontrar causa raíz de errores"""
        try:
            root_cause_analyses = []
            
            # Agrupar errores relacionados
            error_groups = self._group_related_errors(detected_errors)
            
            for group_id, error_group in error_groups.items():
                analysis = self._analyze_error_group(error_group, error_context, historical_data)
                analysis["group_id"] = group_id
                root_cause_analyses.append(analysis)
            
            # Análisis agregado
            aggregate_analysis = self._perform_aggregate_analysis(root_cause_analyses, error_context)
            
            return {
                "success": True,
                "root_cause_analyses": root_cause_analyses,
                "aggregate_analysis": aggregate_analysis,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "analysis_method": "pattern_based_causal_analysis"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error in root cause analysis: {str(e)}",
                "root_cause_analyses": []
            }

    def _group_related_errors(self, detected_errors: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Agrupar errores relacionados"""
        groups = {}
        
        for error in detected_errors:
            # Crear clave de grupo basada en fuente y tipo
            group_key = f"{error.get('source')}_{error.get('error_type')}"
            
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(error)
        
        return groups

    def _analyze_error_group(self, error_group: List[Dict[str, Any]], 
                            error_context: Dict[str, Any],
                            historical_data: Optional[Dict[str, Any]]) -> RootCauseAnalysis:
        """Analizar grupo de errores para encontrar causa raíz"""
        primary_error = error_group[0]  # Usar el primer error como principal
        
        # Determinar causa principal basada en patrones
        primary_cause = self._determine_primary_cause(primary_error, error_context)
        
        # Identificar factores contribuyentes
        contributing_factors = self._identify_contributing_factors(error_group, error_context)
        
        # Recopilar evidencia
        evidence = self._collect_evidence(error_group, error_context)
        
        # Calcular confianza
        confidence = self._calculate_analysis_confidence(error_group, error_context, historical_data)
        
        # Generar recomendaciones
        recommendations = self._generate_cause_recommendations(primary_cause, contributing_factors)
        
        return RootCauseAnalysis(
            primary_cause=primary_cause,
            contributing_factors=contributing_factors,
            evidence=evidence,
            confidence_level=confidence,
            analysis_method="pattern_based_analysis",
            recommendations=recommendations
        )

    def _determine_primary_cause(self, error: Dict[str, Any], 
                                context: Dict[str, Any]) -> str:
        """Determinar causa principal del error"""
        error_type = error.get("error_type", "")
        source = error.get("source", "")
        
        # Mapeo de tipos de error a causas comunes
        cause_mapping = {
            "timeout": "Processing time exceeded configured limits",
            "agent_failure": "Agent encountered unhandled exception during processing",
            "sla_breach": "Processing duration exceeded service level agreement",
            "quality_failure": "Data quality did not meet minimum requirements",
            "pipeline_blocked": "Critical dependency failure preventing continuation",
            "connectivity_error": "Network connectivity issues with external services",
            "authentication_error": "Authentication credentials invalid or expired",
            "validation_failure": "Data validation rules not satisfied"
        }
        
        base_cause = cause_mapping.get(error_type, "Unknown error condition")
        
        # Refinar causa basada en contexto específico
        if error_type == "timeout" and "processing_duration" in error.get("context", {}):
            duration = error["context"]["processing_duration"]
            base_cause = f"Processing timeout after {duration:.1f} seconds"
        
        elif error_type == "agent_failure" and error.get("context", {}).get("agent_errors"):
            agent_errors = error["context"]["agent_errors"]
            if agent_errors:
                base_cause = f"Agent failure: {agent_errors[0] if isinstance(agent_errors, list) else str(agent_errors)}"
        return base_cause

    def _identify_contributing_factors(self, error_group: List[Dict[str, Any]], 
                                     context: Dict[str, Any]) -> List[str]:
        """Identificar factores que contribuyen al error"""
        factors = []
        
        # Analizar patrones en el grupo de errores
        error_types = [error.get("error_type") for error in error_group]
        sources = [error.get("source") for error in error_group]
        
        # Factor: Múltiples errores del mismo tipo
        if len(set(error_types)) == 1 and len(error_group) > 1:
            factors.append(f"Repeated {error_types[0]} errors indicating systematic issue")
        
        # Factor: Errores en cascada
        if len(set(sources)) > 1:
            factors.append("Cross-system error propagation detected")
        
        # Factor: Carga del sistema
        system_load = context.get("system_load", 0)
        if system_load > 0.8:
            factors.append(f"High system load ({system_load:.1%}) contributing to performance issues")
        
        # Factor: Hora del día
        current_hour = datetime.utcnow().hour
        if current_hour in range(9, 17):  # Business hours
            factors.append("Peak business hours may be contributing to resource contention")
        
        # Factor: Configuración
        if any("configuration" in error.get("error_type", "") for error in error_group):
            factors.append("System configuration issues detected")
        
        # Factor: Dependencias externas
        if any(error.get("source") == "external_system" for error in error_group):
            factors.append("External system dependencies causing failures")
        
        return factors

    def _collect_evidence(self, error_group: List[Dict[str, Any]], 
                         context: Dict[str, Any]) -> List[str]:
        """Recopilar evidencia del error"""
        evidence = []
        
        for error in error_group:
            # Timestamp del error
            if "timestamp" in error:
                evidence.append(f"Error occurred at {error['timestamp']}")
            
            # Contexto específico
            error_context = error.get("context", {})
            if error_context:
                for key, value in error_context.items():
                    if key in ["agent_id", "stage", "duration", "error_count"]:
                        evidence.append(f"{key}: {value}")
            
            # Descripción del error
            if "description" in error:
                evidence.append(f"Error description: {error['description']}")
        
        # Evidencia del contexto general
        if "employee_priority" in context:
            evidence.append(f"Employee priority: {context['employee_priority']}")
        
        if "pipeline_stage" in context:
            evidence.append(f"Pipeline stage: {context['pipeline_stage']}")
        
        return evidence

    def _calculate_analysis_confidence(self, error_group: List[Dict[str, Any]], 
                                     context: Dict[str, Any],
                                     historical_data: Optional[Dict[str, Any]]) -> float:
        """Calcular confianza en el análisis"""
        base_confidence = 0.7
        
        # Mayor confianza con más evidencia
        evidence_count = sum(len(error.get("context", {})) for error in error_group)
        if evidence_count > 5:
            base_confidence += 0.1
        
        # Mayor confianza con datos históricos
        if historical_data and len(historical_data) > 0:
            base_confidence += 0.1
        
        # Mayor confianza para errores conocidos
        known_error_types = ["timeout", "sla_breach", "quality_failure", "agent_failure"]
        if all(error.get("error_type") in known_error_types for error in error_group):
            base_confidence += 0.1
        
        return min(1.0, base_confidence)

    def _generate_cause_recommendations(self, primary_cause: str, 
                                      contributing_factors: List[str]) -> List[str]:
        """Generar recomendaciones basadas en causa raíz"""
        recommendations = []
        
        # Recomendaciones basadas en causa principal
        if "timeout" in primary_cause.lower():
            recommendations.extend([
                "Increase timeout configuration for affected agents",
                "Optimize processing algorithms to reduce execution time",
                "Implement asynchronous processing for long-running tasks"
            ])
        
        elif "agent failure" in primary_cause.lower():
            recommendations.extend([
                "Implement enhanced error handling in affected agent",
                "Add input validation to prevent invalid data processing",
                "Set up automated agent restart procedures"
            ])
        
        elif "sla breach" in primary_cause.lower():
            recommendations.extend([
                "Review and adjust SLA thresholds based on historical performance",
                "Implement priority queuing for high-priority employees",
                "Optimize resource allocation during peak hours"
            ])
        
        elif "quality failure" in primary_cause.lower():
            recommendations.extend([
                "Review and adjust quality gate thresholds",
                "Implement additional data validation steps",
                "Provide training on data quality requirements"
            ])
        
        # Recomendaciones basadas en factores contribuyentes
        for factor in contributing_factors:
            if "system load" in factor.lower():
                recommendations.append("Implement load balancing and resource scaling")
            elif "business hours" in factor.lower():
                recommendations.append("Consider processing distribution across time zones")
            elif "configuration" in factor.lower():
                recommendations.append("Conduct comprehensive configuration review")
        
        return list(set(recommendations))  # Remove duplicates

    def _perform_aggregate_analysis(self, analyses: List[RootCauseAnalysis], 
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """Realizar análisis agregado de todas las causas raíz"""
        if not analyses:
            return {"summary": "No root cause analyses available"}
        
        # Analizar patrones comunes
        common_causes = {}
        all_factors = []
        all_recommendations = []
        
        for analysis in analyses:
            # Contar causas comunes
            cause_key = analysis.primary_cause[:50]  # Truncar para agrupación
            common_causes[cause_key] = common_causes.get(cause_key, 0) + 1
            
            # Recopilar factores y recomendaciones
            all_factors.extend(analysis.contributing_factors)
            all_recommendations.extend(analysis.recommendations)
        
        # Identificar la causa más común
        most_common_cause = max(common_causes.items(), key=lambda x: x[1]) if common_causes else ("Unknown", 0)
        
        # Factores más frecuentes
        factor_counts = {}
        for factor in all_factors:
            factor_counts[factor] = factor_counts.get(factor, 0) + 1
        
        top_factors = sorted(factor_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Recomendaciones prioritarias
        rec_counts = {}
        for rec in all_recommendations:
            rec_counts[rec] = rec_counts.get(rec, 0) + 1
        
        priority_recommendations = sorted(rec_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "summary": f"Analyzed {len(analyses)} error groups",
            "most_common_cause": {
                "cause": most_common_cause[0],
                "frequency": most_common_cause[1]
            },
            "top_contributing_factors": [{"factor": factor, "frequency": freq} for factor, freq in top_factors],
            "priority_recommendations": [{"recommendation": rec, "frequency": freq} for rec, freq in priority_recommendations],
            "overall_confidence": sum(analysis.confidence_level for analysis in analyses) / len(analyses),
            "systemic_issues_detected": len(common_causes) < len(analyses) / 2  # Si hay muchas causas repetidas
        }

class RoutingEngineTool(BaseTool):
    """Herramienta para enrutar errores a handlers apropiados"""
    name: str = "routing_engine_tool"
    description: str = "Determina el routing y handlers apropiados para errores clasificados"

    def _run(self, classification_results: List[Dict[str, Any]], 
             system_capabilities: Dict[str, Any]) -> Dict[str, Any]:
        """Enrutar errores a handlers apropiados"""
        try:
            routing_decisions = []
            
            for result in classification_results:
                routing_decision = self._determine_routing(result, system_capabilities)
                routing_decisions.append(routing_decision)
            
            # Consolidar decisiones de routing
            consolidated_routing = self._consolidate_routing_decisions(routing_decisions)
            
            return {
                "success": True,
                "routing_decisions": routing_decisions,
                "consolidated_routing": consolidated_routing,
                "routing_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error in routing engine: {str(e)}",
                "routing_decisions": []
            }

    def _determine_routing(self, classification_result: Dict[str, Any], 
                          system_capabilities: Dict[str, Any]) -> Dict[str, Any]:
        """Determinar routing para un error específico"""
        error_category = classification_result.get("error_category")
        error_severity = classification_result.get("severity_level")
        recovery_strategy = classification_result.get("recovery_strategy")
        
        # Determinar handler primario
        primary_handler = self._select_primary_handler(
            error_category, error_severity, recovery_strategy, system_capabilities
        )
        
        # Determinar handlers secundarios
        secondary_handlers = self._select_secondary_handlers(
            error_category, error_severity, system_capabilities
        )
        
        # Determinar escalation path
        escalation_path = self._determine_escalation_path(
            error_severity, classification_result.get("escalation_path", [])
        )
        
        # Calcular prioridad de routing
        routing_priority = self._calculate_routing_priority(error_severity, error_category)
        
        return {
            "classification_id": classification_result.get("classification_id"),
            "primary_handler": primary_handler,
            "secondary_handlers": secondary_handlers,
            "escalation_path": escalation_path,
            "routing_priority": routing_priority,
            "estimated_resolution_time": self._estimate_resolution_time(
                primary_handler, error_category, error_severity
            ),
            "routing_rationale": self._explain_routing_decision(
                primary_handler, error_category, error_severity
            )
        }

    def _select_primary_handler(self, error_category: str, error_severity: str, 
                               recovery_strategy: str, 
                               system_capabilities: Dict[str, Any]) -> Dict[str, Any]:
        """Seleccionar handler primario para el error"""
        
        # Mapeo de estrategias de recuperación a handlers
        strategy_handlers = {
            RecoveryStrategy.AUTOMATIC_RETRY: {
                "handler_type": "recovery_agent",
                "handler_id": "automatic_recovery_system",
                "capabilities": ["retry_logic", "backoff_strategies", "circuit_breaker"]
            },
            RecoveryStrategy.MANUAL_INTERVENTION: {
                "handler_type": "human_handoff_agent", 
                "handler_id": "manual_intervention_handler",
                "capabilities": ["human_notification", "context_packaging", "escalation_management"]
            },
            RecoveryStrategy.ESCALATION_REQUIRED: {
                "handler_type": "human_handoff_agent",
                "handler_id": "escalation_handler", 
                "capabilities": ["management_notification", "priority_routing", "crisis_management"]
            },
            RecoveryStrategy.SYSTEM_RESTART: {
                "handler_type": "recovery_agent",
                "handler_id": "system_recovery_handler",
                "capabilities": ["service_restart", "health_checks", "dependency_validation"]
            },
            RecoveryStrategy.HUMAN_HANDOFF: {
                "handler_type": "human_handoff_agent",
                "handler_id": "human_specialist_router",
                "capabilities": ["specialist_identification", "context_preservation", "handoff_coordination"]
            }
        }
        
        # Seleccionar handler basado en estrategia
        if recovery_strategy in strategy_handlers:
            return strategy_handlers[recovery_strategy]
        
        # Fallback basado en categoría de error
        category_handlers = {
            ErrorCategory.AGENT_FAILURE: {
                "handler_type": "recovery_agent",
                "handler_id": "agent_recovery_system",
                "capabilities": ["agent_restart", "state_recovery", "dependency_check"]
            },
            ErrorCategory.SLA_BREACH: {
                "handler_type": "human_handoff_agent", 
                "handler_id": "sla_escalation_handler",
                "capabilities": ["management_notification", "timeline_extension", "resource_escalation"]
            },
            ErrorCategory.QUALITY_FAILURE: {
                "handler_type": "recovery_agent",
                "handler_id": "quality_recovery_system", 
                "capabilities": ["data_reprocessing", "validation_retry", "manual_review_queue"]
            }
        }
        
        return category_handlers.get(error_category, {
            "handler_type": "human_handoff_agent",
            "handler_id": "general_escalation_handler",
            "capabilities": ["general_support", "triage", "routing"]
        })

    def _select_secondary_handlers(self, error_category: str, error_severity: str,
                                  system_capabilities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Seleccionar handlers secundarios"""
        secondary_handlers = []
        
        # Siempre incluir monitoring para errores críticos
        if error_severity in [ErrorSeverity.CRITICAL, ErrorSeverity.EMERGENCY]:
            secondary_handlers.append({
                "handler_type": "monitoring_system",
                "handler_id": "critical_error_monitor",
                "role": "continuous_monitoring"
            })
        
        # Incluir audit trail para todos los errores
        secondary_handlers.append({
            "handler_type": "audit_system", 
            "handler_id": "error_audit_logger",
            "role": "audit_trail"
        })
        
        # Incluir notification system para errores de alta severidad
        if error_severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL, ErrorSeverity.EMERGENCY]:
            secondary_handlers.append({
                "handler_type": "notification_system",
                "handler_id": "stakeholder_notifier", 
                "role": "stakeholder_communication"
            })
        
        return secondary_handlers

    def _determine_escalation_path(self, error_severity: str, 
                                  existing_path: List[str]) -> List[Dict[str, Any]]:
        """Determinar path de escalación"""
        escalation_path = []
        
        # Escalation basada en severidad
        if error_severity == ErrorSeverity.EMERGENCY:
            escalation_path = [
                {"level": 1, "target": "incident_commander", "timeout_minutes": 5},
                {"level": 2, "target": "cto_office", "timeout_minutes": 15},
                {"level": 3, "target": "executive_team", "timeout_minutes": 30}
            ]
        elif error_severity == ErrorSeverity.CRITICAL:
            escalation_path = [
                {"level": 1, "target": "team_lead", "timeout_minutes": 15},
                {"level": 2, "target": "department_manager", "timeout_minutes": 30},
                {"level": 3, "target": "senior_management", "timeout_minutes": 60}
            ]
        elif error_severity == ErrorSeverity.HIGH:
            escalation_path = [
                {"level": 1, "target": "senior_engineer", "timeout_minutes": 30},
                {"level": 2, "target": "team_lead", "timeout_minutes": 60}
            ]
        
        return escalation_path

    def _calculate_routing_priority(self, error_severity: str, error_category: str) -> int:
        """Calcular prioridad de routing (1=más alta, 5=más baja)"""
        severity_priority = {
            ErrorSeverity.EMERGENCY: 1,
            ErrorSeverity.CRITICAL: 1, 
            ErrorSeverity.HIGH: 2,
            ErrorSeverity.MEDIUM: 3,
            ErrorSeverity.LOW: 4
        }
        
        category_modifier = {
            ErrorCategory.SECURITY_ISSUE: -1,  # Aumenta prioridad
            ErrorCategory.SYSTEM_ERROR: -1,
            ErrorCategory.SLA_BREACH: 0,
            ErrorCategory.QUALITY_FAILURE: 1   # Disminuye prioridad
        }
        
        base_priority = severity_priority.get(error_severity, 3)
        modifier = category_modifier.get(error_category, 0)
        
        return max(1, min(5, base_priority + modifier))

    def _estimate_resolution_time(self, primary_handler: Dict[str, Any],
                                 error_category: str, error_severity: str) -> Dict[str, Any]:
        """Estimar tiempo de resolución"""
        # Tiempos base por tipo de handler (en minutos)
        handler_times = {
            "recovery_agent": {"min": 5, "max": 30, "avg": 15},
            "human_handoff_agent": {"min": 30, "max": 240, "avg": 90}
        }
        
        # Multiplicadores por severidad
        severity_multipliers = {
            ErrorSeverity.EMERGENCY: 0.5,  # Resolución más rápida
            ErrorSeverity.CRITICAL: 0.7,
            ErrorSeverity.HIGH: 1.0,
            ErrorSeverity.MEDIUM: 1.5,
            ErrorSeverity.LOW: 2.0
        }
        
        handler_type = primary_handler.get("handler_type", "human_handoff_agent")
        base_times = handler_times.get(handler_type, handler_times["human_handoff_agent"])
        multiplier = severity_multipliers.get(error_severity, 1.0)
        
        return {
            "estimated_min_minutes": int(base_times["min"] * multiplier),
            "estimated_max_minutes": int(base_times["max"] * multiplier), 
            "estimated_avg_minutes": int(base_times["avg"] * multiplier),
            "confidence": 0.7  # Confidence in estimate
        }

    def _explain_routing_decision(self, primary_handler: Dict[str, Any],
                                 error_category: str, error_severity: str) -> str:
        """Explicar la decisión de routing"""
        handler_type = primary_handler.get("handler_type", "unknown")
        
        explanations = {
            "recovery_agent": f"Automated recovery selected for {error_category} with {error_severity} severity - suitable for automatic remediation",
            "human_handoff_agent": f"Human intervention required for {error_category} with {error_severity} severity - complexity requires manual expertise"
        }
        
        return explanations.get(handler_type, 
                              f"Default routing applied for {error_category} error with {error_severity} severity")

    def _consolidate_routing_decisions(self, routing_decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Consolidar múltiples decisiones de routing"""
        if not routing_decisions:
            return {"summary": "No routing decisions to consolidate"}
        
        # Analizar distribución de handlers
        handler_distribution = {}
        priority_distribution = {}
        
        for decision in routing_decisions:
            handler_type = decision["primary_handler"].get("handler_type", "unknown")
            priority = decision["routing_priority"]
            
            handler_distribution[handler_type] = handler_distribution.get(handler_type, 0) + 1
            priority_distribution[priority] = priority_distribution.get(priority, 0) + 1
        
        # Determinar si hay conflictos de prioridad
        high_priority_count = sum(count for priority, count in priority_distribution.items() if priority <= 2)
        
        return {
            "total_routing_decisions": len(routing_decisions),
            "handler_distribution": handler_distribution,
            "priority_distribution": priority_distribution,
            "high_priority_errors": high_priority_count,
            "coordination_required": high_priority_count > 1,  # Multiple high-priority errors need coordination
            "estimated_total_resolution_time": self._calculate_total_resolution_time(routing_decisions)
        }

    def _calculate_total_resolution_time(self, routing_decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcular tiempo total de resolución estimado"""
        if not routing_decisions:
            return {"estimated_total_minutes": 0}
        
        # Para errores que pueden resolverse en paralelo vs secuencial
        parallel_times = []
        sequential_times = []
        
        for decision in routing_decisions:
            est_time = decision.get("estimated_resolution_time", {})
            avg_time = est_time.get("estimated_avg_minutes", 60)
            
            handler_type = decision["primary_handler"].get("handler_type")
            if handler_type == "recovery_agent":
                parallel_times.append(avg_time)  # Recovery agents can work in parallel
            else:
                sequential_times.append(avg_time)  # Human handlers often sequential
        
        # Calcular tiempo total
        parallel_max = max(parallel_times) if parallel_times else 0
        sequential_sum = sum(sequential_times)
        
        return {
            "estimated_total_minutes": parallel_max + sequential_sum,
            "parallel_resolution_time": parallel_max,
            "sequential_resolution_time": sequential_sum,
            "can_parallelize": len(parallel_times) > 0
        }

# Export tools
error_detector_tool = ErrorDetectorTool()
severity_analyzer_tool = SeverityAnalyzerTool() 
root_cause_finder_tool = RootCauseFinderTool()
routing_engine_tool = RoutingEngineTool()                
        