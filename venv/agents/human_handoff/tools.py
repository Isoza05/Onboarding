from typing import Dict, Any, List, Optional
from langchain.tools import BaseTool
from datetime import datetime, timedelta
import json
from .schemas import (
    EscalationLevel, HandoffStatus, SpecialistType, NotificationChannel,
    EscalationDepartment, SpecialistAssignment, ContextPackage, 
    EscalationTicket, NotificationEvent
)

class EscalationRouterTool(BaseTool):
    """Herramienta para determinar especialista apropiado"""
    name: str = "escalation_router_tool"
    description: str = "Determina el especialista apropiado basado en tipo de error y contexto"

    def _run(self, error_classification: Dict[str, Any], 
             escalation_level: str, session_id: str) -> Dict[str, Any]:
        """Enrutar escalación al especialista apropiado"""
        try:
            from core.state_management.state_manager import state_manager
            
            # Obtener contexto del empleado
            employee_context = state_manager.get_employee_context(session_id)
            employee_id = employee_context.employee_id if employee_context else "unknown"
            
            # Mapeo de categorías de error a especialistas
            routing_matrix = {
                "agent_failure": {
                    "timeout": [SpecialistType.IT_SPECIALIST, SpecialistType.SYSTEM_ADMIN],
                    "processing_error": [SpecialistType.IT_SPECIALIST, SpecialistType.SYSTEM_ADMIN],
                    "resource_exhaustion": [SpecialistType.SYSTEM_ADMIN, SpecialistType.IT_SPECIALIST]
                },
                "sla_breach": {
                    "critical": [SpecialistType.DEPARTMENT_MANAGER, SpecialistType.IT_SPECIALIST],
                    "performance": [SpecialistType.IT_SPECIALIST, SpecialistType.SYSTEM_ADMIN]
                },
                "quality_failure": {
                    "validation_failure": [SpecialistType.HR_MANAGER, SpecialistType.COMPLIANCE_OFFICER],
                    "completeness_issue": [SpecialistType.HR_MANAGER],
                    "compliance": [SpecialistType.COMPLIANCE_OFFICER, SpecialistType.LEGAL_COUNSEL]
                },
                "security_issue": {
                    "authentication_error": [SpecialistType.SECURITY_ANALYST, SpecialistType.IT_SPECIALIST],
                    "data_breach": [SpecialistType.CISO, SpecialistType.SECURITY_ANALYST],
                    "unauthorized_access": [SpecialistType.SECURITY_ANALYST, SpecialistType.CISO]
                },
                "system_error": {
                    "connectivity_error": [SpecialistType.SYSTEM_ADMIN, SpecialistType.IT_SPECIALIST],
                    "configuration_error": [SpecialistType.IT_SPECIALIST, SpecialistType.SYSTEM_ADMIN]
                },
                "business_rule_violation": {
                    "compliance": [SpecialistType.COMPLIANCE_OFFICER, SpecialistType.HR_MANAGER],
                    "policy": [SpecialistType.HR_MANAGER, SpecialistType.LEGAL_COUNSEL]
                }
            }
            
            # Extraer información del error
            error_category = error_classification.get("error_category", "system_error")
            error_type = error_classification.get("error_type", "unknown")
            severity = error_classification.get("severity_level", "medium")
            
            # Determinar especialistas apropiados
            specialists = []
            if error_category in routing_matrix:
                if error_type in routing_matrix[error_category]:
                    specialists = routing_matrix[error_category][error_type]
                else:
                    # Fallback: usar el primer tipo disponible para la categoría
                    specialists = list(routing_matrix[error_category].values())[0]
            
            # Fallback si no se encuentran especialistas
            if not specialists:
                if severity in ["emergency", "critical"]:
                    specialists = [SpecialistType.SYSTEM_ADMIN, SpecialistType.DEPARTMENT_MANAGER]
                else:
                    specialists = [SpecialistType.IT_SPECIALIST]
            
            # Determinar departamento principal
            department_mapping = {
                SpecialistType.IT_SPECIALIST: EscalationDepartment.IT_DEPARTMENT,
                SpecialistType.SYSTEM_ADMIN: EscalationDepartment.IT_DEPARTMENT,
                SpecialistType.HR_MANAGER: EscalationDepartment.HR_DEPARTMENT,
                SpecialistType.LEGAL_COUNSEL: EscalationDepartment.LEGAL_DEPARTMENT,
                SpecialistType.SECURITY_ANALYST: EscalationDepartment.SECURITY_DEPARTMENT,
                SpecialistType.CISO: EscalationDepartment.SECURITY_DEPARTMENT,
                SpecialistType.COMPLIANCE_OFFICER: EscalationDepartment.COMPLIANCE_DEPARTMENT,
                SpecialistType.DEPARTMENT_MANAGER: EscalationDepartment.MANAGEMENT,
                SpecialistType.EXECUTIVE: EscalationDepartment.EXECUTIVE_OFFICE
            }
            
            primary_department = department_mapping.get(specialists[0], EscalationDepartment.IT_DEPARTMENT)
            
            # Calcular SLA deadline
            sla_minutes = self._get_sla_minutes(escalation_level)
            sla_deadline = datetime.utcnow() + timedelta(minutes=sla_minutes)
            
            # Crear asignaciones de especialistas
            assignments = []
            specialist_directory = self._get_specialist_directory()
            
            for i, specialist_type in enumerate(specialists[:2]):  # Máximo 2 especialistas
                specialist_info = self._get_available_specialist(specialist_type, specialist_directory)
                
                assignment = SpecialistAssignment(
                    specialist_type=specialist_type,
                    department=department_mapping.get(specialist_type, EscalationDepartment.IT_DEPARTMENT),
                    specialist_name=specialist_info["name"],
                    specialist_contact=specialist_info["contact"],
                    backup_specialist=specialist_info.get("backup"),
                    estimated_response_time=sla_minutes,
                    sla_deadline=sla_deadline,
                    assignment_reason=f"Primary specialist for {error_category} - {error_type}"
                )
                assignments.append(assignment)
            
            return {
                "success": True,
                "employee_id": employee_id,
                "session_id": session_id,
                "routing_result": {
                    "primary_department": primary_department.value,
                    "specialist_assignments": [assignment.dict() for assignment in assignments],
                    "escalation_level": escalation_level,
                    "sla_deadline": sla_deadline.isoformat(),
                    "routing_rationale": f"Error category '{error_category}' with type '{error_type}' routed to {primary_department.value}",
                    "estimated_response_minutes": sla_minutes
                },
                "routing_metadata": {
                    "error_category": error_category,
                    "error_type": error_type,
                    "severity": severity,
                    "specialists_available": len(assignments),
                    "routing_timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error in escalation routing: {str(e)}",
                "session_id": session_id,
                "routing_result": None
            }
    
    def _get_sla_minutes(self, escalation_level: str) -> int:
        """Obtener minutos SLA según nivel de escalación"""
        sla_mapping = {
            "emergency": 5,
            "critical": 15,
            "high": 60,
            "medium": 240,  # 4 hours
            "low": 1440     # 24 hours
        }
        return sla_mapping.get(escalation_level, 240)
    
    def _get_specialist_directory(self) -> Dict[str, List[Dict[str, str]]]:
        """Obtener directorio de especialistas (simulado)"""
        return {
            "it_specialist": [
                {"name": "Carlos IT Manager", "contact": "carlos.it@empresa.com", "backup": "ana.systems@empresa.com"},
                {"name": "Ana Systems Admin", "contact": "ana.systems@empresa.com", "backup": "carlos.it@empresa.com"}
            ],
            "hr_manager": [
                {"name": "María HR Director", "contact": "maria.hr@empresa.com", "backup": "luis.hr@empresa.com"},
                {"name": "Luis HR Manager", "contact": "luis.hr@empresa.com", "backup": "maria.hr@empresa.com"}
            ],
            "legal_counsel": [
                {"name": "Dr. Roberto Legal", "contact": "roberto.legal@empresa.com", "backup": "sofia.compliance@empresa.com"}
            ],
            "security_analyst": [
                {"name": "Sofia Security", "contact": "sofia.security@empresa.com", "backup": "ricardo.ciso@empresa.com"}
            ],
            "ciso": [
                {"name": "Ricardo CISO", "contact": "ricardo.ciso@empresa.com", "backup": "sofia.security@empresa.com"}
            ],
            "compliance_officer": [
                {"name": "Patricia Compliance", "contact": "patricia.compliance@empresa.com", "backup": "roberto.legal@empresa.com"}
            ],
            "department_manager": [
                {"name": "Director General", "contact": "director@empresa.com", "backup": "subdirector@empresa.com"}
            ],
            "system_admin": [
                {"name": "Ana Systems Admin", "contact": "ana.systems@empresa.com", "backup": "carlos.it@empresa.com"}
            ],
            "executive": [
                {"name": "CEO Ejecutivo", "contact": "ceo@empresa.com", "backup": "cto@empresa.com"}
            ]
        }
    
    def _get_available_specialist(self, specialist_type: SpecialistType, directory: Dict) -> Dict[str, str]:
        """Obtener especialista disponible"""
        specialists = directory.get(specialist_type.value, [])
        if specialists:
            # Simular selección del primer disponible
            return specialists[0]
        else:
            # Fallback genérico
            return {
                "name": f"Default {specialist_type.value.replace('_', ' ').title()}",
                "contact": f"{specialist_type.value}@empresa.com",
                "backup": "admin@empresa.com"
            }

class ContextPackagerTool(BaseTool):
    """Herramienta para empaquetar contexto completo"""
    name: str = "context_packager_tool"
    description: str = "Empaqueta contexto completo del empleado y error para handoff"

    def _run(self, session_id: str, error_classification: Dict[str, Any],
             recovery_attempts: Dict[str, Any]) -> Dict[str, Any]:
        """Crear paquete completo de contexto"""
        try:
            from core.state_management.state_manager import state_manager
            
            # Obtener contexto completo del empleado
            employee_context = state_manager.get_employee_context(session_id)
            if not employee_context:
                return {
                    "success": False,
                    "error": "Employee context not found",
                    "session_id": session_id
                }
            
            employee_id = employee_context.employee_id
            
            # Crear timeline del proceso
            process_timeline = []
            for agent_id, agent_state in employee_context.agent_states.items():
                process_timeline.append({
                    "agent_id": agent_id,
                    "status": agent_state.status.value if hasattr(agent_state.status, 'value') else str(agent_state.status),
                    "last_updated": agent_state.last_updated.isoformat() if agent_state.last_updated else None,
                    "progress": agent_state.progress,
                    "errors": agent_state.errors
                })
            
            # Resumen del error
            error_summary = {
                "classification_id": error_classification.get("classification_id", "unknown"),
                "error_category": error_classification.get("error_category", "unknown"),
                "error_type": error_classification.get("error_type", "unknown"),
                "severity_level": error_classification.get("severity_level", "medium"),
                "root_cause": error_classification.get("root_cause_analysis", {}).get("primary_cause", "unknown"),
                "affected_agents": error_classification.get("affected_agents", []),
                "pipeline_stage": error_classification.get("pipeline_stage", "unknown"),
                "business_impact": error_classification.get("estimated_impact", {}).get("business_impact", "unknown")
            }
            
            # Historia de recuperación
            recovery_history = []
            if isinstance(recovery_attempts, dict) and "recovery_attempts" in recovery_attempts:
                for attempt in recovery_attempts["recovery_attempts"]:
                    recovery_history.append({
                        "attempt_id": attempt.get("attempt_id", "unknown"),
                        "strategy": attempt.get("strategy", "unknown"),
                        "result": attempt.get("result", "unknown"),
                        "timestamp": attempt.get("timestamp", datetime.utcnow().isoformat())
                    })
            
            # Estado actual de agentes
            agent_states = {}
            for agent_id, agent_state in employee_context.agent_states.items():
                agent_states[agent_id] = {
                    "status": agent_state.status.value if hasattr(agent_state.status, 'value') else str(agent_state.status),
                    "current_task": agent_state.current_task,
                    "progress": agent_state.progress,
                    "last_updated": agent_state.last_updated.isoformat() if agent_state.last_updated else None,
                    "errors": agent_state.errors,
                    "data_keys": list(agent_state.data.keys()) if agent_state.data else []
                }
            
            # Estado del pipeline
            pipeline_status = {
                "current_phase": employee_context.phase.value if hasattr(employee_context.phase, 'value') else str(employee_context.phase),
                "started_at": employee_context.started_at.isoformat(),
                "updated_at": employee_context.updated_at.isoformat(),
                "priority": employee_context.priority,
                "requires_manual_review": employee_context.requires_manual_review,
                "raw_data_keys": list(employee_context.raw_data.keys()) if employee_context.raw_data else [],
                "processed_data_keys": list(employee_context.processed_data.keys()) if employee_context.processed_data else []
            }
            
            # Determinar impacto de negocio y urgencia
            business_impact = self._assess_business_impact(error_classification, employee_context)
            urgency_justification = self._create_urgency_justification(error_classification, recovery_attempts)
            
            # Crear paquete de contexto
            context_package = ContextPackage(
                session_id=session_id,
                employee_id=employee_id,
                employee_context=employee_context.dict(),
                process_timeline=process_timeline,
                error_summary=error_summary,
                recovery_history=recovery_history,
                agent_states=agent_states,
                pipeline_status=pipeline_status,
                business_impact=business_impact,
                urgency_justification=urgency_justification,
                escalation_path=[
                    "Automatic Error Detection",
                    "Error Classification",
                    "Recovery Attempts", 
                    "Human Handoff Initiated"
                ],
                expires_at=datetime.utcnow() + timedelta(hours=24)  # Contexto válido por 24 horas
            )
            
            return {
                "success": True,
                "employee_id": employee_id,
                "session_id": session_id,
                "context_package": context_package.dict(),
                "package_metadata": {
                    "package_id": context_package.package_id,
                    "created_at": context_package.created_at.isoformat(),
                    "expires_at": context_package.expires_at.isoformat() if context_package.expires_at else None,
                    "context_completeness": self._calculate_context_completeness(context_package),
                    "critical_data_preserved": True
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error creating context package: {str(e)}",
                "session_id": session_id,
                "context_package": None
            }
    
    def _assess_business_impact(self, error_classification: Dict, employee_context) -> str:
        """Evaluar impacto de negocio"""
        severity = error_classification.get("severity_level", "medium")
        error_category = error_classification.get("error_category", "unknown")
        
        # Determinar impacto basado en severidad y categoría
        if severity == "emergency":
            return "CRITICAL - Onboarding process completely blocked, immediate business impact"
        elif severity == "critical":
            return "HIGH - Significant delays expected, SLA breaches likely"
        elif error_category == "security_issue":
            return "HIGH - Security implications require immediate attention"
        elif error_category == "sla_breach":
            return "MEDIUM - SLA compliance at risk, customer satisfaction impact"
        else:
            return "LOW - Process delays expected but manageable"
    
    def _create_urgency_justification(self, error_classification: Dict, recovery_attempts: Dict) -> str:
        """Crear justificación de urgencia"""
        recovery_failures = recovery_attempts.get("total_attempts", 0) if isinstance(recovery_attempts, dict) else 0
        severity = error_classification.get("severity_level", "medium")
        
        justifications = []
        
        if recovery_failures >= 3:
            justifications.append(f"Multiple recovery attempts failed ({recovery_failures})")
        
        if severity in ["emergency", "critical"]:
            justifications.append(f"High severity error ({severity})")
        
        error_category = error_classification.get("error_category")
        if error_category == "security_issue":
            justifications.append("Security issue requires immediate specialist attention")
        
        if not justifications:
            justifications.append("Standard escalation procedure - automatic recovery unsuccessful")
        
        return "; ".join(justifications)
    
    def _calculate_context_completeness(self, context_package: ContextPackage) -> float:
        """Calcular completitud del contexto (0-100)"""
        completeness_factors = []
        
        # Factor 1: Información del empleado (25%)
        if context_package.employee_context:
            completeness_factors.append(25.0)
        
        # Factor 2: Timeline del proceso (25%)
        if context_package.process_timeline:
            completeness_factors.append(25.0)
        
        # Factor 3: Información del error (25%)
        if context_package.error_summary:
            completeness_factors.append(25.0)
        
        # Factor 4: Estados de agentes (25%)
        if context_package.agent_states:
            completeness_factors.append(25.0)
        
        return sum(completeness_factors)

class TicketManagerTool(BaseTool):
    """Herramienta para crear y gestionar tickets de escalación"""
    name: str = "ticket_manager_tool"
    description: str = "Crea y gestiona tickets de escalación en sistemas externos"

    def _run(self, escalation_request: Dict[str, Any], 
             specialist_assignments: List[Dict[str, Any]],
             context_package: Dict[str, Any]) -> Dict[str, Any]:
        """Crear tickets de escalación"""
        try:
            session_id = escalation_request.get("session_id")
            employee_id = escalation_request.get("employee_id")
            escalation_level = escalation_request.get("escalation_level", "medium")
            
            tickets_created = []
            
            # Crear ticket principal
            primary_assignment = specialist_assignments[0] if specialist_assignments else None
            
            if primary_assignment:
                ticket = self._create_escalation_ticket(
                    session_id=session_id,
                    employee_id=employee_id,
                    escalation_level=escalation_level,
                    assignment=primary_assignment,
                    context_package=context_package,
                    ticket_type="primary"
                )
                tickets_created.append(ticket)
            
            # Crear tickets adicionales para otros especialistas
            for assignment in specialist_assignments[1:]:
                ticket = self._create_escalation_ticket(
                    session_id=session_id,
                    employee_id=employee_id,
                    escalation_level=escalation_level,
                    assignment=assignment,
                    context_package=context_package,
                    ticket_type="collaborative"
                )
                tickets_created.append(ticket)
            
            # Simular integración con sistemas externos
            external_refs = {}
            for ticket in tickets_created:
                # Simular creación en JIRA
                jira_ticket_id = f"ON-{ticket['ticket_id'][-6:]}"
                external_refs[ticket['ticket_id']] = {
                    "jira_ticket": jira_ticket_id,
                    "servicenow_incident": f"INC{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "dashboard_url": f"https://dashboard.empresa.com/tickets/{ticket['ticket_id']}"
                }
            
            return {
                "success": True,
                "employee_id": employee_id,
                "session_id": session_id,
                "ticket_management_result": {
                    "tickets_created": tickets_created,
                    "total_tickets": len(tickets_created),
                    "primary_ticket_id": tickets_created[0]['ticket_id'] if tickets_created else None,
                    "external_references": external_refs,
                    "escalation_tracking_active": True
                },
                "ticket_metadata": {
                    "creation_timestamp": datetime.utcnow().isoformat(),
                    "escalation_level": escalation_level,
                    "specialists_assigned": len(specialist_assignments),
                    "estimated_resolution_time": self._estimate_resolution_time(escalation_level),
                    "sla_compliance_tracking": True
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error creating escalation tickets: {str(e)}",
                "session_id": escalation_request.get("session_id"),
                "ticket_management_result": None
            }
    
    def _create_escalation_ticket(self, session_id: str, employee_id: str,
                                 escalation_level: str, assignment: Dict[str, Any],
                                 context_package: Dict[str, Any], ticket_type: str) -> Dict[str, Any]:
        """Crear ticket individual de escalación"""
        
        # Extraer información del contexto
        error_summary = context_package.get("error_summary", {})
        error_category = error_summary.get("error_category", "unknown")
        error_type = error_summary.get("error_type", "unknown")
        
        # Crear título y descripción
        title = f"[{escalation_level.upper()}] Onboarding Error - {employee_id} - {error_category}"
        
        description = self._generate_ticket_description(
            employee_id=employee_id,
            error_summary=error_summary,
            context_package=context_package,
            assignment=assignment
        )
        
        # Calcular SLA deadline
        sla_minutes = self._get_sla_minutes(escalation_level)
        sla_deadline = datetime.utcnow() + timedelta(minutes=sla_minutes)
        
        # Crear especialista assignment object
        specialist_assignment = SpecialistAssignment(
            specialist_type=SpecialistType(assignment["specialist_type"]),
            department=EscalationDepartment(assignment["department"]),
            specialist_name=assignment["specialist_name"],
            specialist_contact=assignment["specialist_contact"],
            backup_specialist=assignment.get("backup_specialist"),
            estimated_response_time=sla_minutes,
            sla_deadline=sla_deadline,
            assignment_reason=assignment["assignment_reason"]
        )
        
        # Crear ticket
        ticket = EscalationTicket(
            session_id=session_id,
            employee_id=employee_id,
            title=title,
            description=description,
            escalation_level=EscalationLevel(escalation_level),
            category=error_category,
            assigned_department=EscalationDepartment(assignment["department"]),
            assigned_specialist=specialist_assignment,
            sla_deadline=sla_deadline,
            context_package_id=context_package.get("package_id", "unknown")
        )
        
        return ticket.dict()
    
    def _generate_ticket_description(self, employee_id: str, error_summary: Dict,
                                   context_package: Dict, assignment: Dict) -> str:
        """Generar descripción detallada del ticket"""
        
        template = f"""
ESCALATION TICKET - ONBOARDING PROCESS FAILURE

**EMPLOYEE INFORMATION:**
- Employee ID: {employee_id}
- Session ID: {context_package.get('session_id', 'N/A')}
- Current Phase: {context_package.get('pipeline_status', {}).get('current_phase', 'Unknown')}

**ERROR DETAILS:**
- Category: {error_summary.get('error_category', 'Unknown')}
- Type: {error_summary.get('error_type', 'Unknown')}
- Severity: {error_summary.get('severity_level', 'Unknown')}
- Root Cause: {error_summary.get('root_cause', 'Under investigation')}

**BUSINESS IMPACT:**
{context_package.get('business_impact', 'Impact assessment pending')}

**RECOVERY ATTEMPTS:**
{len(context_package.get('recovery_history', []))} recovery attempts made
- All automatic recovery strategies have been exhausted
- Manual intervention required

**ASSIGNED SPECIALIST:**
- Name: {assignment['specialist_name']}
- Department: {assignment['department']}
- Contact: {assignment['specialist_contact']}
- Backup: {assignment.get('backup_specialist', 'N/A')}

**CONTEXT PACKAGE:**
- Package ID: {context_package.get('package_id', 'N/A')}
- Completeness: {context_package.get('context_completeness', 0)}%
- Expires: {context_package.get('expires_at', 'N/A')}

**URGENCY JUSTIFICATION:**
{context_package.get('urgency_justification', 'Standard escalation procedure')}

**IMMEDIATE ACTIONS REQUIRED:**
1. Review context package and error classification
2. Assess current system state and affected components
3. Determine appropriate recovery strategy
4. Coordinate with other departments if necessary
5. Update ticket with progress and resolution

**ESCALATION PATH:**
{' → '.join(context_package.get('escalation_path', []))}

This ticket requires immediate attention according to escalation level: {error_summary.get('severity_level', 'Unknown')}
"""
        return template.strip()
    
    def _get_sla_minutes(self, escalation_level: str) -> int:
        """Obtener minutos SLA según nivel"""
        sla_mapping = {
            "emergency": 5,
            "critical": 15,
            "high": 60,
            "medium": 240,
            "low": 1440
        }
        return sla_mapping.get(escalation_level, 240)
    
    def _estimate_resolution_time(self, escalation_level: str) -> int:
        """Estimar tiempo de resolución en minutos"""
        resolution_estimates = {
            "emergency": 30,     # 30 minutes
            "critical": 120,     # 2 hours
            "high": 480,         # 8 hours
            "medium": 1440,      # 24 hours
            "low": 2880          # 48 hours
        }
        return resolution_estimates.get(escalation_level, 1440)

class NotificationSystemTool(BaseTool):
    """Herramienta para notificar stakeholders apropiados"""
    name: str = "notification_system_tool"
    description: str = "Envía notificaciones a stakeholders según canal y prioridad"

    def _run(self, tickets_created: List[Dict[str, Any]], 
             specialist_assignments: List[Dict[str, Any]],
             escalation_level: str) -> Dict[str, Any]:
        """Enviar notificaciones a stakeholders"""
        try:
            notifications_sent = []
            notification_failures = []
            
            # Determinar canales según escalación
            channels = self._get_notification_channels(escalation_level)
            
            # Crear notificaciones para cada especialista
            for assignment in specialist_assignments:
                for channel in channels:
                    notification = self._create_notification(
                        assignment=assignment,
                        tickets=tickets_created,
                        channel=channel,
                        escalation_level=escalation_level
                    )
                    
                    # Simular envío de notificación
                    send_result = self._send_notification(notification, channel)
                    
                    if send_result["success"]:
                        notification["sent_at"] = datetime.utcnow()
                        notification["delivered_at"] = datetime.utcnow()
                        notifications_sent.append(notification)
                    else:
                        notification_failures.append({
                            "notification": notification,
                            "error": send_result["error"],
                            "channel": channel
                        })
            
            # Notificaciones adicionales para escalación alta
            if escalation_level in ["emergency", "critical"]:
                management_notifications = self._create_management_notifications(
                    tickets_created, escalation_level
                )
                
                for notification in management_notifications:
                    send_result = self._send_notification(notification, NotificationChannel.EMAIL)
                    if send_result["success"]:
                        notification["sent_at"] = datetime.utcnow()
                        notifications_sent.append(notification)
            
            # Crear notificación de dashboard
            dashboard_notification = self._create_dashboard_notification(
                tickets_created, escalation_level
            )
            if dashboard_notification:
                notifications_sent.append(dashboard_notification)
            
            return {
                "success": True,
                "notification_result": {
                    "notifications_sent": notifications_sent,
                    "total_notifications": len(notifications_sent),
                    "notification_failures": notification_failures,
                    "channels_used": list(set([n.get("channel") for n in notifications_sent])),
                    "specialists_notified": len(specialist_assignments),
                    "escalation_level": escalation_level
                },
                "notification_metadata": {
                    "notification_timestamp": datetime.utcnow().isoformat(),
                    "priority_notifications": escalation_level in ["emergency", "critical"],
                    "management_notified": escalation_level in ["emergency", "critical"],
                    "dashboard_updated": True,
                    "retry_scheduled": len(notification_failures) > 0
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error sending notifications: {str(e)}",
                "notification_result": None
            }
    
    def _get_notification_channels(self, escalation_level: str) -> List[NotificationChannel]:
        """Determinar canales de notificación según nivel"""
        channel_mapping = {
            "emergency": [NotificationChannel.PHONE, NotificationChannel.SMS, 
                         NotificationChannel.SLACK, NotificationChannel.EMAIL],
            "critical": [NotificationChannel.SLACK, NotificationChannel.EMAIL, 
                        NotificationChannel.SMS],
            "high": [NotificationChannel.SLACK, NotificationChannel.EMAIL],
            "medium": [NotificationChannel.EMAIL, NotificationChannel.SLACK],
            "low": [NotificationChannel.EMAIL]
        }
        return channel_mapping.get(escalation_level, [NotificationChannel.EMAIL])
    
    def _create_notification(self, assignment: Dict, tickets: List[Dict], 
                           channel: NotificationChannel, escalation_level: str) -> Dict[str, Any]:
        """Crear notificación individual"""
        
        primary_ticket = tickets[0] if tickets else {}
        
        # Templates por canal
        if channel == NotificationChannel.SLACK:
            subject = f"🚨 ESCALATION: {escalation_level.upper()} - {primary_ticket.get('employee_id', 'Unknown')}"
            message = self._create_slack_message(assignment, primary_ticket, escalation_level)
        elif channel == NotificationChannel.EMAIL:
            subject = f"ESCALATION REQUIRED - {escalation_level.upper()} - Ticket {primary_ticket.get('ticket_id', 'Unknown')}"
            message = self._create_email_message(assignment, primary_ticket, escalation_level)
        elif channel == NotificationChannel.SMS:
            subject = f"URGENT: Escalation {primary_ticket.get('ticket_id', 'Unknown')}"
            message = f"Escalation assigned - {escalation_level.upper()} priority. Check dashboard immediately."
        else:
            subject = f"Escalation: {primary_ticket.get('ticket_id', 'Unknown')}"
            message = f"New escalation assigned to {assignment['specialist_name']}"
        
        notification = NotificationEvent(
            ticket_id=primary_ticket.get('ticket_id', 'unknown'),
            session_id=primary_ticket.get('session_id', 'unknown'),
            recipient=assignment['specialist_contact'],
            channel=channel,
            specialist_type=SpecialistType(assignment['specialist_type']),
            subject=subject,
            message=message,
            priority_flag=escalation_level in ["emergency", "critical"],
            template_used=f"{channel.value}_escalation_template"
        )
        
        return notification.dict()
    
    def _create_slack_message(self, assignment: Dict, ticket: Dict, escalation_level: str) -> str:
        """Crear mensaje para Slack"""
        emoji_map = {
            "emergency": "🔥",
            "critical": "🚨", 
            "high": "⚠️",
            "medium": "📋",
            "low": "📝"
        }
        
        emoji = emoji_map.get(escalation_level, "📋")
        
        return f"""
{emoji} **ONBOARDING ESCALATION ASSIGNED**

**Priority:** {escalation_level.upper()}
**Employee:** {ticket.get('employee_id', 'Unknown')}
**Ticket:** {ticket.get('ticket_id', 'Unknown')}

**Assigned to:** {assignment['specialist_name']} ({assignment['department']})
**SLA Deadline:** {ticket.get('sla_deadline', 'Unknown')}

**Error:** {ticket.get('category', 'Unknown')} - {ticket.get('title', 'Unknown')}

**Actions:**
• Review ticket details in dashboard
• Check context package
• Begin investigation immediately
• Update ticket with progress

**Dashboard:** https://dashboard.empresa.com/tickets/{ticket.get('ticket_id', 'unknown')}
"""
    
    def _create_email_message(self, assignment: Dict, ticket: Dict, escalation_level: str) -> str:
        """Crear mensaje para email"""
        return f"""
Dear {assignment['specialist_name']},

An onboarding process escalation has been assigned to you with {escalation_level.upper()} priority.

ESCALATION DETAILS:
- Employee ID: {ticket.get('employee_id', 'Unknown')}
- Ticket ID: {ticket.get('ticket_id', 'Unknown')}
- Category: {ticket.get('category', 'Unknown')}
- Department: {assignment['department']}
- SLA Deadline: {ticket.get('sla_deadline', 'Unknown')}

DESCRIPTION:
{ticket.get('description', 'No description available')[:200]}...

IMMEDIATE ACTIONS REQUIRED:
1. Log into the escalation dashboard
2. Review the complete context package
3. Begin investigation and troubleshooting
4. Update the ticket with your progress
5. Coordinate with backup specialist if needed

BACKUP SPECIALIST: {assignment.get('backup_specialist', 'Not assigned')}

ACCESS DASHBOARD: https://dashboard.empresa.com/tickets/{ticket.get('ticket_id', 'unknown')}

This escalation requires immediate attention. Please acknowledge receipt and begin work immediately.

Best regards,
Automated Onboarding System
"""
    
    def _create_management_notifications(self, tickets: List[Dict], escalation_level: str) -> List[Dict]:
        """Crear notificaciones para management"""
        notifications = []
        
        management_contacts = [
            {"name": "IT Director", "email": "it.director@empresa.com"},
            {"name": "HR Director", "email": "hr.director@empresa.com"},
            {"name": "Operations Manager", "email": "operations@empresa.com"}
        ]
        
        primary_ticket = tickets[0] if tickets else {}
        
        for contact in management_contacts:
            notification = NotificationEvent(
                ticket_id=primary_ticket.get('ticket_id', 'unknown'),
                session_id=primary_ticket.get('session_id', 'unknown'),
                recipient=contact['email'],
                channel=NotificationChannel.EMAIL,
                specialist_type=SpecialistType.DEPARTMENT_MANAGER,
                subject=f"MANAGEMENT ALERT - {escalation_level.upper()} Onboarding Escalation",
                message=f"""
Management Alert: High priority onboarding escalation

Employee: {primary_ticket.get('employee_id', 'Unknown')}
Ticket: {primary_ticket.get('ticket_id', 'Unknown')}
Escalation Level: {escalation_level.upper()}

Multiple specialists have been notified and are responding.
This incident is being tracked and will be resolved according to SLA requirements.

Dashboard: https://dashboard.empresa.com/management/escalations
""",
                priority_flag=True,
                template_used="management_alert_template"
            )
            notifications.append(notification.dict())
        
        return notifications
    
    def _create_dashboard_notification(self, tickets: List[Dict], escalation_level: str) -> Dict:
        """Crear notificación para dashboard"""
        primary_ticket = tickets[0] if tickets else {}
        
        notification = NotificationEvent(
            ticket_id=primary_ticket.get('ticket_id', 'unknown'),
            session_id=primary_ticket.get('session_id', 'unknown'),
            recipient="dashboard_system",
            channel=NotificationChannel.DASHBOARD,
            specialist_type=SpecialistType.SYSTEM_ADMIN,
            subject="Dashboard Update",
            message=f"New escalation created - {escalation_level} priority",
            priority_flag=escalation_level in ["emergency", "critical"],
            template_used="dashboard_update_template"
        )
        
        notification_dict = notification.dict()
        notification_dict["sent_at"] = datetime.utcnow()
        notification_dict["delivered_at"] = datetime.utcnow()
        
        return notification_dict
    
    def _send_notification(self, notification: Dict, channel: NotificationChannel) -> Dict[str, Any]:
        """Simular envío de notificación"""
        try:
            # Simular diferentes tasas de éxito por canal
            success_rates = {
                NotificationChannel.EMAIL: 0.95,
                NotificationChannel.SLACK: 0.98,
                NotificationChannel.SMS: 0.90,
                NotificationChannel.PHONE: 0.85,
                NotificationChannel.DASHBOARD: 0.99
            }
            
            import random
            success_rate = success_rates.get(channel, 0.95)
            
            if random.random() <= success_rate:
                return {
                    "success": True,
                    "channel": channel.value,
                    "delivery_time": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"Delivery failed for {channel.value}",
                    "channel": channel.value
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Notification error: {str(e)}",
                "channel": channel.value
            }

# Export tools
escalation_router_tool = EscalationRouterTool()
context_packager_tool = ContextPackagerTool()
ticket_manager_tool = TicketManagerTool()
notification_system_tool = NotificationSystemTool()