from typing import Dict, Any, List, Optional
from langchain.tools import BaseTool
from datetime import datetime, timedelta
import json
from .schemas import (
    HandoffPriority, SpecialistType, SpecialistProfile, SpecialistAssignment,
    ContextPackage, EscalationTicket, NotificationEvent, NotificationChannel,
    HandoffStatus
)

class EscalationRouterTool(BaseTool):
    """Herramienta para determinar especialista apropiado"""
    name: str = "escalation_router_tool"
    description: str = "Determina el especialista humano más apropiado basado en error y contexto"

    def _run(self, handoff_request: Dict[str, Any], 
             available_specialists: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Enrutar a especialista apropiado"""
        try:
            # Simular base de datos de especialistas
            if not available_specialists:
                available_specialists = self._get_default_specialists()
            
            error_category = handoff_request.get("error_category", "")
            error_severity = handoff_request.get("error_severity", "")
            handoff_priority = handoff_request.get("handoff_priority", HandoffPriority.MEDIUM.value)
            
            # Determinar tipo de especialista requerido
            required_specialist_type = self._determine_specialist_type(error_category)
            
            # Filtrar especialistas disponibles
            candidate_specialists = self._filter_specialists(
                available_specialists, required_specialist_type, handoff_priority
            )
            
            # Ranking de especialistas
            ranked_specialists = self._rank_specialists(
                candidate_specialists, error_category, error_severity
            )
            
            if not ranked_specialists:
                return {
                    "success": False,
                    "error": "No suitable specialists available",
                    "fallback_required": True
                }
            
            # Seleccionar especialista principal y backups
            primary_specialist = ranked_specialists[0]
            backup_specialists = ranked_specialists[1:3] if len(ranked_specialists) > 1 else []
            
            # Crear asignación
            assignment = self._create_specialist_assignment(
                handoff_request, primary_specialist, backup_specialists
            )
            
            # Determinar escalation chain
            escalation_chain = self._build_escalation_chain(
                primary_specialist, error_category, handoff_priority
            )
            
            return {
                "success": True,
                "specialist_assignment": assignment,
                "escalation_chain": escalation_chain,
                "assignment_confidence": self._calculate_assignment_confidence(
                    primary_specialist, error_category
                ),
                "backup_specialists": backup_specialists,
                "routing_rationale": self._generate_routing_rationale(
                    primary_specialist, error_category, error_severity
                )
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error in escalation routing: {str(e)}",
                "fallback_required": True
            }

    def _get_default_specialists(self) -> List[Dict[str, Any]]:
        """Obtener lista de especialistas por defecto"""
        return [
            {
                "specialist_id": "it_001",
                "name": "Carlos Méndez",
                "specialist_type": SpecialistType.IT_SPECIALIST.value,
                "department": "IT",
                "is_available": True,
                "current_workload": 2,
                "max_concurrent_cases": 5,
                "expertise_areas": ["agent_failures", "timeouts", "system_errors"],
                "handling_categories": ["agent_failure", "system_error", "integration_error"],
                "email": "carlos.mendez@company.com",
                "slack_id": "carlos.mendez",
                "average_resolution_time_hours": 4.0,
                "success_rate": 0.92
            },
            {
                "specialist_id": "hr_001", 
                "name": "María Rodríguez",
                "specialist_type": SpecialistType.HR_MANAGER.value,
                "department": "HR",
                "is_available": True,
                "current_workload": 1,
                "max_concurrent_cases": 4,
                "expertise_areas": ["compliance", "data_validation", "quality_issues"],
                "handling_categories": ["quality_failure", "data_validation", "business_rule_violation"],
                "email": "maria.rodriguez@company.com",
                "teams_id": "maria.rodriguez",
                "average_resolution_time_hours": 6.0,
                "success_rate": 0.95
            },
            {
                "specialist_id": "sec_001",
                "name": "Diego Vargas", 
                "specialist_type": SpecialistType.SECURITY_SPECIALIST.value,
                "department": "Security",
                "is_available": True,
                "current_workload": 0,
                "max_concurrent_cases": 3,
                "expertise_areas": ["security_issues", "authentication", "compliance"],
                "handling_categories": ["security_issue", "authentication_error"],
                "email": "diego.vargas@company.com",
                "phone": "+506-8888-1234",
                "average_resolution_time_hours": 2.0,
                "success_rate": 0.98
            },
            {
                "specialist_id": "legal_001",
                "name": "Ana Jiménez",
                "specialist_type": SpecialistType.LEGAL_SPECIALIST.value,
                "department": "Legal",
                "is_available": True,
                "current_workload": 1,
                "max_concurrent_cases": 3,
                "expertise_areas": ["contract_issues", "compliance", "business_rules"],
                "handling_categories": ["business_rule_violation", "quality_failure"],
                "email": "ana.jimenez@company.com",
                "average_resolution_time_hours": 12.0,
                "success_rate": 0.96
            }
        ]

    def _determine_specialist_type(self, error_category: str) -> SpecialistType:
        """Determinar tipo de especialista basado en categoría de error"""
        category_mapping = {
            "agent_failure": SpecialistType.IT_SPECIALIST,
            "system_error": SpecialistType.IT_SPECIALIST,
            "integration_error": SpecialistType.IT_SPECIALIST,
            "sla_breach": SpecialistType.IT_SPECIALIST,
            "quality_failure": SpecialistType.HR_MANAGER,
            "data_validation": SpecialistType.HR_MANAGER,
            "business_rule_violation": SpecialistType.LEGAL_SPECIALIST,
            "security_issue": SpecialistType.SECURITY_SPECIALIST
        }
        return category_mapping.get(error_category, SpecialistType.IT_SPECIALIST)

    def _filter_specialists(self, specialists: List[Dict], 
                          required_type: SpecialistType,
                          priority: str) -> List[Dict]:
        """Filtrar especialistas disponibles"""
        filtered = []
        for specialist in specialists:
            # Check availability
            if not specialist.get("is_available", False):
                continue
                
            # Check workload capacity
            current_load = specialist.get("current_workload", 0)
            max_load = specialist.get("max_concurrent_cases", 5)
            if current_load >= max_load:
                continue
                
            # Check specialist type match
            if specialist.get("specialist_type") == required_type.value:
                filtered.append(specialist)
            
            # For high priority, also include generalists
            elif priority in ["emergency", "critical"]:
                if specialist.get("specialist_type") in [
                    SpecialistType.SYSTEM_ADMIN.value,
                    SpecialistType.IT_SPECIALIST.value
                ]:
                    filtered.append(specialist)
        
        return filtered

    def _rank_specialists(self, specialists: List[Dict],
                         error_category: str,
                         error_severity: str) -> List[Dict]:
        """Ranking de especialistas por idoneidad"""
        scored_specialists = []
        
        for specialist in specialists:
            score = self._calculate_specialist_score(
                specialist, error_category, error_severity
            )
            scored_specialists.append((specialist, score))
        
        # Sort by score (higher is better)
        scored_specialists.sort(key=lambda x: x[1], reverse=True)
        return [specialist for specialist, score in scored_specialists]

    def _calculate_specialist_score(self, specialist: Dict,
                                   error_category: str,
                                   error_severity: str) -> float:
        """Calcular score de idoneidad del especialista"""
        score = 0.0
        
        # Expertise match (40%)
        expertise_areas = specialist.get("expertise_areas", [])
        if any(area in error_category for area in expertise_areas):
            score += 0.4
        
        # Category handling (30%)  
        handling_categories = specialist.get("handling_categories", [])
        if error_category in handling_categories:
            score += 0.3
            
        # Performance metrics (20%)
        success_rate = specialist.get("success_rate", 0.5)
        score += 0.2 * success_rate
        
        # Availability/workload (10%)
        current_load = specialist.get("current_workload", 0)
        max_load = specialist.get("max_concurrent_cases", 5)
        availability_factor = 1 - (current_load / max_load)
        score += 0.1 * availability_factor
        
        return score

    def _create_specialist_assignment(self, handoff_request: Dict,
                                    primary_specialist: Dict,
                                    backup_specialists: List[Dict]) -> Dict[str, Any]:
        """Crear asignación de especialista"""
        handoff_id = handoff_request.get("handoff_id", "unknown")
        
        # Convert to SpecialistProfile
        specialist_profile = {
            "specialist_id": primary_specialist.get("specialist_id"),
            "name": primary_specialist.get("name"),
            "specialist_type": primary_specialist.get("specialist_type"),
            "department": primary_specialist.get("department"),
            "is_available": primary_specialist.get("is_available", True),
            "current_workload": primary_specialist.get("current_workload", 0),
            "email": primary_specialist.get("email"),
            "slack_id": primary_specialist.get("slack_id"),
            "success_rate": primary_specialist.get("success_rate", 0.9)
        }
        
        # Calculate expected resolution time
        avg_resolution_hours = primary_specialist.get("average_resolution_time_hours", 8.0)
        expected_resolution = datetime.utcnow() + timedelta(hours=avg_resolution_hours)
        
        return {
            "handoff_id": handoff_id,
            "assigned_specialist": specialist_profile,
            "assignment_method": "automatic",
            "assignment_reason": f"Best match for {handoff_request.get('error_category')} category",
            "expected_resolution_time": expected_resolution.isoformat(),
            "backup_specialists": backup_specialists,
            "assigned_at": datetime.utcnow().isoformat()
        }

    def _build_escalation_chain(self, primary_specialist: Dict,
                               error_category: str,
                               priority: str) -> List[str]:
        """Construir cadena de escalación"""
        escalation_chain = [primary_specialist.get("specialist_id")]
        
        # Level 2: Department lead
        department = primary_specialist.get("department", "IT")
        escalation_chain.append(f"{department.lower()}_manager")
        
        # Level 3: Senior management for critical issues
        if priority in ["critical", "emergency"]:
            if error_category in ["security_issue", "system_error"]:
                escalation_chain.append("ciso_director")
            else:
                escalation_chain.append("operations_director")
        
        # Level 4: Executive level for emergency
        if priority == "emergency":
            escalation_chain.append("cto_executive")
        
        return escalation_chain

    def _calculate_assignment_confidence(self, specialist: Dict,
                                       error_category: str) -> float:
        """Calcular confianza en la asignación"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on expertise match
        expertise_areas = specialist.get("expertise_areas", [])
        if any(area in error_category for area in expertise_areas):
            confidence += 0.3
            
        # Increase based on success rate
        success_rate = specialist.get("success_rate", 0.5)
        confidence += 0.2 * success_rate
        
        return min(1.0, confidence)

    def _generate_routing_rationale(self, specialist: Dict,
                                  error_category: str,
                                  error_severity: str) -> str:
        """Generar justificación del routing"""
        name = specialist.get("name", "Unknown")
        dept = specialist.get("department", "Unknown")
        success_rate = specialist.get("success_rate", 0.0)
        
        return (f"Assigned to {name} from {dept} department based on expertise in "
               f"{error_category} issues. Specialist has {success_rate:.1%} success rate "
               f"and appropriate availability for {error_severity} severity level.")

class ContextPackagerTool(BaseTool):
    """Herramienta para empaquetar contexto completo"""
    name: str = "context_packager_tool" 
    description: str = "Empaqueta contexto completo del empleado, error y sistema para handoff"

    def _run(self, handoff_request: Dict[str, Any],
             system_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Empaquetar contexto para handoff"""
        try:
            from core.state_management.state_manager import state_manager
            
            session_id = handoff_request.get("session_id")
            employee_id = handoff_request.get("employee_id")
            handoff_id = handoff_request.get("handoff_id")
            
            # Obtener contexto del empleado
            employee_context = None
            if session_id:
                employee_context = state_manager.get_employee_context(session_id)
            
            # Crear paquete de contexto
            context_package = {
                "package_id": f"ctx_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "handoff_id": handoff_id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Employee context
            if employee_context:
                context_package["employee_data"] = {
                    "employee_id": employee_context.employee_id,
                    "session_id": employee_context.session_id,
                    "phase": employee_context.phase.value if hasattr(employee_context.phase, 'value') else str(employee_context.phase),
                    "started_at": employee_context.started_at.isoformat() if employee_context.started_at else None,
                    "priority": employee_context.priority,
                    "raw_data_summary": self._summarize_data(employee_context.raw_data),
                    "processed_data_summary": self._summarize_data(employee_context.processed_data)
                }
                
                # Employee journey
                context_package["employee_journey"] = self._build_employee_journey(employee_context)
                
                # Current pipeline stage
                context_package["current_pipeline_stage"] = employee_context.phase.value if hasattr(employee_context.phase, 'value') else str(employee_context.phase)
                
                # Agent states
                context_package["agent_states"] = {
                    agent_id: {
                        "status": state.status.value if hasattr(state.status, 'value') else str(state.status),
                        "last_updated": state.last_updated.isoformat() if state.last_updated else None,
                        "error_count": len(state.errors) if state.errors else 0,
                        "has_data": bool(state.data)
                    }
                    for agent_id, state in employee_context.agent_states.items()
                }
            else:
                context_package.update({
                    "employee_data": {"employee_id": employee_id, "context_unavailable": True},
                    "employee_journey": [],
                    "current_pipeline_stage": "unknown",
                    "agent_states": {}
                })
            
            # Error context
            error_context = handoff_request.get("error_context", {})
            context_package["error_timeline"] = self._build_error_timeline(error_context)
            context_package["failed_operations"] = self._extract_failed_operations(error_context)
            
            # Recovery attempts
            recovery_attempts = handoff_request.get("recovery_attempts", [])
            context_package["recovery_attempts_log"] = self._process_recovery_attempts(recovery_attempts)
            
            # System context
            system_overview = state_manager.get_system_overview()
            context_package["system_state_snapshot"] = {
                "active_sessions": system_overview.get("active_sessions", 0),
                "registered_agents": system_overview.get("registered_agents", 0),
                "agents_status": system_overview.get("agents_status", {}),
                "last_updated": system_overview.get("last_updated")
            }
            
            # Business context
            context_package["business_impact_assessment"] = self._assess_business_impact(
                handoff_request, employee_context
            )
            
            # SLA status
            context_package["sla_status"] = self._get_sla_status(handoff_request)
            
            # Documentation
            context_package["relevant_documents"] = self._gather_relevant_documents(
                employee_id, session_id
            )
            
            # Logs extract
            context_package["logs_extract"] = self._extract_relevant_logs(
                session_id, employee_id
            )
            
            # Suggested actions
            context_package["suggested_actions"] = self._generate_suggested_actions(
                handoff_request, error_context
            )
            
            # Calculate package completeness
            completeness_score = self._calculate_package_completeness(context_package)
            context_package["package_completeness"] = completeness_score
            
            # Identify missing critical info
            context_package["critical_info_missing"] = self._identify_missing_info(
                context_package, completeness_score
            )
            
            return {
                "success": True,
                "context_package": context_package,
                "package_completeness": completeness_score,
                "handoff_ready": completeness_score >= 0.7,
                "critical_info_complete": len(context_package["critical_info_missing"]) == 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error creating context package: {str(e)}",
                "context_package": None,
                "package_completeness": 0.0
            }

    def _summarize_data(self, data_dict: Dict) -> Dict[str, Any]:
        """Resumir datos para contexto"""
        if not data_dict:
            return {"empty": True}
        
        return {
            "field_count": len(data_dict),
            "has_personal_info": any(key in data_dict for key in ["name", "email", "id_card"]),
            "has_employment_info": any(key in data_dict for key in ["position", "department", "salary"]),
            "sample_fields": list(data_dict.keys())[:5]
        }

    def _build_employee_journey(self, employee_context) -> List[Dict[str, Any]]:
        """Construir timeline del empleado"""
        journey = []
        
        # Journey from agent states
        for agent_id, agent_state in employee_context.agent_states.items():
            journey.append({
                "timestamp": agent_state.last_updated.isoformat() if agent_state.last_updated else None,
                "agent": agent_id,
                "status": agent_state.status.value if hasattr(agent_state.status, 'value') else str(agent_state.status),
                "has_data": bool(agent_state.data),
                "errors": len(agent_state.errors) if agent_state.errors else 0
            })
        
        # Sort by timestamp
        journey.sort(key=lambda x: x["timestamp"] or "")
        return journey

    def _build_error_timeline(self, error_context: Dict) -> List[Dict[str, Any]]:
        """Construir timeline de errores"""
        timeline = []
        
        # Extract error events from context
        if "errors" in error_context:
            for error in error_context["errors"]:
                timeline.append({
                    "timestamp": error.get("timestamp", datetime.utcnow().isoformat()),
                    "event_type": "error_occurred",
                    "error_type": error.get("error_type", "unknown"),
                    "severity": error.get("severity", "medium"),
                    "source": error.get("source", "unknown")
                })
        
        return sorted(timeline, key=lambda x: x["timestamp"])

    def _extract_failed_operations(self, error_context: Dict) -> List[Dict[str, Any]]:
        """Extraer operaciones fallidas"""
        failed_ops = []
        
        if "failed_operations" in error_context:
            for op in error_context["failed_operations"]:
                failed_ops.append({
                    "operation_type": op.get("type", "unknown"),
                    "agent_id": op.get("agent_id", "unknown"),
                    "failure_reason": op.get("error", "unknown"),
                    "timestamp": op.get("timestamp", datetime.utcnow().isoformat())
                })
        
        return failed_ops

    def _process_recovery_attempts(self, recovery_attempts: List) -> List[Dict[str, Any]]:
        """Procesar intentos de recuperación"""
        processed = []
        
        for attempt in recovery_attempts:
            processed.append({
                "recovery_id": attempt.get("recovery_id", "unknown"),
                "strategy": attempt.get("strategy", "unknown"),
                "status": attempt.get("status", "unknown"),
                "actions_executed": attempt.get("actions", []),
                "success": attempt.get("success", False),
                "timestamp": attempt.get("timestamp", datetime.utcnow().isoformat())
            })
        
        return processed

    def _assess_business_impact(self, handoff_request: Dict, employee_context) -> Dict[str, Any]:
        """Evaluar impacto en el negocio"""
        impact = {
            "severity": handoff_request.get("business_impact", "medium"),
            "employee_waiting": True,
            "onboarding_delayed": True,
            "stakeholders_affected": []
        }
        
        # Determine stakeholders based on employee data
        if employee_context and employee_context.raw_data:
            dept = employee_context.raw_data.get("department", "")
            position = employee_context.raw_data.get("position", "")
            
            impact["stakeholders_affected"] = [
                f"{dept}_team",
                "hr_department",
                "hiring_manager"
            ]
            
            # High impact for senior positions
            if "senior" in position.lower() or "manager" in position.lower():
                impact["severity"] = "high"
                impact["stakeholders_affected"].append("department_leadership")
        
        return impact

    def _get_sla_status(self, handoff_request: Dict) -> Dict[str, Any]:
        """Obtener estado de SLA"""
        priority = handoff_request.get("handoff_priority", "medium")
        created_at = handoff_request.get("created_at")
        
        # SLA targets by priority
        sla_targets = {
            "emergency": 5,    # minutes
            "critical": 15,    # minutes
            "high": 60,        # minutes  
            "medium": 240,     # minutes (4 hours)
            "low": 1440        # minutes (24 hours)
        }
        
        target_minutes = sla_targets.get(priority, 240)
        
        if created_at:
            try:
                if isinstance(created_at, str):
                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    created_time = created_at
                
                elapsed_minutes = (datetime.utcnow() - created_time).total_seconds() / 60
                remaining_minutes = max(0, target_minutes - elapsed_minutes)
                
                return {
                    "target_response_minutes": target_minutes,
                    "elapsed_minutes": round(elapsed_minutes, 1),
                    "remaining_minutes": round(remaining_minutes, 1),
                    "sla_breach": elapsed_minutes > target_minutes,
                    "sla_at_risk": remaining_minutes < (target_minutes * 0.2)  # 20% remaining
                }
            except Exception:
                pass
        
        return {
            "target_response_minutes": target_minutes,
            "elapsed_minutes": 0,
            "remaining_minutes": target_minutes,
            "sla_breach": False,
            "sla_at_risk": False
        }

    def _gather_relevant_documents(self, employee_id: str, session_id: str) -> List[Dict[str, Any]]:
        """Recopilar documentos relevantes"""
        # Simulate document gathering
        return [
            {
                "document_type": "error_report",
                "title": f"Error Report - {employee_id}",
                "location": f"/logs/errors/{session_id}.log",
                "size_kb": 45,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "document_type": "employee_data",
                "title": f"Employee Context - {employee_id}",
                "location": f"/data/employees/{employee_id}.json",
                "size_kb": 12,
                "created_at": datetime.utcnow().isoformat()
            }
        ]

    def _extract_relevant_logs(self, session_id: str, employee_id: str) -> List[str]:
        """Extraer logs relevantes"""
        return [
            f"[ERROR] {datetime.utcnow().isoformat()} - Agent failure in session {session_id}",
            f"[WARN] {datetime.utcnow().isoformat()} - SLA risk detected for employee {employee_id}",
            f"[INFO] {datetime.utcnow().isoformat()} - Recovery attempt initiated"
        ]

    def _generate_suggested_actions(self, handoff_request: Dict, error_context: Dict) -> List[str]:
        """Generar acciones sugeridas"""
        actions = []
        
        error_category = handoff_request.get("error_category", "")
        
        if error_category == "agent_failure":
            actions.extend([
                "Check agent logs for specific error details",
                "Restart affected agent if safe",
                "Verify agent dependencies and connectivity"
            ])
        elif error_category == "quality_failure":
            actions.extend([
                "Review quality gate configuration", 
                "Validate employee data completeness",
                "Consider manual quality override if appropriate"
            ])
        elif error_category == "sla_breach":
            actions.extend([
                "Assess SLA extension options",
                "Notify stakeholders of delays",
                "Implement priority escalation"
            ])
        
        # Always include general actions
        actions.extend([
            "Review complete error timeline",
            "Validate system state consistency",
            "Consider employee communication needs"
        ])
        
        return actions

    def _calculate_package_completeness(self, package: Dict) -> float:
        """Calcular completitud del paquete"""
        required_sections = [
            "employee_data", "employee_journey", "current_pipeline_stage",
            "error_timeline", "system_state_snapshot", "business_impact_assessment"
        ]
        
        complete_sections = 0
        for section in required_sections:
            if section in package and package[section]:
                complete_sections += 1
        
        return complete_sections / len(required_sections)

    def _identify_missing_info(self, package: Dict, completeness: float) -> List[str]:
        """Identificar información crítica faltante"""
        missing = []
        
        if completeness < 0.8:
            if not package.get("employee_data", {}).get("employee_id"):
                missing.append("Employee identification missing")
            
            if not package.get("error_timeline"):
                missing.append("Error timeline incomplete")
                
            if not package.get("system_state_snapshot"):
                missing.append("System state snapshot missing")
        
        return missing

class TicketManagerTool(BaseTool):
    """Herramienta para crear y gestionar tickets de escalación"""
    name: str = "ticket_manager_tool"
    description: str = "Crea y gestiona tickets de escalación en sistema de ticketing"

    def _run(self, handoff_request: Dict[str, Any],
             specialist_assignment: Dict[str, Any] = None,
             context_package: Dict[str, Any] = None) -> Dict[str, Any]:
        """Crear ticket de escalación"""
        try:
            handoff_id = handoff_request.get("handoff_id")
            employee_id = handoff_request.get("employee_id")
            session_id = handoff_request.get("session_id")
            
            # Generate ticket
            ticket = self._create_escalation_ticket(
                handoff_request, specialist_assignment, context_package
            )
            
            # Submit to ticketing system (simulated)
            submission_result = self._submit_to_ticketing_system(ticket)
            
            # Calculate SLA targets
            sla_info = self._calculate_ticket_sla(handoff_request)
            
            # Generate ticket URL
            ticket_url = f"https://tickets.company.com/ticket/{ticket['ticket_id']}"
            
            return {
                "success": True,
                "escalation_ticket": ticket,
                "ticket_url": ticket_url,
                "ticket_submitted": submission_result["success"],
                "sla_info": sla_info,
                "tracking_info": {
                    "ticket_id": ticket["ticket_id"],
                    "assigned_to": ticket["assigned_to"],
                    "priority": ticket["priority"],
                    "due_date": ticket["due_date"]
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error creating escalation ticket: {str(e)}",
                "escalation_ticket": None
            }

    def _create_escalation_ticket(self, handoff_request: Dict,
                                 specialist_assignment: Dict = None,
                                 context_package: Dict = None) -> Dict[str, Any]:
        """Crear ticket de escalación"""
        handoff_id = handoff_request.get("handoff_id")
        employee_id = handoff_request.get("employee_id")
        error_category = handoff_request.get("error_category", "unknown")
        error_severity = handoff_request.get("error_severity", "medium")
        priority = handoff_request.get("handoff_priority", "medium")
        
        # Generate title and description
        title = self._generate_ticket_title(employee_id, error_category, error_severity)
        description = self._generate_ticket_description(
            handoff_request, specialist_assignment, context_package
        )
        
        # Determine assignment
        assigned_to = "unassigned"
        assigned_team = "general_support"
        
        if specialist_assignment:
            specialist = specialist_assignment.get("assigned_specialist", {})
            assigned_to = specialist.get("name", "unassigned")
            assigned_team = specialist.get("department", "general_support")
        
        # Calculate due date
        due_date = self._calculate_due_date(priority)
        
        ticket = {
            "ticket_id": f"TKT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "handoff_id": handoff_id,
            "title": title,
            "description": description,
            "category": error_category,
            "priority": priority,
            "severity": error_severity,
            "assigned_to": assigned_to,
            "assigned_team": assigned_team,
            "created_by": "human_handoff_agent",
            "status": "open",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "due_date": due_date.isoformat(),
            "context_package_id": context_package.get("package_id") if context_package else None,
            "employee_id": employee_id,
            "session_id": handoff_request.get("session_id"),
            "comments": [],
            "attachments": []
        }
        
        # Add initial comment with context
        initial_comment = self._create_initial_comment(handoff_request, context_package)
        ticket["comments"].append(initial_comment)
        
        return ticket

    def _generate_ticket_title(self, employee_id: str, error_category: str, 
                              error_severity: str) -> str:
        """Generar título del ticket"""
        severity_prefix = {
            "emergency": "[EMERGENCY]",
            "critical": "[CRITICAL]",
            "high": "[HIGH]", 
            "medium": "",
            "low": "[LOW]"
        }
        
        prefix = severity_prefix.get(error_severity, "")
        category_readable = error_category.replace("_", " ").title()
        
        return f"{prefix} {category_readable} - Employee {employee_id} Onboarding Issue".strip()

    def _generate_ticket_description(self, handoff_request: Dict,
                                   specialist_assignment: Dict = None,
                                   context_package: Dict = None) -> str:
        """Generar descripción del ticket"""
        lines = [
            "## Onboarding System Escalation",
            f"**Employee ID:** {handoff_request.get('employee_id')}",
            f"**Session ID:** {handoff_request.get('session_id')}",
            f"**Error Category:** {handoff_request.get('error_category')}",
            f"**Severity:** {handoff_request.get('error_severity')}",
            f"**Priority:** {handoff_request.get('handoff_priority')}",
            "",
            "## Issue Summary",
            "Automated onboarding pipeline has encountered an error that requires human intervention.",
            ""
        ]
        
        # Add error context
        if "error_context" in handoff_request:
            lines.extend([
                "## Error Details",
                f"```json",
                json.dumps(handoff_request["error_context"], indent=2),
                "```",
                ""
            ])
        
        # Add recovery attempts
        if "recovery_attempts" in handoff_request:
            lines.extend([
                "## Recovery Attempts",
                f"Previous recovery attempts: {len(handoff_request['recovery_attempts'])}",
                ""
            ])
            
        # Add specialist assignment info
        if specialist_assignment:
            specialist = specialist_assignment.get("assigned_specialist", {})
            lines.extend([
                "## Assignment Information",
                f"**Assigned Specialist:** {specialist.get('name', 'Unknown')}",
                f"**Department:** {specialist.get('department', 'Unknown')}",
                f"**Assignment Reason:** {specialist_assignment.get('assignment_reason', 'Automated routing')}",
                ""
            ])
        
        # Add context package reference
        if context_package:
            lines.extend([
                "## Context Package",
                f"**Package ID:** {context_package.get('package_id')}",
                f"**Completeness:** {context_package.get('package_completeness', 0):.1%}",
                f"**Created:** {context_package.get('created_at')}",
                ""
            ])
        
        lines.extend([
            "## Next Steps",
            "1. Review complete context package",
            "2. Analyze error timeline and recovery attempts", 
            "3. Determine appropriate resolution strategy",
            "4. Execute resolution and update ticket status",
            "",
            "## SLA Requirements",
            f"This ticket must be addressed according to {handoff_request.get('handoff_priority', 'medium')} priority SLA requirements."
        ])
        
        return "\n".join(lines)

    def _calculate_due_date(self, priority: str) -> datetime:
        """Calcular fecha límite basada en prioridad"""
        priority_hours = {
            "emergency": 0.08,  # 5 minutes 
            "critical": 0.25,   # 15 minutes
            "high": 1.0,        # 1 hour
            "medium": 4.0,      # 4 hours
            "low": 24.0         # 24 hours
        }
        
        hours = priority_hours.get(priority, 4.0)
        return datetime.utcnow() + timedelta(hours=hours)

    def _create_initial_comment(self, handoff_request: Dict, 
                               context_package: Dict = None) -> Dict[str, Any]:
        """Crear comentario inicial del ticket"""
        return {
            "comment_id": f"comment_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "author": "human_handoff_agent",
            "timestamp": datetime.utcnow().isoformat(),
            "comment_type": "system_generated",
            "content": f"Ticket created automatically by Human Handoff Agent. "
                      f"Handoff ID: {handoff_request.get('handoff_id')}. "
                      f"Context package available with {context_package.get('package_completeness', 0):.1%} completeness." 
                      if context_package else "Context package not available."
        }

    def _submit_to_ticketing_system(self, ticket: Dict) -> Dict[str, Any]:
        """Enviar ticket al sistema de ticketing (simulado)"""
        # Simulate API call to ticketing system
        try:
            # Simulate network delay
            import time
            time.sleep(0.1)
            
            return {
                "success": True,
                "ticket_id": ticket["ticket_id"],
                "external_id": f"EXT-{ticket['ticket_id']}",
                "submission_timestamp": datetime.utcnow().isoformat(),
                "assigned_queue": ticket["assigned_team"]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "ticket_id": ticket["ticket_id"]
            }

    def _calculate_ticket_sla(self, handoff_request: Dict) -> Dict[str, Any]:
        """Calcular información de SLA del ticket"""
        priority = handoff_request.get("handoff_priority", "medium")
        
        sla_targets = {
            "emergency": {"response_minutes": 5, "resolution_hours": 1},
            "critical": {"response_minutes": 15, "resolution_hours": 4}, 
            "high": {"response_minutes": 60, "resolution_hours": 8},
            "medium": {"response_minutes": 240, "resolution_hours": 24},
            "low": {"response_minutes": 1440, "resolution_hours": 72}
        }
        
        target = sla_targets.get(priority, sla_targets["medium"])
        
        return {
            "priority": priority,
            "response_target_minutes": target["response_minutes"],
            "resolution_target_hours": target["resolution_hours"],
            "created_at": datetime.utcnow().isoformat(),
            "response_due": (datetime.utcnow() + timedelta(minutes=target["response_minutes"])).isoformat(),
            "resolution_due": (datetime.utcnow() + timedelta(hours=target["resolution_hours"])).isoformat()
        }

class NotificationSystemTool(BaseTool):
    """Herramienta para enviar notificaciones a stakeholders"""
    name: str = "notification_system_tool"
    description: str = "Envía notificaciones a stakeholders apropiados via múltiples canales"

    def _run(self, handoff_request: Dict[str, Any],
             specialist_assignment: Dict[str, Any] = None,
             escalation_ticket: Dict[str, Any] = None) -> Dict[str, Any]:
        """Enviar notificaciones"""
        try:
            notifications_sent = []
            
            # Determine recipients
            recipients = self._determine_notification_recipients(
                handoff_request, specialist_assignment
            )
            
            # Send specialist assignment notification
            if specialist_assignment and recipients.get("specialist"):
                specialist_notification = self._send_specialist_notification(
                    handoff_request, specialist_assignment, escalation_ticket
                )
                notifications_sent.append(specialist_notification)
            
            # Send stakeholder notifications
            if recipients.get("stakeholders"):
                for stakeholder in recipients["stakeholders"]:
                    stakeholder_notification = self._send_stakeholder_notification(
                        handoff_request, stakeholder, escalation_ticket
                    )
                    notifications_sent.append(stakeholder_notification)
            
            # Send management notification for high priority
            priority = handoff_request.get("handoff_priority", "medium")
            if priority in ["critical", "emergency"] and recipients.get("management"):
                management_notification = self._send_management_notification(
                    handoff_request, escalation_ticket
                )
                notifications_sent.append(management_notification)
            
            # Count successful notifications
            successful_notifications = len([n for n in notifications_sent if n.get("status") == "sent"])
            failed_notifications = len([n for n in notifications_sent if n.get("status") == "failed"])
            
            return {
                "success": True,
                "notifications_sent": notifications_sent,
                "successful_notifications": successful_notifications,
                "failed_notifications": failed_notifications,
                "total_notifications": len(notifications_sent),
                "notification_summary": self._create_notification_summary(notifications_sent)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error sending notifications: {str(e)}",
                "notifications_sent": [],
                "successful_notifications": 0,
                "failed_notifications": 0
            }

    def _determine_notification_recipients(self, handoff_request: Dict,
                                         specialist_assignment: Dict = None) -> Dict[str, List]:
        """Determinar destinatarios de notificaciones"""
        recipients = {
            "specialist": None,
            "stakeholders": [],
            "management": []
        }
        
        # Primary specialist
        if specialist_assignment:
            recipients["specialist"] = specialist_assignment.get("assigned_specialist")
        
        # Stakeholders based on error category
        error_category = handoff_request.get("error_category", "")
        
        if error_category in ["agent_failure", "system_error"]:
            recipients["stakeholders"].extend([
                {"type": "team", "id": "it_support", "channel": "slack"},
                {"type": "individual", "id": "system_admin", "channel": "email"}
            ])
        
        if error_category in ["quality_failure", "data_validation"]:
            recipients["stakeholders"].extend([
                {"type": "team", "id": "hr_team", "channel": "teams"},
                {"type": "individual", "id": "quality_manager", "channel": "email"}
            ])
        
        # Management for high priority
        priority = handoff_request.get("handoff_priority", "medium")
        if priority in ["critical", "emergency"]:
            recipients["management"].extend([
                {"type": "individual", "id": "operations_manager", "channel": "slack"},
                {"type": "individual", "id": "hr_director", "channel": "email"}
            ])
        
        return recipients

    def _send_specialist_notification(self, handoff_request: Dict,
                                    specialist_assignment: Dict,
                                    escalation_ticket: Dict = None) -> Dict[str, Any]:
        """Enviar notificación al especialista asignado"""
        specialist = specialist_assignment.get("assigned_specialist", {})
        
        # Determine preferred channel
        preferred_channel = self._get_specialist_preferred_channel(specialist)
        
        # Create notification
        notification = {
            "notification_id": f"notify_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "handoff_id": handoff_request.get("handoff_id"),
            "notification_type": "specialist_assignment",
            "channel": preferred_channel,
            "recipient": specialist.get("name", "Unknown"),
            "recipient_type": "specialist"
        }
        
        # Generate message
        subject, message = self._generate_specialist_message(
            handoff_request, specialist, escalation_ticket
        )
        
        notification.update({
            "subject": subject,
            "message": message,
            "priority": handoff_request.get("handoff_priority", "medium")
        })
        
        # Simulate sending
        delivery_result = self._simulate_notification_delivery(notification, specialist)
        notification.update(delivery_result)
        
        return notification

    def _send_stakeholder_notification(self, handoff_request: Dict,
                                     stakeholder: Dict,
                                     escalation_ticket: Dict = None) -> Dict[str, Any]:
        """Enviar notificación a stakeholder"""
        notification = {
            "notification_id": f"notify_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "handoff_id": handoff_request.get("handoff_id"),
            "notification_type": "stakeholder_alert",
            "channel": stakeholder.get("channel", "email"),
            "recipient": stakeholder.get("id", "unknown"),
            "recipient_type": stakeholder.get("type", "individual")
        }
        
        # Generate message
        subject, message = self._generate_stakeholder_message(
            handoff_request, stakeholder, escalation_ticket
        )
        
        notification.update({
            "subject": subject,
            "message": message,
            "priority": handoff_request.get("handoff_priority", "medium")
        })
        
        # Simulate sending
        delivery_result = self._simulate_notification_delivery(notification, stakeholder)
        notification.update(delivery_result)
        
        return notification

    def _send_management_notification(self, handoff_request: Dict,
                                    escalation_ticket: Dict = None) -> Dict[str, Any]:
        """Enviar notificación a management"""
        notification = {
            "notification_id": f"notify_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "handoff_id": handoff_request.get("handoff_id"),
            "notification_type": "management_escalation",
            "channel": "slack",  # High priority via Slack
            "recipient": "operations_manager",
            "recipient_type": "management"
        }
        
        # Generate message
        subject, message = self._generate_management_message(
            handoff_request, escalation_ticket
        )
        
        notification.update({
            "subject": subject,
            "message": message,
            "priority": handoff_request.get("handoff_priority", "critical"),
            "requires_acknowledgment": True
        })
        
        # Simulate sending
        delivery_result = self._simulate_notification_delivery(notification, {"type": "management"})
        notification.update(delivery_result)
        
        return notification

    def _get_specialist_preferred_channel(self, specialist: Dict) -> str:
        """Obtener canal preferido del especialista"""
        if specialist.get("slack_id"):
            return "slack"
        elif specialist.get("teams_id"):
            return "teams"
        else:
            return "email"

    def _generate_specialist_message(self, handoff_request: Dict,
                                   specialist: Dict,
                                   escalation_ticket: Dict = None) -> tuple:
        """Generar mensaje para especialista"""
        employee_id = handoff_request.get("employee_id")
        error_category = handoff_request.get("error_category", "unknown")
        priority = handoff_request.get("handoff_priority", "medium")
        
        subject = f"[{priority.upper()}] Onboarding Issue Assignment - Employee {employee_id}"
        
        message_lines = [
            f"Hi {specialist.get('name', 'there')},",
            "",
            f"You have been assigned a new onboarding escalation case:",
            "",
            f"**Employee ID:** {employee_id}",
            f"**Issue Category:** {error_category.replace('_', ' ').title()}",
            f"**Priority:** {priority.title()}",
            f"**Session ID:** {handoff_request.get('session_id')}",
        ]
        
        if escalation_ticket:
            message_lines.extend([
                "",
                f"**Ticket:** {escalation_ticket.get('ticket_id')}",
                f"**Due Date:** {escalation_ticket.get('due_date')}",
                f"**Ticket URL:** https://tickets.company.com/ticket/{escalation_ticket.get('ticket_id')}"
            ])
        
        message_lines.extend([
            "",
            "**Assignment Reason:** Best match for this type of issue based on your expertise",
            "",
            "Please review the complete context package and ticket details to begin resolution.",
            "",
            "Thank you,",
            "Onboarding System"
        ])
        
        return subject, "\n".join(message_lines)

    def _generate_stakeholder_message(self, handoff_request: Dict,
                                    stakeholder: Dict,
                                    escalation_ticket: Dict = None) -> tuple:
        """Generar mensaje para stakeholder"""
        employee_id = handoff_request.get("employee_id")
        error_category = handoff_request.get("error_category", "unknown")
        priority = handoff_request.get("handoff_priority", "medium")
        
        subject = f"Onboarding Alert - {error_category.replace('_', ' ').title()} Issue"
        
        message_lines = [
            f"Onboarding system alert:",
            "",
            f"An issue has been detected that may require attention from your team.",
            "",
            f"**Employee ID:** {employee_id}",
            f"**Issue Type:** {error_category.replace('_', ' ').title()}",
            f"**Priority:** {priority.title()}",
            f"**Status:** Escalated to specialist",
        ]
        
        if escalation_ticket:
            message_lines.extend([
                "",
                f"**Tracking:** {escalation_ticket.get('ticket_id')}",
                f"**Assigned Team:** {escalation_ticket.get('assigned_team')}"
            ])
        
        message_lines.extend([
            "",
            "This is an automated notification. No immediate action required unless specifically requested.",
            "",
            "Onboarding System"
        ])
        
        return subject, "\n".join(message_lines)

    def _generate_management_message(self, handoff_request: Dict,
                                   escalation_ticket: Dict = None) -> tuple:
        """Generar mensaje para management"""
        employee_id = handoff_request.get("employee_id")
        error_category = handoff_request.get("error_category", "unknown")
        priority = handoff_request.get("handoff_priority", "critical")
        
        subject = f"🚨 {priority.upper()} Onboarding Escalation - {employee_id}"
        
        message_lines = [
            f"**CRITICAL ONBOARDING ESCALATION**",
            "",
            f"A {priority} priority issue requires management attention:",
            "",
            f"📋 **Employee:** {employee_id}",
            f"⚠️ **Issue:** {error_category.replace('_', ' ').title()}",
            f"🕐 **Detected:** {handoff_request.get('created_at', datetime.utcnow().isoformat())}",
            f"🎯 **Priority:** {priority.upper()}",
        ]
        
        if escalation_ticket:
            message_lines.extend([
                "",
                f"🎫 **Ticket:** {escalation_ticket.get('ticket_id')}",
                f"👤 **Assigned:** {escalation_ticket.get('assigned_to')}",
                f"⏰ **Due:** {escalation_ticket.get('due_date')}"
            ])
        
        message_lines.extend([
            "",
            "**Business Impact:** Employee onboarding delayed, potential cascade effects",
            "",
            "Please acknowledge this escalation and provide guidance if needed.",
            "",
            "🤖 Onboarding System"
        ])
        
        return subject, "\n".join(message_lines)

    def _simulate_notification_delivery(self, notification: Dict, 
                                      recipient_info: Dict) -> Dict[str, Any]:
        """Simular envío de notificación"""
        channel = notification.get("channel", "email")
        
        # Simulate different success rates by channel
        success_rates = {
            "slack": 0.95,
            "teams": 0.90,
            "email": 0.85,
            "sms": 0.98
        }
        
        import random
        success_rate = success_rates.get(channel, 0.85)
        delivery_successful = random.random() < success_rate
        
        if delivery_successful:
            return {
                "status": "sent",
                "sent_at": datetime.utcnow().isoformat(),
                "delivered_at": (datetime.utcnow() + timedelta(seconds=random.randint(1, 30))).isoformat(),
                "delivery_attempts": 1
            }
        else:
            return {
                "status": "failed",
                "delivery_attempts": 1,
                "last_attempt_at": datetime.utcnow().isoformat(),
                "error": f"Failed to deliver via {channel}"
            }

    def _create_notification_summary(self, notifications: List[Dict]) -> Dict[str, Any]:
        """Crear resumen de notificaciones"""
        by_channel = {}
        by_status = {}
        by_recipient_type = {}
        
        for notification in notifications:
            # By channel
            channel = notification.get("channel", "unknown")
            by_channel[channel] = by_channel.get(channel, 0) + 1
            
            # By status
            status = notification.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1
            
            # By recipient type
            recipient_type = notification.get("recipient_type", "unknown")
            by_recipient_type[recipient_type] = by_recipient_type.get(recipient_type, 0) + 1
        
        return {
            "total_notifications": len(notifications),
            "by_channel": by_channel,
            "by_status": by_status,
            "by_recipient_type": by_recipient_type,
            "delivery_rate": by_status.get("sent", 0) / len(notifications) if notifications else 0.0
        }

# Export tools
escalation_router_tool = EscalationRouterTool()
context_packager_tool = ContextPackagerTool()
ticket_manager_tool = TicketManagerTool()
notification_system_tool = NotificationSystemTool()