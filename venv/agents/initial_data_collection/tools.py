from typing import Dict, Any, List, Optional
import re
from datetime import datetime, date
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from core.logging_config import get_audit_logger

logger = get_audit_logger("data_collection_tools")

class EmailParserInput(BaseModel):
    email_body: str = Field(description="Cuerpo del email a procesar")

class DataExtractorInput(BaseModel):
    parsed_content: Dict[str, Any] = Field(description="Contenido parseado del email")

class FormatValidatorInput(BaseModel):
    employee_data: Dict[str, Any] = Field(description="Datos del empleado a validar")

class QualityAssessorInput(BaseModel):
    employee_data: Dict[str, Any] = Field(description="Datos del empleado para evaluar calidad")

@tool(args_schema=EmailParserInput)
def email_parser_tool(email_body: str) -> Dict[str, Any]:
    """
    Parsea el contenido de un email de onboarding y extrae la estructura de datos.
    
    Args:
        email_body: Cuerpo del email en texto plano
        
    Returns:
        Diccionario con los datos estructurados encontrados
    """
    try:
        logger.info("Iniciando parseo de email")
        
        # Patrones de extracción para diferentes campos
        patterns = {
            # Información básica
            "id_card": r"Id Card\s*[|:]\s*([^\n\r]+)",
            "type_of_hire": r"Type of Hire\s*[|:]\s*([^\n\r]+)",
            "type_of_information": r"Type of information\s*[|:]\s*([^\n\r]+)",
            "passport": r"Passport\s*[|:]\s*([^\n\r]+)",
            "first_name": r"First Name\s*[|:]\s*([^\n\r]+)",
            "middle_name": r"Middle Name\s*[|:]\s*([^\n\r]+)",
            "name_of_preference": r"Name of Preference\s*[|:]\s*([^\n\r]+)",
            "last_name": r"Last Name\s*[|:]\s*([^\n\r]+)",
            "mothers_lastname": r"Mother's Lastname\s*[|:]\s*([^\n\r]+)",
            
            # Información personal
            "gender": r"Gender\s*[|:]\s*([^\n\r]+)",
            "english_level": r"English level\s*[|:]\s*([^\n\r]+)",
            "birth_date": r"Birth date\s*[|:]\s*([^\n\r]+)",
            "university": r"University\s*[|:]\s*([^\n\r]+)",
            "career": r"Career\s*[|:]\s*([^\n\r]+)",
            "country_of_birth": r"Country of birth\s*[|:]\s*([^\n\r]+)",
            "marital_status": r"Marital status\s*[|:]\s*([^\n\r]+)",
            "children": r"Children\s*[|:]\s*([^\n\r]+)",
            "nationality": r"Nationality\s*[|:]\s*([^\n\r]+)",
            "district": r"District\s*[|:]\s*([^\n\r]+)",
            
            # Detalles de posición
            "start_date": r"Start Date\s*[|:]\s*([^\n\r]+)",
            "customer": r"Customer\s*[|:]\s*([^\n\r]+)",
            "client_interview": r"Client Interview\s*[|:]\s*([^\n\r]+)",
            "position": r"Position\s*[|:]\s*([^\n\r]+)",
            "position_area": r"Position Area\s*[|:]\s*([^\n\r]+)",
            "technology": r"Technology\s*[|:]\s*([^\n\r]+)",
            
            # Información del proyecto
            "project_manager": r"Project Manager\s*[|:]\s*([^\n\r]+)",
            "office": r"Office\s*[|:]\s*([^\n\r]+)",
            "collaborator_type": r"Collaborator Type\s*[|:]\s*([^\n\r]+)",
            "billable_type": r"Billable Type\s*[|:]\s*([^\n\r]+)",
            "contracting_type": r"Contracting Type\s*[|:]\s*([^\n\r]+)",
            "contracting_time": r"Contracting Time\s*[|:]\s*([^\n\r]+)",
            "contracting_office": r"Contracting office\s*[|:]\s*([^\n\r]+)",
            "reference_market": r"Reference Market\s*[|:]\s*([^\n\r]+)",
            "gm_total": r"GM Total\s*[|:]\s*([^\n\r]+)",
            "partner_name": r"Partner name\s*[|:]\s*([^\n\r]+)",
            "project_need": r"Project Need\s*[|:]\s*([^\n\r]+)",
            "user_will_provide_windows_laptop": r"The user will provide Windows Laptop\s*[|:]\s*([^\n\r]+)",
            
            # Detalles de dirección
            "country": r"Country\s*[|:]\s*([^\n\r]+)",
            "city": r"City\s*[|:]\s*([^\n\r]+)",
            "current_address": r"Current Address\s*[|:]\s*([^\n\r]+)",
            "email": r"Email\s*[|:]\s*([^\n\r]+)",
            "comments": r"Comments\s*[|:]\s*([^\n\r]+)"
        }
        
        extracted_data = {}
        
        for field, pattern in patterns.items():
            match = re.search(pattern, email_body, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                # Limpiar valores vacíos o guiones
                if value and value != "-" and value.lower() != "none":
                    extracted_data[field] = value
        
        logger.info(f"Parseo completado. Campos extraídos: {len(extracted_data)}")
        
        return {
            "success": True,
            "extracted_data": extracted_data,
            "fields_found": len(extracted_data),
            "processing_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en parseo de email: {e}")
        return {
            "success": False,
            "error": str(e),
            "extracted_data": {},
            "fields_found": 0
        }

@tool(args_schema=DataExtractorInput)
def data_extractor_tool(parsed_content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrae y estructura los datos parseados en el formato del schema definido.
    
    Args:
        parsed_content: Contenido parseado del email
        
    Returns:
        Datos estructurados según el schema EmployeeData
    """
    try:
        logger.info("Iniciando extracción y estructuración de datos")
        
        if not parsed_content.get("success", False):
            raise Exception("Datos de entrada no válidos")
        
        extracted = parsed_content.get("extracted_data", {})
        
        # Estructurar según el schema
        structured_data = {
            "basic_info": {
                "id_card": extracted.get("id_card", ""),
                "type_of_hire": extracted.get("type_of_hire", "New Hire"),
                "type_of_information": extracted.get("type_of_information", "New collaborator entry"),
                "passport": extracted.get("passport"),
                "first_name": extracted.get("first_name", ""),
                "middle_name": extracted.get("middle_name"),
                "name_of_preference": extracted.get("name_of_preference"),
                "last_name": extracted.get("last_name", ""),
                "mothers_lastname": extracted.get("mothers_lastname")
            },
            "personal_info": {
                "gender": extracted.get("gender"),
                "english_level": extracted.get("english_level"),
                "birth_date": _parse_date(extracted.get("birth_date")),
                "university": extracted.get("university"),
                "career": extracted.get("career"),
                "country_of_birth": extracted.get("country_of_birth"),
                "marital_status": extracted.get("marital_status"),
                "children": _parse_int(extracted.get("children")),
                "nationality": extracted.get("nationality"),
                "district": extracted.get("district")
            },
            "position_details": {
                "customer": extracted.get("customer"),
                "client_interview": extracted.get("client_interview"),
                "position": extracted.get("position"),
                "position_area": extracted.get("position_area"),
                "technology": extracted.get("technology"),
                "start_date": _parse_date(extracted.get("start_date"))
            },
            "project_info": {
                "project_manager": extracted.get("project_manager"),
                "office": extracted.get("office"),
                "collaborator_type": extracted.get("collaborator_type"),
                "billable_type": extracted.get("billable_type"),
                "contracting_type": extracted.get("contracting_type"),
                "contracting_time": extracted.get("contracting_time"),
                "contracting_office": extracted.get("contracting_office"),
                "reference_market": extracted.get("reference_market"),
                "gm_total": extracted.get("gm_total"),
                "partner_name": extracted.get("partner_name"),
                "project_need": extracted.get("project_need"),
                "user_will_provide_windows_laptop": extracted.get("user_will_provide_windows_laptop")
            },
            "address_details": {
                "country": extracted.get("country"),
                "city": extracted.get("city"),
                "current_address": extracted.get("current_address"),
                "email": extracted.get("email")
            },
            "comments": extracted.get("comments")
        }
        
        logger.info("Extracción y estructuración completada exitosamente")
        
        return {
            "success": True,
            "structured_data": structured_data,
            "processing_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en extracción de datos: {e}")
        return {
            "success": False,
            "error": str(e),
            "structured_data": None
        }

@tool(args_schema=FormatValidatorInput)
def format_validator_tool(employee_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida el formato y consistencia de los datos extraídos.
    
    Args:
        employee_data: Datos del empleado a validar
        
    Returns:
        Resultado de la validación con errores encontrados
    """
    try:
        logger.info("Iniciando validación de formato")
        
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "field_validations": {}
        }
        
        # Validar campos requeridos
        required_fields = [
            ("basic_info.id_card", "ID Card"),
            ("basic_info.first_name", "First Name"),
            ("basic_info.last_name", "Last Name")
        ]
        
        for field_path, field_name in required_fields:
            if not _get_nested_value(employee_data, field_path):
                validation_results["errors"].append(f"{field_name} es requerido")
                validation_results["is_valid"] = False
                validation_results["field_validations"][field_path] = "missing"
            else:
                validation_results["field_validations"][field_path] = "valid"
        
        # Validar formato de email si existe
        email = _get_nested_value(employee_data, "address_details.email")
        if email:
            if not _validate_email_format(email):
                validation_results["errors"].append("Formato de email inválido")
                validation_results["field_validations"]["address_details.email"] = "invalid_format"
            else:
                validation_results["field_validations"]["address_details.email"] = "valid"
        
        # Validar fechas
        birth_date = _get_nested_value(employee_data, "personal_info.birth_date")
        if birth_date and not _validate_date_format(birth_date):
            validation_results["warnings"].append("Formato de fecha de nacimiento puede ser inválido")
        
        start_date = _get_nested_value(employee_data, "position_details.start_date")
        if start_date and not _validate_date_format(start_date):
            validation_results["warnings"].append("Formato de fecha de inicio puede ser inválido")
        
        logger.info(f"Validación completada. Válido: {validation_results['is_valid']}")
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Error en validación: {e}")
        return {
            "is_valid": False,
            "errors": [f"Error en validación: {str(e)}"],
            "warnings": [],
            "field_validations": {}
        }

@tool(args_schema=QualityAssessorInput)
def quality_assessor_tool(employee_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evalúa la calidad y completitud de los datos extraídos.
    
    Args:
        employee_data: Datos del empleado para evaluar
        
    Returns:
        Puntuación de calidad y análisis de completitud
    """
    try:
        logger.info("Iniciando evaluación de calidad de datos")
        
               # Definir campos y sus pesos
        field_weights = {
            # Campos críticos (peso alto)
            "basic_info.id_card": 3.0,
            "basic_info.first_name": 3.0,
            "basic_info.last_name": 3.0,
            "position_details.position": 2.5,
            "position_details.start_date": 2.5,
            
            # Campos importantes (peso medio)
            "basic_info.passport": 2.0,
            "personal_info.birth_date": 2.0,
            "address_details.email": 2.0,
            "position_details.customer": 1.5,
            "project_info.office": 1.5,
            
            # Campos opcionales (peso bajo)
            "basic_info.middle_name": 1.0,
            "personal_info.gender": 1.0,
            "personal_info.nationality": 1.0,
            "address_details.country": 1.0
        }
        
        total_weight = sum(field_weights.values())
        achieved_weight = 0.0
        missing_fields = []
        present_fields = []
        
        for field_path, weight in field_weights.items():
            value = _get_nested_value(employee_data, field_path)
            if value and str(value).strip():
                achieved_weight += weight
                present_fields.append(field_path)
            else:
                missing_fields.append(field_path)
        
        # Calcular puntuación de calidad (0-100)
        quality_score = (achieved_weight / total_weight) * 100
        
        # Determinar si requiere revisión manual
        requires_manual_review = (
            quality_score < 80 or
            len([f for f in missing_fields if field_weights[f] >= 2.5]) > 0
        )
        
        assessment = {
            "quality_score": round(quality_score, 2),
            "completeness_percentage": round((len(present_fields) / len(field_weights)) * 100, 2),
            "missing_fields": missing_fields,
            "present_fields": present_fields,
            "total_fields_evaluated": len(field_weights),
            "critical_fields_missing": [f for f in missing_fields if field_weights.get(f, 0) >= 2.5],
            "requires_manual_review": requires_manual_review,
            "assessment_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Evaluación de calidad completada. Puntuación: {quality_score:.2f}")
        
        return assessment
        
    except Exception as e:
        logger.error(f"Error en evaluación de calidad: {e}")
        return {
            "quality_score": 0.0,
            "completeness_percentage": 0.0,
            "missing_fields": [],
            "present_fields": [],
            "requires_manual_review": True,
            "error": str(e)
        }

# Funciones auxiliares
def _parse_date(date_str: Optional[str]) -> Optional[str]:
    """Parsear fecha en formato ISO"""
    if not date_str:
        return None
    
    try:
        # Intentar varios formatos de fecha
        formats = ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"]
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt).date()
                return parsed.isoformat()
            except ValueError:
                continue
        return date_str  # Retornar original si no se puede parsear
    except:
        return date_str

def _parse_int(int_str: Optional[str]) -> Optional[int]:
    """Parsear entero de string"""
    if not int_str:
        return None
    try:
        return int(int_str)
    except ValueError:
        return None

def _get_nested_value(data: Dict[str, Any], path: str) -> Any:
    """Obtener valor anidado usando notación punto"""
    try:
        keys = path.split('.')
        value = data
        for key in keys:
            value = value.get(key) if isinstance(value, dict) else None
            if value is None:
                break
        return value
    except:
        return None

def _validate_email_format(email: str) -> bool:
    """Validar formato básico de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def _validate_date_format(date_str: str) -> bool:
    """Validar si la fecha tiene un formato reconocible"""
    if not date_str:
        return False
    
    formats = ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"]
    for fmt in formats:
        try:
            datetime.strptime(date_str, fmt)
            return True
        except ValueError:
            continue
    return False