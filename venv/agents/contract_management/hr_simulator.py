import random
import time
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional
from .schemas import (
    HRDepartmentResponse, ContractDocument, EmploymentTerms, CompensationDetails,
    BenefitsPackage, LegalClause, ContractType, ComplianceLevel, HRSimulatorConfig
)

class HRDepartmentSimulator:
    """Simulador completo del departamento HR con procesos legales y compliance"""
    
    def __init__(self):
        self.config = HRSimulatorConfig()
        self._setup_default_config()
        self.active_requests = {}
        
    def _setup_default_config(self):
        """Configurar templates y configuraciones por defecto"""
        self.config.contract_templates = {
            "full_time_engineer": {
                "base_template": "standard_employment_contract_cr",
                "clauses": ["employment_terms", "compensation", "benefits", "confidentiality", "termination"],
                "probation_period": 90,
                "vacation_days": 15
            },
            "senior_engineer": {
                "base_template": "senior_employment_contract_cr", 
                "clauses": ["employment_terms", "compensation", "benefits", "confidentiality", "termination", "equity"],
                "probation_period": 90,
                "vacation_days": 18
            },
            "manager": {
                "base_template": "management_contract_cr",
                "clauses": ["employment_terms", "compensation", "benefits", "confidentiality", "termination", "equity", "management_responsibilities"],
                "probation_period": 90,
                "vacation_days": 20
            },
            "executive": {
                "base_template": "executive_contract_cr",
                "clauses": ["employment_terms", "compensation", "benefits", "confidentiality", "termination", "equity", "executive_provisions"],
                "probation_period": 180,
                "vacation_days": 25
            }
        }
        
        self.config.legal_clause_library = [
            LegalClause(
                clause_id="employment_001",
                clause_type="employment_terms",
                title="Términos de Empleo",
                content="El empleado prestará servicios bajo las siguientes condiciones de empleo...",
                is_mandatory=True,
                jurisdiction="Costa Rica",
                legal_reference="Código de Trabajo de Costa Rica, Art. 18-25"
            ),
            LegalClause(
                clause_id="compensation_001", 
                clause_type="compensation",
                title="Compensación y Beneficios",
                content="La compensación del empleado será pagada según los términos establecidos...",
                is_mandatory=True,
                jurisdiction="Costa Rica",
                legal_reference="Código de Trabajo de Costa Rica, Art. 162-165"
            ),
            LegalClause(
                clause_id="confidentiality_001",
                clause_type="confidentiality",
                title="Confidencialidad y Propiedad Intelectual",
                content="El empleado se compromete a mantener la confidencialidad de toda información...",
                is_mandatory=True,
                jurisdiction="Costa Rica",
                legal_reference="Ley de Protección de Datos Personales N° 8968"
            ),
            LegalClause(
                clause_id="termination_001",
                clause_type="termination", 
                title="Terminación del Contrato",
                content="Este contrato podrá terminarse por las causales establecidas en el Código de Trabajo...",
                is_mandatory=True,
                jurisdiction="Costa Rica",
                legal_reference="Código de Trabajo de Costa Rica, Art. 81-85"
            )
        ]
        
        self.config.benefits_packages = {
            "standard": BenefitsPackage(
                health_insurance={"provider": "CCSS", "coverage": "100%", "family_included": True},
                dental_insurance={"provider": "INS", "coverage": "80%"},
                life_insurance={"coverage_amount": 50000, "provider": "INS"},
                retirement_plan={"type": "pension_fund", "employer_contribution": "9.34%"},
                vacation_days=15,
                sick_days=12,
                personal_days=3,
                professional_development={"annual_budget": 2000, "currency": "USD"},
                meal_allowance=200.0,
                transport_allowance=150.0
            ),
            "senior": BenefitsPackage(
                health_insurance={"provider": "CCSS + Private", "coverage": "100%", "family_included": True},
                dental_insurance={"provider": "Private", "coverage": "100%"},
                life_insurance={"coverage_amount": 100000, "provider": "Private"},
                retirement_plan={"type": "pension_fund + 401k", "employer_contribution": "12%"},
                vacation_days=18,
                sick_days=15,
                personal_days=5,
                professional_development={"annual_budget": 3500, "currency": "USD"},
                gym_membership=True,
                meal_allowance=300.0,
                transport_allowance=200.0
            ),
            "executive": BenefitsPackage(
                health_insurance={"provider": "Premium Private", "coverage": "100%", "family_included": True},
                dental_insurance={"provider": "Premium Private", "coverage": "100%"},
                life_insurance={"coverage_amount": 250000, "provider": "Premium"},
                retirement_plan={"type": "executive_package", "employer_contribution": "15%"},
                vacation_days=25,
                sick_days=20,
                personal_days=10,
                professional_development={"annual_budget": 7500, "currency": "USD"},
                gym_membership=True,
                meal_allowance=500.0,
                transport_allowance=400.0
            )
        }

    async def process_contract_request(self, employee_data: Dict[str, Any], 
                                     it_credentials: Dict[str, Any],
                                     contractual_requirements: Dict[str, Any] = None) -> HRDepartmentResponse:
        """Procesar solicitud de contrato con simulación HR realista"""
        
        request_id = f"HR-CONT-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{employee_data.get('employee_id', 'UNK')}"
        
        # Simular tiempo de procesamiento HR
        processing_minutes = random.randint(
            self.config.response_delay_min, 
            self.config.response_delay_max
        ) / 60  # Convertir para demo rápida
        
        # Simular delay (reducido para testing)
        await self._simulate_processing_delay(processing_minutes * 8)  # 8 segundos por minuto simulado
        
        # Determinar tipo de contrato y template
        contract_template = self._select_contract_template(employee_data)
        
        # Generar cláusulas legales
        legal_clauses = self._generate_legal_clauses(employee_data, contract_template)
        
        # Configurar paquete de beneficios
        benefits_package = self._configure_benefits_package(employee_data)
        
        # Determinar requisitos de compliance
        compliance_requirements = self._assess_compliance_requirements(employee_data)
        
        # Configurar workflow de aprobación
        approval_workflow = self._setup_approval_workflow(employee_data, compliance_requirements)
        
        # Registrar request
        self.active_requests[request_id] = {
            "employee_id": employee_data.get("employee_id"),
            "status": "completed",
            "created_at": datetime.utcnow(),
            "processing_time": processing_minutes
        }
        
        return HRDepartmentResponse(
            request_id=request_id,
            employee_id=employee_data.get("employee_id", ""),
            processing_time_minutes=processing_minutes,
            contract_template=contract_template,
            legal_clauses=legal_clauses,
            compliance_requirements=compliance_requirements,
            benefits_configuration=benefits_package,
            approval_workflow=approval_workflow,
            completion_notes=[
                f"Contract template prepared for {employee_data.get('position', 'Employee')}",
                f"Legal clauses validated for Costa Rica jurisdiction",
                f"Benefits package configured according to position level",
                f"Compliance requirements assessed and documented",
                f"Approval workflow established with {len(approval_workflow)} steps"
            ]
        )

    def _select_contract_template(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """Seleccionar template de contrato apropiado"""
        position = employee_data.get("position", "").lower()
        salary = employee_data.get("salary", 0)
        
        # Determinar tipo de template
        template_type = "full_time_engineer"  # Default
        
        if "senior" in position or "lead" in position:
            template_type = "senior_engineer"
        elif "manager" in position or "director" in position:
            template_type = "manager"
        elif "executive" in position or "ceo" in position or "cto" in position:
            template_type = "executive"
        elif salary > 120000:  # High salary = senior level
            template_type = "senior_engineer"
            
        base_template = self.config.contract_templates.get(template_type, self.config.contract_templates["full_time_engineer"])
        
        # Personalizar template
        personalized_template = {
            **base_template,
            "employee_id": employee_data.get("employee_id"),
            "position_title": employee_data.get("position"),
            "department": employee_data.get("department", "Engineering"),
            "start_date": employee_data.get("start_date"),
            "salary": employee_data.get("salary"),
            "currency": employee_data.get("currency", "USD"),
            "work_location": employee_data.get("office", "Costa Rica"),
            "reporting_manager": employee_data.get("project_manager", "TBD"),
            "template_type": template_type,
            "jurisdiction": "Costa Rica",
            "language": "Spanish"
        }
        
        return personalized_template

    def _generate_legal_clauses(self, employee_data: Dict[str, Any], 
                              contract_template: Dict[str, Any]) -> List[LegalClause]:
        """Generar cláusulas legales específicas"""
        required_clauses = contract_template.get("clauses", [])
        legal_clauses = []
        
        # Filtrar cláusulas de la librería
        for clause_type in required_clauses:
            matching_clauses = [
                clause for clause in self.config.legal_clause_library 
                if clause.clause_type == clause_type
            ]
            if matching_clauses:
                # Personalizar la cláusula
                base_clause = matching_clauses[0]
                personalized_clause = LegalClause(
                    clause_id=f"{base_clause.clause_id}_{employee_data.get('employee_id', 'EMP')}",
                    clause_type=base_clause.clause_type,
                    title=base_clause.title,
                    content=self._personalize_clause_content(base_clause.content, employee_data),
                    is_mandatory=base_clause.is_mandatory,
                    jurisdiction=base_clause.jurisdiction,
                    legal_reference=base_clause.legal_reference
                )
                legal_clauses.append(personalized_clause)
        
        # Agregar cláusulas específicas según posición
        position = employee_data.get("position", "").lower()
        if "engineer" in position or "developer" in position:
            legal_clauses.append(
                LegalClause(
                    clause_id=f"tech_specific_{employee_data.get('employee_id')}",
                    clause_type="technology_provisions",
                    title="Provisiones Tecnológicas",
                    content=f"El empleado tendrá acceso a las siguientes herramientas tecnológicas: {employee_data.get('technology', 'Herramientas estándar de desarrollo')}",
                    is_mandatory=False,
                    jurisdiction="Costa Rica"
                )
            )
            
        # Agregar cláusula de IT credentials
        it_clause = LegalClause(
            clause_id=f"it_provisions_{employee_data.get('employee_id')}",
            clause_type="it_provisions",
            title="Provisiones de Tecnología de Información",
            content="El empleado recibirá credenciales de acceso a sistemas corporativos, equipamiento tecnológico y acceso a redes según lo establecido por el departamento de IT.",
            is_mandatory=True,
            jurisdiction="Costa Rica"
        )
        legal_clauses.append(it_clause)
        
        return legal_clauses

    def _personalize_clause_content(self, base_content: str, employee_data: Dict[str, Any]) -> str:
        """Personalizar contenido de cláusulas con datos del empleado"""
        personalized = base_content
        
        # Reemplazos básicos
        replacements = {
            "[EMPLOYEE_NAME]": f"{employee_data.get('first_name', '')} {employee_data.get('last_name', '')}",
            "[POSITION]": employee_data.get("position", "Empleado"),
            "[DEPARTMENT]": employee_data.get("department", "Departamento"),
            "[START_DATE]": employee_data.get("start_date", "TBD"),
            "[SALARY]": str(employee_data.get("salary", "TBD")),
            "[OFFICE]": employee_data.get("office", "Oficina Principal")
        }
        
        for placeholder, value in replacements.items():
            personalized = personalized.replace(placeholder, value)
            
        return personalized

    def _configure_benefits_package(self, employee_data: Dict[str, Any]) -> BenefitsPackage:
        """Configurar paquete de beneficios según posición"""
        position = employee_data.get("position", "").lower()
        salary = employee_data.get("salary", 0)
        
        # Determinar nivel de beneficios
        benefits_level = "standard"
        if "senior" in position or "lead" in position or salary > 80000:
            benefits_level = "senior"
        elif "manager" in position or "director" in position or "executive" in position or salary > 120000:
            benefits_level = "executive"
            
        base_benefits = self.config.benefits_packages.get(benefits_level, self.config.benefits_packages["standard"])
        
        # Personalizar beneficios
        personalized_benefits = BenefitsPackage(
            health_insurance=base_benefits.health_insurance,
            dental_insurance=base_benefits.dental_insurance,
            life_insurance=base_benefits.life_insurance,
            retirement_plan=base_benefits.retirement_plan,
            vacation_days=base_benefits.vacation_days,
            sick_days=base_benefits.sick_days,
            personal_days=base_benefits.personal_days,
            professional_development=base_benefits.professional_development,
            gym_membership=base_benefits.gym_membership,
            meal_allowance=base_benefits.meal_allowance,
            transport_allowance=base_benefits.transport_allowance
        )
        
        return personalized_benefits

    def _assess_compliance_requirements(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluar requisitos de compliance"""
        position = employee_data.get("position", "").lower()
        department = employee_data.get("department", "").lower()
        salary = employee_data.get("salary", 0)
        
        compliance_requirements = {
            "background_check": True,
            "reference_verification": True,
            "education_verification": "engineer" in position or "developer" in position,
            "drug_screening": False,  # No común en Costa Rica
            "financial_check": "executive" in position or salary > 150000,
            "security_clearance": department in ["security", "finance", "legal"],
            "work_permit_verification": employee_data.get("nationality", "").lower() != "costarricense",
            "tax_compliance": True,
            "social_security_registration": True,
            "professional_license_check": position in ["legal", "accounting", "medical"],
            "compliance_training_required": True,
            "data_protection_agreement": True,
            "code_of_conduct_acknowledgment": True
        }
        
        # Requisitos específicos por jurisdicción (Costa Rica)
        costa_rica_requirements = {
            "ccss_registration": True,  # Caja Costarricense de Seguro Social
            "ins_registration": True,   # Instituto Nacional de Seguros
            "labor_ministry_notification": True,
            "municipal_license": department in ["sales", "marketing"] and "field" in position,
            "professional_college_registration": position in ["engineering", "legal", "accounting"]
        }
        
        compliance_requirements.update(costa_rica_requirements)
        
        return {
            "requirements": compliance_requirements,
            "compliance_level": ComplianceLevel.ENHANCED.value if any([
                "executive" in position, 
                salary > 150000,
                department in ["security", "finance", "legal"]
            ]) else ComplianceLevel.STANDARD.value,
            "jurisdiction": "Costa Rica",
            "estimated_completion_days": 5 if compliance_requirements["background_check"] else 2,
            "required_documents": [
                "Cédula de identidad",
                "Certificado de antecedentes penales",
                "Constancia salarial CCSS",
                "Comprobante de domicilio",
                "Títulos académicos"
            ],
            "regulatory_compliance": [
                "Código de Trabajo de Costa Rica",
                "Ley de Protección de Datos Personales N° 8968",
                "Reglamento de Salud Ocupacional"
            ]
        }

    def _setup_approval_workflow(self, employee_data: Dict[str, Any], 
                                compliance_requirements: Dict[str, Any]) -> List[str]:
        """Configurar workflow de aprobación"""
        position = employee_data.get("position", "").lower()
        salary = employee_data.get("salary", 0)
        compliance_level = compliance_requirements.get("compliance_level", "standard")
        
        workflow_steps = [
            "1. HR Initial Review",
            "2. Position Requirements Verification",
            "3. Salary Band Approval"
        ]
        
        # Agregar pasos según nivel
        if "senior" in position or salary > 80000:
            workflow_steps.append("4. Department Manager Approval")
            
        if "manager" in position or "director" in position:
            workflow_steps.append("5. VP/Director Approval")
            
        if "executive" in position or salary > 150000:
            workflow_steps.extend([
                "6. Executive Committee Review",
                "7. Board Approval (if required)"
            ])
            
        # Revisión legal si es necesario
        if compliance_level == ComplianceLevel.ENHANCED.value:
            workflow_steps.append("Legal Department Review")
            
        # Pasos finales
        workflow_steps.extend([
            "Contract Generation",
            "Legal Validation",
            "Signature Process",
            "Document Archival"
        ])
        
        return workflow_steps

    async def _simulate_processing_delay(self, seconds: float):
        """Simular delay de procesamiento HR"""
        import asyncio
        await asyncio.sleep(min(seconds, 3.0))  # Máximo 3 segundos para testing

    def get_request_status(self, request_id: str) -> Dict[str, Any]:
        """Obtener estado de una solicitud"""
        if request_id in self.active_requests:
            return {
                "found": True,
                "request_id": request_id,
                **self.active_requests[request_id]
            }
        return {"found": False, "request_id": request_id}

    def get_department_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del departamento HR"""
        return {
            "active_requests": len(self.active_requests),
            "contract_templates": len(self.config.contract_templates),
            "legal_clauses": len(self.config.legal_clause_library),
            "benefits_packages": len(self.config.benefits_packages),
            "average_processing_time": "6.5 minutes",
            "compliance_rate": "98.5%",
            "current_load": "normal",
            "legal_review_queue": random.randint(0, 3)
        }

    def generate_contract_preview(self, employee_data: Dict[str, Any], 
                                it_credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Generar preview del contrato"""
        try:
            template = self._select_contract_template(employee_data)
            benefits = self._configure_benefits_package(employee_data)
            
            contract_preview = {
                "employee_name": f"{employee_data.get('first_name', '')} {employee_data.get('last_name', '')}",
                "position": employee_data.get("position"),
                "department": employee_data.get("department"),
                "start_date": employee_data.get("start_date"),
                "salary": employee_data.get("salary"),
                "currency": employee_data.get("currency", "USD"),
                "benefits_summary": {
                    "vacation_days": benefits.vacation_days,
                    "health_insurance": benefits.health_insurance.get("provider", "CCSS"),
                    "professional_development": benefits.professional_development.get("annual_budget", 0) if benefits.professional_development else 0
                },
                "it_provisions": {
                    "email": it_credentials.get("email", ""),
                    "username": it_credentials.get("username", ""),
                    "equipment_assigned": bool(it_credentials.get("equipment_assignment"))
                },
                "contract_type": template.get("template_type", "full_time_engineer"),
                "jurisdiction": "Costa Rica",
                "estimated_pages": random.randint(12, 18)
            }
            
            return {
                "success": True,
                "contract_preview": contract_preview,
                "generation_ready": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error generating contract preview: {str(e)}"
            }