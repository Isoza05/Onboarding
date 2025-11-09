from langchain.tools import tool
from typing import Dict, Any, List
import json
import asyncio
from datetime import datetime, date, timedelta
from .hr_simulator import HRDepartmentSimulator
from .schemas import (
    ContractDocument, EmploymentTerms, CompensationDetails, BenefitsPackage,
    ContractType, ContractStatus, SignatureDetails, SignatureType, 
    ContractValidationResult, ContractArchive
)
import uuid

# Instancia global del simulador HR
hr_simulator = HRDepartmentSimulator()

@tool
def contract_generator_tool(employee_data: Dict[str, Any], it_credentials: Dict[str, Any], 
                          contractual_data: Dict[str, Any], template_version: str = "v2024.1") -> Dict[str, Any]:
    """
    Genera contrato legal completo usando templates y datos del empleado.
    Integra credenciales IT y términos contractuales.
    
    Args:
        employee_data: Datos personales del empleado
        it_credentials: Credenciales IT del IT Provisioning Agent
        contractual_data: Términos contractuales del Data Aggregator
        template_version: Versión del template a usar
    """
    try:
        if not employee_data or not it_credentials:
            return {"success": False, "error": "Missing required employee or IT credentials data"}
        
        # Generar ID único del contrato
        contract_id = f"CONT-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{employee_data.get('employee_id', 'EMP')}"
        
        # Obtener datos del HR Simulator
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        hr_response = loop.run_until_complete(
            hr_simulator.process_contract_request(employee_data, it_credentials, contractual_data)
        )
        loop.close()
        
        # Construir términos de empleo
        employment_terms = EmploymentTerms(
            position_title=employee_data.get("position", "Employee"),
            department=employee_data.get("department", "General"),
            reporting_manager=employee_data.get("project_manager", "TBD"),
            employment_type=ContractType.FULL_TIME,
            start_date=datetime.strptime(contractual_data.get("start_date", "2025-01-01"), "%Y-%m-%d").date(),
            probation_period_days=contractual_data.get("probation_period", 90),
            work_schedule="full_time",
            work_location=employee_data.get("office", "Main Office"),
            remote_work_allowed=contractual_data.get("work_modality", "hybrid") != "presencial",
            travel_requirements="minimal"
        )
        
        # Construir detalles de compensación
        compensation_details = CompensationDetails(
            base_salary=float(contractual_data.get("salary", 0)),
            currency=contractual_data.get("currency", "USD"),
            payment_frequency="monthly",
            benefits_package=contractual_data.get("benefits", []),
            total_compensation=float(contractual_data.get("salary", 0))
        )
        
        # Usar paquete de beneficios del HR Simulator
        benefits_package = hr_response.benefits_configuration
        
        # Integrar provisiones IT
        it_provisions = {
            "username": it_credentials.get("username", ""),
            "email": it_credentials.get("email", ""),
            "domain_access": it_credentials.get("domain_access", ""),
            "vpn_access": bool(it_credentials.get("vpn_credentials")),
            "badge_access": it_credentials.get("badge_access", ""),
            "security_level": it_credentials.get("access_level", "standard"),
            "equipment_provided": True,
            "it_orientation_required": True
        }
        
        # Construir documento de contrato completo
        contract_document = ContractDocument(
            contract_id=contract_id,
            employee_id=employee_data.get("employee_id", ""),
            document_version="1.0",
            template_version=template_version,
            jurisdiction="Costa Rica",
            language="Spanish",
            employment_terms=employment_terms,
            compensation_details=compensation_details,
            benefits_package=benefits_package,
            legal_clauses=hr_response.legal_clauses,
            it_provisions=it_provisions,
            equipment_assignment=it_credentials.get("equipment_assignment", {}),
            status=ContractStatus.DRAFT
        )
        
        # Generar contenido del contrato
        contract_content = _generate_contract_content(contract_document, employee_data)
        
        return {
            "success": True,
            "contract_document": contract_document.dict(),
            "contract_content": contract_content,
            "hr_response": hr_response.dict(),
            "generation_metadata": {
                "contract_id": contract_id,
                "template_used": hr_response.contract_template.get("template_type", "standard"),
                "clauses_included": len(hr_response.legal_clauses),
                "pages_estimated": len(contract_content) // 500 + 1,  # Estimar páginas
                "jurisdiction": "Costa Rica",
                "language": "Spanish",
                "it_integration": True
            },
            "processing_notes": [
                f"Contract generated for {employee_data.get('first_name', '')} {employee_data.get('last_name', '')}",
                f"Position: {employee_data.get('position', '')}",
                f"Salary: {contractual_data.get('currency', 'USD')} {contractual_data.get('salary', 0):,}",
                f"Start Date: {contractual_data.get('start_date', '')}",
                f"IT provisions integrated: {len(it_provisions)} items",
                f"Legal clauses: {len(hr_response.legal_clauses)} included"
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error generating contract: {str(e)}",
            "contract_document": {},
            "contract_content": ""
        }

@tool
def legal_validator_tool(contract_document: Dict[str, Any], validation_level: str = "standard") -> Dict[str, Any]:
    """
    Valida legalmente el contrato generado verificando compliance y regulaciones.
    Ejecuta checks de compliance para jurisdicción de Costa Rica.
    
    Args:
        contract_document: Documento de contrato a validar
        validation_level: Nivel de validación (basic, standard, strict)
    """
    try:
        if not contract_document:
            return {"success": False, "error": "No contract document provided for validation"}
        
        validation_results = {}
        legal_issues = []
        recommendations = []
        compliance_score = 0
        
        # Validación de cláusulas obligatorias
        required_clauses = ["employment_terms", "compensation", "confidentiality", "termination"]
        clause_validation = {}
        
        contract_clauses = contract_document.get("legal_clauses", [])
        clause_types = [clause.get("clause_type", "") for clause in contract_clauses]
        
        for required_clause in required_clauses:
            is_present = required_clause in clause_types
            clause_validation[required_clause] = is_present
            if not is_present:
                legal_issues.append(f"Missing required clause: {required_clause}")
            
        # Validación de términos de empleo
        employment_terms = contract_document.get("employment_terms", {})
        employment_valid = all([
            employment_terms.get("position_title"),
            employment_terms.get("start_date"),
            employment_terms.get("work_location")
        ])
        
        if not employment_valid:
            legal_issues.append("Incomplete employment terms section")
        
        # Validación de compensación
        compensation = contract_document.get("compensation_details", {})
        salary = compensation.get("base_salary", 0)
        currency = compensation.get("currency", "")
        
        if salary <= 0:
            legal_issues.append("Invalid salary amount")
        if not currency:
            legal_issues.append("Missing currency specification")
            
        # Validación de compliance Costa Rica
        compliance_checks = {}
        
        # Salario mínimo Costa Rica (aproximado)
        min_salary_colones = 350000  # Aproximado para profesionales
        min_salary_usd = 600
        
        if currency.upper() == "CRC" and salary < min_salary_colones:
            compliance_checks["minimum_wage_compliance"] = False
            legal_issues.append("Salary below minimum wage (Costa Rica)")
        elif currency.upper() == "USD" and salary < min_salary_usd:
            compliance_checks["minimum_wage_compliance"] = False
            legal_issues.append("Salary below minimum wage equivalent (Costa Rica)")
        else:
            compliance_checks["minimum_wage_compliance"] = True
            
        # Validación de vacaciones (mínimo legal Costa Rica: 2 semanas)
        benefits = contract_document.get("benefits_package", {})
        vacation_days = benefits.get("vacation_days", 0)
        if vacation_days < 14:
            compliance_checks["vacation_compliance"] = False
            legal_issues.append("Vacation days below legal minimum (14 days)")
        else:
            compliance_checks["vacation_compliance"] = True
            
        # Validación de seguridad social
        retirement_plan = benefits.get("retirement_plan", {})
        if not retirement_plan:
            compliance_checks["social_security_compliance"] = False
            legal_issues.append("Missing social security/retirement plan provisions")
        else:
            compliance_checks["social_security_compliance"] = True
            
        # Validación de IT provisions
        it_provisions = contract_document.get("it_provisions", {})
        it_validation = {
            "email_assigned": bool(it_provisions.get("email")),
            "equipment_provided": it_provisions.get("equipment_provided", False),
            "access_defined": bool(it_provisions.get("username"))
        }
        
        if not all(it_validation.values()):
            recommendations.append("IT provisions should be more comprehensive")
            
        # Calcular score de compliance
        total_checks = len(clause_validation) + len(compliance_checks) + len(it_validation)
        passed_checks = sum(clause_validation.values()) + sum(compliance_checks.values()) + sum(it_validation.values())
        compliance_score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        # Generar recomendaciones
        if compliance_score < 90:
            recommendations.append("Review and address legal issues before contract execution")
        if compliance_score < 70:
            recommendations.append("Legal review required before proceeding")
        if len(legal_issues) == 0:
            recommendations.append("Contract meets legal requirements for execution")
            
        # Validación específica por nivel
        if validation_level == "strict":
            # Validaciones adicionales para nivel estricto
            if not contract_document.get("jurisdiction"):
                legal_issues.append("Jurisdiction not specified")
            if not contract_document.get("template_version"):
                legal_issues.append("Template version not documented")
                
        return {
            "success": True,
            "validation_result": {
                "is_valid": len(legal_issues) == 0,
                "compliance_score": compliance_score,
                "legal_issues": legal_issues,
                "recommendations": recommendations,
                "clause_validation": clause_validation,
                "compliance_checks": compliance_checks,
                "it_validation": it_validation,
                "jurisdiction_compliance": True,  # Assume Costa Rica compliance
                "validator_id": "legal_validator_v1.0",
                "validation_timestamp": datetime.utcnow().isoformat(),
                "validation_level": validation_level
            },
            "validation_summary": {
                "overall_status": "APPROVED" if len(legal_issues) == 0 else "NEEDS_REVISION",
                "compliance_percentage": f"{compliance_score:.1f}%",
                "issues_count": len(legal_issues),
                "recommendations_count": len(recommendations),
                "ready_for_signature": len(legal_issues) == 0 and compliance_score >= 85
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error in legal validation: {str(e)}",
            "validation_result": {}
        }

@tool
def signature_manager_tool(contract_document: Dict[str, Any], employee_data: Dict[str, Any],
                         signature_type: str = "digital") -> Dict[str, Any]:
    """
    Gestiona el proceso de firma digital/electrónica del contrato.
    Simula DocuSign o proceso de firma electrónica.
    
    Args:
        contract_document: Documento de contrato validado
        employee_data: Datos del empleado para firma
        signature_type: Tipo de firma (digital, electronic, physical)
    """
    try:
        if not contract_document or not employee_data:
            return {"success": False, "error": "Missing contract document or employee data"}
        
        contract_id = contract_document.get("contract_id", "")
        employee_id = employee_data.get("employee_id", "")
        
        # Simular proceso de firma
        signature_process_id = f"SIG-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}-{employee_id}"
        
        # Configurar firmas requeridas
        employee_signature = SignatureDetails(
            signature_type=SignatureType(signature_type),
            signer_name=f"{employee_data.get('first_name', '')} {employee_data.get('last_name', '')}",
            signer_title="Employee",
            signer_email=employee_data.get("email", ""),
            signature_date=datetime.utcnow(),
            signature_location="Digital Platform",
            ip_address="192.168.1.100",  # Simulado
            device_info="Web Browser - Chrome"
        )
        
        # Firma del empleador
        employer_signature = SignatureDetails(
            signature_type=SignatureType(signature_type),
            signer_name="María López Hernández",
            signer_title="HR Director",
            signer_email="hr.director@company.com",
            signature_date=datetime.utcnow(),
            signature_location="Digital Platform",
            ip_address="10.0.1.50",  # Simulado
            device_info="Web Browser - Edge"
        )
        
        # Simular delay del proceso de firma
        processing_delay = 2.5  # segundos simulados
        
        # Actualizar documento con firmas
        signed_contract = {
            **contract_document,
            "employee_signature": employee_signature.dict(),
            "employer_signature": employer_signature.dict(),
            "status": ContractStatus.SIGNED.value,
            "signature_process_id": signature_process_id,
            "signature_completion_date": datetime.utcnow().isoformat(),
            "signatures_collected": 2,
            "signatures_required": 2,
            "signature_method": signature_type,
            "signature_platform": "Company Digital Signature Platform",
            "legal_validity": True
        }
        
        # Generar certificado de firma
        signature_certificate = {
            "certificate_id": f"CERT-{signature_process_id}",
            "contract_id": contract_id,
            "signatures": [
                {
                    "signer": employee_signature.signer_name,
                    "timestamp": employee_signature.signature_date.isoformat(),
                    "verification": "verified"
                },
                {
                    "signer": employer_signature.signer_name,
                    "timestamp": employer_signature.signature_date.isoformat(),
                    "verification": "verified"
                }
            ],
            "certificate_authority": "Company Legal Department",
            "validity_period": "7 years",
            "jurisdiction": "Costa Rica",
            "legal_validity": True
        }
        
        return {
            "success": True,
            "signed_contract": signed_contract,
            "signature_certificate": signature_certificate,
            "signature_process": {
                "process_id": signature_process_id,
                "completion_time": processing_delay,
                "signatures_collected": 2,
                "signatures_required": 2,
                "process_status": "completed",
                "signature_method": signature_type,
                "platform_used": "Company Digital Signature Platform"
            },
            "legal_verification": {
                "all_signatures_valid": True,
                "timestamp_verified": True,
                "identity_verified": True,
                "document_integrity": True,
                "legal_requirements_met": True,
                "jurisdiction_compliant": True
            },
            "processing_notes": [
                f"Contract signed by {employee_signature.signer_name}",
                f"Contract signed by {employer_signature.signer_name}",
                f"Signature process completed in {processing_delay:.1f} seconds",
                f"Legal validity confirmed for Costa Rica jurisdiction",
                f"Digital certificate generated: {signature_certificate['certificate_id']}"
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error in signature process: {str(e)}",
            "signed_contract": {},
            "signature_certificate": {}
        }

@tool
def archive_system_tool(signed_contract: Dict[str, Any], employee_data: Dict[str, Any],
                       archive_location: str = "company_contract_repository") -> Dict[str, Any]:
    """
    Archiva el contrato firmado en el sistema de gestión documental.
    Genera documentos finales y establece retención.
    
    Args:
        signed_contract: Contrato firmado completo
        employee_data: Datos del empleado
        archive_location: Ubicación del archivo
    """
    try:
        if not signed_contract or not employee_data:
            return {"success": False, "error": "Missing signed contract or employee data"}
        
        contract_id = signed_contract.get("contract_id", "")
        employee_id = employee_data.get("employee_id", "")
        
        # Generar ID de archivo
        archive_id = f"ARCH-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}-{employee_id}"
        
        # Simular generación de documentos
        document_generation = {
            "pdf_contract": f"/contracts/pdf/{contract_id}.pdf",
            "signed_pdf": f"/contracts/signed/{contract_id}_signed.pdf",
            "metadata_file": f"/contracts/metadata/{contract_id}_metadata.json",
            "signature_certificate": f"/contracts/certificates/{contract_id}_cert.pdf",
            "backup_copy": f"/contracts/backup/{contract_id}_backup.pdf"
        }
        
        # Calcular fecha de expiración (7 años según ley laboral CR)
        retention_years = 7
        expiration_date = datetime.utcnow() + timedelta(days=retention_years * 365)
        
        # Crear registro de archivo
        contract_archive = ContractArchive(
            archive_id=archive_id,
            contract_id=contract_id,
            employee_id=employee_id,
            pdf_document=document_generation["pdf_contract"],
            signed_document=document_generation["signed_pdf"],
            metadata_file=document_generation["metadata_file"],
            archive_location=archive_location,
            retention_period_years=retention_years,
            access_level="confidential",
            archived_at=datetime.utcnow(),
            expires_at=expiration_date
        )
        
        # Metadatos del archivo
        archive_metadata = {
            "employee_name": f"{employee_data.get('first_name', '')} {employee_data.get('last_name', '')}",
            "position": employee_data.get("position", ""),
            "department": employee_data.get("department", ""),
            "hire_date": signed_contract.get("employment_terms", {}).get("start_date", ""),
            "salary": signed_contract.get("compensation_details", {}).get("base_salary", 0),
            "contract_type": signed_contract.get("employment_terms", {}).get("employment_type", ""),
            "archive_date": datetime.utcnow().isoformat(),
            "retention_until": expiration_date.isoformat(),
            "jurisdiction": "Costa Rica",
            "access_restrictions": "HR and Legal departments only",
            "backup_locations": ["primary_server", "secure_cloud", "offsite_backup"]
        }
        
        # Configurar acceso y permisos
        access_configuration = {
            "authorized_roles": ["HR_Manager", "HR_Director", "Legal_Counsel", "CEO", "Employee_Self"],
            "read_permissions": ["HR_Team", "Legal_Team", "Auditors"],
            "modification_permissions": ["Legal_Counsel", "HR_Director"],
            "deletion_permissions": ["Legal_Counsel", "System_Admin"],
            "audit_trail_required": True,
            "encryption_level": "AES-256",
            "backup_frequency": "daily",
            "disaster_recovery": True
        }
        
        # Compliance y auditoría
        compliance_tracking = {
            "gdpr_compliant": True,
            "local_privacy_law_compliant": True,  # Ley 8968 Costa Rica
            "retention_policy_applied": True,
            "access_controls_configured": True,
            "audit_trail_enabled": True,
            "encryption_applied": True,
            "backup_verified": True,
            "legal_hold_capability": True
        }
        
        return {
            "success": True,
            "contract_archive": contract_archive.dict(),
            "archive_metadata": archive_metadata,
            "document_generation": document_generation,
            "access_configuration": access_configuration,
            "compliance_tracking": compliance_tracking,
            "archive_summary": {
                "archive_id": archive_id,
                "contract_id": contract_id,
                "employee_id": employee_id,
                "documents_generated": len(document_generation),
                "retention_period": f"{retention_years} years",
                "expires_on": expiration_date.date().isoformat(),
                "access_level": "confidential",
                "compliance_status": "fully_compliant",
                "backup_status": "completed"
            },
            "processing_notes": [
                f"Contract archived with ID: {archive_id}",
                f"PDF documents generated: {len(document_generation)}",
                f"Retention period: {retention_years} years (expires {expiration_date.date()})",
                f"Access configured for {len(access_configuration['authorized_roles'])} roles",
                f"Compliance verified for Costa Rica jurisdiction",
                f"Backup completed to {len(archive_metadata['backup_locations'])} locations"
            ],
            "legal_compliance": {
                "jurisdiction": "Costa Rica",
                "retention_compliant": True,
                "privacy_compliant": True,
                "access_controlled": True,
                "audit_ready": True
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error in contract archival: {str(e)}",
            "contract_archive": {},
            "archive_summary": {}
        }

def _generate_contract_content(contract_document: ContractDocument, employee_data: Dict[str, Any]) -> str:
    """Generar contenido textual del contrato"""
    
    content = f"""
CONTRATO DE TRABAJO

Entre la empresa TECHCORP SOLUTIONS COSTA RICA S.A., sociedad constituida bajo las leyes de Costa Rica, 
representada por su Director de Recursos Humanos, María López Hernández, mayor de edad, con domicilio en 
San José, Costa Rica (en adelante "LA EMPRESA"), y {employee_data.get('first_name', '')} {employee_data.get('last_name', '')}, 
mayor de edad, portador de la cédula de identidad número {employee_data.get('id_card', '')}, 
con domicilio en {employee_data.get('current_address', '')}, (en adelante "EL EMPLEADO"), 
se celebra el presente CONTRATO DE TRABAJO, sujeto a las siguientes cláusulas:

PRIMERA: OBJETO DEL CONTRATO
LA EMPRESA contrata los servicios profesionales de EL EMPLEADO para desempeñar el cargo de 
{contract_document.employment_terms.position_title} en el departamento de {contract_document.employment_terms.department}.

SEGUNDA: REMUNERACIÓN
EL EMPLEADO devengará un salario mensual de {contract_document.compensation_details.currency} 
{contract_document.compensation_details.base_salary:,.2f}, pagadero mensualmente.

TERCERA: JORNADA LABORAL
EL EMPLEADO cumplirá una jornada de trabajo de tiempo completo, con modalidad 
{contract_document.employment_terms.work_schedule}, en las instalaciones ubicadas en 
{contract_document.employment_terms.work_location}.

CUARTA: BENEFICIOS
EL EMPLEADO tendrá derecho a {contract_document.benefits_package.vacation_days} días de vacaciones anuales, 
seguro de salud con {contract_document.benefits_package.health_insurance.get('provider', 'CCSS')}, 
y demás beneficios establecidos por ley.

QUINTA: PROVISIONES TECNOLÓGICAS
LA EMPRESA proporcionará las siguientes credenciales y equipamiento tecnológico:
- Usuario: {contract_document.it_provisions.get('username', '')}
- Correo electrónico: {contract_document.it_provisions.get('email', '')}
- Acceso VPN: {'Sí' if contract_document.it_provisions.get('vpn_access') else 'No'}
- Equipamiento según especificaciones del Departamento de IT.

El presente contrato se rige por el Código de Trabajo de Costa Rica y entra en vigor el 
{contract_document.employment_terms.start_date}.

En fe de lo cual firman las partes en la fecha indicada.

_________________                    _________________
EL EMPLEADO                         LA EMPRESA
{employee_data.get('first_name', '')} {employee_data.get('last_name', '')}                    María López Hernández
                                    Directora de Recursos Humanos
"""
    
    return content.strip()