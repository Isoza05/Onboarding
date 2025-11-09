from langchain.tools import tool
from typing import Dict, Any, List
import json
import asyncio
from datetime import datetime
from .it_simulator import ITDepartmentSimulator
from .schemas import ITProvisioningRequest, ITProvisioningResult, SecurityLevel

# Instancia global del simulador IT
it_simulator = ITDepartmentSimulator()

@tool
def it_request_generator_tool(employee_data: Dict[str, Any], equipment_specs: Dict[str, Any] = None, priority: str = "medium") -> Dict[str, Any]:
    """
    Genera solicitudes IT profesionales formateadas para el departamento IT.
    Convierte datos del empleado en requests estructurados.
    
    Args:
        employee_data: Datos del empleado del Data Aggregator
        equipment_specs: Especificaciones de equipamiento opcional
        priority: Prioridad de la solicitud (low, medium, high)
    """
    try:
        if not employee_data:
            return {"success": False, "error": "No employee data provided"}
        
        if equipment_specs is None:
            equipment_specs = {}
            
        # Extraer información clave
        employee_id = employee_data.get("employee_id", "")
        first_name = employee_data.get("first_name", "")
        last_name = employee_data.get("last_name", "")
        position = employee_data.get("position", "")
        department = employee_data.get("department", "IT")
        office = employee_data.get("office", "Main Office")
        start_date = employee_data.get("start_date", "")
        
        # Determinar nivel de seguridad basado en posición
        security_level = SecurityLevel.BASIC
        position_lower = position.lower()
        if "senior" in position_lower or "lead" in position_lower:
            security_level = SecurityLevel.STANDARD
        elif "manager" in position_lower or "director" in position_lower:
            security_level = SecurityLevel.ELEVATED
        elif "executive" in position_lower or "ceo" in position_lower:
            security_level = SecurityLevel.EXECUTIVE
            
        # Determinar requisitos de equipamiento
        equipment_requirements = {
            "laptop_required": True,
            "monitor_required": "engineer" in position_lower or "developer" in position_lower,
            "mobile_device": "manager" in position_lower or "executive" in position_lower,
            "specialized_software": []
        }
        
        if "data" in position_lower:
            equipment_requirements["specialized_software"].extend([
                "SQL Server Management Studio", "Power BI", "Python", "R Studio"
            ])
        elif "developer" in position_lower or "engineer" in position_lower:
            equipment_requirements["specialized_software"].extend([
                "Visual Studio", "Git", "Docker", "Postman"
            ])
            
        # Generar request formal
        it_request = {
            "request_type": "NEW_HIRE_PROVISIONING",
            "priority": priority.upper(),
            "employee_details": {
                "employee_id": employee_id,
                "full_name": f"{first_name} {last_name}",
                "position": position,
                "department": department,
                "office_location": office,
                "start_date": start_date,
                "security_clearance_required": security_level.value
            },
            "access_requirements": {
                "domain_access": True,
                "email_account": True,
                "vpn_access": security_level in [SecurityLevel.STANDARD, SecurityLevel.ELEVATED, SecurityLevel.EXECUTIVE],
                "remote_access": security_level in [SecurityLevel.ELEVATED, SecurityLevel.EXECUTIVE],
                "shared_drives": True,
                "application_access": [
                    "Office 365", "Teams", "SharePoint", "Time Tracking"
                ]
            },
            "equipment_requirements": equipment_requirements,
            "security_requirements": {
                "badge_access": True,
                "parking_permit": security_level in [SecurityLevel.ELEVATED, SecurityLevel.EXECUTIVE],
                "two_factor_auth": security_level in [SecurityLevel.ELEVATED, SecurityLevel.EXECUTIVE],
                "security_training": True
            },
            "deadline": "Before start date",
            "special_instructions": equipment_specs.get("special_instructions", []),
            "requested_by": "HR Onboarding System",
            "approval_required": security_level == SecurityLevel.EXECUTIVE
        }
        
        return {
            "success": True,
            "it_request": it_request,
            "request_summary": {
                "employee": f"{first_name} {last_name} ({employee_id})",
                "position": position,
                "security_level": security_level.value,
                "equipment_items": sum([
                    1,  # laptop
                    1 if equipment_requirements["monitor_required"] else 0,
                    1 if equipment_requirements["mobile_device"] else 0,
                    len(equipment_requirements["specialized_software"])
                ]),
                "access_level": "Standard" if security_level == SecurityLevel.STANDARD else security_level.value.title()
            },
            "processing_notes": [
                f"New hire provisioning for {position}",
                f"Security level: {security_level.value}",
                f"Office location: {office}",
                f"Start date: {start_date}"
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error generating IT request: {str(e)}",
            "it_request": {},
            "request_summary": {}
        }

@tool
def email_communicator_tool(it_request: Dict[str, Any], communication_type: str = "send_request") -> Dict[str, Any]:
    """
    Simula comunicación por email con el departamento IT.
    Envía requests y recibe respuestas de manera asíncrona.
    
    Args:
        it_request: Solicitud IT generada por it_request_generator_tool
        communication_type: Tipo de comunicación (send_request, check_response)
    """
    try:
        if not it_request:
            return {"success": False, "error": "No IT request provided"}
            
        # Simular envío de email
        if communication_type == "send_request":
            # Formatear email profesional
            employee_details = it_request.get("employee_details", {})
            full_name = employee_details.get("full_name", "Unknown Employee")
            position = employee_details.get("position", "Unknown Position")
            employee_id = employee_details.get("employee_id", "Unknown ID")
            
            email_content = {
                "to": "it-provisioning@company.com",
                "from": "hr-onboarding@company.com",
                "subject": f"New Hire IT Provisioning Request - {full_name} ({employee_id})",
                "body": f"""
Dear IT Provisioning Team,

We have a new hire requiring IT setup and provisioning:

EMPLOYEE INFORMATION:
- Name: {full_name}
- Employee ID: {employee_id}
- Position: {position}
- Department: {employee_details.get('department', 'N/A')}
- Office: {employee_details.get('office_location', 'N/A')}
- Start Date: {employee_details.get('start_date', 'N/A')}

REQUIREMENTS:
- Security Level: {employee_details.get('security_clearance_required', 'standard')}
- Equipment: {json.dumps(it_request.get('equipment_requirements', {}), indent=2)}
- Access: {json.dumps(it_request.get('access_requirements', {}), indent=2)}
- Security: {json.dumps(it_request.get('security_requirements', {}), indent=2)}

PRIORITY: {it_request.get('priority', 'MEDIUM')}
DEADLINE: {it_request.get('deadline', 'Before start date')}

Please process this request and provide confirmation once completed.

Best regards,
HR Onboarding System
                """,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "sent"
            }
            
            return {
                "success": True,
                "communication_type": "email_sent",
                "email_details": email_content,
                "expected_response_time": "2-8 minutes (simulated)",
                "tracking_id": f"EMAIL-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}-{employee_id}",
                "next_step": "wait_for_response"
            }
            
        elif communication_type == "check_response":
            return {
                "success": True,
                "communication_type": "response_check",
                "has_response": True,
                "response_status": "processing",
                "estimated_completion": "Processing in IT queue"
            }
            
        else:
            return {
                "success": False,
                "error": f"Unknown communication type: {communication_type}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error in email communication: {str(e)}",
            "communication_type": "error"
        }

@tool
def credential_processor_tool(it_response: Dict[str, Any], employee_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Procesa respuestas del departamento IT y extrae credenciales.
    Parsea y valida credenciales recibidas del simulador IT.
    
    Args:
        it_response: Respuesta del departamento IT (del simulador)
        employee_data: Datos del empleado para contexto adicional
    """
    try:
        if not it_response:
            return {"success": False, "error": "No IT response provided"}
        
        if employee_data is None:
            employee_data = {}
            
        # Procesar credenciales
        credentials_data = it_response.get("credentials", {})
        if not credentials_data:
            return {"success": False, "error": "No credentials found in IT response"}
            
        # Validar credenciales recibidas
        required_fields = ["username", "email", "temporary_password", "domain_access"]
        missing_fields = []
        
        for field in required_fields:
            if not credentials_data.get(field):
                missing_fields.append(field)
                
        if missing_fields:
            return {
                "success": False,
                "error": f"Missing credential fields: {', '.join(missing_fields)}",
                "missing_fields": missing_fields
            }
            
        # Procesar y formatear credenciales
        processed_credentials = {
            "username": credentials_data.get("username"),
            "email": credentials_data.get("email"),
            "temporary_password": credentials_data.get("temporary_password"),
            "domain_access": credentials_data.get("domain_access"),
            "vpn_credentials": credentials_data.get("vpn_credentials"),
            "badge_access": credentials_data.get("badge_access"),
            "employee_id": credentials_data.get("employee_id", employee_data.get("employee_id")),
            "created_at": credentials_data.get("created_at", datetime.utcnow().isoformat()),
            "expires_at": credentials_data.get("expires_at"),
            "must_change_password": credentials_data.get("must_change_password", True),
            "status": "active",
            "validation_status": "verified"
        }
        
        # Validar formato de credenciales
        validation_results = {
            "username_valid": bool(processed_credentials["username"] and "@" not in processed_credentials["username"]),
            "email_valid": bool(processed_credentials["email"] and "@" in processed_credentials["email"]),
            "password_complex": len(processed_credentials["temporary_password"]) >= 8,
            "domain_format": bool(processed_credentials["domain_access"] and "\\" in processed_credentials["domain_access"]),
            "expiration_set": bool(processed_credentials["expires_at"])
        }
        
        validation_score = (sum(validation_results.values()) / len(validation_results)) * 100
        
        return {
            "success": True,
            "processed_credentials": processed_credentials,
            "validation_results": validation_results,
            "validation_score": validation_score,
            "credentials_ready": validation_score >= 80.0,
            "processing_notes": [
                f"Credentials processed for {processed_credentials['username']}",
                f"Email configured: {processed_credentials['email']}",
                f"Domain access: {processed_credentials['domain_access']}",
                f"VPN access: {'Yes' if processed_credentials['vpn_credentials'] else 'No'}",
                f"Badge access: {'Yes' if processed_credentials['badge_access'] else 'No'}"
            ],
            "security_notes": [
                "Temporary password must be changed on first login",
                "VPN credentials provided for remote access",
                "Badge access configured for office entry",
                "Account expires in 90 days if not activated"
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error processing credentials: {str(e)}",
            "processed_credentials": {},
            "validation_score": 0.0
        }

@tool
def assignment_manager_tool(processed_credentials: Dict[str, Any], equipment_assignment: Dict[str, Any] = None, 
                          access_permissions: Dict[str, Any] = None, security_setup: Dict[str, Any] = None,
                          employee_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Asigna credenciales y equipamiento al empleado en el sistema.
    Gestiona la asignación final y genera reportes de completitud.
    
    Args:
        processed_credentials: Credenciales procesadas
        equipment_assignment: Equipamiento asignado
        access_permissions: Permisos de acceso
        security_setup: Configuración de seguridad
        employee_data: Datos del empleado
    """
    try:
        if not processed_credentials:
            return {"success": False, "error": "No processed credentials provided"}
        
        if equipment_assignment is None:
            equipment_assignment = {}
        if access_permissions is None:
            access_permissions = {}
        if security_setup is None:
            security_setup = {}  
        if employee_data is None:
            employee_data = {}
            
        employee_id = employee_data.get("employee_id", processed_credentials.get("employee_id", ""))
        
        # Crear perfil completo del empleado
        employee_profile = {
            "employee_id": employee_id,
            "personal_info": {
                "full_name": f"{employee_data.get('first_name', '')} {employee_data.get('last_name', '')}",
                "email": processed_credentials.get("email", ""),
                "position": employee_data.get("position", ""),
                "department": employee_data.get("department", ""),
                "office": employee_data.get("office", ""),
                "start_date": employee_data.get("start_date", "")
            },
            "it_credentials": processed_credentials,
            "equipment_assigned": equipment_assignment,
            "access_permissions": access_permissions,
            "security_configuration": security_setup,
            "assignment_timestamp": datetime.utcnow().isoformat(),
            "status": "assigned"
        }
        
        # Calcular métricas de completitud
        completion_metrics = {
            "credentials_assigned": bool(processed_credentials.get("username")),
            "equipment_assigned": bool(equipment_assignment.get("laptop")),
            "access_configured": bool(access_permissions.get("systems")),
            "security_setup": bool(security_setup.get("badge_access")),
            "email_ready": bool(processed_credentials.get("email")),
            "domain_access": bool(processed_credentials.get("domain_access"))
        }
        
        completion_score = (sum(completion_metrics.values()) / len(completion_metrics)) * 100
        
        # Generar lista de activos asignados
        assigned_assets = []
        
        # Credenciales
        if processed_credentials:
            assigned_assets.extend([
                f"Username: {processed_credentials.get('username', 'N/A')}",
                f"Email: {processed_credentials.get('email', 'N/A')}",
                f"Domain Access: {processed_credentials.get('domain_access', 'N/A')}"
            ])
            
        # Equipamiento
        if equipment_assignment:
            laptop = equipment_assignment.get("laptop", {})
            if laptop:
                assigned_assets.append(f"Laptop: {laptop.get('model', 'Unknown')} ({laptop.get('serial', 'No Serial')})")
                
            monitor = equipment_assignment.get("monitor", {})
            if monitor:
                assigned_assets.append(f"Monitor: {monitor.get('size', 'Unknown')} ({monitor.get('serial', 'No Serial')})")
                
            peripherals = equipment_assignment.get("peripherals", [])
            for peripheral in peripherals:
                assigned_assets.append(f"Peripheral: {peripheral.get('model', 'Unknown')} ({peripheral.get('serial', 'No Serial')})")
                
        # Verificar si está listo para siguiente fase
        ready_for_contract = completion_score >= 80.0 and processed_credentials.get("email")
        
        # Próximas acciones
        next_actions = []
        if ready_for_contract:
            next_actions.extend([
                "Proceed to Contract Management Agent",
                "Generate employment contract with IT credentials",
                "Schedule IT orientation session",
                "Prepare welcome email with login instructions"
            ])
        else:
            next_actions.extend([
                "Complete missing IT assignments",
                "Verify credential processing",
                "Resolve equipment allocation issues"
            ])
            
        return {
            "success": True,
            "employee_profile": employee_profile,
            "completion_metrics": completion_metrics,
            "completion_score": completion_score,
            "assigned_assets": assigned_assets,
            "assets_count": len(assigned_assets),
            "ready_for_contract": ready_for_contract,
            "next_actions": next_actions,
            "assignment_summary": {
                "employee_id": employee_id,
                "credentials_ready": completion_metrics["credentials_assigned"],
                "equipment_ready": completion_metrics["equipment_assigned"],
                "access_ready": completion_metrics["access_configured"],
                "security_ready": completion_metrics["security_setup"],
                "overall_completion": f"{completion_score:.1f}%"
            },
            "integration_data": {
                "username": processed_credentials.get("username"),
                "email": processed_credentials.get("email"),
                "equipment_serial_numbers": [
                    equipment_assignment.get("laptop", {}).get("serial", ""),
                    equipment_assignment.get("monitor", {}).get("serial", "") if equipment_assignment.get("monitor") else ""
                ],
                "access_level": security_setup.get("security_clearance", "basic") if security_setup else "basic"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error in assignment management: {str(e)}",
            "employee_profile": {},
            "completion_score": 0.0,
            "ready_for_contract": False
        }