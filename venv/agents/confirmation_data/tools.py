from typing import Dict, Any, List, Optional
import re
from datetime import datetime, date, timedelta
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from core.logging_config import get_audit_logger
from core.observability import observability_manager

logger = get_audit_logger("confirmation_data_tools")

class SalaryValidatorInput(BaseModel):
    salary_data: Dict[str, Any] = Field(description="Datos salariales a validar")

class ContractValidatorInput(BaseModel):
    contract_data: Dict[str, Any] = Field(description="Datos contractuales a validar")

class OfferGeneratorInput(BaseModel):
    employee_data: Dict[str, Any] = Field(description="Datos del empleado para generar oferta")

class ComplianceCheckerInput(BaseModel):
    contract_terms: Dict[str, Any] = Field(description="Términos contractuales para verificar compliance")

@tool(args_schema=SalaryValidatorInput)
@observability_manager.trace_agent_execution("confirmation_data_agent")
def salary_validator_tool(salary_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida información salarial contra políticas de la empresa y rangos del mercado.
    
    Args:
        salary_data: Datos salariales incluyendo posición, salario, moneda
        
    Returns:
        Resultado de la validación salarial
    """
    try:
        logger.info("Iniciando validación salarial")
        
        # Extraer datos relevantes
        position = salary_data.get("position", "").lower()
        salary = salary_data.get("salary", 0)
        currency = salary_data.get("currency", "USD")
        location = salary_data.get("location", "").lower()
        
        # Rangos salariales simulados (en producción vendría de una base de datos)
        salary_bands = {
            "data engineer": {"min": 50000, "max": 120000, "currency": "USD"},
            "software engineer": {"min": 60000, "max": 130000, "currency": "USD"},
            "project manager": {"min": 70000, "max": 140000, "currency": "USD"},
            "analyst": {"min": 40000, "max": 80000, "currency": "USD"},
            "senior": {"multiplier": 1.3},  # 30% más para roles senior
            "junior": {"multiplier": 0.8},  # 20% menos para roles junior
        }
        
        validation_results = {
            "is_valid": False,
            "within_band": False,
            "band_min": 0,
            "band_max": 0,
            "salary_provided": salary,
            "currency": currency,
            "warnings": [],
            "recommendations": []
        }
        
        # Buscar banda salarial apropiada
        band_found = None
        for role, band in salary_bands.items():
            if role in position:
                band_found = band.copy()
                break
        
        if not band_found:
            # Usar banda por defecto si no se encuentra la posición específica
            band_found = {"min": 45000, "max": 100000, "currency": "USD"}
            validation_results["warnings"].append("Posición no encontrada en bandas salariales, usando rango por defecto")
        
        # Aplicar multiplicadores según seniority
        if "senior" in position:
            band_found["min"] = int(band_found["min"] * salary_bands["senior"]["multiplier"])
            band_found["max"] = int(band_found["max"] * salary_bands["senior"]["multiplier"])
        elif "junior" in position:
            band_found["min"] = int(band_found["min"] * salary_bands["junior"]["multiplier"])
            band_found["max"] = int(band_found["max"] * salary_bands["junior"]["multiplier"])
        
        # Ajuste por ubicación (simulado)
        location_adjustments = {
            "costa rica": 0.7,  # 30% menos que USD estándar
            "mexico": 0.6,      # 40% menos
            "colombia": 0.5,    # 50% menos
            "usa": 1.0,         # Sin ajuste
            "europe": 0.9       # 10% menos
        }
        
        location_multiplier = 1.0
        for loc, multiplier in location_adjustments.items():
            if loc in location:
                location_multiplier = multiplier
                break
        
        band_found["min"] = int(band_found["min"] * location_multiplier)
        band_found["max"] = int(band_found["max"] * location_multiplier)
        
        # Validar salario contra banda
        validation_results["band_min"] = band_found["min"]
        validation_results["band_max"] = band_found["max"]
        
        if band_found["min"] <= salary <= band_found["max"]:
            validation_results["is_valid"] = True
            validation_results["within_band"] = True
        elif salary < band_found["min"]:
            validation_results["warnings"].append(f"Salario por debajo del mínimo de banda (${band_found['min']:,})")
            validation_results["recommendations"].append(f"Considerar ajustar a al menos ${band_found['min']:,}")
        else:
            validation_results["warnings"].append(f"Salario por encima del máximo de banda (${band_found['max']:,})")
            validation_results["recommendations"].append("Requiere aprobación especial de management")
        
        # Validaciones adicionales
        if currency != "USD":
            validation_results["warnings"].append(f"Moneda {currency} requiere conversión a USD para comparación")
        
        if salary <= 0:
            validation_results["is_valid"] = False
            validation_results["warnings"].append("Salario debe ser mayor a 0")
        
        logger.info(f"Validación salarial completada. Válido: {validation_results['is_valid']}")
        
        return {
            "success": True,
            "validation_results": validation_results,
            "processing_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en validación salarial: {e}")
        return {
            "success": False,
            "error": str(e),
            "validation_results": {
                "is_valid": False,
                "warnings": [f"Error en validación: {str(e)}"]
            }
        }

@tool(args_schema=ContractValidatorInput)
@observability_manager.trace_agent_execution("confirmation_data_agent")
# ... existing code ...

def contract_validator_tool(contract_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida términos contractuales contra políticas de la empresa.
    Args:
        contract_data: Datos del contrato a validar
    Returns:
        Resultado de la validación contractual
    """
    try:
        logger.info("Iniciando validación contractual")
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "contract_checks": {}
        }
        
        # Validar fecha de inicio - manejar tanto string como date object
        start_date_value = contract_data.get("start_date")
        if start_date_value:
            try:
                # Si es un objeto date, convertirlo a string primero
                if isinstance(start_date_value, date):
                    start_date = start_date_value
                elif isinstance(start_date_value, str):
                    start_date = datetime.fromisoformat(start_date_value).date()
                else:
                    raise ValueError("Formato de fecha no soportado")
                    
                today = date.today()
                if start_date < today:
                    validation_results["errors"].append("Fecha de inicio no puede ser en el pasado")
                    validation_results["is_valid"] = False
                elif start_date > (today + timedelta(days=90)):
                    validation_results["warnings"].append("Fecha de inicio muy lejana (>90 días)")
                validation_results["contract_checks"]["start_date"] = "valid"
            except ValueError as e:
                validation_results["errors"].append(f"Formato de fecha de inicio inválido: {str(e)}")
                validation_results["is_valid"] = False
                validation_results["contract_checks"]["start_date"] = "invalid"

        # ... rest of existing validation code ...

        logger.info(f"Validación contractual completada. Válido: {validation_results['is_valid']}")
        return {
            "success": True,
            "validation_results": validation_results,
            "processing_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en validación contractual: {e}")
        return {
            "success": False,
            "error": str(e),
            "validation_results": {
                "is_valid": False,
                "errors": [f"Error en validación: {str(e)}"]
            }
        }

@tool(args_schema=OfferGeneratorInput)
@observability_manager.trace_agent_execution("confirmation_data_agent")
def offer_generator_tool(employee_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera carta de oferta digital basada en datos del empleado.
    
    Args:
        employee_data: Datos completos del empleado y contrato
        
    Returns:
        Carta de oferta generada
    """
    try:
        logger.info("Iniciando generación de carta de oferta")
        
        # Extraer información relevante
        basic_info = employee_data.get("basic_info", {})
        contract_info = employee_data.get("contract_terms", {})
        position_info = employee_data.get("position_info", {})
        
        # Plantilla de carta de oferta
        offer_template = """
CARTA DE OFERTA DE EMPLEO

Estimado/a {full_name},

Nos complace informarle que ha sido seleccionado/a para la posición de {position_title} 
en nuestro departamento de {department}.

DETALLES DE LA OFERTA:
• Posición: {position_title}
• Departamento: {department}
• Tipo de empleo: {employment_type}
• Modalidad: {work_modality}
• Fecha de inicio: {start_date}
• Salario: ${salary:,} {currency} anuales
• Período de prueba: {probation_period} días
• Ubicación: {location}

BENEFICIOS INCLUIDOS:
{benefits}

Esta oferta es válida hasta {expiration_date}.

Para aceptar esta oferta, por favor responda a este correo confirmando su aceptación.

Atentamente,
Departamento de Recursos Humanos
"""
        
        # Construir datos para la plantilla
        full_name = f"{basic_info.get('first_name', '')} {basic_info.get('last_name', '')}"
        
        # Calcular fecha de expiración (7 días desde hoy)
        expiration_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Procesar beneficios
        benefits_list = contract_info.get("benefits", [])
        benefits_text = "\n".join([f"• {benefit}" for benefit in benefits_list]) if benefits_list else "• Según políticas de la empresa"
        
        # Generar carta
        offer_letter = offer_template.format(
            full_name=full_name.strip(),
            position_title=position_info.get("position_title", "N/A"),
            department=position_info.get("department", "N/A"),
            employment_type=contract_info.get("employment_type", "Full-time"),
            work_modality=contract_info.get("work_modality", "Hybrid"),
            start_date=contract_info.get("start_date", "A definir"),
            salary=contract_info.get("salary", 0),
            currency=contract_info.get("currency", "USD"),
            probation_period=contract_info.get("probation_period", 90),
            location=position_info.get("location", "N/A"),
            benefits=benefits_text,
            expiration_date=expiration_date
        )
        
        # Generar metadata
        offer_metadata = {
            "document_type": "offer_letter",
            "employee_id": employee_data.get("employee_id", "unknown"),
            "generated_at": datetime.utcnow().isoformat(),
            "expires_at": expiration_date,
            "template_version": "1.0",
            "language": "es",
            "status": "draft"
        }
        
        logger.info("Carta de oferta generada exitosamente")
        
        return {
            "success": True,
            "offer_letter": offer_letter,
            "metadata": offer_metadata,
            "processing_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generando carta de oferta: {e}")
        return {
            "success": False,
            "error": str(e),
            "offer_letter": None,
            "metadata": {}
        }

@tool(args_schema=ComplianceCheckerInput)
@observability_manager.trace_agent_execution("confirmation_data_agent")
def compliance_checker_tool(contract_terms: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verifica compliance de términos contractuales con regulaciones locales.
    
    Args:
        contract_terms: Términos contractuales a verificar
        
    Returns:
        Resultado de verificación de compliance
    """
    try:
        logger.info("Iniciando verificación de compliance")
        
        compliance_results = {
            "is_compliant": True,
            "violations": [],
            "warnings": [],
            "recommendations": [],
            "compliance_score": 100.0,
            "checks_performed": {}
        }
        
        # Verificación de salario mínimo (por país)
        salary = contract_terms.get("salary", 0)
        location = contract_terms.get("location", "").lower()
        
        minimum_wages = {
            "costa rica": 400,  # USD mensual aprox
            "mexico": 300,
            "colombia": 250,
            "usa": 1500,
            "default": 500
        }
        
        min_wage = minimum_wages.get(location.split()[0] if location else "default", minimum_wages["default"])
        monthly_salary = salary / 12 if salary > 0 else 0
        
        if monthly_salary < min_wage:
            compliance_results["violations"].append(f"Salario por debajo del mínimo legal (${min_wage}/mes)")
            compliance_results["is_compliant"] = False
            compliance_results["compliance_score"] -= 25
        
        compliance_results["checks_performed"]["minimum_wage"] = "passed" if monthly_salary >= min_wage else "failed"
        
        # Verificación de horas de trabajo
        employment_type = contract_terms.get("employment_type", "").lower()
        if employment_type == "full-time":
            # Verificar que no exceda 48 horas semanales (estándar internacional)
            max_hours = contract_terms.get("max_weekly_hours", 40)
            if max_hours > 48:
                compliance_results["violations"].append(f"Horas semanales ({max_hours}) exceden límite legal (48)")
                compliance_results["is_compliant"] = False
                compliance_results["compliance_score"] -= 15
        
        compliance_results["checks_performed"]["working_hours"] = "passed"
        
        # Verificación de período de prueba
        probation = contract_terms.get("probation_period", 0)
        max_probation_days = {
            "costa rica": 90,
            "mexico": 90,
            "colombia": 60,
            "usa": 90,
            "default": 90
        }
        
        max_allowed = max_probation_days.get(location.split()[0] if location else "default", 90)
        if probation > max_allowed:
            compliance_results["warnings"].append(f"Período de prueba ({probation} días) excede recomendado ({max_allowed} días)")
            compliance_results["compliance_score"] -= 5
        
        compliance_results["checks_performed"]["probation_period"] = "passed" if probation <= max_allowed else "warning"
        
        # Verificación de beneficios obligatorios
        benefits = contract_terms.get("benefits", [])
        required_benefits = ["seguro_medico", "vacaciones", "aguinaldo"]
        
        for required in required_benefits:
            if not any(required.lower() in benefit.lower() for benefit in benefits):
                compliance_results["warnings"].append(f"Beneficio '{required}' no especificado explícitamente")
                compliance_results["compliance_score"] -= 3
        
        compliance_results["checks_performed"]["mandatory_benefits"] = "review_needed"
        
        # Recomendaciones generales
        if compliance_results["compliance_score"] < 90:
            compliance_results["recommendations"].append("Revisar términos contractuales con legal")
        
        if not compliance_results["violations"]:
            compliance_results["recommendations"].append("Contrato cumple con verificaciones básicas de compliance")
        
        logger.info(f"Verificación de compliance completada. Score: {compliance_results['compliance_score']}")
        
        return {
            "success": True,
            "compliance_results": compliance_results,
            "processing_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en verificación de compliance: {e}")
        return {
            "success": False,
            "error": str(e),
            "compliance_results": {
                "is_compliant": False,
                "violations": [f"Error en verificación: {str(e)}"],
                "compliance_score": 0.0
            }
        }