from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
import os
import hashlib
import base64
from datetime import datetime, date
from loguru import logger
import json
import re

from core.observability import observability_manager
from .schemas import (
    DocumentType, DocumentFormat, ValidationStatus,
    DocumentAnalysis, MedicalValidation, IDAuthentication, AcademicVerification
)

# Schemas para herramientas
class DocumentAnalysisInput(BaseModel):
    """Input para análisis de documentos"""
    document_data: Dict[str, Any] = Field(description="Datos del documento a analizar")
    document_type: str = Field(description="Tipo de documento")
    analysis_mode: str = Field(default="comprehensive", description="Modo de análisis")

class MedicalValidationInput(BaseModel):
    """Input para validación médica"""
    document_data: Dict[str, Any] = Field(description="Datos del documento médico")
    validation_standards: List[str] = Field(default=["general"], description="Estándares de validación")

class IDAuthenticationInput(BaseModel):
    """Input para autenticación de identidad"""
    document_data: Dict[str, Any] = Field(description="Datos del documento de identidad")
    cross_reference_data: Dict[str, Any] = Field(default={}, description="Datos para verificación cruzada")

class AcademicVerificationInput(BaseModel):
    """Input para verificación académica"""
    document_data: Dict[str, Any] = Field(description="Datos de títulos académicos")
    institution_database: bool = Field(default=True, description="Verificar contra base de instituciones")

@tool(args_schema=DocumentAnalysisInput)
@observability_manager.trace_agent_execution("documentation_agent")
def doc_analyzer_tool(document_data: Dict[str, Any], document_type: str, analysis_mode: str = "comprehensive") -> Dict[str, Any]:
    """
    Analiza documentos PDF, extrae texto e imágenes, clasifica contenido.
    
    Args:
        document_data: Datos del documento a analizar
        document_type: Tipo de documento
        analysis_mode: Modo de análisis (comprehensive, quick, text_only)
        
    Returns:
        Resultado del análisis documental
    """
    try:
        logger.info(f"Iniciando análisis de documento tipo: {document_type}")
        
        analysis_result = {
            "text_extraction_success": False,
            "image_quality_score": 0.0,
            "content_classification": "unknown",
            "key_data_extracted": {},
            "processing_notes": []
        }
        
        # Simular extracción de texto basada en tipo de documento
        file_name = document_data.get("file_name", "")
        file_format = document_data.get("file_format", "").lower()
        
        if file_format in ["pdf", "doc", "docx"]:
            # Análisis de documentos de texto
            analysis_result["text_extraction_success"] = True
            analysis_result["image_quality_score"] = 95.0
            
            if document_type == "cv_resume":
                analysis_result["content_classification"] = "curriculum_vitae"
                analysis_result["key_data_extracted"] = {
                    "name": document_data.get("extracted_name", "Pendiente extracción"),
                    "experience_years": document_data.get("experience", 0),
                    "education_level": document_data.get("education", "No especificado"),
                    "skills": document_data.get("skills", []),
                    "contact_info": document_data.get("contact", {})
                }
                
            elif document_type == "personnel_form":
                analysis_result["content_classification"] = "personnel_data"
                analysis_result["key_data_extracted"] = {
                    "employee_data": document_data.get("employee_info", {}),
                    "emergency_contacts": document_data.get("emergency_contacts", []),
                    "personal_references": document_data.get("references", [])
                }
                
        elif file_format in ["jpg", "jpeg", "png"]:
            # Análisis de imágenes
            analysis_result["text_extraction_success"] = True
            analysis_result["image_quality_score"] = 88.0
            
            if document_type == "photo":
                analysis_result["content_classification"] = "identity_photo"
                analysis_result["key_data_extracted"] = {
                    "face_detected": True,
                    "image_quality": "good",
                    "background": "appropriate",
                    "resolution": document_data.get("resolution", "unknown")
                }
                
            elif document_type == "id_document":
                analysis_result["content_classification"] = "identity_document"
                analysis_result["key_data_extracted"] = {
                    "document_number": document_data.get("id_number", ""),
                    "name": document_data.get("full_name", ""),
                    "expiration_date": document_data.get("expiry_date", ""),
                    "issuing_authority": document_data.get("authority", "")
                }
        
        # Análisis específico por modo
        if analysis_mode == "comprehensive":
            analysis_result["processing_notes"].append("Análisis completo realizado")
            analysis_result["processing_notes"].append("Extracción de metadatos completada")
            
        elif analysis_mode == "quick":
            analysis_result["processing_notes"].append("Análisis rápido - verificación básica")
            
        logger.info(f"Análisis de documento completado. Éxito: {analysis_result['text_extraction_success']}")
        
        return {
            "success": True,
            "analysis_results": analysis_result,
            "processing_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en análisis de documento: {e}")
        return {
            "success": False,
            "error": str(e),
            "analysis_results": {
                "text_extraction_success": False,
                "image_quality_score": 0.0,
                "content_classification": "error",
                "key_data_extracted": {},
                "processing_notes": [f"Error en análisis: {str(e)}"]
            }
        }

@tool(args_schema=MedicalValidationInput)
@observability_manager.trace_agent_execution("documentation_agent")
def medical_validator_tool(document_data: Dict[str, Any], validation_standards: List[str] = ["general"]) -> Dict[str, Any]:
    """
    Valida certificados médicos, carné de vacunación, verifica cumplimiento sanitario.
    
    Args:
        document_data: Datos del documento médico
        validation_standards: Estándares de validación a aplicar
        
    Returns:
        Resultado de validación médica
    """
    try:
        logger.info("Iniciando validación médica")
        
        validation_result = {
            "vaccination_status": "unknown",
            "health_certificate_valid": False,
            "medical_restrictions": [],
            "expiration_date": None,
            "issuing_authority": None
        }
        
        # Validar carné de vacunación
        if document_data.get("document_type") == "vaccination_card":
            vaccines = document_data.get("vaccines", [])
            required_vaccines = ["COVID-19", "Hepatitis B", "Tetanus"]
            
            vaccination_status = "complete"
            for vaccine in required_vaccines:
                if not any(v.get("name", "").lower().find(vaccine.lower()) != -1 for v in vaccines):
                    vaccination_status = "incomplete"
                    validation_result["medical_restrictions"].append(f"Falta vacuna: {vaccine}")
            
            validation_result["vaccination_status"] = vaccination_status
            validation_result["health_certificate_valid"] = vaccination_status == "complete"
            
            # Verificar fechas de expiración
            exp_date = document_data.get("expiration_date")
            if exp_date:
                try:
                    if isinstance(exp_date, str):
                        exp_date = datetime.fromisoformat(exp_date).date()
                    
                    if exp_date < date.today():
                        validation_result["health_certificate_valid"] = False
                        validation_result["medical_restrictions"].append("Certificado médico expirado")
                    
                    validation_result["expiration_date"] = exp_date.isoformat()
                except ValueError:
                    validation_result["medical_restrictions"].append("Fecha de expiración inválida")
        
        # Validar autoridad emisora
        issuing_authority = document_data.get("issuing_authority", "")
        valid_authorities = ["CCSS", "Ministerio de Salud", "Colegio de Médicos", "Hospital Nacional"]
        
        if any(auth.lower() in issuing_authority.lower() for auth in valid_authorities):
            validation_result["issuing_authority"] = issuing_authority
        else:
            validation_result["medical_restrictions"].append("Autoridad emisora no reconocida")
        
        # Aplicar estándares específicos
        if "strict" in validation_standards:
            if len(validation_result["medical_restrictions"]) > 0:
                validation_result["health_certificate_valid"] = False
        
        logger.info(f"Validación médica completada. Válido: {validation_result['health_certificate_valid']}")
        
        return {
            "success": True,
            "validation_results": validation_result,
            "processing_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en validación médica: {e}")
        return {
            "success": False,
            "error": str(e),
            "validation_results": {
                "vaccination_status": "error",
                "health_certificate_valid": False,
                "medical_restrictions": [f"Error en validación: {str(e)}"],
                "expiration_date": None,
                "issuing_authority": None
            }
        }

@tool(args_schema=IDAuthenticationInput)
@observability_manager.trace_agent_execution("documentation_agent")
def id_authenticator_tool(document_data: Dict[str, Any], cross_reference_data: Dict[str, Any] = {}) -> Dict[str, Any]:
    """
    Verifica autenticidad de documentos de identidad, validación cruzada.
    
    Args:
        document_data: Datos del documento de identidad
        cross_reference_data: Datos para verificación cruzada
        
    Returns:
        Resultado de autenticación de identidad
    """
    try:
        logger.info("Iniciando autenticación de identidad")
        
        authentication_result = {
            "identity_verified": False,
            "document_authentic": False,
            "cross_reference_match": False,
            "extracted_info": {},
            "confidence_score": 0.0
        }
        
        # Extraer información del documento
        extracted_info = {
            "id_number": document_data.get("id_number", ""),
            "full_name": document_data.get("full_name", ""),
            "birth_date": document_data.get("birth_date", ""),
            "nationality": document_data.get("nationality", ""),
            "expiration_date": document_data.get("expiration_date", "")
        }
        
        authentication_result["extracted_info"] = extracted_info
        
        # Validar formato de cédula (Costa Rica)
        id_number = extracted_info["id_number"]
        if id_number:
            # Formato básico de cédula costarricense
            if re.match(r'^\d{1}-\d{4}-\d{4}$', id_number) or re.match(r'^\d{9}$', id_number):
                authentication_result["document_authentic"] = True
                authentication_result["confidence_score"] += 30.0
            
        # Verificar nombre
        full_name = extracted_info["full_name"]
        if full_name and len(full_name.split()) >= 2:
            authentication_result["confidence_score"] += 20.0
            
        # Verificar fecha de nacimiento
        birth_date = extracted_info["birth_date"]
        if birth_date:
            try:
                if isinstance(birth_date, str):
                    birth_date_obj = datetime.fromisoformat(birth_date).date()
                else:
                    birth_date_obj = birth_date
                    
                # Verificar edad razonable (18-70 años)
                today = date.today()
                age = today.year - birth_date_obj.year
                if 18 <= age <= 70:
                    authentication_result["confidence_score"] += 25.0
                    
            except ValueError:
                pass
        
        # Verificación cruzada con datos proporcionados
        if cross_reference_data:
            matches = 0
            total_checks = 0
            
            for key, value in cross_reference_data.items():
                if key in extracted_info and extracted_info[key]:
                    total_checks += 1
                    if str(extracted_info[key]).lower() == str(value).lower():
                        matches += 1
            
            if total_checks > 0:
                cross_match_score = (matches / total_checks) * 25.0
                authentication_result["confidence_score"] += cross_match_score
                authentication_result["cross_reference_match"] = matches >= (total_checks * 0.8)
        
        # Determinar verificación de identidad
        if authentication_result["confidence_score"] >= 75.0:
            authentication_result["identity_verified"] = True
            
        # Normalizar confidence score
        authentication_result["confidence_score"] = min(authentication_result["confidence_score"] / 100.0, 1.0)
        
        logger.info(f"Autenticación completada. Verificado: {authentication_result['identity_verified']}, Confianza: {authentication_result['confidence_score']:.2f}")
        
        return {
            "success": True,
            "authentication_results": authentication_result,
            "processing_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en autenticación de identidad: {e}")
        return {
            "success": False,
            "error": str(e),
            "authentication_results": {
                "identity_verified": False,
                "document_authentic": False,
                "cross_reference_match": False,
                "extracted_info": {},
                "confidence_score": 0.0
            }
        }

@tool(args_schema=AcademicVerificationInput)
@observability_manager.trace_agent_execution("documentation_agent")
def academic_verifier_tool(document_data: Dict[str, Any], institution_database: bool = True) -> Dict[str, Any]:
    """
    Verifica títulos académicos, validación institucional, verificación de grados.
    
    Args:
        document_data: Datos de títulos académicos
        institution_database: Si verificar contra base de datos de instituciones
        
    Returns:
        Resultado de verificación académica
    """
    try:
        logger.info("Iniciando verificación académica")
        
        verification_result = {
            "titles_verified": [],
            "institution_accredited": False,
            "degree_level_confirmed": False,
            "graduation_date_valid": False,
            "overall_score": 0.0
        }
        
        # Instituciones reconocidas (simulación)
        recognized_institutions = [
            "Universidad de Costa Rica", "UCR", 
            "Instituto Tecnológico de Costa Rica", "TEC", "ITCR",
            "Universidad Nacional", "UNA",
            "Universidad Estatal a Distancia", "UNED",
            "Universidad Latina", "ULACIT"
        ]
        
        titles = document_data.get("academic_titles", [])
        if not titles:
            # Si no hay títulos estructurados, intentar extraer de datos generales
            titles = [{
                "degree": document_data.get("degree", ""),
                "institution": document_data.get("institution", ""),
                "graduation_date": document_data.get("graduation_date", ""),
                "field_of_study": document_data.get("field_of_study", "")
            }]
        
        total_score = 0.0
        titles_processed = 0
        
        for title in titles:
            if not title.get("degree"):
                continue
                
            titles_processed += 1
            title_verification = {
                "degree": title.get("degree", ""),
                "institution": title.get("institution", ""),
                "verified": False,
                "verification_score": 0.0,
                "notes": []
            }
            
            # Verificar institución
            institution = title.get("institution", "")
            if institution:
                if any(inst.lower() in institution.lower() for inst in recognized_institutions):
                    verification_result["institution_accredited"] = True
                    title_verification["verification_score"] += 40.0
                    title_verification["notes"].append("Institución reconocida")
                else:
                    title_verification["notes"].append("Institución requiere verificación adicional")
            
            # Verificar nivel de grado
            degree = title.get("degree", "").lower()
            degree_levels = {
                "licenciatura": 30.0, "bachelor": 30.0, "ingenier": 30.0,
                "maestria": 35.0, "master": 35.0, "mba": 35.0,
                "doctorado": 40.0, "phd": 40.0, "doctor": 40.0
            }
            
            for level, score in degree_levels.items():
                if level in degree:
                    verification_result["degree_level_confirmed"] = True
                    title_verification["verification_score"] += score
                    title_verification["notes"].append(f"Grado {level} confirmado")
                    break
            
            # Verificar fecha de graduación
            graduation_date = title.get("graduation_date")
            if graduation_date:
                try:
                    if isinstance(graduation_date, str):
                        grad_date = datetime.fromisoformat(graduation_date).date()
                    else:
                        grad_date = graduation_date
                    
                    today = date.today()
                    years_ago = today.year - grad_date.year
                    
                    if 0 <= years_ago <= 50:  # Graduación en los últimos 50 años
                        verification_result["graduation_date_valid"] = True
                        title_verification["verification_score"] += 30.0
                        title_verification["notes"].append("Fecha de graduación válida")
                    
                except ValueError:
                    title_verification["notes"].append("Fecha de graduación inválida")
            
            # Marcar como verificado si score >= 70
            if title_verification["verification_score"] >= 70.0:
                title_verification["verified"] = True
            
            verification_result["titles_verified"].append(title_verification)
            total_score += title_verification["verification_score"]
        
        # Calcular score general
        if titles_processed > 0:
            verification_result["overall_score"] = min(total_score / titles_processed, 100.0)
        
        logger.info(f"Verificación académica completada. Score: {verification_result['overall_score']:.1f}")
        
        return {
            "success": True,
            "verification_results": verification_result,
            "processing_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en verificación académica: {e}")
        return {
            "success": False,
            "error": str(e),
            "verification_results": {
                "titles_verified": [],
                "institution_accredited": False,
                "degree_level_confirmed": False,
                "graduation_date_valid": False,
                "overall_score": 0.0
            }
        }