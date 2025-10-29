from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import threading
import json
import os
from pathlib import Path

from core.state_management.models import (
    SystemState, EmployeeContext, AgentState, StateEvent, 
    AgentStateStatus, OnboardingPhase
)
from core.logging_config import get_audit_logger
from core.config import settings

class CommonStateManager:
    """
    Gestor centralizado de estado para todos los agentes del sistema.
    
    Proporciona:
    - Estado compartido entre agentes
    - Sincronización de contextos
    - Persistencia de datos
    - Notificaciones de cambios
    """
    
    def __init__(self):
        self.logger = get_audit_logger("state_manager")
        self._lock = threading.RLock()
        
        # Estado en memoria
        self._system_state = SystemState()
        
        # Callbacks para notificaciones
        self._callbacks: Dict[str, List[Callable]] = {
            "state_change": [],
            "data_update": [],
            "error": [],
            "phase_change": []
        }
        
        # Configuración de persistencia
        self._state_file = Path("data/system_state.json")
        self._backup_file = Path("data/system_state_backup.json")
        
        # Crear directorios necesarios
        os.makedirs("data", exist_ok=True)
        
        # Cargar estado previo si existe
        self._load_state()
        
        self.logger.info("Common State Manager inicializado")
    
    def register_agent(self, agent_id: str, initial_data: Dict[str, Any] = None) -> bool:
        """Registrar un agente en el sistema"""
        try:
            with self._lock:
                agent_state = AgentState(
                    agent_id=agent_id,
                    status=AgentStateStatus.IDLE,
                    data=initial_data or {},
                    last_updated=datetime.utcnow()
                )
                
                self._system_state.agent_registry[agent_id] = agent_state
                self._system_state.last_updated = datetime.utcnow()
                
                self._persist_state()
                self._notify_callbacks("state_change", {
                    "agent_id": agent_id,
                    "action": "agent_registered",
                    "status": AgentStateStatus.IDLE
                })
                
                self.logger.info(f"Agente registrado: {agent_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error registrando agente {agent_id}: {e}")
            return False
    
    def create_employee_context(self, employee_data: Dict[str, Any], session_id: str = None) -> Optional[str]:
        """Crear contexto para un nuevo empleado"""
        try:
            with self._lock:
                # Si no se proporciona session_id, EmployeeContext lo generará automáticamente
                if session_id is None:
                    context = EmployeeContext(
                        employee_id=employee_data.get("employee_id", f"emp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"),
                        raw_data=employee_data,
                        phase=OnboardingPhase.INITIATED
                    )
                else:
                    context = EmployeeContext(
                        employee_id=employee_data.get("employee_id", f"emp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"),
                        session_id=session_id,
                        raw_data=employee_data,
                        phase=OnboardingPhase.INITIATED
                    )
                
                self._system_state.active_sessions[context.session_id] = context
                self._system_state.last_updated = datetime.utcnow()
                
                self._persist_state()
                self._notify_callbacks("data_update", {
                    "session_id": context.session_id,
                    "employee_id": context.employee_id,
                    "action": "context_created"
                })
                
                self.logger.info(f"Contexto creado para empleado: {context.employee_id}")
                return context.session_id
                
        except Exception as e:
            self.logger.error(f"Error creando contexto: {e}")
            return None
    
    def update_agent_state(self, agent_id: str, status: AgentStateStatus, 
                          data: Dict[str, Any] = None, session_id: str = None) -> bool:
        """Actualizar estado de un agente"""
        try:
            with self._lock:
                # Actualizar registro global del agente
                if agent_id in self._system_state.agent_registry:
                    agent_state = self._system_state.agent_registry[agent_id]
                    agent_state.status = status
                    agent_state.last_updated = datetime.utcnow()
                    
                    if data:
                        agent_state.data.update(data)
                
                # Actualizar estado en sesión específica si existe
                if session_id and session_id in self._system_state.active_sessions:
                    context = self._system_state.active_sessions[session_id]
                    
                    if agent_id not in context.agent_states:
                        context.agent_states[agent_id] = AgentState(
                            agent_id=agent_id,
                            status=status
                        )
                    else:
                        context.agent_states[agent_id].status = status
                        context.agent_states[agent_id].last_updated = datetime.utcnow()
                    
                    if data:
                        context.agent_states[agent_id].data.update(data)
                    
                    context.updated_at = datetime.utcnow()
                
                self._system_state.last_updated = datetime.utcnow()
                self._persist_state()
                
                self._notify_callbacks("state_change", {
                    "agent_id": agent_id,
                    "status": status,
                    "session_id": session_id,
                    "data": data
                })
                
                self.logger.info(f"Estado actualizado - Agent: {agent_id}, Status: {status}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error actualizando estado de {agent_id}: {e}")
            return False
    
    def get_employee_context(self, session_id: str) -> Optional[EmployeeContext]:
        """Obtener contexto completo de un empleado"""
        try:
            with self._lock:
                return self._system_state.active_sessions.get(session_id)
        except Exception as e:
            self.logger.error(f"Error obteniendo contexto: {e}")
            return None
    
    def get_agent_state(self, agent_id: str, session_id: str = None) -> Optional[AgentState]:
        """Obtener estado de un agente"""
        try:
            with self._lock:
                # Si se proporciona session_id, buscar en el contexto específico
                if session_id and session_id in self._system_state.active_sessions:
                    context = self._system_state.active_sessions[session_id]
                    if agent_id in context.agent_states:
                        return context.agent_states[agent_id]
                
                # Buscar en el registro global de agentes
                return self._system_state.agent_registry.get(agent_id)
                
        except Exception as e:
            self.logger.error(f"Error obteniendo estado de agente {agent_id}: {e}")
            return None

    def update_employee_data(self, session_id: str, data: Dict[str, Any], 
                        data_type: str = "processed") -> bool:
        """Actualizar datos de empleado"""
        try:
            with self._lock:
                if session_id not in self._system_state.active_sessions:
                    self.logger.warning(f"Sesión no encontrada: {session_id}")
                    return False
                
                context = self._system_state.active_sessions[session_id]
                
                if data_type == "processed":
                    context.processed_data.update(data)
                elif data_type == "validation":
                    context.validation_results.update(data)
                elif data_type == "raw":
                    context.raw_data.update(data)
                
                context.updated_at = datetime.utcnow()
                self._system_state.last_updated = datetime.utcnow()
                
                self._persist_state()
                self._notify_callbacks("data_update", {
                    "session_id": session_id,
                    "data_type": data_type,
                    "employee_id": context.employee_id
                })
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error actualizando datos de empleado: {e}")
            return False



    def get_system_overview(self) -> Dict[str, Any]:
        """Obtener vista general del sistema"""
        try:
            with self._lock:
                return {
                    "active_sessions": len(self._system_state.active_sessions),
                    "registered_agents": len(self._system_state.agent_registry),
                    "agents_status": {
                        agent_id: state.status 
                        for agent_id, state in self._system_state.agent_registry.items()
                    },
                    "last_updated": self._system_state.last_updated
                }
        except Exception as e:
            self.logger.error(f"Error obteniendo overview: {e}")
            return {}
    
    def subscribe_to_changes(self, event_type: str, callback: Callable):
        """Suscribirse a notificaciones de cambios"""
        if event_type in self._callbacks:
            self._callbacks[event_type].append(callback)
            self.logger.info(f"Callback registrado para {event_type}")
    
    def _notify_callbacks(self, event_type: str, data: Dict[str, Any]):
        """Notificar callbacks registrados"""
        try:
            for callback in self._callbacks.get(event_type, []):
                try:
                    callback(data)
                except Exception as e:
                    self.logger.warning(f"Error en callback {event_type}: {e}")
        except Exception as e:
            self.logger.error(f"Error notificando callbacks: {e}")
    
    def _persist_state(self):
        """Persistir estado en archivo"""
        try:
            # Crear backup del estado anterior
            if self._state_file.exists():
                import shutil
                shutil.copy2(self._state_file, self._backup_file)
            
            # Usar el método dict() de Pydantic para serializar
            state_dict = self._system_state.dict()
            
            # Convertir datetime a string para JSON y manejar referencias circulares
            def convert_datetime(obj, seen=None):
                if seen is None:
                    seen = set()
                
                # Detectar referencias circulares
                obj_id = id(obj)
                if obj_id in seen:
                    return {"_circular_ref": True, "_type": str(type(obj))}
                
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    seen.add(obj_id)
                    result = {}
                    for k, v in obj.items():
                        try:
                            result[k] = convert_datetime(v, seen.copy())
                        except RecursionError:
                            result[k] = {"_recursion_error": True, "_key": k}
                    return result
                elif isinstance(obj, list):
                    seen.add(obj_id)
                    try:
                        return [convert_datetime(item, seen.copy()) for item in obj]
                    except RecursionError:
                        return {"_recursion_error": True, "_type": "list", "_length": len(obj)}
                else:
                    return obj
            
            state_dict = convert_datetime(state_dict)
            
            # Guardar nuevo estado
            with open(self._state_file, 'w') as f:
                json.dump(state_dict, f, indent=2)
                
        except Exception as e:
            self.logger.warning(f"Error persistiendo estado: {e}")
    
    def _load_state(self):
        """Cargar estado desde archivo"""
        try:
            if self._state_file.exists():
                with open(self._state_file, 'r') as f:
                    data = json.load(f)
                    
                # Convertir strings de datetime de vuelta
                def convert_datetime_strings(obj):
                    if isinstance(obj, dict):
                        result = {}
                        for k, v in obj.items():
                            if k.endswith('_at') or k == 'last_updated' or k == 'timestamp':
                                try:
                                    result[k] = datetime.fromisoformat(v) if isinstance(v, str) else v
                                except:
                                    result[k] = v
                            else:
                                result[k] = convert_datetime_strings(v)
                        return result
                    elif isinstance(obj, list):
                        return [convert_datetime_strings(item) for item in obj]
                    return obj
                
                data = convert_datetime_strings(data)
                
                # Usar Pydantic para crear el objeto
                self._system_state = SystemState(**data)
                self.logger.info("Estado previo cargado exitosamente")
            else:
                self.logger.info("No hay estado previo, iniciando limpio")
        except Exception as e:
            self.logger.warning(f"Error cargando estado: {e}")
            self._system_state = SystemState()

# Instancia global del gestor de estado
state_manager = CommonStateManager()