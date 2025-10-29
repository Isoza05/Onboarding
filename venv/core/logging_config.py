import os
from loguru import logger
from core.config import settings

def setup_logging():
    """Configurar sistema de logging con auditabilidad"""
    
    # Crear directorio de logs si no existe
    os.makedirs("logs", exist_ok=True)
    
    # Remover handler por defecto
    logger.remove()
    
    # Configurar formato de logs para auditabilidad
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<blue>{extra[agent_id]}</blue> | "
        "<blue>{extra[user_id]}</blue> | "
        "<level>{message}</level>"
    )
    
    # Handler para consola
    logger.add(
        sink=lambda msg: print(msg, end=""),
        format=log_format,
        level=settings.log_level,
        colorize=True
    )
    
    # Handler para archivo (auditoria completa)
    logger.add(
        sink=settings.log_file,
        format=log_format,
        level="DEBUG",
        rotation="1 day",
        retention="90 days",
        compression="zip",
        enqueue=True
    )
    
    # Handler para errores críticos
    logger.add(
        sink="logs/errors.log",
        format=log_format,
        level="ERROR",
        rotation="1 week",
        retention="1 year",
        backtrace=True,
        diagnose=True
    )

def get_audit_logger(agent_id: str, user_id: str = "system"):
    """Obtener logger con contexto de auditoría"""
    return logger.bind(agent_id=agent_id, user_id=user_id)