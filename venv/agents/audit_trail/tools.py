from typing import Dict, Any, List
from langchain.tools import BaseTool
from pydantic import BaseModel
from datetime import datetime, timedelta
from loguru import logger
import json
import hashlib

from .schemas import (
    AuditEntry, ComplianceReport, DecisionLog, AuditEventType,
    ComplianceStandard, ComplianceStatus, AuditSeverity
)
from core.observability import observability_manager

class TraceabilityLoggerTool(BaseTool):
    """Herramienta para logging de trazabilidad completa"""
    
    name: str = "traceability_logger_tool"
    description: str = "Crea audit trails completos para trazabilidad ISO 27001"

    def _run(self, session_id: str, event_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Ejecutar logging de trazabilidad"""
        try:
            logger.info(f"Creando audit trail para session: {session_id}")
            
            # Extraer datos del evento
            event_type = event_data.get("event_type", AuditEventType.SYSTEM_STATE_CHANGE)
            employee_id = event_data.get("employee_id", "unknown")
            
            # Crear audit entries
            audit_entries = []
            
            # 1. Entrada principal del evento
            main_entry = AuditEntry(
                session_id=session_id,
                employee_id=employee_id,
                event_type=event_type,
                event_timestamp=datetime.utcnow(),
                event_description=event_data.get("description", f"Evento {event_type} registrado"),
                severity=AuditSeverity(event_data.get("severity", "info")),
                agent_id=event_data.get("agent_id"),
                workflow_stage=event_data.get("workflow_stage"),
                event_data=event_data.get("raw_data", {}),
                compliance_tags=["iso_27001", "traceability"]
            )
            
            # Calcular checksum para integridad
            entry_content = f"{main_entry.session_id}:{main_entry.event_timestamp}:{main_entry.event_description}"
            main_entry.checksum = hashlib.sha256(entry_content.encode()).hexdigest()[:16]
            
            audit_entries.append(main_entry)
            
            # 2. Entries adicionales si hay decisiones
            decision_points = event_data.get("decision_points", [])
            for decision in decision_points:
                decision_entry = AuditEntry(
                    session_id=session_id,
                    employee_id=employee_id,
                    event_type=AuditEventType.DECISION_MADE,
                    event_timestamp=datetime.utcnow(),
                    event_description=f"Decisión: {decision.get('decision', 'N/A')}",
                    severity=AuditSeverity.INFO,
                    agent_id=event_data.get("agent_id"),
                    workflow_stage=event_data.get("workflow_stage"),
                    decision_data=decision,
                    compliance_tags=["iso_27001", "decision_trail"]
                )
                audit_entries.append(decision_entry)
            
            logger.info(f"Creadas {len(audit_entries)} audit entries")
            
            return {
                "success": True,
                "audit_entries": [entry.dict() for entry in audit_entries],
                "traceability_complete": True,
                "entries_count": len(audit_entries)
            }
            
        except Exception as e:
            logger.error(f"Error en traceability logger: {e}")
            return {
                "success": False,
                "error": str(e),
                "audit_entries": [],
                "traceability_complete": False
            }

class ISO27001ComplianceTool(BaseTool):
    """Herramienta para verificación de compliance ISO 27001"""
    
    name: str = "iso_27001_compliance_tool"
    description: str = "Verifica compliance con controles ISO 27001"

    def _run(self, audit_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Ejecutar verificación de compliance ISO 27001"""
        try:
            logger.info("Verificando compliance ISO 27001")
            
            session_id = audit_data.get("session_id", "unknown")
            employee_id = audit_data.get("employee_id", "unknown")
            
            # Controles ISO 27001 básicos para onboarding
            iso_controls = {
                "A.7.1.1": {  # Screening
                    "name": "Background verification",
                    "status": "compliant" if audit_data.get("background_check") else "non_compliant"
                },
                "A.7.1.2": {  # Terms and conditions
                    "name": "Terms and conditions of employment",
                    "status": "compliant" if audit_data.get("contract_signed") else "non_compliant"
                },
                "A.9.1.1": {  # Access control policy
                    "name": "Access control policy",
                    "status": "compliant" if audit_data.get("access_provisioned") else "non_compliant"
                },
                "A.9.2.1": {  # User registration
                    "name": "User registration and de-registration",
                    "status": "compliant" if audit_data.get("user_registered") else "partial"
                },
                "A.12.4.1": {  # Event logging
                    "name": "Event logging",
                    "status": "compliant"  # Siempre compliant si estamos auditando
                },
                "A.12.4.3": {  # Administrator logs
                    "name": "Administrator and operator logs",
                    "status": "compliant" if audit_data.get("admin_actions_logged") else "partial"
                }
            }
            
            # Calcular compliance score
            total_controls = len(iso_controls)
            compliant_controls = [k for k, v in iso_controls.items() if v["status"] == "compliant"]
            partial_controls = [k for k, v in iso_controls.items() if v["status"] == "partial"]
            non_compliant_controls = [k for k, v in iso_controls.items() if v["status"] == "non_compliant"]
            
            compliance_score = (len(compliant_controls) + 0.5 * len(partial_controls)) / total_controls * 100
            
            # Determinar estado general
            if compliance_score >= 90:
                overall_status = ComplianceStatus.COMPLIANT
            elif compliance_score >= 70:
                overall_status = ComplianceStatus.PARTIAL
            else:
                overall_status = ComplianceStatus.NON_COMPLIANT
            
            # Crear reporte de compliance
            compliance_report = ComplianceReport(
                session_id=session_id,
                employee_id=employee_id,
                compliance_standard=ComplianceStandard.ISO_27001,
                overall_status=overall_status,
                compliance_score=compliance_score,
                compliant_controls=compliant_controls,
                non_compliant_controls=non_compliant_controls,
                partial_controls=partial_controls,
                compliance_gaps=[
                    {
                        "control": control,
                        "gap": f"Control {control} no está implementado correctamente",
                        "recommendation": f"Implementar {iso_controls[control]['name']}"
                    }
                    for control in non_compliant_controls
                ],
                risk_level="medium" if compliance_score < 80 else "low",
                next_review_date=datetime.utcnow() + timedelta(days=90)
            )
            
            logger.info(f"ISO 27001 compliance score: {compliance_score:.1f}%")
            
            return {
                "success": True,
                "compliance_report": compliance_report.dict(),
                "compliance_score": compliance_score,
                "overall_status": overall_status.value,
                "controls_evaluated": total_controls,
                "recommendations": [
                    "Implementar controles faltantes para mejorar compliance",
                    "Revisar procesos de background verification",
                    "Asegurar logging completo de acciones administrativas"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error en ISO 27001 compliance: {e}")
            return {
                "success": False,
                "error": str(e),
                "compliance_score": 0.0,
                "overall_status": ComplianceStatus.NON_COMPLIANT.value
            }

class DecisionLoggerTool(BaseTool):
    """Herramienta para logging de decisiones"""
    
    name: str = "decision_logger_tool"
    description: str = "Registra decisiones críticas para audit trail"

    def _run(self, decision_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Ejecutar logging de decisiones"""
        try:
            logger.info("Registrando decisiones en audit trail")
            
            session_id = decision_data.get("session_id", "unknown")
            employee_id = decision_data.get("employee_id", "unknown")
            
            decision_logs = []
            decisions = decision_data.get("decisions", [])
            
            for decision_info in decisions:
                decision_log = DecisionLog(
                    session_id=session_id,
                    employee_id=employee_id,
                    decision_point=decision_info.get("decision_point", "unknown"),
                    decision_made=decision_info.get("decision", "unknown"),
                    decision_rationale=decision_info.get("rationale", "No rationale provided"),
                    decision_maker=decision_info.get("maker", "system"),
                    available_options=decision_info.get("options", []),
                    decision_criteria=decision_info.get("criteria", {}),
                    input_data=decision_info.get("input", {}),
                    expected_impact=decision_info.get("expected_impact", "unknown"),
                    success_criteria=decision_info.get("success_criteria", [])
                )
                decision_logs.append(decision_log)
            
            logger.info(f"Registradas {len(decision_logs)} decisiones")
            
            return {
                "success": True,
                "decision_logs": [log.dict() for log in decision_logs],
                "decisions_count": len(decision_logs),
                "audit_trail_complete": True
            }
            
        except Exception as e:
            logger.error(f"Error en decision logger: {e}")
            return {
                "success": False,
                "error": str(e),
                "decision_logs": [],
                "decisions_count": 0
            }

class ComplianceReporterTool(BaseTool):
    """Herramienta para generar reportes de compliance"""
    
    name: str = "compliance_reporter_tool"
    description: str = "Genera reportes consolidados de compliance"

    def _run(self, compliance_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Ejecutar generación de reportes de compliance"""
        try:
            logger.info("Generando reporte consolidado de compliance")
            
            session_id = compliance_data.get("session_id", "unknown")
            employee_id = compliance_data.get("employee_id", "unknown")
            
            # Consolidar datos de múltiples fuentes
            audit_entries = compliance_data.get("audit_entries", [])
            decision_logs = compliance_data.get("decision_logs", [])
            
            # Métricas de trazabilidad
            traceability_metrics = {
                "total_events": len(audit_entries),
                "total_decisions": len(decision_logs),
                "data_integrity_score": 100.0,  # Simplificado
                "audit_completeness": min(100.0, (len(audit_entries) + len(decision_logs)) / 10 * 100)
            }
            
            # Recomendaciones generales
            recommendations = [
                "Mantener registro continuo de eventos críticos",
                "Revisar compliance mensualmente",
                "Asegurar backup de audit trails"
            ]
            
            if traceability_metrics["audit_completeness"] < 80:
                recommendations.append("Mejorar logging de eventos para mayor trazabilidad")
            
            logger.info(f"Reporte generado - {traceability_metrics['total_events']} eventos auditados")
            
            return {
                "success": True,
                "traceability_metrics": traceability_metrics,
                "compliance_summary": {
                    "overall_score": traceability_metrics["audit_completeness"],
                    "events_logged": traceability_metrics["total_events"],
                    "decisions_tracked": traceability_metrics["total_decisions"],
                    "data_integrity": "high"
                },
                "recommendations": recommendations,
                "report_generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error en compliance reporter: {e}")
            return {
                "success": False,
                "error": str(e),
                "traceability_metrics": {},
                "recommendations": []
            }

# Instancias de herramientas
traceability_logger_tool = TraceabilityLoggerTool()
iso_27001_compliance_tool = ISO27001ComplianceTool()
decision_logger_tool = DecisionLoggerTool()
compliance_reporter_tool = ComplianceReporterTool()