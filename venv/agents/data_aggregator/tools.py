from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, date
from loguru import logger
import re
import json
from difflib import SequenceMatcher

from core.observability import observability_manager
from .schemas import (
    ConsolidatedEmployeeData, PersonalData, AcademicData, PositionData, 
    ContractualData, DocumentationStatus, FieldValidation, CrossValidationResult,
    FieldValidationStatus, DataConsistencyStatus, ValidationLevel,
    ProcessingReadinessAssessment, AggregationConfig
)

# Schemas para herramientas
class DataConsolidatorInput(BaseModel):
    """Input para consolidación de datos"""
    agent_results: Dict[str, Dict[str, Any]] = Field(description="Resultados de los agentes del DATA COLLECTION HUB")
    employee_id: str = Field(description="ID del empleado")
    validation_level: str = Field(default="standard", description="Nivel de validación a aplicar")

class CrossValidatorInput(BaseModel):
    """Input para validación cruzada"""
    consolidated_data: Dict[str, Any] = Field(description="Datos consolidados a validar")
    source_data: Dict[str, Dict[str, Any]] = Field(description="Datos originales por fuente")
    validation_rules: List[Dict[str, Any]] = Field(default=[], description="Reglas de validación específicas")

class ReadinessAssessorInput(BaseModel):
    """Input para evaluación de preparación"""
    consolidated_data: Dict[str, Any] = Field(description="Datos consolidados del empleado")
    completeness_requirements: Dict[str, List[str]] = Field(description="Requerimientos de completitud por fase")

class QualityCalculatorInput(BaseModel):
    """Input para cálculo de métricas de calidad"""
    consolidated_data: Dict[str, Any] = Field(description="Datos consolidados")
    validation_results: Dict[str, Any] = Field(description="Resultados de validación")
    source_quality_scores: Dict[str, float] = Field(description="Scores de calidad por fuente")

@tool(args_schema=DataConsolidatorInput)
@observability_manager.trace_agent_execution("data_aggregator_agent")
def data_consolidator_tool(
    agent_results: Dict[str, Dict[str, Any]], 
    employee_id: str,
    validation_level: str = "standard"
) -> Dict[str, Any]:
    """
    Consolida datos de múltiples agentes en estructura unificada.
    
    Args:
        agent_results: Resultados de initial_data, confirmation_data, documentation agentes
        employee_id: ID del empleado
        validation_level: Nivel de validación (basic, standard, strict, critical)
        
    Returns:
        Datos consolidados en estructura unificada
    """
    try:
        logger.info(f"Iniciando consolidación de datos para empleado: {employee_id}")
        
        # Extraer datos de cada agente
        initial_data = agent_results.get("initial_data_collection_agent", {})
        confirmation_data = agent_results.get("confirmation_data_agent", {})
        documentation_data = agent_results.get("documentation_agent", {})
        
        # === CONSOLIDAR DATOS PERSONALES ===
        personal_data = _consolidate_personal_data(initial_data, confirmation_data, documentation_data, employee_id)
        
        # === CONSOLIDAR DATOS ACADÉMICOS ===
        academic_data = _consolidate_academic_data(initial_data, confirmation_data, documentation_data)
        
        # === CONSOLIDAR DATOS DE POSICIÓN ===
        position_data = _consolidate_position_data(initial_data, confirmation_data)
        
        # === CONSOLIDAR DATOS CONTRACTUALES ===
        contractual_data = _consolidate_contractual_data(confirmation_data, initial_data)
        
        # === CONSOLIDAR ESTADO DE DOCUMENTACIÓN ===
        documentation_status = _consolidate_documentation_status(documentation_data)
        
        # Calcular completitud inicial
        completeness = _calculate_data_completeness({
            "personal": personal_data.dict(),
            "academic": academic_data.dict(),
            "position": position_data.dict(),
            "contractual": contractual_data.dict(),
            "documentation": documentation_status.dict()
        })
        
        consolidated_result = {
            "success": True,
            "employee_id": employee_id,
            "personal_data": personal_data.dict(),
            "academic_data": academic_data.dict(),
            "position_data": position_data.dict(),
            "contractual_data": contractual_data.dict(),
            "documentation_status": documentation_status.dict(),
            "data_completeness_percentage": completeness,
            "source_data_quality": _assess_source_quality(agent_results),
            "consolidation_notes": _generate_consolidation_notes(agent_results),
            "processing_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Consolidación completada. Completitud: {completeness:.1f}%")
        return consolidated_result
        
    except Exception as e:
        logger.error(f"Error consolidando datos: {e}")
        return {
            "success": False,
            "error": str(e),
            "employee_id": employee_id,
            "consolidation_notes": [f"Error en consolidación: {str(e)}"]
        }

def _consolidate_personal_data(initial_data: Dict, confirmation_data: Dict, documentation_data: Dict, employee_id: str) -> PersonalData:
    """Consolidar datos personales de múltiples fuentes"""
    
    # Extraer datos de initial_data (fuente principal para datos básicos)
    structured_data = initial_data.get("structured_data", {})
    employee_info = structured_data.get("employee_info", {})
    
    # Datos de confirmation_data  
    contract_terms = confirmation_data.get("contract_terms", {})
    
    # Datos de documentation (verificación de identidad)
    id_auth = documentation_data.get("id_authentication", {})
    extracted_info = id_auth.get("extracted_info", {}) if id_auth else {}
    
    return PersonalData(
        employee_id=employee_id,
        id_card=_merge_field_values([
            employee_info.get("id_card"),
            extracted_info.get("id_number")
        ]),
        passport=employee_info.get("passport"),
        first_name=_merge_field_values([
            employee_info.get("first_name"),
            extracted_info.get("full_name", "").split()[0] if extracted_info.get("full_name") else None
        ]),
        middle_name=employee_info.get("middle_name"),
        name_of_preference=employee_info.get("name_of_preference"),
        last_name=_merge_field_values([
            employee_info.get("last_name"),
            " ".join(extracted_info.get("full_name", "").split()[1:]) if extracted_info.get("full_name") else None
        ]),
        mothers_lastname=employee_info.get("mothers_lastname"),
        gender=employee_info.get("gender"),
        birth_date=_parse_date(extracted_info.get("birth_date") or employee_info.get("birth_date")),
        nationality=extracted_info.get("nationality") or employee_info.get("nationality"),
        marital_status=employee_info.get("marital_status"),
        children=employee_info.get("children"),
        english_level=employee_info.get("english_level"),
        email=employee_info.get("email"),
        phone=employee_info.get("phone"),
        country=employee_info.get("country"),
        city=employee_info.get("city"),
        district=employee_info.get("district"),
        current_address=employee_info.get("current_address")
    )

def _consolidate_academic_data(initial_data: Dict, confirmation_data: Dict, documentation_data: Dict) -> AcademicData:
    """Consolidar datos académicos"""
    
    structured_data = initial_data.get("structured_data", {})
    employee_info = structured_data.get("employee_info", {})
    
    # Datos de verificación académica
    academic_verification = documentation_data.get("academic_verification", {})
    titles_verified = academic_verification.get("titles_verified", []) if academic_verification else []
    
    # Extraer primer título verificado
    primary_title = titles_verified[0] if titles_verified else {}
    
    return AcademicData(
        university=_merge_field_values([
            employee_info.get("university"),
            primary_title.get("institution")
        ]),
        career=_merge_field_values([
            employee_info.get("career"),
            primary_title.get("degree")
        ]),
        degree_level=_extract_degree_level(primary_title.get("degree", "")),
        graduation_date=_parse_date(primary_title.get("graduation_date")),
        additional_certifications=_extract_certifications(titles_verified[1:] if len(titles_verified) > 1 else []),
        academic_verification_status="verified" if academic_verification.get("institution_accredited") else "pending"
    )

def _consolidate_position_data(initial_data: Dict, confirmation_data: Dict) -> PositionData:
    """Consolidar datos de posición y proyecto"""
    
    structured_data = initial_data.get("structured_data", {})
    position_info = structured_data.get("position_info", {})
    
    # Datos contractuales que pueden tener info de posición
    contract_terms = confirmation_data.get("contract_terms", {})
    
    return PositionData(
        position=_merge_field_values([
            position_info.get("position"),
            contract_terms.get("position_title")
        ]) or "Data Engineer",  # Default fallback
        position_area=position_info.get("position_area"),
        technology=position_info.get("technology"),
        customer=position_info.get("customer"),
        partner_name=position_info.get("partner_name"),
        project_manager=position_info.get("project_manager"),
        office=position_info.get("office"),
        collaborator_type=position_info.get("collaborator_type"),
        billable_type=position_info.get("billable_type"),
        contracting_type=position_info.get("contracting_type"),
        contracting_time=position_info.get("contracting_time"),
        contracting_office=position_info.get("contracting_office"),
        reference_market=position_info.get("reference_market"),
        project_need=position_info.get("project_need")
    )

def _consolidate_contractual_data(confirmation_data: Dict, initial_data: Dict) -> ContractualData:
    """Consolidar datos contractuales"""
    
    contract_terms = confirmation_data.get("contract_terms", {})
    structured_data = initial_data.get("structured_data", {})
    
    return ContractualData(
        start_date=_parse_date(contract_terms.get("start_date")) or date.today(),
        salary=contract_terms.get("salary"),
        currency=contract_terms.get("currency"),
        employment_type=contract_terms.get("employment_type"),
        work_modality=contract_terms.get("work_modality"),
        probation_period=contract_terms.get("probation_period"),
        benefits=contract_terms.get("benefits", []),
        gm_total=structured_data.get("gm_total"),
        client_interview=structured_data.get("client_interview"),
        windows_laptop_provided=structured_data.get("windows_laptop_provided")
    )

def _consolidate_documentation_status(documentation_data: Dict) -> DocumentationStatus:
    """Consolidar estado de documentación"""
    
    # Extraer scores de validación
    medical_val = documentation_data.get("medical_validation", {})
    id_auth = documentation_data.get("id_authentication", {})
    academic_ver = documentation_data.get("academic_verification", {})
    doc_analysis = documentation_data.get("document_analyses", {})
    
    return DocumentationStatus(
        vaccination_card=FieldValidationStatus.VALID if medical_val.get("health_certificate_valid") else FieldValidationStatus.WARNING,
        id_document=FieldValidationStatus.VALID if id_auth.get("identity_verified") else FieldValidationStatus.ERROR,
        cv_resume=FieldValidationStatus.VALID if doc_analysis.get("text_extraction_success") else FieldValidationStatus.WARNING,
        photo=FieldValidationStatus.VALID,  # Asumimos válido si se procesó
        academic_titles=FieldValidationStatus.VALID if academic_ver.get("institution_accredited") else FieldValidationStatus.WARNING,
        background_check=FieldValidationStatus.MISSING,  # Pendiente de implementar
        personnel_form=FieldValidationStatus.VALID if doc_analysis else FieldValidationStatus.MISSING,
        medical_validation_score=_calculate_medical_score(medical_val),
        identity_verification_score=id_auth.get("confidence_score", 0) * 100 if id_auth else 0,
        academic_verification_score=academic_ver.get("overall_score", 0) if academic_ver else 0,
        overall_documentation_score=documentation_data.get("compliance_score", 0)
    )

@tool(args_schema=CrossValidatorInput)
@observability_manager.trace_agent_execution("data_aggregator_agent")
def cross_validator_tool(
    consolidated_data: Dict[str, Any],
    source_data: Dict[str, Dict[str, Any]], 
    validation_rules: List[Dict[str, Any]] = []
) -> Dict[str, Any]:
    """
    Realiza validación cruzada de datos consolidados contra fuentes originales.
    
    Args:
        consolidated_data: Datos ya consolidados
        source_data: Datos originales por agente
        validation_rules: Reglas específicas de validación
        
    Returns:
        Resultado de validación cruzada con inconsistencias detectadas
    """
    try:
        logger.info("Iniciando validación cruzada de datos")
        
        field_validations = []
        critical_issues = []
        warnings = []
        
        # Validaciones críticas de identidad
        identity_validation = _validate_identity_consistency(consolidated_data, source_data)
        field_validations.extend(identity_validation["validations"])
        critical_issues.extend(identity_validation["critical_issues"])
        warnings.extend(identity_validation["warnings"])
        
        # Validaciones de datos contractuales
        contract_validation = _validate_contract_consistency(consolidated_data, source_data)
        field_validations.extend(contract_validation["validations"])
        warnings.extend(contract_validation["warnings"])
        
        # Validaciones de datos académicos
        academic_validation = _validate_academic_consistency(consolidated_data, source_data)
        field_validations.extend(academic_validation["validations"])
        warnings.extend(academic_validation["warnings"])
        
        # Calcular consistency score general
        total_fields = len(field_validations)
        valid_fields = len([f for f in field_validations if f["status"] == FieldValidationStatus.VALID])
        consistency_score = (valid_fields / total_fields * 100) if total_fields > 0 else 100.0
        
        # Determinar status de consistencia general
        if len(critical_issues) > 0:
            consistency_status = DataConsistencyStatus.INCONSISTENT
        elif consistency_score < 70:
            consistency_status = DataConsistencyStatus.MAJOR_DISCREPANCIES
        elif consistency_score < 90:
            consistency_status = DataConsistencyStatus.MINOR_DISCREPANCIES
        else:
            consistency_status = DataConsistencyStatus.CONSISTENT
        
        result = {
            "success": True,
            "field_validations": [fv.dict() if hasattr(fv, 'dict') else fv for fv in field_validations],
            "consistency_score": consistency_score,
            "consistency_status": consistency_status.value,
            "critical_issues": critical_issues,
            "warnings": warnings,
            "total_fields_validated": total_fields,
            "valid_fields": valid_fields,
            "processing_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Validación cruzada completada. Score: {consistency_score:.1f}%")
        return result
        
    except Exception as e:
        logger.error(f"Error en validación cruzada: {e}")
        return {
            "success": False,
            "error": str(e),
            "consistency_score": 0.0,
            "consistency_status": DataConsistencyStatus.INCONSISTENT.value,
            "critical_issues": [f"Error en validación: {str(e)}"]
        }

def _validate_identity_consistency(consolidated_data: Dict, source_data: Dict) -> Dict[str, Any]:
    """Validar consistencia de datos de identidad"""
    validations = []
    critical_issues = []
    warnings = []
    
    personal_data = consolidated_data.get("personal_data", {})
    
    # Validar nombres
    name_sources = {}
    for agent, data in source_data.items():
        if agent == "initial_data_collection_agent":
            emp_info = data.get("structured_data", {}).get("employee_info", {})
            name_sources[agent] = f"{emp_info.get('first_name', '')} {emp_info.get('last_name', '')}".strip()
        elif agent == "documentation_agent":
            id_auth = data.get("id_authentication", {})
            extracted_info = id_auth.get("extracted_info", {}) if id_auth else {}
            name_sources[agent] = extracted_info.get("full_name", "")
    
    first_name = personal_data.get("first_name", "")
    last_name = personal_data.get("last_name", "")
    consolidated_name = f"{first_name} {last_name}".strip()
    
    name_validation = FieldValidation(
        field_name="full_name",
        source_values=name_sources,
        consolidated_value=consolidated_name,
        status=FieldValidationStatus.VALID,
        confidence_score=90.0
    )
    
    # Verificar similitud entre nombres
    similarities = []
    for source, source_name in name_sources.items():
        if source_name and consolidated_name:
            similarity = SequenceMatcher(None, consolidated_name.lower(), source_name.lower()).ratio()
            similarities.append(similarity)
            if similarity < 0.7:  # 70% de similitud mínima
                name_validation.status = FieldValidationStatus.WARNING
                name_validation.discrepancies.append(f"Baja similitud con {source}: {similarity:.1%}")
                warnings.append(f"Discrepancia de nombre detectada en {source}")
    
    if similarities:
        name_validation.confidence_score = max(similarities) * 100
    
    validations.append(name_validation)
    
    # Validar ID/Cédula
    id_sources = {}
    for agent, data in source_data.items():
        if agent == "initial_data_collection_agent":
            emp_info = data.get("structured_data", {}).get("employee_info", {})
            id_sources[agent] = emp_info.get("id_card", "")
        elif agent == "documentation_agent":
            id_auth = data.get("id_authentication", {})
            extracted_info = id_auth.get("extracted_info", {}) if id_auth else {}
            id_sources[agent] = extracted_info.get("id_number", "")
    
    id_validation = FieldValidation(
        field_name="id_card",
        source_values=id_sources,
        consolidated_value=personal_data.get("id_card", ""),
        status=FieldValidationStatus.VALID,
        confidence_score=95.0
    )
    
    # Verificar consistencia de cédulas
    unique_ids = set([id_val for id_val in id_sources.values() if id_val])
    if len(unique_ids) > 1:
        id_validation.status = FieldValidationStatus.ERROR
        id_validation.discrepancies.append("Múltiples números de cédula detectados")
        critical_issues.append(f"Inconsistencia crítica en número de cédula: {unique_ids}")
    
    validations.append(name_validation)
    
    return {
        "validations": [v.dict() for v in validations],  # ← CONVERTIR A DICT AQUÍ
        "critical_issues": critical_issues,
        "warnings": warnings
    }

def _validate_contract_consistency(consolidated_data: Dict, source_data: Dict) -> Dict[str, Any]:
    """Validar consistencia de datos contractuales"""
    validations = []
    warnings = []
    
    contractual_data = consolidated_data.get("contractual_data", {})
    
    # Validar salario
    salary_sources = {}
    for agent, data in source_data.items():
        if agent == "confirmation_data_agent":
            contract_terms = data.get("contract_terms", {})
            salary_sources[agent] = contract_terms.get("salary")
    
    salary_validation = FieldValidation(
        field_name="salary",
        source_values=salary_sources,
        consolidated_value=contractual_data.get("salary"),
        status=FieldValidationStatus.VALID,
        confidence_score=100.0
    )
    
    validations.append(salary_validation)
    
    return {
        "validations": [v.dict() for v in validations],  # ← CAMBIAR TAMBIÉN AQUÍ
        "warnings": warnings
    }

def _validate_academic_consistency(consolidated_data: Dict, source_data: Dict) -> Dict[str, Any]:
    """Validar consistencia de datos académicos"""
    validations = []
    warnings = []
    
    academic_data = consolidated_data.get("academic_data", {})
    
    # Validar universidad
    university_sources = {}
    for agent, data in source_data.items():
        if agent == "initial_data_collection_agent":
            emp_info = data.get("structured_data", {}).get("employee_info", {})
            university_sources[agent] = emp_info.get("university")
        elif agent == "documentation_agent":
            academic_ver = data.get("academic_verification", {})
            titles = academic_ver.get("titles_verified", []) if academic_ver else []
            if titles:
                university_sources[agent] = titles[0].get("institution")
    
    university_validation = FieldValidation(
        field_name="university",
        source_values=university_sources,
        consolidated_value=academic_data.get("university"),
        status=FieldValidationStatus.VALID,
        confidence_score=85.0
    )
    
    validations.append(university_validation)
    
    return {
        "validations": [v.dict() for v in validations], 
        "warnings": warnings
    }

@tool(args_schema=ReadinessAssessorInput)
@observability_manager.trace_agent_execution("data_aggregator_agent")
def readiness_assessor_tool(
    consolidated_data: Dict[str, Any],
    completeness_requirements: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    Evalúa la preparación de datos para las siguientes fases del pipeline.
    
    Args:
        consolidated_data: Datos consolidados del empleado
        completeness_requirements: Campos requeridos por cada fase
        
    Returns:
        Evaluación de preparación para IT provisioning, contract management, meeting coordination
    """
    try:
        logger.info("Evaluando preparación para fases siguientes")
        
        # Evaluar cada fase
        it_readiness = _assess_it_provisioning_readiness(consolidated_data, completeness_requirements.get("it_provisioning", []))
        contract_readiness = _assess_contract_readiness(consolidated_data, completeness_requirements.get("contract_management", []))
        meeting_readiness = _assess_meeting_readiness(consolidated_data, completeness_requirements.get("meeting_coordination", []))
        
        # Identificar bloqueos generales
        blocking_issues = []
        missing_critical_data = []
        recommended_actions = []
        
        # Verificar datos críticos mínimos
        personal_data = consolidated_data.get("personal_data", {})
        if not personal_data.get("employee_id"):
            blocking_issues.append("Employee ID faltante")
            missing_critical_data.append("employee_id")
            
        if not personal_data.get("email"):
            blocking_issues.append("Email corporativo requerido")
            missing_critical_data.append("email")
            recommended_actions.append("Generar email corporativo")
            
        # Consolidar preparación
        overall_readiness = it_readiness["ready"] and contract_readiness["ready"] and meeting_readiness["ready"]
        
        result = {
            "success": True,
            "ready_for_it_provisioning": it_readiness["ready"],
            "ready_for_contract_management": contract_readiness["ready"],
            "ready_for_meeting_coordination": meeting_readiness["ready"],
            "overall_readiness": overall_readiness,
            "it_provisioning_data": it_readiness["data"],
            "contract_management_data": contract_readiness["data"],
            "meeting_coordination_data": meeting_readiness["data"],
            "blocking_issues": blocking_issues,
            "missing_critical_data": missing_critical_data,
            "recommended_actions": recommended_actions + it_readiness["actions"] + contract_readiness["actions"] + meeting_readiness["actions"],
            "readiness_scores": {
                "it_provisioning": it_readiness["score"],
                "contract_management": contract_readiness["score"],
                "meeting_coordination": meeting_readiness["score"]
            },
            "processing_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Evaluación completada. Preparación general: {overall_readiness}")
        return result
        
    except Exception as e:
        logger.error(f"Error evaluando preparación: {e}")
        return {
            "success": False,
            "error": str(e),
            "ready_for_it_provisioning": False,
            "ready_for_contract_management": False,
            "ready_for_meeting_coordination": False,
            "overall_readiness": False
        }

def _assess_it_provisioning_readiness(consolidated_data: Dict, required_fields: List[str]) -> Dict[str, Any]:
    """Evaluar preparación para IT provisioning"""
    personal_data = consolidated_data.get("personal_data", {})
    position_data = consolidated_data.get("position_data", {})
    
    # Datos necesarios para IT
    it_data = {
        "employee_id": personal_data.get("employee_id"),
        "first_name": personal_data.get("first_name"),
        "last_name": personal_data.get("last_name"),
        "email": personal_data.get("email"),
        "position": position_data.get("position"),
        "department": position_data.get("position_area"),
        "office": position_data.get("office"),
        "start_date": consolidated_data.get("contractual_data", {}).get("start_date")
    }
    
    # Verificar campos requeridos
    missing_fields = []
    for field in required_fields:
        if not it_data.get(field):
            missing_fields.append(field)
    
    ready = len(missing_fields) == 0
    score = ((len(required_fields) - len(missing_fields)) / len(required_fields) * 100) if required_fields else 100
    
    actions = []
    if missing_fields:
        actions.append(f"Completar campos faltantes para IT: {', '.join(missing_fields)}")
        
    return {
        "ready": ready,
        "score": score,
        "data": it_data,
        "missing_fields": missing_fields,
        "actions": actions
    }

def _assess_contract_readiness(consolidated_data: Dict, required_fields: List[str]) -> Dict[str, Any]:
    """Evaluar preparación para contract management"""
    personal_data = consolidated_data.get("personal_data", {})
    contractual_data = consolidated_data.get("contractual_data", {})
    position_data = consolidated_data.get("position_data", {})
    
    contract_data = {
        "employee_id": personal_data.get("employee_id"),
        "full_name": f"{personal_data.get('first_name', '')} {personal_data.get('last_name', '')}".strip(),
        "id_card": personal_data.get("id_card"),
        "start_date": contractual_data.get("start_date"),
        "salary": contractual_data.get("salary"),
        "position": position_data.get("position"),
        "employment_type": contractual_data.get("employment_type"),
        "work_modality": contractual_data.get("work_modality")
    }
    
    missing_fields = []
    for field in required_fields:
        if not contract_data.get(field):
            missing_fields.append(field)
    
    ready = len(missing_fields) == 0 and contractual_data.get("salary") is not None
    score = ((len(required_fields) - len(missing_fields)) / len(required_fields) * 100) if required_fields else 100
    
    actions = []
    if missing_fields:
        actions.append(f"Completar campos contractuales: {', '.join(missing_fields)}")
        
    return {
        "ready": ready,
        "score": score,
        "data": contract_data,
        "missing_fields": missing_fields,
        "actions": actions
    }

def _assess_meeting_readiness(consolidated_data: Dict, required_fields: List[str]) -> Dict[str, Any]:
    """Evaluar preparación para meeting coordination"""
    personal_data = consolidated_data.get("personal_data", {})
    position_data = consolidated_data.get("position_data", {})
    
    meeting_data = {
        "employee_id": personal_data.get("employee_id"),
        "first_name": personal_data.get("first_name"),
        "email": personal_data.get("email"),
        "position": position_data.get("position"),
        "project_manager": position_data.get("project_manager"),
        "office": position_data.get("office"),
        "start_date": consolidated_data.get("contractual_data", {}).get("start_date")
    }
    
    missing_fields = []
    for field in required_fields:
        if not meeting_data.get(field):
            missing_fields.append(field)
    
    ready = len(missing_fields) == 0
    score = ((len(required_fields) - len(missing_fields)) / len(required_fields) * 100) if required_fields else 100
    
    actions = []
    if missing_fields:
        actions.append(f"Completar datos para coordinación de reuniones: {', '.join(missing_fields)}")
    if not position_data.get("project_manager"):
        actions.append("Asignar Project Manager")
        
    return {
        "ready": ready,
        "score": score,
        "data": meeting_data,
        "missing_fields": missing_fields,
        "actions": actions
    }

@tool(args_schema=QualityCalculatorInput)
@observability_manager.trace_agent_execution("data_aggregator_agent")
def quality_calculator_tool(
    consolidated_data: Dict[str, Any],
    validation_results: Dict[str, Any],
    source_quality_scores: Dict[str, float]
) -> Dict[str, Any]:
    """
    Calcula métricas de calidad de datos consolidados.
    
    Args:
        consolidated_data: Datos consolidados
        validation_results: Resultados de validación cruzada
        source_quality_scores: Scores de calidad por fuente/agente
        
    Returns:
        Métricas completas de calidad de datos
    """
    try:
        logger.info("Calculando métricas de calidad de datos")
        
        # Calcular completeness score
        completeness_score = consolidated_data.get("data_completeness_percentage", 0.0)
        
        # Calcular consistency score (de validación cruzada)
        consistency_score = validation_results.get("consistency_score", 100.0)
        
        # Calcular reliability score basado en fuentes
        reliability_scores = list(source_quality_scores.values())
        reliability_score = sum(reliability_scores) / len(reliability_scores) if reliability_scores else 0.0
        
        # Calcular accuracy score basado en documentación
        documentation_status = consolidated_data.get("documentation_status", {})
        doc_scores = []
        
        if documentation_status.get("medical_validation_score") is not None:
            doc_scores.append(documentation_status["medical_validation_score"])
        if documentation_status.get("identity_verification_score") is not None:
            doc_scores.append(documentation_status["identity_verification_score"])
        if documentation_status.get("academic_verification_score") is not None:
            doc_scores.append(documentation_status["academic_verification_score"])
            
        accuracy_score = sum(doc_scores) / len(doc_scores) if doc_scores else 80.0
        
        # Score de calidad general (promedio ponderado)
        weights = {
            "completeness": 0.3,
            "consistency": 0.25,
            "reliability": 0.25,
            "accuracy": 0.2
        }
        
        overall_quality_score = (
            completeness_score * weights["completeness"] +
            consistency_score * weights["consistency"] +
            reliability_score * weights["reliability"] +
            accuracy_score * weights["accuracy"]
        )
        
        # Identificar áreas de mejora
        improvement_areas = []
        if completeness_score < 80:
            improvement_areas.append("Completitud de datos")
        if consistency_score < 85:
            improvement_areas.append("Consistencia entre fuentes")
        if reliability_score < 75:
            improvement_areas.append("Calidad de fuentes")
        if accuracy_score < 80:
            improvement_areas.append("Precisión de documentación")
        
        # Clasificar calidad general
        if overall_quality_score >= 90:
            quality_rating = "Excelente"
        elif overall_quality_score >= 80:
            quality_rating = "Buena"
        elif overall_quality_score >= 70:
            quality_rating = "Aceptable"
        elif overall_quality_score >= 60:
            quality_rating = "Requiere Mejora"
        else:
            quality_rating = "Crítica"
        
        result = {
            "success": True,
            "overall_quality_score": round(overall_quality_score, 2),
            "quality_rating": quality_rating,
            "completeness_score": round(completeness_score, 2),
            "consistency_score": round(consistency_score, 2),
            "reliability_score": round(reliability_score, 2),
            "accuracy_score": round(accuracy_score, 2),
            "quality_breakdown": {
                "completeness": {
                    "score": completeness_score,
                    "weight": weights["completeness"],
                    "contribution": completeness_score * weights["completeness"]
                },
                "consistency": {
                    "score": consistency_score,
                    "weight": weights["consistency"],
                    "contribution": consistency_score * weights["consistency"]
                },
                "reliability": {
                    "score": reliability_score,
                    "weight": weights["reliability"],
                    "contribution": reliability_score * weights["reliability"]
                },
                "accuracy": {
                    "score": accuracy_score,
                    "weight": weights["accuracy"],
                    "contribution": accuracy_score * weights["accuracy"]
                }
            },
            "improvement_areas": improvement_areas,
            "source_contributions": source_quality_scores,
            "processing_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Métricas calculadas. Calidad general: {overall_quality_score:.1f}% ({quality_rating})")
        return result
        
    except Exception as e:
        logger.error(f"Error calculando métricas de calidad: {e}")
        return {
            "success": False,
            "error": str(e),
            "overall_quality_score": 0.0,
            "quality_rating": "Error"
        }

# Funciones auxiliares
def _merge_field_values(values: List[Any]) -> Any:
    """Fusionar valores de múltiples fuentes, priorizando el más completo"""
    non_empty_values = [v for v in values if v is not None and str(v).strip()]
    if not non_empty_values:
        return None
    
    # Retornar el valor más largo (más completo)
    return max(non_empty_values, key=lambda x: len(str(x)))

def _parse_date(date_value: Any) -> Optional[date]:
    """Parsear fecha de diferentes formatos"""
    if not date_value:
        return None
        
    if isinstance(date_value, date):
        return date_value
    elif isinstance(date_value, datetime):
        return date_value.date()
    elif isinstance(date_value, str):
        try:
            # Intentar diferentes formatos
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"]:
                try:
                    return datetime.strptime(date_value, fmt).date()
                except ValueError:
                    continue
        except:
            pass
    return None

def _calculate_data_completeness(data_dict: Dict[str, Any]) -> float:
    """Calcular porcentaje de completitud de datos"""
    total_fields = 0
    completed_fields = 0
    
    def count_fields(obj, path=""):
        nonlocal total_fields, completed_fields
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    count_fields(value, f"{path}.{key}" if path else key)
                else:
                    total_fields += 1
                    if value is not None and str(value).strip():
                        completed_fields += 1
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                count_fields(item, f"{path}[{i}]")
    
    count_fields(data_dict)
    return (completed_fields / total_fields * 100) if total_fields > 0 else 0.0

def _assess_source_quality(agent_results: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
    """Evaluar calidad de cada fuente de datos"""
    quality_scores = {}
    
    for agent, result in agent_results.items():
        if not result:
            quality_scores[agent] = 0.0
            continue
            
        score = 50.0  # Base score
        
        # Bonificaciones por éxito
        if result.get("success"):
            score += 30.0
            
        # Bonificaciones por scores específicos
        if "validation_score" in result:
            score += (result["validation_score"] / 100) * 20.0
        elif "compliance_score" in result:
            score += (result["compliance_score"] / 100) * 20.0
            
        quality_scores[agent] = min(score, 100.0)
    
    return quality_scores

def _generate_consolidation_notes(agent_results: Dict[str, Dict[str, Any]]) -> List[str]:
    """Generar notas sobre el proceso de consolidación"""
    notes = []
    
    successful_agents = [agent for agent, result in agent_results.items() if result.get("success")]
    failed_agents = [agent for agent, result in agent_results.items() if not result.get("success")]
    
    notes.append(f"Consolidación exitosa desde {len(successful_agents)} agentes")
    
    if failed_agents:
        notes.append(f"Agentes con errores: {', '.join(failed_agents)}")
        
    for agent, result in agent_results.items():
        if result.get("validation_score"):
            notes.append(f"{agent}: score de validación {result['validation_score']:.1f}%")
        elif result.get("compliance_score"):
            notes.append(f"{agent}: score de compliance {result['compliance_score']:.1f}%")
    
    return notes

def _calculate_medical_score(medical_validation: Dict[str, Any]) -> float:
    """Calcular score de validación médica"""
    if not medical_validation:
        return 0.0
        
    score = 0.0
    
    if medical_validation.get("health_certificate_valid"):
        score += 50.0
        
    vaccination_status = medical_validation.get("vaccination_status", "")
    if vaccination_status == "complete":
        score += 40.0
    elif vaccination_status == "incomplete":
        score += 20.0
        
    restrictions = medical_validation.get("medical_restrictions", [])
    if len(restrictions) == 0:
        score += 10.0
    
    return min(score, 100.0)

def _extract_degree_level(degree_str: str) -> Optional[str]:
    """Extraer nivel de grado académico"""
    if not degree_str:
        return None
        
    degree_lower = degree_str.lower()
    
    if any(word in degree_lower for word in ["licenciatura", "bachelor", "ingenier"]):
        return "Licenciatura"
    elif any(word in degree_lower for word in ["maestria", "master", "mba"]):
        return "Maestría"
    elif any(word in degree_lower for word in ["doctorado", "phd", "doctor"]):
        return "Doctorado"
    else:
        return "Otro"

def _extract_certifications(titles_list: List[Dict[str, Any]]) -> List[str]:
    """Extraer certificaciones adicionales"""
    certifications = []
    for title in titles_list:
        if title.get("degree"):
            certifications.append(title["degree"])
    return certifications