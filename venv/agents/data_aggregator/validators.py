from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, date, timedelta
import re
from enum import Enum
from loguru import logger

from .schemas import FieldValidationStatus, ValidationLevel

class ValidatorType(str, Enum):
    """Tipos de validadores disponibles"""
    REQUIRED = "required"
    FORMAT = "format"
    RANGE = "range"
    PATTERN = "pattern"
    CROSS_REFERENCE = "cross_reference"
    BUSINESS_RULE = "business_rule"

class FieldValidator:
    """Validador base para campos específicos"""
    
    def __init__(self, field_name: str, validator_type: ValidatorType, config: Dict[str, Any] = None):
        self.field_name = field_name
        self.validator_type = validator_type
        self.config = config or {}
        
    def validate(self, value: Any, context: Dict[str, Any] = None) -> Tuple[FieldValidationStatus, List[str], float]:
        """
        Validar un valor específico
        
        Returns:
            Tuple de (status, errores/warnings, confidence_score)
        """
        raise NotImplementedError

class RequiredFieldValidator(FieldValidator):
    """Validador para campos obligatorios"""
    
    def __init__(self, field_name: str, allow_empty_string: bool = False):
        super().__init__(field_name, ValidatorType.REQUIRED, {"allow_empty_string": allow_empty_string})
    
    def validate(self, value: Any, context: Dict[str, Any] = None) -> Tuple[FieldValidationStatus, List[str], float]:
        if value is None:
            return FieldValidationStatus.MISSING, [f"{self.field_name} es requerido"], 0.0
        
        if not self.config.get("allow_empty_string", False) and isinstance(value, str) and not value.strip():
            return FieldValidationStatus.MISSING, [f"{self.field_name} no puede estar vacío"], 0.0
            
        return FieldValidationStatus.VALID, [], 100.0

class EmailValidator(FieldValidator):
    """Validador para emails"""
    
    def __init__(self, field_name: str = "email"):
        super().__init__(field_name, ValidatorType.FORMAT)
        
    def validate(self, value: Any, context: Dict[str, Any] = None) -> Tuple[FieldValidationStatus, List[str], float]:
        if not value:
            return FieldValidationStatus.MISSING, ["Email es requerido"], 0.0
            
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, str(value)):
            return FieldValidationStatus.ERROR, ["Formato de email inválido"], 0.0
            
        # Verificar dominio corporativo si está configurado
        corporate_domains = context.get("corporate_domains", []) if context else []
        if corporate_domains:
            domain = str(value).split('@')[1].lower()
            if domain not in [d.lower() for d in corporate_domains]:
                return FieldValidationStatus.WARNING, [f"Email no es de dominio corporativo: {domain}"], 70.0
                
        return FieldValidationStatus.VALID, [], 100.0

class CostaRicaIDValidator(FieldValidator):
    """Validador para cédulas de Costa Rica"""
    
    def __init__(self, field_name: str = "id_card"):
        super().__init__(field_name, ValidatorType.PATTERN)
        
    def validate(self, value: Any, context: Dict[str, Any] = None) -> Tuple[FieldValidationStatus, List[str], float]:
        if not value:
            return FieldValidationStatus.MISSING, ["Número de cédula es requerido"], 0.0
            
        id_str = str(value).strip()
        
        # Formatos aceptados: 1-2345-6789 o 123456789
        patterns = [
            r'^\d{1}-\d{4}-\d{4}$',  # Formato con guiones
            r'^\d{9}$',              # Formato sin guiones
            r'^\d{1}\d{4}\d{4}$'     # Formato compacto
        ]
        
        valid_format = any(re.match(pattern, id_str) for pattern in patterns)
        
        if not valid_format:
            return FieldValidationStatus.ERROR, ["Formato de cédula inválido. Use: 1-2345-6789 o 123456789"], 0.0
            
        # Validar estructura básica
        digits_only = re.sub(r'[^0-9]', '', id_str)
        
        if len(digits_only) != 9:
            return FieldValidationStatus.ERROR, ["Cédula debe tener exactamente 9 dígitos"], 0.0
            
        # Validar provincia (primer dígito)
        province_digit = int(digits_only[0])
        if province_digit < 1 or province_digit > 9:
            return FieldValidationStatus.ERROR, ["Primer dígito de cédula inválido (debe ser 1-9)"], 0.0
            
        return FieldValidationStatus.VALID, [], 100.0

class DateValidator(FieldValidator):
    """Validador para fechas"""
    
    def __init__(self, field_name: str, min_date: date = None, max_date: date = None):
        super().__init__(field_name, ValidatorType.RANGE, {
            "min_date": min_date,
            "max_date": max_date
        })
        
    def validate(self, value: Any, context: Dict[str, Any] = None) -> Tuple[FieldValidationStatus, List[str], float]:
        if not value:
            return FieldValidationStatus.MISSING, [f"{self.field_name} es requerido"], 0.0
            
        # Convertir a date si es necesario
        if isinstance(value, str):
            try:
                # Intentar diferentes formatos
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
                    try:
                        parsed_date = datetime.strptime(value, fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    return FieldValidationStatus.ERROR, ["Formato de fecha inválido"], 0.0
            except:
                return FieldValidationStatus.ERROR, ["No se pudo parsear la fecha"], 0.0
        elif isinstance(value, datetime):
            parsed_date = value.date()
        elif isinstance(value, date):
            parsed_date = value
        else:
            return FieldValidationStatus.ERROR, ["Tipo de fecha inválido"], 0.0
            
        warnings = []
        
        # Validar rango
        min_date = self.config.get("min_date")
        max_date = self.config.get("max_date")
        
        if min_date and parsed_date < min_date:
            return FieldValidationStatus.ERROR, [f"{self.field_name} no puede ser anterior a {min_date}"], 0.0
            
        if max_date and parsed_date > max_date:
            return FieldValidationStatus.ERROR, [f"{self.field_name} no puede ser posterior a {max_date}"], 0.0
            
        # Validaciones específicas por campo
        if self.field_name == "birth_date":
            today = date.today()
            age = today.year - parsed_date.year - ((today.month, today.day) < (parsed_date.month, parsed_date.day))
            
            if age < 18:
                return FieldValidationStatus.ERROR, ["Empleado debe ser mayor de 18 años"], 0.0
            elif age > 70:
                warnings.append("Edad inusual para nuevo empleado")
                
        elif self.field_name == "start_date":
            today = date.today()
            days_diff = (parsed_date - today).days
            
            if days_diff < -30:  # Más de 30 días en el pasado
                return FieldValidationStatus.ERROR, ["Fecha de inicio no puede ser muy antigua"], 0.0
            elif days_diff > 365:  # Más de 1 año en el futuro
                warnings.append("Fecha de inicio muy lejana")
                
        status = FieldValidationStatus.WARNING if warnings else FieldValidationStatus.VALID
        confidence = 85.0 if warnings else 100.0
        
        return status, warnings, confidence

class SalaryValidator(FieldValidator):
    """Validador para salarios"""
    
    def __init__(self, field_name: str = "salary", min_salary: float = None, max_salary: float = None, currency: str = "USD"):
        super().__init__(field_name, ValidatorType.RANGE, {
            "min_salary": min_salary,
            "max_salary": max_salary,
            "currency": currency
        })
        
    def validate(self, value: Any, context: Dict[str, Any] = None) -> Tuple[FieldValidationStatus, List[str], float]:
        if not value:
            return FieldValidationStatus.MISSING, ["Salario es requerido"], 0.0
            
        try:
            salary = float(value)
        except (ValueError, TypeError):
            return FieldValidationStatus.ERROR, ["Salario debe ser un número válido"], 0.0
            
        if salary <= 0:
            return FieldValidationStatus.ERROR, ["Salario debe ser mayor a 0"], 0.0
            
        warnings = []
        currency = self.config.get("currency", "USD")
        
        # Rangos típicos por moneda
        salary_ranges = {
            "USD": {"min": 30000, "max": 200000, "typical_min": 40000, "typical_max": 120000},
            "CRC": {"min": 600000, "max": 20000000, "typical_min": 800000, "typical_max": 3000000}
        }
        
        ranges = salary_ranges.get(currency, salary_ranges["USD"])
        
        # Validar rangos configurados
        min_salary = self.config.get("min_salary") or ranges["min"]
        max_salary = self.config.get("max_salary") or ranges["max"]
        
        if salary < min_salary:
            return FieldValidationStatus.ERROR, [f"Salario muy bajo para {currency}: mínimo {min_salary:,.0f}"], 0.0
            
        if salary > max_salary:
            return FieldValidationStatus.ERROR, [f"Salario muy alto para {currency}: máximo {max_salary:,.0f}"], 0.0
            
        # Advertencias para rangos atípicos
        if salary < ranges["typical_min"]:
            warnings.append(f"Salario bajo para {currency}: {salary:,.0f}")
        elif salary > ranges["typical_max"]:
            warnings.append(f"Salario alto para {currency}: {salary:,.0f}")
            
        status = FieldValidationStatus.WARNING if warnings else FieldValidationStatus.VALID
        confidence = 85.0 if warnings else 100.0
        
        return status, warnings, confidence

class PositionValidator(FieldValidator):
    """Validador para posiciones/cargos"""
    
    def __init__(self, field_name: str = "position"):
        super().__init__(field_name, ValidatorType.BUSINESS_RULE)
        
    def validate(self, value: Any, context: Dict[str, Any] = None) -> Tuple[FieldValidationStatus, List[str], float]:
        if not value:
            return FieldValidationStatus.MISSING, ["Posición es requerida"], 0.0
            
        position_str = str(value).strip()
        
        if len(position_str) < 3:
            return FieldValidationStatus.ERROR, ["Nombre de posición muy corto"], 0.0
            
        # Lista de posiciones válidas/comunes
        valid_positions = [
            "data engineer", "software engineer", "developer", "analyst", "manager",
            "coordinator", "specialist", "consultant", "architect", "lead", 
            "senior", "junior", "intern", "trainee"
        ]
        
        position_lower = position_str.lower()
        is_valid_position = any(pos in position_lower for pos in valid_positions)
        
        warnings = []
        if not is_valid_position:
            warnings.append("Posición no está en lista de posiciones estándar")
            
        # Validar consistencia con área
        department = context.get("department", "") if context else ""
        if department:
            # Validaciones específicas por departamento
            if "engineering" in department.lower() and "engineer" not in position_lower:
                warnings.append("Posición puede no coincidir con departamento de Engineering")
                
        status = FieldValidationStatus.WARNING if warnings else FieldValidationStatus.VALID
        confidence = 80.0 if warnings else 100.0
        
        return status, warnings, confidence

class CrossReferenceValidator(FieldValidator):
    """Validador para consistencia entre campos relacionados"""
    
    def __init__(self, primary_field: str, reference_field: str, validation_rule: str):
        super().__init__(primary_field, ValidatorType.CROSS_REFERENCE, {
            "reference_field": reference_field,
            "validation_rule": validation_rule
        })
        
    def validate(self, value: Any, context: Dict[str, Any] = None) -> Tuple[FieldValidationStatus, List[str], float]:
        if not context:
            return FieldValidationStatus.VALID, [], 100.0
            
        reference_field = self.config["reference_field"]
        reference_value = context.get(reference_field)
        validation_rule = self.config["validation_rule"]
        
        if not value or not reference_value:
            return FieldValidationStatus.VALID, [], 100.0  # No validar si faltan datos
            
        warnings = []
        
        if validation_rule == "name_consistency":
            # Validar que nombres sean consistentes
            primary_name = str(value).lower().strip()
            reference_name = str(reference_value).lower().strip()
            
            # Calcular similitud básica
            if primary_name != reference_name:
                # Verificar si uno contiene al otro
                if primary_name not in reference_name and reference_name not in primary_name:
                    warnings.append(f"Inconsistencia entre {self.field_name} y {reference_field}")
                    
        elif validation_rule == "date_logical_order":
            # Validar orden lógico de fechas
            try:
                date1 = self._parse_date(value)
                date2 = self._parse_date(reference_value)
                
                if date1 and date2:
                    if self.field_name == "start_date" and reference_field == "birth_date":
                        if date1 <= date2:
                            return FieldValidationStatus.ERROR, ["Fecha de inicio debe ser posterior a fecha de nacimiento"], 0.0
                            
            except:
                pass  # Ignorar errores de parsing
                
        status = FieldValidationStatus.WARNING if warnings else FieldValidationStatus.VALID
        confidence = 85.0 if warnings else 100.0
        
        return status, warnings, confidence
    
    def _parse_date(self, value: Any) -> Optional[date]:
        """Parsear fecha de diferentes formatos"""
        if isinstance(value, date):
            return value
        elif isinstance(value, datetime):
            return value.date()
        elif isinstance(value, str):
            try:
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
                    try:
                        return datetime.strptime(value, fmt).date()
                    except ValueError:
                        continue
            except:
                pass
        return None

class ValidationEngine:
    """Motor de validación que coordina todos los validadores"""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        self.validation_level = validation_level
        self.validators = self._initialize_validators()
        
    def _initialize_validators(self) -> Dict[str, List[FieldValidator]]:
        """Inicializar validadores por campo"""
        validators = {
            "employee_id": [
                RequiredFieldValidator("employee_id")
            ],
            "first_name": [
                RequiredFieldValidator("first_name")
            ],
            "last_name": [
                RequiredFieldValidator("last_name")
            ],
            "email": [
                EmailValidator("email")
            ],
            "id_card": [
                CostaRicaIDValidator("id_card")
            ],
            "birth_date": [
                DateValidator("birth_date", 
                           min_date=date(1950, 1, 1), 
                           max_date=date.today())
            ],
            "start_date": [
                DateValidator("start_date",
                           min_date=date.today() - timedelta(days=30),
                           max_date=date.today() + timedelta(days=365))
            ],
            "salary": [
                SalaryValidator("salary")
            ],
            "position": [
                PositionValidator("position")
            ]
        }
        
        # Agregar validadores de cross-reference
        if self.validation_level in [ValidationLevel.STRICT, ValidationLevel.CRITICAL]:
            validators["full_name_consistency"] = [
                CrossReferenceValidator("first_name", "extracted_name", "name_consistency")
            ]
            validators["date_consistency"] = [
                CrossReferenceValidator("start_date", "birth_date", "date_logical_order")
            ]
            
        return validators
    
    def validate_field(self, field_name: str, value: Any, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validar un campo específico"""
        field_validators = self.validators.get(field_name, [])
        
        if not field_validators:
            return {
                "field_name": field_name,
                "status": FieldValidationStatus.VALID,
                "messages": [],
                "confidence_score": 100.0
            }
            
        all_messages = []
        min_confidence = 100.0
        worst_status = FieldValidationStatus.VALID
        
        for validator in field_validators:
            try:
                status, messages, confidence = validator.validate(value, context)
                
                all_messages.extend(messages)
                min_confidence = min(min_confidence, confidence)
                
                # Determinar peor status
                status_priority = {
                    FieldValidationStatus.VALID: 0,
                    FieldValidationStatus.WARNING: 1,
                    FieldValidationStatus.ERROR: 2,
                    FieldValidationStatus.MISSING: 3,
                    FieldValidationStatus.CONFLICTED: 4
                }
                
                if status_priority.get(status, 0) > status_priority.get(worst_status, 0):
                    worst_status = status
                    
            except Exception as e:
                logger.error(f"Error validando campo {field_name} con {validator.__class__.__name__}: {e}")
                all_messages.append(f"Error en validación: {str(e)}")
                worst_status = FieldValidationStatus.ERROR
                min_confidence = 0.0
                
        return {
            "field_name": field_name,
            "status": worst_status,
            "messages": all_messages,
            "confidence_score": min_confidence
        }
    
    def validate_consolidated_data(self, consolidated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validar todos los datos consolidados"""
        validation_results = []
        context = self._build_validation_context(consolidated_data)
        
        # Validar datos personales
        personal_data = consolidated_data.get("personal_data", {})
        for field_name in ["employee_id", "first_name", "last_name", "email", "id_card", "birth_date"]:
            result = self.validate_field(field_name, personal_data.get(field_name), context)
            validation_results.append(result)
            
        # Validar datos contractuales
        contractual_data = consolidated_data.get("contractual_data", {})
        for field_name in ["start_date", "salary"]:
            result = self.validate_field(field_name, contractual_data.get(field_name), context)
            validation_results.append(result)
            
        # Validar datos de posición
        position_data = consolidated_data.get("position_data", {})
        result = self.validate_field("position", position_data.get("position"), context)
        validation_results.append(result)
        
        # Calcular estadísticas generales
        total_validations = len(validation_results)
        valid_count = len([r for r in validation_results if r["status"] == FieldValidationStatus.VALID])
        warning_count = len([r for r in validation_results if r["status"] == FieldValidationStatus.WARNING])
        error_count = len([r for r in validation_results if r["status"] in [FieldValidationStatus.ERROR, FieldValidationStatus.MISSING]])
        
        overall_score = (valid_count / total_validations * 100) if total_validations > 0 else 0
        
        return {
            "validation_results": validation_results,
            "overall_score": overall_score,
            "total_validations": total_validations,
            "valid_count": valid_count,
            "warning_count": warning_count,
            "error_count": error_count,
            "validation_level": self.validation_level.value
        }
    
    def _build_validation_context(self, consolidated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Construir contexto para validaciones cross-reference"""
        context = {}
        
        # Agregar todos los datos para cross-reference
        for section_name, section_data in consolidated_data.items():
            if isinstance(section_data, dict):
                for field_name, field_value in section_data.items():
                    context[field_name] = field_value
                    
        # Agregar configuraciones específicas
        context["corporate_domains"] = ["empresa.com", "company.com"]  # Ejemplo
        
        return context

# Función de conveniencia para validación rápida
def quick_validate(field_name: str, value: Any, validation_level: ValidationLevel = ValidationLevel.STANDARD) -> bool:
    """Validación rápida de un campo específico"""
    engine = ValidationEngine(validation_level)
    result = engine.validate_field(field_name, value)
    return result["status"] == FieldValidationStatus.VALID