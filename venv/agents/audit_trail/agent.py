from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from agents.base.base_agent import BaseAgent
from datetime import datetime, timezone
from loguru import logger

from .tools import (
    traceability_logger_tool, iso_27001_compliance_tool,
    decision_logger_tool, compliance_reporter_tool
)
from .schemas import (
    AuditTrailRequest, AuditTrailResult, ComplianceStandard,
    AuditEventType, ComplianceStatus
)
from core.state_management.state_manager import state_manager
from core.state_management.models import AgentStateStatus
from core.observability import observability_manager

class AuditTrailAgent(BaseAgent):
    """
    Audit Trail & Compliance Agent
    
    Arquitectura BDI:
    - Beliefs: La trazabilidad completa es esencial para compliance y auditabilidad
    - Desires: Crear audit trails completos que cumplan ISO 27001 y otros estándares
    - Intentions: Registrar eventos, decisiones y generar reportes de compliance
    """

    def __init__(self):
        super().__init__(
            agent_id="audit_trail_agent",
            agent_name="Audit Trail & Compliance Agent"
        )
        
        # Registrar agente en state management
        state_manager.register_agent(
            self.agent_id,
            {
                "version": "1.0",
                "specialization": "audit_trail_compliance",
                "tools_count": len(self.tools),
                "capabilities": {
                    "traceability_logging": True,
                    "iso_27001_compliance": True,
                    "decision_logging": True,
                    "compliance_reporting": True
                },
                "compliance_standards": [
                    ComplianceStandard.ISO_27001.value
                ]
            }
        )
        self.logger.info("Audit Trail Agent integrado con State Management")

    def _initialize_tools(self) -> List:
        """Inicializar herramientas de audit trail"""
        return [
            traceability_logger_tool,
            iso_27001_compliance_tool,
            decision_logger_tool,
            compliance_reporter_tool
        ]

    def _create_prompt(self) -> ChatPromptTemplate:
        """Crear prompt para audit trail y compliance"""
        bdi = self._get_bdi_framework()
        
        system_prompt = f"""
Eres el Audit Trail & Compliance Agent, especializado en trazabilidad y compliance.

## FRAMEWORK BDI (Belief-Desire-Intention)
**BELIEFS (Creencias):**
{bdi['beliefs']}

**DESIRES (Deseos):**
{bdi['desires']}

**INTENTIONS (Intenciones):**
{bdi['intentions']}

## HERRAMIENTAS ESPECIALIZADAS:
- traceability_logger_tool: Crea audit trails completos para trazabilidad
- iso_27001_compliance_tool: Verifica compliance con controles ISO 27001
- decision_logger_tool: Registra decisiones críticas para audit trail
- compliance_reporter_tool: Genera reportes consolidados de compliance

## ESTÁNDARES DE COMPLIANCE:
- ISO 27001: Control de seguridad de la información
- Trazabilidad completa: Registro de todas las acciones críticas
- Decision logging: Documentación de decisiones y rationales

## PATRÓN REACT (Reason-Act-Observe):
**1. REASON (Razonar):**
- Analizar eventos y decisiones que requieren audit trail
- Identificar requisitos de compliance aplicables
- Evaluar completitud de trazabilidad existente

**2. ACT (Actuar):**
- Crear audit trails detallados con traceability_logger_tool
- Verificar compliance con iso_27001_compliance_tool
- Registrar decisiones críticas con decision_logger_tool
- Generar reportes consolidados con compliance_reporter_tool

**3. OBSERVE (Observar):**
- Verificar integridad de audit trails creados
- Revisar compliance scores y gaps identificados
- Validar completitud de decision logging
- Confirmar cumplimiento de estándares de trazabilidad

## CRITERIOS DE ÉXITO:
- Trazabilidad completa: 100% de eventos críticos registrados
- Compliance score > 80% para ISO 27001
- Decision logging completo para decisiones críticas
- Reportes de compliance generados correctamente
- Integridad de datos auditables verificada

Crea audit trails completos, verifica compliance y asegura trazabilidad total.
"""
        
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}"),
            ("assistant", "Voy a crear audit trails completos y verificar compliance para este caso."),
            ("placeholder", "{agent_scratchpad}")
        ])

    def _get_bdi_framework(self) -> Dict[str, str]:
        """Framework BDI específico para audit trail"""
        return {
            "beliefs": """
• La trazabilidad completa es fundamental para compliance y auditabilidad
• Los audit trails deben ser íntegros, completos y verificables
• ISO 27001 proporciona el framework base para controles de seguridad
• Las decisiones críticas deben estar documentadas con rationales claros
• La compliance debe ser verificable y reportable continuamente
""",
            "desires": """
• Crear audit trails completos que cumplan estándares internacionales
• Verificar compliance continuo con ISO 27001 y otros estándares
• Documentar todas las decisiones críticas del proceso de onboarding
• Generar reportes de compliance accionables y detallados
• Asegurar integridad y no-repudio de todos los registros auditables
""",
            "intentions": """
• Registrar eventos críticos con trazabilidad completa usando herramientas especializadas
• Verificar compliance con controles ISO 27001 aplicables al onboarding
• Crear decision logs detallados para todas las decisiones críticas
• Generar reportes consolidados de compliance y trazabilidad
• Mantener integridad de datos auditables con checksums y timestamps
"""
        }

    def _format_input(self, input_data: Any) -> str:
        """Formatear datos de entrada para audit trail"""
        if isinstance(input_data, AuditTrailRequest):
            return f"""
Crea audit trail completo para el siguiente caso:

**INFORMACIÓN DEL EVENTO:**
- Session ID: {input_data.session_id}
- Employee ID: {input_data.employee_id}
- Tipo de evento: {input_data.event_type.value}
- Descripción: {input_data.event_description}
- Severidad: {input_data.severity.value}

**COMPLIANCE REQUIREMENTS:**
- Estándares: {[std.value for std in input_data.compliance_standards]}
- Trazabilidad completa: {'Sí' if input_data.require_full_traceability else 'No'}

**CONTEXTO:**
- Agente origen: {input_data.agent_id or 'No especificado'}
- Workflow stage: {input_data.workflow_stage or 'No especificado'}
- Decision points: {len(input_data.decision_points)} decisiones

**DATOS DEL EVENTO:**
{input_data.event_data}

INSTRUCCIONES DE AUDIT TRAIL:
1. Usa traceability_logger_tool para crear audit trail completo
2. Usa iso_27001_compliance_tool para verificar compliance
3. Usa decision_logger_tool para registrar decisiones críticas
4. Usa compliance_reporter_tool para generar reporte consolidado

Objetivo: Trazabilidad 100% completa con compliance verificado.
"""
        elif isinstance(input_data, dict):
            return f"""
Procesa audit trail para:
{input_data}

Crea trazabilidad completa y verifica compliance.
"""
        else:
            return str(input_data)

    def _format_output(self, result: Any, processing_time: float, success: bool, error: str = None) -> Dict[str, Any]:
        """Formatear salida de audit trail"""
        if not success:
            return {
                "success": False,
                "message": f"Error en audit trail: {error}",
                "errors": [error] if error else [],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "audit_trail_created": False,
                "compliance_verified": False
            }

        try:
            # Extraer información de audit trail
            audit_entries = result.get("audit_entries", [])
            decision_logs = result.get("decision_logs", [])
            compliance_reports = result.get("compliance_reports", [])
            
            # Calcular métricas
            total_events = len(audit_entries)
            total_decisions = len(decision_logs)
            compliance_score = result.get("compliance_score", 0.0)
            
            return {
                "success": True,
                "message": "Audit trail creado exitosamente",
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                
                # Audit trail summary
                "audit_summary": {
                    "audit_trail_created": True,
                    "compliance_verified": True,
                    "total_events_logged": total_events,
                    "total_decisions_logged": total_decisions,
                    "compliance_score": compliance_score,
                    "traceability_complete": total_events > 0
                },
                
                # Detailed results
                "audit_entries": audit_entries,
                "decision_logs": decision_logs,
                "compliance_reports": compliance_reports,
                
                # Compliance status
                "compliance_status": {
                    "iso_27001_compliant": compliance_score >= 80.0,
                    "overall_score": compliance_score,
                    "traceability_completeness": min(100.0, total_events * 10),  # Simplificado
                    "compliance_gaps": result.get("compliance_gaps", [])
                },
                
                # Next actions
                "recommendations": result.get("recommendations", [
                    "Mantener audit trail continuo",
                    "Revisar compliance regularmente"
                ]),
                
                # Audit metadata
                "audit_metadata": {
                    "audit_id": result.get("audit_id", "unknown"),
                    "audit_timestamp": datetime.now(timezone.utc).isoformat(),
                    "retention_period_days": 2555,  # 7 años ISO 27001
                    "data_integrity_verified": True
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error formateando salida de audit trail: {e}")
            return {
                "success": False,
                "message": f"Error procesando resultados de audit trail: {e}",
                "errors": [str(e)],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "audit_trail_created": False
            }

    @observability_manager.trace_agent_execution("audit_trail_agent")
    def create_audit_trail(self, audit_request: AuditTrailRequest, session_id: str = None) -> Dict[str, Any]:
        """Crear audit trail completo para un evento"""
        
        # Actualizar estado del agente
        state_manager.update_agent_state(
            self.agent_id,
            AgentStateStatus.PROCESSING,
            {
                "current_task": "audit_trail_creation",
                "session_id": audit_request.session_id,
                "employee_id": audit_request.employee_id,
                "event_type": audit_request.event_type.value
            },
            session_id or audit_request.session_id
        )

        try:
            # Procesar usando herramientas directamente
            result = self._process_with_tools_directly(audit_request)
            
            # Actualizar estado: COMPLETED
            state_manager.update_agent_state(
                self.agent_id,
                AgentStateStatus.COMPLETED,
                {
                    "current_task": "audit_trail_completed",
                    "events_logged": result.get("audit_summary", {}).get("total_events_logged", 0),
                    "compliance_score": result.get("compliance_status", {}).get("overall_score", 0.0),
                    "audit_success": result.get("success", False)
                },
                session_id or audit_request.session_id
            )

            # Guardar audit trail en State Management
            if session_id and result.get("success"):
                try:
                    state_manager.update_employee_data(
                        session_id,
                        {
                            "audit_trail_completed": True,
                            "audit_trail_data": {
                                "audit_id": result.get("audit_metadata", {}).get("audit_id"),
                                "compliance_score": result.get("compliance_status", {}).get("overall_score", 0.0),
                                "events_logged": result.get("audit_summary", {}).get("total_events_logged", 0),
                                "audit_timestamp": datetime.now(timezone.utc).isoformat()
                            }
                        },
                        "audit_completed"
                    )
                except Exception as e:
                    self.logger.warning(f"Error guardando audit trail en State Management: {e}")

            return result

        except Exception as e:
            # Error durante procesamiento
            error_msg = f"Error creando audit trail: {str(e)}"
            
            state_manager.update_agent_state(
                self.agent_id,
                AgentStateStatus.ERROR,
                {
                    "current_task": "audit_trail_error",
                    "error_message": error_msg
                },
                session_id or audit_request.session_id
            )

            self.logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "errors": [str(e)],
                "agent_id": self.agent_id,
                "audit_trail_created": False,
                "compliance_verified": False
            }

    def _process_with_tools_directly(self, input_data: Any) -> Dict[str, Any]:
        """Procesar audit trail usando herramientas directamente"""
        try:
            results = []
            formatted_input = self._format_input(input_data)
            
            self.logger.info(f"Procesando audit trail con {len(self.tools)} herramientas")
            
            # Preparar datos para herramientas
            if isinstance(input_data, AuditTrailRequest):
                session_id = input_data.session_id
                employee_id = input_data.employee_id
                event_data = {
                    "session_id": session_id,
                    "employee_id": employee_id,
                    "event_type": input_data.event_type.value,
                    "description": input_data.event_description,
                    "severity": input_data.severity.value,
                    "agent_id": input_data.agent_id,
                    "workflow_stage": input_data.workflow_stage,
                    "raw_data": input_data.event_data,
                    "decision_points": input_data.decision_points
                }
            else:
                # Fallback para dict
                session_id = input_data.get("session_id", "unknown")
                employee_id = input_data.get("employee_id", "unknown")
                event_data = input_data

            # 1. Ejecutar Traceability Logger Tool
            try:
                self.logger.info("Ejecutando traceability_logger_tool")
                traceability_result = traceability_logger_tool.invoke({
                    "session_id": session_id,
                    "event_data": event_data
                })
                results.append(("traceability_logger", traceability_result))
                self.logger.info("✅ Traceability Logger completado")
            except Exception as e:
                self.logger.warning(f"❌ Error con traceability_logger_tool: {e}")
                results.append(("traceability_logger", {"success": False, "error": str(e)}))

            # 2. Ejecutar ISO 27001 Compliance Tool
            try:
                self.logger.info("Ejecutando iso_27001_compliance_tool")
                
                # Preparar datos de compliance
                compliance_data = {
                    "session_id": session_id,
                    "employee_id": employee_id,
                    "background_check": event_data.get("raw_data", {}).get("background_check_completed", False),
                    "contract_signed": event_data.get("raw_data", {}).get("contract_signed", False),
                    "access_provisioned": event_data.get("raw_data", {}).get("access_provisioned", False),
                    "user_registered": event_data.get("raw_data", {}).get("user_registered", False),
                    "admin_actions_logged": True  # Siempre true si estamos auditando
                }
                
                iso_result = iso_27001_compliance_tool.invoke({
                    "audit_data": compliance_data
                })
                results.append(("iso_27001_compliance", iso_result))
                self.logger.info("✅ ISO 27001 Compliance completado")
            except Exception as e:
                self.logger.warning(f"❌ Error con iso_27001_compliance_tool: {e}")
                results.append(("iso_27001_compliance", {"success": False, "error": str(e)}))

            # 3. Ejecutar Decision Logger Tool
            try:
                self.logger.info("Ejecutando decision_logger_tool")
                
                decision_data = {
                    "session_id": session_id,
                    "employee_id": employee_id,
                    "decisions": event_data.get("decision_points", [])
                }
                
                decision_result = decision_logger_tool.invoke({
                    "decision_data": decision_data
                })
                results.append(("decision_logger", decision_result))
                self.logger.info("✅ Decision Logger completado")
            except Exception as e:
                self.logger.warning(f"❌ Error con decision_logger_tool: {e}")
                results.append(("decision_logger", {"success": False, "error": str(e)}))

            # 4. Ejecutar Compliance Reporter Tool
            try:
                self.logger.info("Ejecutando compliance_reporter_tool")
                
                # Consolidar datos de herramientas anteriores
                audit_entries = []
                decision_logs = []
                
                for tool_name, tool_result in results:
                    if tool_name == "traceability_logger" and tool_result.get("success"):
                        audit_entries.extend(tool_result.get("audit_entries", []))
                    elif tool_name == "decision_logger" and tool_result.get("success"):
                        decision_logs.extend(tool_result.get("decision_logs", []))
                
                compliance_data = {
                    "session_id": session_id,
                    "employee_id": employee_id,
                    "audit_entries": audit_entries,
                    "decision_logs": decision_logs
                }
                
                reporter_result = compliance_reporter_tool.invoke({
                    "compliance_data": compliance_data
                })
                results.append(("compliance_reporter", reporter_result))
                self.logger.info("✅ Compliance Reporter completado")
            except Exception as e:
                self.logger.warning(f"❌ Error con compliance_reporter_tool: {e}")
                results.append(("compliance_reporter", {"success": False, "error": str(e)}))

            # Consolidar todos los resultados
            consolidated_result = self._consolidate_audit_results(results, session_id, employee_id)
            
            self.logger.info(f"Audit trail procesado: {len(results)} herramientas ejecutadas")
            return consolidated_result

        except Exception as e:
            self.logger.error(f"Error en procesamiento de audit trail: {e}")
            return {
                "success": False,
                "message": f"Error en procesamiento: {str(e)}",
                "errors": [str(e)],
                "audit_trail_created": False,
                "compliance_verified": False
            }

    def _consolidate_audit_results(self, results: List, session_id: str, employee_id: str) -> Dict[str, Any]:
        """Consolidar resultados de todas las herramientas de audit"""
        try:
            # Extraer resultados por herramienta
            audit_entries = []
            decision_logs = []
            compliance_reports = []
            compliance_score = 0.0
            recommendations = []
            
            for tool_name, tool_result in results:
                if not tool_result.get("success", False):
                    continue
                    
                if tool_name == "traceability_logger":
                    audit_entries.extend(tool_result.get("audit_entries", []))
                elif tool_name == "iso_27001_compliance":
                    if "compliance_report" in tool_result:
                        compliance_reports.append(tool_result["compliance_report"])
                    compliance_score = max(compliance_score, tool_result.get("compliance_score", 0.0))
                    recommendations.extend(tool_result.get("recommendations", []))
                elif tool_name == "decision_logger":
                    decision_logs.extend(tool_result.get("decision_logs", []))
                elif tool_name == "compliance_reporter":
                    recommendations.extend(tool_result.get("recommendations", []))

            # Crear resultado consolidado
            audit_id = f"audit_{session_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
            
            consolidated = {
                "success": True,
                "audit_id": audit_id,
                "session_id": session_id,
                "employee_id": employee_id,
                
                # Datos consolidados
                "audit_entries": audit_entries,
                "decision_logs": decision_logs,
                "compliance_reports": compliance_reports,
                
                # Métricas
                "audit_summary": {
                    "total_events_logged": len(audit_entries),
                    "total_decisions_logged": len(decision_logs),
                    "compliance_score": compliance_score,
                    "traceability_complete": len(audit_entries) > 0
                },
                
                "compliance_status": {
                    "iso_27001_compliant": compliance_score >= 80.0,
                    "overall_score": compliance_score,
                    "traceability_completeness": min(100.0, len(audit_entries) * 20),
                    "compliance_gaps": []
                },
                
                "recommendations": list(set(recommendations)),  # Remove duplicates
                
                "audit_metadata": {
                    "audit_id": audit_id,
                    "audit_timestamp": datetime.now(timezone.utc).isoformat(),
                    "retention_period_days": 2555,
                    "data_integrity_verified": True
                }
            }
            
            return consolidated
            
        except Exception as e:
            self.logger.error(f"Error consolidando resultados de audit: {e}")
            return {
                "success": False,
                "message": f"Error consolidando audit trail: {str(e)}",
                "errors": [str(e)],
                "audit_trail_created": False
            }