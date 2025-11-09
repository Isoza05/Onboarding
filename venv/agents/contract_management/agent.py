from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from agents.base.base_agent import BaseAgent
from datetime import datetime
import json
import asyncio

# Imports del Contract Management
from .tools import (
    contract_generator_tool, legal_validator_tool,
    signature_manager_tool, archive_system_tool
)
from .schemas import (
    ContractGenerationRequest, ContractManagementResult, ContractDocument,
    ContractType, ContractStatus, ComplianceLevel
)
from .hr_simulator import HRDepartmentSimulator

# Imports para integración
from core.state_management.state_manager import state_manager
from core.state_management.models import AgentStateStatus, OnboardingPhase
from core.observability import observability_manager
from core.database import db_manager

class ContractManagementAgent(BaseAgent):
    """
    Contract Management Agent - Gestiona generación, validación y firma de contratos legales.
    
    Implementa arquitectura BDI:
    - Beliefs: Los contratos deben ser legalmente válidos y compliance completo
    - Desires: Generación eficiente de contratos ejecutables y archivados correctamente
    - Intentions: Generar, validar, firmar y archivar contratos con máxima calidad legal
    
    Recibe: Datos consolidados + Credenciales IT del IT Provisioning Agent
    Produce: Contrato firmado, validado legalmente y archivado correctamente
    """
    
    def __init__(self):
        super().__init__(
            agent_id="contract_management_agent",
            agent_name="Contract Management & Legal Processing Agent"
        )
        
        # Inicializar simulador HR
        self.hr_simulator = HRDepartmentSimulator()
        self.active_contracts = {}
        
        # Registrar agente en state management
        state_manager.register_agent(
            self.agent_id,
            {
                "version": "1.0",
                "specialization": "legal_contract_signature_management",
                "tools_count": len(self.tools),
                "capabilities": {
                    "contract_generation": True,
                    "legal_validation": True,
                    "signature_management": True,
                    "document_archival": True,
                    "compliance_verification": True
                },
                "contract_types": [ct.value for ct in ContractType],
                "compliance_levels": [cl.value for cl in ComplianceLevel],
                "jurisdictions": ["Costa Rica"],
                "integration_points": ["hr_department_simulator", "common_state", "meeting_agent"]
            }
        )
        
        self.logger.info("Contract Management Agent integrado con State Management y HR Simulator")

    def _initialize_tools(self) -> List:
        """Inicializar herramientas de Contract Management"""
        return [
            contract_generator_tool,
            legal_validator_tool,
            signature_manager_tool,
            archive_system_tool
        ]

    def _create_prompt(self) -> ChatPromptTemplate:
        """Crear prompt con framework BDI y patrón ReAct para contract management"""
        bdi = self._get_bdi_framework()
        
        system_prompt = f"""
Eres el Contract Management & Legal Processing Agent, especialista en generación y gestión de contratos legales.

## FRAMEWORK BDI (Belief-Desire-Intention)
**BELIEFS (Creencias):**
{bdi['beliefs']}

**DESIRES (Deseos):**
{bdi['desires']}

**INTENTIONS (Intenciones):**
{bdi['intentions']}

## HERRAMIENTAS DE CONTRACT MANAGEMENT:
- contract_generator_tool: Genera contratos legales completos usando templates y datos
- legal_validator_tool: Valida contratos según compliance y regulaciones de Costa Rica
- signature_manager_tool: Gestiona proceso de firma digital/electrónica
- archive_system_tool: Archiva contratos firmados con retención y compliance

## DATOS DE ENTRADA (IT Provisioning Agent Output):
1. **Employee Data**: Información personal, posición, departamento
2. **IT Credentials**: Username, email, equipamiento, permisos de acceso
3. **Contractual Data**: Salario, beneficios, términos de empleo, fechas
4. **Position Data**: Responsabilidades, reporting, ubicación

## DATOS DE SALIDA (Para Meeting Coordination Agent):
1. **Signed Contract**: Contrato legalmente ejecutado con firmas válidas
2. **Legal Validation**: Compliance verificado para Costa Rica
3. **Archive Information**: Documentos archivados con acceso controlado
4. **Employment Details**: Términos finales para coordinación de reuniones

## PROCESO DE CONTRACT MANAGEMENT:
1. **Contract Generation**: Crear contrato usando templates HR y datos del empleado
2. **Legal Validation**: Verificar compliance, cláusulas obligatorias, regulaciones CR
3. **Signature Process**: Ejecutar firma digital/electrónica con empleado y empresa
4. **Document Archival**: Archivar contrato firmado con retención y acceso controlado

## TIPOS DE CONTRATOS:
- **FULL_TIME**: Empleados tiempo completo, beneficios completos
- **PART_TIME**: Empleados medio tiempo, beneficios proporcionales
- **CONTRACTOR**: Contratistas independientes, sin beneficios empleado
- **EXECUTIVE**: Ejecutivos con provisiones especiales y equity

## COMPLIANCE COSTA RICA:
- **Código de Trabajo**: Cláusulas obligatorias, salario mínimo, vacaciones
- **CCSS**: Seguro social obligatorio, contribuciones patronales
- **Ley 8968**: Protección de datos personales, confidencialidad
- **INS**: Seguros obligatorios, riesgos del trabajo

## PATRÓN REACT (Reason-Act-Observe):
**1. REASON (Razonar):**
- Analizar datos del empleado y credenciales IT para determinar tipo de contrato
- Evaluar nivel de compliance requerido según posición y salario
- Identificar cláusulas legales obligatorias y especiales necesarias
- Planificar proceso de firma según tipo de empleado y urgencia

**2. ACT (Actuar):**
- Generar contrato completo con contract_generator_tool usando templates HR
- Validar legalmente con legal_validator_tool para compliance Costa Rica
- Ejecutar proceso de firma con signature_manager_tool (digital/electrónica)
- Archivar documento final con archive_system_tool con retención apropiada

**3. OBSERVE (Observar):**
- Verificar que contrato incluya todas las cláusulas obligatorias
- Confirmar que validation legal pase con score >90% compliance
- Asegurar que firmas sean válidas y verificables legalmente
- Validar que archivo esté completo con acceso controlado

## CRITERIOS DE ÉXITO:
- **Contract Generation**: Template apropiado, datos completos, IT integrado
- **Legal Validation**: >90% compliance, cero issues críticos, CR compliant
- **Signature Process**: Firmas válidas empleado+empresa, certificado generado
- **Document Archival**: PDF firmado, metadata completa, retención 7 años
- **Overall Completion**: >95% para proceder a Meeting Coordination

## ESCALACIÓN:
- Compliance score <85%: Requiere revisión legal manual
- Salarios >$150k USD: Requiere aprobación ejecutiva adicional
- Posiciones ejecutivas: Requiere board approval y cláusulas especiales
- Issues legales críticos: Escalar a Legal Department inmediatamente

## INSTRUCCIONES CRÍTICAS:
1. SIEMPRE genera contrato usando HR simulator para templates actualizados
2. Valida TODOS los aspectos legales antes de proceder a firma
3. Asegura que firmas digitales cumplan estándares legales de Costa Rica
4. Archiva documentos con nivel de acceso y retención apropiados
5. Actualiza Common State con contrato ejecutado y detalles finales
6. Prepara datos específicos para Meeting Coordination Agent

Procesa con precisión legal, valida con rigor compliance, y ejecuta con excelencia documental.
"""
        
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}"),
            ("assistant", "Voy a procesar la generación, validación y firma del contrato legal completo."),
            ("placeholder", "{agent_scratchpad}")
        ])

    def _get_bdi_framework(self) -> Dict[str, str]:
        """Framework BDI específico para contract management"""
        return {
            "beliefs": """
• Los contratos deben ser legalmente válidos y ejecutables en Costa Rica
• Compliance completo es crítico para proteger empresa y empleado
• Las firmas digitales deben cumplir estándares legales y ser verificables
• La documentación debe archivarse con retención apropiada (7 años mínimo)
• Los términos contractuales deben integrar provisiones IT y beneficios
• La validación legal debe ser exhaustiva antes de cualquier firma
""",
            "desires": """
• Contratos generados eficientemente con templates legales actualizados
• Validation legal completa con 100% compliance para jurisdicción Costa Rica
• Proceso de firma digital fluido y legalmente válido
• Archivo documental seguro con acceso controlado y retención completa
• Integración perfecta de datos IT, HR y términos contractuales
• Preparación completa de datos para coordinación de reuniones de onboarding
""",
            "intentions": """
• Generar contratos usando templates HR actualizados y datos empleado completos
• Validar exhaustivamente todos los aspectos legales y compliance obligatorio
• Ejecutar proceso de firma digital con empleado y representante empresa
• Archivar documentos firmados con nivel de seguridad y retención apropiados
• Integrar seamlessly credenciales IT y beneficios en términos contractuales
• Proporcionar datos contract execution completos para Meeting Coordination Agent
"""
        }

    def _format_input(self, input_data: Any) -> str:
        """Formatear datos de entrada para contract management"""
        if isinstance(input_data, ContractGenerationRequest):
            personal_data = input_data.personal_data
            position_data = input_data.position_data
            contractual_data = input_data.contractual_data
            it_credentials = input_data.it_credentials
            
            return f"""
Procesa generación de contrato legal para el siguiente empleado:

**IDENTIFICACIÓN:**
- Employee ID: {input_data.employee_id}
- Session ID: {input_data.session_id}
- Tipo de contrato: {input_data.contract_type.value}
- Nivel de compliance: {input_data.compliance_level.value}
- Prioridad: {input_data.priority.value}

**DATOS PERSONALES:**
- Nombre: {personal_data.get('first_name', '')} {personal_data.get('last_name', '')}
- Cédula: {personal_data.get('id_card', 'N/A')}
- Email: {personal_data.get('email', 'N/A')}
- Dirección: {personal_data.get('current_address', 'N/A')}
- Teléfono: {personal_data.get('phone', 'N/A')}

**DATOS DE POSICIÓN:**
- Posición: {position_data.get('position', 'N/A')}
- Departamento: {position_data.get('department', 'N/A')}
- Oficina: {position_data.get('office', 'N/A')}
- Project Manager: {position_data.get('project_manager', 'N/A')}
- Cliente: {position_data.get('customer', 'N/A')}

**DATOS CONTRACTUALES:**
- Fecha de inicio: {contractual_data.get('start_date', 'N/A')}
- Salario: {contractual_data.get('salary', 0)} {contractual_data.get('currency', 'USD')}
- Tipo de empleo: {contractual_data.get('employment_type', 'N/A')}
- Modalidad: {contractual_data.get('work_modality', 'N/A')}
- Período de prueba: {contractual_data.get('probation_period', 90)} días
- Beneficios: {', '.join(contractual_data.get('benefits', [])) if contractual_data.get('benefits') else 'Estándar'}

**CREDENCIALES IT:**
- Username: {it_credentials.get('username', 'N/A')}
- Email corporativo: {it_credentials.get('email', 'N/A')}
- Acceso al dominio: {it_credentials.get('domain_access', 'N/A')}
- VPN: {'Sí' if it_credentials.get('vpn_credentials') else 'No'}
- Badge access: {it_credentials.get('badge_access', 'N/A')}
- Equipamiento: {'Asignado' if it_credentials.get('equipment_assignment') else 'Pendiente'}

**CLÁUSULAS ESPECIALES:**
- Cláusulas adicionales: {', '.join(input_data.special_clauses) if input_data.special_clauses else 'Ninguna'}
- Requisitos legales: {', '.join(input_data.legal_requirements) if input_data.legal_requirements else 'Estándar'}

**INSTRUCCIONES DE PROCESAMIENTO:**
1. Usa contract_generator_tool para crear contrato completo con templates HR
2. Usa legal_validator_tool para validación compliance Costa Rica
3. Usa signature_manager_tool para proceso de firma digital
4. Usa archive_system_tool para archivo documental con retención

**OBJETIVO:** Generar contrato legalmente ejecutado listo para Meeting Coordination Agent.
"""
        elif isinstance(input_data, dict):
            return f"""
Procesa contract management para los siguientes datos:
{json.dumps(input_data, indent=2, default=str)}

Ejecuta proceso completo: generation → validation → signature → archival.
"""
        else:
            return str(input_data)

    def _format_output(self, result: Any, processing_time: float, success: bool, error: str = None) -> Dict[str, Any]:
        """Formatear salida de contract management"""
        if not success:
            return {
                "success": False,
                "message": f"Error en contract management: {error}",
                "errors": [error] if error else [],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "contract_status": "failed",
                "contract_generated": False,
                "legal_validation_passed": False,
                "signature_process_complete": False,
                "document_archived": False,
                "ready_for_meeting_coordination": False,
                "next_actions": ["Revisar errores de contract management", "Verificar compliance legal"]
            }

        try:
            # Extraer resultados de herramientas
            contract_result = None
            validation_result = None
            signature_result = None
            archive_result = None
            
            if isinstance(result, dict) and "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    if isinstance(step, tuple) and len(step) >= 2:
                        tool_name = step[0]
                        tool_result = step[1]
                        
                        if "contract_generator_tool" in str(tool_name):
                            contract_result = tool_result
                        elif "legal_validator_tool" in str(tool_name):
                            validation_result = tool_result
                        elif "signature_manager_tool" in str(tool_name):
                            signature_result = tool_result
                        elif "archive_system_tool" in str(tool_name):
                            archive_result = tool_result

            # Calcular métricas de éxito
            contract_generated = contract_result and contract_result.get("success", False)
            legal_validation_passed = validation_result and validation_result.get("success", False)
            signature_process_complete = signature_result and signature_result.get("success", False)
            document_archived = archive_result and archive_result.get("success", False)
            
            # Determinar compliance score
            compliance_score = 0
            if validation_result and validation_result.get("success"):
                validation_data = validation_result.get("validation_result", {})
                compliance_score = validation_data.get("compliance_score", 0)

            # Determinar si está listo para meeting coordination
            ready_for_meeting = (
                contract_generated and 
                legal_validation_passed and 
                signature_process_complete and 
                document_archived and
                compliance_score >= 90.0
            )

            # Extraer información del contrato
            contract_id = None
            employee_contract_details = {}
            
            if contract_result and contract_result.get("success"):
                contract_doc = contract_result.get("contract_document", {})
                contract_id = contract_doc.get("contract_id", "")
                employee_contract_details = {
                    "position": contract_doc.get("employment_terms", {}).get("position_title", ""),
                    "department": contract_doc.get("employment_terms", {}).get("department", ""),
                    "start_date": contract_doc.get("employment_terms", {}).get("start_date", ""),
                    "salary": contract_doc.get("compensation_details", {}).get("base_salary", 0),
                    "benefits": contract_doc.get("benefits_package", {}),
                    "it_provisions": contract_doc.get("it_provisions", {})
                }

            # Extraer próximas acciones
            next_actions = []
            if ready_for_meeting:
                next_actions.extend([
                    "Proceder a Meeting Coordination Agent",
                    "Programar reuniones de onboarding",
                    "Enviar contrato firmado a empleado",
                    "Notificar a manager sobre nuevo empleado"
                ])
            else:
                if not contract_generated:
                    next_actions.append("Completar generación de contrato")
                if not legal_validation_passed:
                    next_actions.append("Resolver issues de validación legal")
                if not signature_process_complete:
                    next_actions.append("Completar proceso de firma")
                if not document_archived:
                    next_actions.append("Finalizar archivo documental")

            return {
                "success": True,
                "message": "Contract management completado exitosamente",
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "contract_status": "executed" if ready_for_meeting else "in_process",
                
                # Métricas de contract management
                "contract_generated": contract_generated,
                "legal_validation_passed": legal_validation_passed,
                "signature_process_complete": signature_process_complete,
                "document_archived": document_archived,
                "compliance_score": compliance_score,
                
                # Datos para Meeting Coordination Agent
                "contract_id": contract_id,
                "employee_contract_details": employee_contract_details,
                "signed_contract_location": archive_result.get("contract_archive", {}).get("signed_document", "") if archive_result else "",
                
                # Estado y control
                "ready_for_meeting_coordination": ready_for_meeting,
                "requires_manual_review": compliance_score < 85.0,
                "next_actions": next_actions,
                
                # Resultados detallados por herramienta
                "contract_management_details": {
                    "contract_generation": contract_result,
                    "legal_validation": validation_result,
                    "signature_process": signature_result,
                    "document_archival": archive_result
                },
                
                # Resumen ejecutivo
                "contract_summary": {
                    "contract_ready": ready_for_meeting,
                    "generation_status": "Complete" if contract_generated else "Pending",
                    "validation_status": "Passed" if legal_validation_passed else "Failed",
                    "signature_status": "Signed" if signature_process_complete else "Pending",
                    "archive_status": "Archived" if document_archived else "Pending",
                    "compliance_percentage": f"{compliance_score:.1f}%"
                }
            }

        except Exception as e:
            self.logger.error(f"Error formateando salida de contract management: {e}")
            return {
                "success": False,
                "message": f"Error procesando resultados de contract management: {e}",
                "errors": [str(e)],
                "agent_id": self.agent_id,
                "processing_time": processing_time,
                "contract_status": "error"
            }

    @observability_manager.trace_agent_execution("contract_management_agent")
    def execute_contract_management(self, contract_request: ContractGenerationRequest, session_id: str = None) -> Dict[str, Any]:
        """Ejecutar contract management completo con integración a Common State"""
        
        # Generar contract_id
        contract_id = f"cont_mgmt_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{contract_request.employee_id}"
        
        # Actualizar estado del agente: PROCESSING
        state_manager.update_agent_state(
            self.agent_id,
            AgentStateStatus.PROCESSING,
            {
                "current_task": "contract_management",
                "contract_id": contract_id,
                "employee_id": contract_request.employee_id,
                "contract_type": contract_request.contract_type.value,
                "compliance_level": contract_request.compliance_level.value,
                "priority": contract_request.priority.value,
                "started_at": datetime.utcnow().isoformat()
            },
            session_id
        )

        # Registrar métricas iniciales
        observability_manager.log_agent_metrics(
            self.agent_id,
            {
                "contract_type": contract_request.contract_type.value,
                "compliance_level": contract_request.compliance_level.value,
                "priority": contract_request.priority.value,
                "special_clauses_count": len(contract_request.special_clauses),
                "legal_requirements": len(contract_request.legal_requirements),
                "template_version": contract_request.template_version
            },
            session_id
        )

        try:
            # Procesar con el método base
            result = self.process_request(contract_request, session_id)

            # Si fue exitoso, actualizar State Management
            if result["success"]:
                # Actualizar datos del empleado con información contractual
                if session_id:
                    contract_data = {
                        "contract_management_completed": True,
                        "contract_id": contract_id,
                        "signed_contract": result.get("contract_id", ""),
                        "employee_contract_details": result.get("employee_contract_details", {}),
                        "compliance_score": result.get("compliance_score", 0),
                        "contract_status": result.get("contract_status", ""),
                        "ready_for_meeting": result.get("ready_for_meeting_coordination", False),
                        "next_phase": "meeting_coordination"
                    }
                    
                    state_manager.update_employee_data(
                        session_id,
                        contract_data,
                        "processed"
                    )

                # Actualizar estado del agente: COMPLETED
                state_manager.update_agent_state(
                    self.agent_id,
                    AgentStateStatus.COMPLETED,
                    {
                        "current_task": "completed",
                        "contract_id": contract_id,
                        "contract_generated": result.get("contract_generated", False),
                        "legal_validation_passed": result.get("legal_validation_passed", False),
                        "signature_complete": result.get("signature_process_complete", False),
                        "document_archived": result.get("document_archived", False),
                        "compliance_score": result.get("compliance_score", 0),
                        "ready_for_meeting": result.get("ready_for_meeting_coordination", False),
                        "completed_at": datetime.utcnow().isoformat()
                    },
                    session_id
                )

                # Registrar en contratos activos
                self.active_contracts[contract_id] = {
                    "status": "executed",
                    "result": result,
                    "completed_at": datetime.utcnow()
                }

            else:
                # Error en contract management
                state_manager.update_agent_state(
                    self.agent_id,
                    AgentStateStatus.ERROR,
                    {
                        "current_task": "error",
                        "contract_id": contract_id,
                        "errors": result.get("errors", []),
                        "failed_at": datetime.utcnow().isoformat()
                    },
                    session_id
                )

            # Agregar información de sesión al resultado
            result["contract_management_id"] = contract_id
            result["session_id"] = session_id
            return result

        except Exception as e:
            # Error durante contract management
            error_msg = f"Error ejecutando contract management: {str(e)}"
            state_manager.update_agent_state(
                self.agent_id,
                AgentStateStatus.ERROR,
                {
                    "current_task": "error",
                    "contract_id": contract_id,
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
                "contract_management_id": contract_id,
                "session_id": session_id,
                "agent_id": self.agent_id,
                "processing_time": 0,
                "contract_status": "failed"
            }

    def _process_with_tools_directly(self, input_data: Any) -> Dict[str, Any]:
        """Procesar usando herramientas directamente con flujo específico de contract management"""
        results = []
        formatted_input = self._format_input(input_data)
        self.logger.info(f"Procesando contract management con {len(self.tools)} herramientas especializadas")

        # Variables para almacenar resultados
        contract_result = None
        validation_result = None
        signature_result = None
        archive_result = None

        # Preparar datos según tipo de entrada
        if isinstance(input_data, ContractGenerationRequest):
            employee_data = {
                **input_data.personal_data,
                **input_data.position_data,
                "employee_id": input_data.employee_id
            }
            it_credentials = input_data.it_credentials
            contractual_data = input_data.contractual_data
            template_version = input_data.template_version
        else:
            # Fallback para datos genéricos
            employee_data = input_data.get("employee_data", {}) if isinstance(input_data, dict) else {}
            it_credentials = input_data.get("it_credentials", {}) if isinstance(input_data, dict) else {}
            contractual_data = input_data.get("contractual_data", {}) if isinstance(input_data, dict) else {}
            template_version = "v2024.1"

        # Ejecutar herramientas en secuencia
        for tool in self.tools:
            try:
                self.logger.info(f"Ejecutando herramienta: {tool.name}")
                
                if tool.name == "contract_generator_tool":
                    # Usar single dict como en el test exitoso
                    tool_input = {
                        "employee_data": employee_data,
                        "it_credentials": it_credentials,
                        "contractual_data": contractual_data,
                        "template_version": template_version
                    }
                    result = tool.invoke(tool_input)
                    contract_result = result
                    
                elif tool.name == "legal_validator_tool":
                    if contract_result and contract_result.get("success"):
                        contract_document = contract_result.get("contract_document", {})
                        tool_input = {
                            "contract_document": contract_document,
                            "validation_level": "standard"
                        }
                        result = tool.invoke(tool_input)
                        validation_result = result
                    else:
                        result = {"success": False, "error": "No contract document available for validation"}
                        
                elif tool.name == "signature_manager_tool":
                    if (validation_result and validation_result.get("success") and 
                        validation_result.get("validation_result", {}).get("is_valid", False)):
                        contract_document = contract_result.get("contract_document", {})
                        tool_input = {
                            "contract_document": contract_document,
                            "employee_data": employee_data,
                            "signature_type": "digital"
                        }
                        result = tool.invoke(tool_input)
                        signature_result = result
                    else:
                        result = {"success": False, "error": "Contract validation failed, cannot proceed to signature"}
                        
                elif tool.name == "archive_system_tool":
                    if signature_result and signature_result.get("success"):
                        signed_contract = signature_result.get("signed_contract", {})
                        tool_input = {
                            "signed_contract": signed_contract,
                            "employee_data": employee_data,
                            "archive_location": "company_contract_repository"
                        }
                        result = tool.invoke(tool_input)
                        archive_result = result
                    else:
                        result = {"success": False, "error": "Signature process incomplete, cannot archive"}
                        
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
            "output": "Procesamiento de contract management completado",
            "intermediate_steps": results,
            "contract_result": contract_result,
            "validation_result": validation_result,
            "signature_result": signature_result,
            "archive_result": archive_result,
            "successful_tools": successful_tools,
            "overall_success": overall_success,
            "tools_executed": len(results)
        }
    def get_contract_status(self, contract_id: str) -> Dict[str, Any]:
        """Obtener estado de un contrato específico"""
        try:
            if contract_id in self.active_contracts:
                return {
                    "found": True,
                    "contract_id": contract_id,
                    **self.active_contracts[contract_id]
                }
            else:
                return {
                    "found": False,
                    "contract_id": contract_id,
                    "message": "Contrato no encontrado en registros activos"
                }
        except Exception as e:
            return {"found": False, "error": str(e)}

    def get_hr_department_status(self) -> Dict[str, Any]:
        """Obtener estado del departamento HR simulado"""
        try:
            return self.hr_simulator.get_department_stats()
        except Exception as e:
            return {"error": str(e), "status": "unavailable"}

    def generate_contract_preview(self, employee_data: Dict[str, Any], 
                                it_credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Generar preview del contrato sin ejecutar proceso completo"""
        try:
            return self.hr_simulator.generate_contract_preview(employee_data, it_credentials)
        except Exception as e:
            return {
                "success": False,
                "error": f"Error generating contract preview: {str(e)}"
            }