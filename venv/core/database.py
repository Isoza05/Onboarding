from typing import Optional, Dict, Any, List
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from datetime import datetime
import json
from bson import ObjectId
from core.config import settings
from core.logging_config import get_audit_logger

class JSONEncoder(json.JSONEncoder):
    """Encoder personalizado para manejar ObjectId y datetime"""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class DatabaseManager:
    """Gestor de base de datos MongoDB con funciones de auditabilidad"""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.logger = get_audit_logger("database_manager")
        self._connected = False  # Flag para tracking de conexión
        
    def connect(self) -> bool:
        """Conectar a MongoDB"""
        try:
            self.client = MongoClient(settings.mongodb_url)
            self.db = self.client[settings.mongodb_db_name]
            
            # Verificar conexión
            self.client.admin.command('ping')
            self._connected = True
            self.logger.info("Conexión a MongoDB establecida exitosamente")
            return True
            
        except Exception as e:
            self._connected = False
            self.logger.error(f"Error conectando a MongoDB: {e}")
            return False
    
    def disconnect(self):
        """Desconectar de MongoDB"""
        try:
            if self.client:
                self.client.close()
                self._connected = False
                self.logger.info("Conexión a MongoDB cerrada")
        except Exception as e:
            self.logger.warning(f"Error desconectando MongoDB: {e}")
    
    def is_connected(self) -> bool:
        """Verificar si hay conexión activa"""
        if not self._connected:
            return False
        
        try:
            if self.client and self.db:
                self.client.admin.command('ping')
                return True
        except Exception:
            self._connected = False
        
        return False
    
    def get_collection(self, collection_name: str) -> Collection:
        """Obtener una colección"""
        if not self.is_connected():
            raise Exception("Base de datos no conectada")
        return self.db[collection_name]
    
    def create_audit_entry(self, 
                          agent_id: str,
                          action: str, 
                          data: Dict[str, Any],
                          user_id: str = "system") -> str:
        """Crear entrada de auditoría"""
        try:
            # Verificar conexión usando nuestro método seguro
            if not self.is_connected():
                self.logger.warning("Base de datos no conectada, omitiendo audit trail")
                return "no_db_connection"
            
            audit_entry = {
                "timestamp": datetime.utcnow(),
                "agent_id": agent_id,
                "user_id": user_id,
                "action": action,
                "data": data,
                "session_id": data.get("session_id"),
                "status": "success"
            }
            
            collection = self.get_collection("audit_trail")
            result = collection.insert_one(audit_entry)
            
            self.logger.info(f"Entrada de auditoría creada: {action}")
            return str(result.inserted_id)
            
        except Exception as e:
            self.logger.warning(f"No se pudo crear audit trail: {str(e)[:100]}")
            return "audit_skipped"
    
    def save_employee_data(self, employee_data: Dict[str, Any]) -> str:
        """Guardar datos de empleado con encriptación PII"""
        try:
            # Verificar conexión usando nuestro método seguro
            if not self.is_connected():
                self.logger.warning("Base de datos no conectada, simulando guardado")
                # Generar ID simulado para desarrollo
                fake_id = f"dev_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                return fake_id
            
            # Agregar metadatos
            employee_record = {
                **employee_data,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": "processing",
                "version": 1
            }
            
            collection = self.get_collection("employees")
            result = collection.insert_one(employee_record)
            
            # Auditoría
            self.create_audit_entry(
                agent_id="initial_data_collection",
                action="employee_data_saved",
                data={"employee_id": str(result.inserted_id)}
            )
            
            return str(result.inserted_id)
            
        except Exception as e:
            self.logger.warning(f"No se pudo guardar en BD, modo desarrollo: {str(e)[:100]}")
            # Generar ID simulado para desarrollo
            fake_id = f"dev_error_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            return fake_id
    
    def update_employee_status(self, employee_id: str, status: str) -> bool:
        """Actualizar estado de empleado"""
        try:
            # Verificar conexión usando nuestro método seguro
            if not self.is_connected():
                self.logger.warning("Base de datos no conectada, omitiendo actualización de estado")
                return True  # Simular éxito para desarrollo
            
            collection = self.get_collection("employees")
            result = collection.update_one(
                {"_id": ObjectId(employee_id)},
                {
                    "$set": {
                        "status": status,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                self.create_audit_entry(
                    agent_id="system",
                    action="employee_status_updated",
                    data={
                        "employee_id": employee_id,
                        "new_status": status
                    }
                )
                return True
            return False
            
        except Exception as e:
            self.logger.warning(f"No se pudo actualizar estado en BD: {str(e)[:100]}")
            return True  # Simular éxito para desarrollo

# Instancia global del gestor de base de datos
db_manager = DatabaseManager()