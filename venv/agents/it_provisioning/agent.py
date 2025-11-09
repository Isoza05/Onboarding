from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from agents.base.base_agent import BaseAgent
from datetime import datetime
import json
import asyncio

# Imports del IT provisioning
from .tools import (
    it_request_generator_tool, email_communicator_tool,
    credential_processor_tool, assignment_manager_tool
)
from .schemas import (
    ITProvisioningRequest, ITProvisioningResult, ITCredentials,
    EquipmentAssignment, AccessPermissions, SecuritySetup, SecurityLevel
)
from .it_simulator import ITDepartmentSimulator

# Imports para integración
from core.state_management.state_manager import state_manager
from core.state_management.models import AgentStateStatus, OnboardingPhase
from core.observability import observability_manager
from core.database import db_manager

class ITProvisioningAgent(BaseAgent):
    """
    IT Provisioning Agent - Gestiona provisioning completo de IT para nuevos empleados.
    
    Implementa arquitectura BDI:
    - Beliefs: Las credenciales y equipamiento deben estar listos antes del primer día
    - Desires: Provisioning completo, seguro y eficiente para todos los nuevos empleados
    - Intentions: Generar requests IT, procesar credenciales, asignar equipamiento
    
    Recibe: Datos consolidados del Data Aggregator Agent
    Produce: Credenciales IT, equipamiento asignado, configuración de seguridad
    """
    
    def __init__(self):
        super().__init__(
            agent_id="it_provisioning_agent",
            agent_name="IT Provisioning & Systems Integration Agent"
        )
        
        # Inicializar simulador IT
        self.it_simulator = ITDepartmentSimulator()
        self.active_provisions = {}
        
        # Registrar agente en state management
        state_manager.register_agent(
            self.agent_id,
            {
                "version": "1.0",
                "specialization": "it_provisioning_credential_management",
                "tools_count": len(self.tools),
                "capabilities": {
                    "credential_generation": True,
                    "equipment_allocation": True,
                    "access_management": True,
                    "security_configuration": True,
                    "it_communication": True
                },
                "security_levels": [level.value for level in SecurityLevel],
                "equipment_types": ["laptop", "monitor", "peripherals", "mobile"],
                "integration_points": ["it_department_simulator", "common_state", "contract_agent"]
            }
        )
        
        self.logger.info("IT Provisioning Agent integrado con State Management y IT Simulator")

    def _initialize_tools(self) -> List:
        """Inicializar herramientas de IT provisioning"""
        return [
            it_request_generator_tool,
            email_communicator_tool, 
            credential_processor_tool,
            assignment_manager_tool
        ]

    def _create_prompt(self) -> ChatPromptTemplate:
        """Crear prompt con framework BDI y patrón ReAct para IT provisioning"""
        bdi = self._get_bdi_framework()
        
        system_prompt = f"""
Eres el IT Provisioning & Systems Integration Agent, especialista en provisioning IT y gestión de credenciales.

## FRAMEWORK BDI (Belief-Desire-Intention)
**BELIEFS (Creencias):**
{bdi['beliefs']}

**DESIRES (Deseos):**
{bdi['desires']}

**INTENTIONS (Intenciones):**
{bdi['intentions']}

## HERRAMIENTAS DE IT PROVISIONING:
- it_request_generator_tool: Genera solicitudes IT profesionales formateadas
- email_communicator_tool: Simula comunicación asíncrona con departamento IT
- credential_processor_tool: Procesa respuestas IT y extrae credenciales
- assignment_manager_tool: Asigna credenciales y equipamiento al empleado

## DATOS DE ENTRADA (Data Aggregator Output):
1. **Personal Data**: Employee ID, nombres, email, información básica
2. **Position Data**: Posición, departamento, oficina, nivel de seguridad
3. **Contractual Data**: Fecha de inicio, tipo de empleo, requisitos especiales

## DATOS DE SALIDA (Para Contract Management Agent):
1. **IT Credentials**: Username, email corporativo, credenciales de acceso
2. **Equipment Assignment**: Laptop, monitor, periféricos, software
3. **Access Permissions**: Sistemas, aplicaciones, drives de red
4. **Security Configuration**: Badge access, VPN, nivel de seguridad

## PROCESO DE PROVISIONING:
1. **Análisis de Requisitos**: Determinar nivel de seguridad y equipamiento basado en posición
2. **Generación de Request**: Crear solicitud IT formal y profesional
3. **Comunicación IT**: Enviar request al departamento IT (simulado)
4. **Procesamiento de Respuesta**: Parsear credenciales y configuraciones recibidas
5. **Asignación Final**: Asignar todo al empleado y verificar completitud

## NIVELES DE SEGURIDAD:
- **BASIC**: Empleados estándar, acceso básico a sistemas
- **STANDARD**: Profesionales senior, acceso a herramientas de desarrollo
- **ELEVATED**: Managers/Directors, acceso administrativo limitado
- **EXECUTIVE**: C-Level, acceso completo a sistemas críticos

## REQUISITOS DE EQUIPAMIENTO POR ROL:
- **Engineers/Developers**: Laptop potente, monitor dual, software especializado
- **Managers**: Laptop business, mobile device, acceso remoto
- **Executives**: MacBook Pro, acceso VIP, dispositivos premium
- **Standard**: Laptop básico, periféricos estándar

## PATRÓN REACT (Reason-Act-Observe):
**1. REASON (Razonar):**
- Analizar datos del empleado para determinar requisitos IT
- Evaluar nivel de seguridad basado en posición y departamento
- Identificar equipamiento necesario según rol y ubicación
- Planificar timeline de provisioning según fecha de inicio

**2. ACT (Actuar):**
- Generar request IT profesional con it_request_generator_tool
- Enviar comunicación formal con email_communicator_tool
- Procesar respuesta del departamento IT con credential_processor_tool
- Asignar credenciales y equipamiento con assignment_manager_tool

**3. OBSERVE (Observar):**
- Verificar que credenciales estén correctamente configuradas
- Confirmar que equipamiento esté asignado y disponible
- Validar que permisos de acceso sean apropiados para el rol
- Asegurar que configuración de seguridad cumple políticas

## CRITERIOS DE ÉXITO:
- **Credenciales IT**: Username, email, password temporal, acceso al dominio
- **Equipamiento**: Laptop asignado, periféricos, software instalado
- **Acceso**: Permisos configurados, VPN habilitado, drives mapeados
- **Seguridad**: Badge access, 2FA si requerido, training programado
- **Completitud**: >90% para proceder a Contract Management

## ESCALACIÓN:
- Nivel de seguridad EXECUTIVE: Requiere aprobación manual
- Equipamiento especializado: Verificar disponibilidad en inventario
- Conflictos de acceso: Escalar a IT Security team
- Delays en provisioning: Notificar a HR y hiring manager

## INSTRUCCIONES CRÍTICAS:
1. SIEMPRE genera request IT profesional antes de procesar
2. Simula comunicación realista con delays apropiados
3. Valida todas las credenciales antes de asignar
4. Verifica completitud antes de marcar como ready
5. Actualiza Common State con todos los resultados
6. Prepara datos específicos para Contract Management Agent

Procesa con precisión técnica, comunica profesionalmente, y provisiona con excelencia operativa.
"""
        
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}"),
            ("assistant", "Voy a procesar el provisioning IT completo para el nuevo empleado."),
            ("placeholder", "{agent_scratchpad}")
        ])

    def _get_bdi_framework(self) -> Dict[str, str]:
        """Framework BDI específico para IT provisioning"""
        return {
            "beliefs": """
• Las credenciales IT deben estar listas antes del primer día del empleado
• El equipamiento apropiado es crítico para la productividad desde día uno
• Los permisos de acceso deben ser exactos: ni más ni menos de lo necesario
• La comunicación con IT debe ser formal, clara y documentada
• Los delays en provisioning IT causan delays en todo el onboarding
• La seguridad debe ser balanceada con la funcionalidad operativa
""",
            "desires": """
• Provisioning IT completo y funcional para todos los nuevos empleados
• Credenciales seguras y fáciles de usar para el empleado
• Equipamiento de calidad apropiado para cada rol y departamento
• Permisos de acceso precisos que permitan productividad inmediata
• Comunicación eficiente y profesional con el departamento IT
• Integración perfecta con el siguiente paso del onboarding
""",
            "intentions": """
• Generar requests IT profesionales y detallados
• Coordinar con el departamento IT para provisioning eficiente
• Procesar y validar todas las credenciales recibidas
• Asignar equipamiento apropiado basado en rol y ubicación
• Configurar permisos de acceso según nivel de seguridad requerido  
• Preparar datos completos para Contract Management Agent
"""
        }

    def _format_input(self, input_data: Any) -> str:
        """Formatear datos de entrada para IT provisioning"""
        if isinstance(input_data, ITProvisioningRequest):
            personal_data = input_data.personal_data
            position_data = input_data.position_data
            
            return f"""
Procesa provisioning IT para el siguiente empleado:

**IDENTIFICACIÓN:**
- Employee ID: {input_data.employee_id}
- Session ID: {input_data.session_id}
- Prioridad: {input_data.priority.value}
- Nivel de seguridad requerido: {input_data.security_level.value}

**DATOS PERSONALES:**
- Nombre: {personal_data.get('first_name', '')} {personal_data.get('last_name', '')}
- Email: {personal_data.get('email', 'N/A')}
- Cédula: {personal_data.get('id_card', 'N/A')}
- Teléfono: {personal_data.get('phone', 'N/A')}

**DATOS DE POSICIÓN:**
- Posición: {position_data.get('position', 'N/A')}
- Departamento: {position_data.get('department', 'N/A')}
- Oficina: {position_data.get('office', 'N/A')}
- Project Manager: {position_data.get('project_manager', 'N/A')}
- Tecnologías: {position_data.get('technology', 'N/A')}

**DATOS CONTRACTUALES:**
- Fecha de inicio: {input_data.contractual_data.get('start_date', 'N/A')}
- Tipo de empleo: {input_data.contractual_data.get('employment_type', 'N/A')}
- Modalidad de trabajo: {input_data.contractual_data.get('work_modality', 'N/A')}

**ESPECIFICACIONES IT:**
- Equipamiento especial: {json.dumps(input_data.equipment_specs, indent=2) if input_data.equipment_specs else 'Estándar'}
- Requisitos especiales: {', '.join(input_data.special_requirements) if input_data.special_requirements else 'Ninguno'}

**INSTRUCCIONES DE PROCESAMIENTO:**
1. Usa it_request_generator_tool para crear solicitud IT formal
2. Usa email_communicator_tool para enviar request al departamento IT
3. Usa credential_processor_tool para procesar respuesta y credenciales
4. Usa assignment_manager_tool para asignación final y verificación

**OBJETIVO:** Generar provisioning IT completo listo para Contract Management Agent.
"""
        elif isinstance(input_data, dict):
            return f"""
Procesa provisioning IT para los siguientes datos:
{json.dumps(input_data, indent=2, default=str)}

Ejecuta proceso completo: request generation → IT communication → credential processing → assignment.
"""
        else:
            return str(input_data)

    def _format_output(self, result: Any, processing_time: float, success: bool, error: str = None) -> Dict[str, Any]:
        """Formatear salida de IT provisioning"""
        if not success:
            return {
                "success": False,
                "message": f"Error en IT provisioning: {error}",
                "errors": [error] if error else [],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "provisioning_status": "failed",
                "credentials_created": 0,
                "equipment_assigned": 0,
                "ready_for_contract": False,
                "next_actions": ["Revisar errores de provisioning", "Verificar conectividad con IT"]
            }

        try:
            # Extraer resultados de herramientas
            it_request_result = None
            communication_result = None
            credential_result = None
            assignment_result = None
            
            if isinstance(result, dict) and "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    if isinstance(step, tuple) and len(step) >= 2:
                        tool_name = step[0]
                        tool_result = step[1]
                        

                        if "it_request_generator_tool" in str(tool_name):
                            it_request_result = tool_result
                        elif "email_communicator_tool" in str(tool_name):
                            communication_result = tool_result
                        elif "credential_processor_tool" in str(tool_name):
                            credential_result = tool_result
                        elif "assignment_manager_tool" in str(tool_name):
                            assignment_result = tool_result

            # Calcular métricas de éxito
            credentials_created = 0
            equipment_assigned = 0
            permissions_granted = 0
            security_configured = False
            
            if credential_result and credential_result.get("success"):
                credentials_created = len(credential_result.get("processed_credentials", {}))
                
            if assignment_result and assignment_result.get("success"):
                completion_metrics = assignment_result.get("completion_metrics", {})
                equipment_assigned = 1 if completion_metrics.get("equipment_assigned") else 0
                permissions_granted = 1 if completion_metrics.get("access_configured") else 0
                security_configured = completion_metrics.get("security_setup", False)

            # Determinar si está listo para contrato
            ready_for_contract = (
                assignment_result and 
                assignment_result.get("ready_for_contract", False) and
                assignment_result.get("completion_score", 0) >= 80.0
            )

            # Extraer próximas acciones
            next_actions = []
            if assignment_result:
                next_actions.extend(assignment_result.get("next_actions", []))
            elif ready_for_contract:
                next_actions.extend([
                    "Proceder a Contract Management Agent",
                    "Incluir credenciales IT en contrato",
                    "Programar sesión de orientación IT"
                ])

            # Extraer datos para Contract Agent
            it_credentials = None
            equipment_details = None
            
            if credential_result and credential_result.get("success"):
                it_credentials = credential_result.get("processed_credentials", {})
                
            if assignment_result and assignment_result.get("success"):
                employee_profile = assignment_result.get("employee_profile", {})
                equipment_details = employee_profile.get("equipment_assigned", {})

            return {
                "success": True,
                "message": "IT provisioning completado exitosamente",
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "provisioning_status": "completed",
                
                # Métricas de provisioning
                "credentials_created": credentials_created,
                "equipment_assigned": equipment_assigned,
                "permissions_granted": permissions_granted,
                "security_configured": security_configured,
                
                # Datos para Contract Management Agent
                "it_credentials": it_credentials,
                "equipment_assignment": equipment_details,
                "provisioning_completion_score": assignment_result.get("completion_score", 0) if assignment_result else 0,
                
                # Estado y control
                "ready_for_contract": ready_for_contract,
                "requires_manual_review": assignment_result.get("requires_manual_review", False) if assignment_result else False,
                "next_actions": next_actions,
                
                # Resultados detallados por herramienta
                "provisioning_details": {
                    "it_request": it_request_result,
                    "communication": communication_result,
                    "credential_processing": credential_result,
                    "assignment": assignment_result
                },
                
                # Resumen ejecutivo
                "provisioning_summary": {
                    "employee_ready": ready_for_contract,
                    "credentials_status": "Ready" if credentials_created > 0 else "Pending",
                    "equipment_status": "Assigned" if equipment_assigned > 0 else "Pending",
                    "security_status": "Configured" if security_configured else "Pending",
                    "overall_completion": f"{assignment_result.get('completion_score', 0):.1f}%" if assignment_result else "0%"
                }
            }

        except Exception as e:
            self.logger.error(f"Error formateando salida de IT provisioning: {e}")
            return {
                "success": False,
                "message": f"Error procesando resultados de IT provisioning: {e}",
                "errors": [str(e)],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "provisioning_status": "error"
            }

    @observability_manager.trace_agent_execution("it_provisioning_agent")
    def provision_it_services(self, provisioning_request: ITProvisioningRequest, session_id: str = None) -> Dict[str, Any]:
        """Ejecutar provisioning IT completo con integración a Common State"""
        
        # Generar provision_id
        provision_id = f"it_prov_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{provisioning_request.employee_id}"
        
        # Actualizar estado del agente: PROCESSING
        state_manager.update_agent_state(
            self.agent_id,
            AgentStateStatus.PROCESSING,
            {
                "current_task": "it_provisioning", 
                "provision_id": provision_id,
                "employee_id": provisioning_request.employee_id,
                "security_level": provisioning_request.security_level.value,
                "priority": provisioning_request.priority.value,
                "started_at": datetime.utcnow().isoformat()
            },
            session_id
        )

        # Registrar métricas iniciales
        observability_manager.log_agent_metrics(
            self.agent_id,
            {
                "security_level": provisioning_request.security_level.value,
                "priority": provisioning_request.priority.value,
                "equipment_specs_count": len(provisioning_request.equipment_specs),
                "special_requirements": len(provisioning_request.special_requirements),
                "request_type": provisioning_request.request_type.value
            },
            session_id
        )

        try:
            # Procesar con el método base
            result = self.process_request(provisioning_request, session_id)

            # Si fue exitoso, actualizar State Management
            if result["success"]:
                # Actualizar datos del empleado con información IT
                if session_id:
                    it_data = {
                        "it_provisioning_completed": True,
                        "provision_id": provision_id,
                        "it_credentials": result.get("it_credentials", {}),
                        "equipment_assignment": result.get("equipment_assignment", {}),
                        "provisioning_score": result.get("provisioning_completion_score", 0),
                        "ready_for_contract": result.get("ready_for_contract", False),
                        "next_phase": "contract_management"
                    }
                    
                    state_manager.update_employee_data(
                        session_id,
                        it_data,
                        "processed"
                    )

                # Actualizar estado del agente: COMPLETED
                state_manager.update_agent_state(
                    self.agent_id,
                    AgentStateStatus.COMPLETED,
                    {
                        "current_task": "completed",
                        "provision_id": provision_id,
                        "credentials_created": result.get("credentials_created", 0),
                        "equipment_assigned": result.get("equipment_assigned", 0),
                        "provisioning_score": result.get("provisioning_completion_score", 0),
                        "ready_for_contract": result.get("ready_for_contract", False),
                        "completed_at": datetime.utcnow().isoformat()
                    },
                    session_id
                )

                # Registrar en provisiones activas
                self.active_provisions[provision_id] = {
                    "status": "completed",
                    "result": result,
                    "completed_at": datetime.utcnow()
                }

            else:
                # Error en provisioning
                state_manager.update_agent_state(
                    self.agent_id,
                    AgentStateStatus.ERROR,
                    {
                        "current_task": "error",
                        "provision_id": provision_id,
                        "errors": result.get("errors", []),
                        "failed_at": datetime.utcnow().isoformat()
                    },
                    session_id
                )

            # Agregar información de sesión al resultado
            result["provision_id"] = provision_id
            result["session_id"] = session_id
            return result

        except Exception as e:
            # Error durante provisioning
            error_msg = f"Error ejecutando IT provisioning: {str(e)}"
            state_manager.update_agent_state(
                self.agent_id,
                AgentStateStatus.ERROR,
                {
                    "current_task": "error",
                    "provision_id": provision_id,
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
                "provision_id": provision_id,
                "session_id": session_id,
                "agent_id": self.agent_id,
                "processing_time": 0,
                "provisioning_status": "failed"
            }

    def _process_with_tools_directly(self, input_data: Any) -> Dict[str, Any]:
        """Procesar usando herramientas directamente con flujo específico de IT provisioning"""
        results = []
        formatted_input = self._format_input(input_data)
        self.logger.info(f"Procesando IT provisioning con {len(self.tools)} herramientas especializadas")

        # Variables para almacenar resultados
        it_request_result = None
        communication_result = None  
        credential_result = None
        assignment_result = None

        # Preparar datos según tipo de entrada
        if isinstance(input_data, ITProvisioningRequest):
            employee_data = {
                **input_data.personal_data,
                **input_data.position_data,
                "employee_id": input_data.employee_id,
                "security_level": input_data.security_level.value
            }
            equipment_specs = input_data.equipment_specs
            priority = input_data.priority.value
        else:
            # Fallback para datos genéricos
            employee_data = input_data.get("employee_data", {}) if isinstance(input_data, dict) else {}
            equipment_specs = input_data.get("equipment_specs", {}) if isinstance(input_data, dict) else {}
            priority = "medium"

        # Ejecutar herramientas en secuencia
        for tool in self.tools:
            try:
                self.logger.info(f"Ejecutando herramienta: {tool.name}")
                
                if tool.name == "it_request_generator_tool":
                    result = tool.invoke({
                        "employee_data": employee_data,
                        "equipment_specs": equipment_specs,
                        "priority": priority
                    })
                    it_request_result = result
                    
                elif tool.name == "email_communicator_tool":
                    if it_request_result and it_request_result.get("success"):
                        # Simular envío de email
                        result = tool.invoke({
                            "it_request": it_request_result.get("it_request", {}),
                            "type": "send_request"
                        })
                        communication_result = result
                    else:
                        result = {"success": False, "error": "No IT request available for communication"}
                        
                elif tool.name == "credential_processor_tool":
                    if communication_result and communication_result.get("success"):
                        # Simular procesamiento con IT simulator
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            it_response = loop.run_until_complete(
                                self.it_simulator.process_it_request(employee_data, equipment_specs)
                            )
                            loop.close()
                            
                            result = tool.invoke({
                                "it_response": it_response.dict(),
                                "employee_data": employee_data
                            })
                            credential_result = result
                        except Exception as e:
                            result = {"success": False, "error": f"Error with IT simulator: {str(e)}"}
                    else:
                        result = {"success": False, "error": "No communication result available"}
                        
                elif tool.name == "assignment_manager_tool":
                    if credential_result and credential_result.get("success"):
                        # Obtener datos del simulador para assignment
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            it_response = loop.run_until_complete(
                                self.it_simulator.process_it_request(employee_data, equipment_specs)
                            )
                            loop.close()
                            
                            result = tool.invoke({
                                "processed_credentials": credential_result.get("processed_credentials", {}),
                                "equipment_assignment": it_response.equipment.dict(),
                                "access_permissions": it_response.access_permissions.dict(),
                                "security_setup": it_response.security_setup.dict(),
                                "employee_data": employee_data
                            })
                            assignment_result = result
                        except Exception as e:
                            result = {"success": False, "error": f"Error in assignment: {str(e)}"}
                    else:
                        result = {"success": False, "error": "No processed credentials available"}
                        
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
        overall_success = successful_tools >= 3  # Al menos 3 herramientas exitosas

        return {
            "output": "Procesamiento de IT provisioning completado",
            "intermediate_steps": results,
            "it_request_result": it_request_result,
            "communication_result": communication_result,
            "credential_result": credential_result,
            "assignment_result": assignment_result,
            "successful_tools": successful_tools,
            "overall_success": overall_success,
            "tools_executed": len(results)
        }

    def get_provisioning_status(self, provision_id: str) -> Dict[str, Any]:
        """Obtener estado de un provisioning específico"""
        try:
            if provision_id in self.active_provisions:
                return {
                    "found": True,
                    "provision_id": provision_id,
                    **self.active_provisions[provision_id]
                }
            else:
                return {
                    "found": False,
                    "provision_id": provision_id,
                    "message": "Provisioning no encontrado en registros activos"
                }
        except Exception as e:
            return {"found": False, "error": str(e)}

    def get_it_department_status(self) -> Dict[str, Any]:
        """Obtener estado del departamento IT simulado"""
        try:
            return self.it_simulator.get_department_stats()
        except Exception as e:
            return {"error": str(e), "status": "unavailable"}