from typing import Optional, Dict, Any
from functools import wraps
import time
from datetime import datetime

try:
    from langfuse import Langfuse
    HAS_LANGFUSE = True
except ImportError:
    HAS_LANGFUSE = False
    print("⚠️ LangFuse no disponible, usando observabilidad básica")

from core.config import settings
from core.logging_config import get_audit_logger

class ObservabilityManager:
    """Gestor de observabilidad con LangFuse y logging local"""
    
    def __init__(self):
        self.logger = get_audit_logger("observability")
        self.langfuse_client = None
        
        if HAS_LANGFUSE and settings.langfuse_enabled:
            try:
                self.langfuse_client = Langfuse(
                    secret_key=settings.langfuse_secret_key,
                    public_key=settings.langfuse_public_key,
                    host=settings.langfuse_host
                )
                
                self.logger.info("LangFuse inicializado correctamente")
                
            except Exception as e:
                self.logger.warning(f"Error inicializando LangFuse: {e}")
                self.langfuse_client = None
        else:
            self.logger.info("LangFuse deshabilitado, usando observabilidad local")
    
    def trace_agent_execution(self, agent_id: str, session_id: str = None):
        """Decorator para trazar ejecución de agentes"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                trace_data = {
                    "agent_id": agent_id,
                    "session_id": session_id,
                    "function": func.__name__,
                    "timestamp": datetime.utcnow().isoformat(),
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys())
                }
                
                # Crear trace si LangFuse está disponible
                trace = None
                if self.langfuse_client:
                    try:
                        trace = self.langfuse_client.trace(
                            name=f"{agent_id}_{func.__name__}",
                            user_id=session_id or "system",
                            metadata=trace_data
                        )
                    except Exception as e:
                        self.logger.warning(f"Error creando trace: {e}")
                
                try:
                    # Ejecutar función
                    result = func(*args, **kwargs)
                    
                    # Calcular tiempo de ejecución
                    execution_time = time.time() - start_time
                    trace_data.update({
                        "status": "success",
                        "execution_time": execution_time,
                        "result_type": type(result).__name__
                    })
                    
                    # Log local
                    self.logger.info(f"Agent {agent_id} executed {func.__name__} in {execution_time:.2f}s")
                    
                    # Actualizar trace si existe
                    if trace:
                        try:
                            trace.update(
                                output={"success": True, "execution_time": execution_time},
                                metadata=trace_data
                            )
                        except Exception as e:
                            self.logger.warning(f"Error actualizando trace: {e}")
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    trace_data.update({
                        "status": "error",
                        "execution_time": execution_time,
                        "error": str(e)
                    })
                    
                    self.logger.error(f"Agent {agent_id} failed in {func.__name__}: {e}")
                    
                    # Actualizar trace con error si existe
                    if trace:
                        try:
                            trace.update(
                                output={"success": False, "error": str(e)},
                                metadata=trace_data
                            )
                        except:
                            pass
                    
                    raise
            
            return wrapper
        return decorator
    
    def log_agent_metrics(self, agent_id: str, metrics: Dict[str, Any], session_id: str = None):
        """Log métricas específicas de agentes"""
        try:
            # Log local
            self.logger.info(f"Metrics for {agent_id}: {metrics}")
            
            # LangFuse metrics si está disponible
            if self.langfuse_client:
                try:
                    self.langfuse_client.score(
                        name=f"{agent_id}_metrics",
                        value=metrics.get("quality_score", 0),
                        trace_id=session_id,
                        metadata=metrics
                    )
                except Exception as e:
                    self.logger.warning(f"Error enviando métricas a LangFuse: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error logging métricas: {e}")
    
    def create_simple_trace(self, name: str, session_id: str = None, metadata: Dict[str, Any] = None):
        """Crear trace simple para operaciones básicas"""
        if self.langfuse_client:
            try:
                return self.langfuse_client.trace(
                    name=name,
                    user_id=session_id or "system",
                    metadata=metadata or {}
                )
            except Exception as e:
                self.logger.warning(f"Error creando trace simple: {e}")
        return None

# Instancia global
observability_manager = ObservabilityManager()