import pytest
from datetime import datetime
import sys
import os

# Agregar el directorio padre al path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.initial_data_collection.agent import InitialDataCollectionAgent
from tests.mock_data import (
    COMPLETE_ONBOARDING_EMAIL,
    INCOMPLETE_ONBOARDING_EMAIL, 
    MALFORMED_EMAIL
)
from core.database import db_manager
from core.logging_config import setup_logging

# Configurar logging para tests
setup_logging()

@pytest.fixture
def agent():
    """Fixture para crear agente de prueba"""
    return InitialDataCollectionAgent()

@pytest.fixture
def setup_database():
    """Fixture para configurar base de datos de prueba"""
    # Conectar a base de datos (usar DB de prueba en producción)
    db_manager.connect()
    yield
    # Cleanup si es necesario
    
class TestInitialDataCollectionAgent:
    """Tests para Initial Data Collection Agent"""
    
    def test_agent_initialization(self, agent):
        """Test de inicialización del agente"""
        assert agent.agent_id == "initial_data_collection"
        assert agent.agent_name == "Initial Data Collection Agent"
        assert len(agent.tools) == 4
        assert agent.llm is not None
        
    def test_process_complete_email(self, agent, setup_database):
        """Test procesamiento de email completo"""
        result = agent.process_onboarding_email(COMPLETE_ONBOARDING_EMAIL)
        
        assert result.success is True
        assert result.employee_data is not None
        assert result.employee_data.basic_info.id_card == "123456789"
        assert result.employee_data.basic_info.first_name == "Juan"
        assert result.employee_data.basic_info.last_name == "Pérez"
        assert result.data_quality_score > 80.0
        assert result.requires_manual_review is False
        
    def test_process_incomplete_email(self, agent):
        """Test procesamiento de email incompleto"""
        result = agent.process_onboarding_email(INCOMPLETE_ONBOARDING_EMAIL)
        
        assert result.success is True
        assert result.employee_data is not None
        assert len(result.missing_fields) > 0
        assert result.data_quality_score < 80.0
        assert result.requires_manual_review is True
        
    def test_process_malformed_email(self, agent):
        """Test procesamiento de email con formato incorrecto"""
        result = agent.process_onboarding_email(MALFORMED_EMAIL)
        
        # Debería procesar aunque sea con baja calidad
        assert result.success is True
        assert result.data_quality_score < 50.0
        assert result.requires_manual_review is True
        
    def test_agent_status(self, agent):
        """Test obtención de estado del agente"""
        status = agent.get_status()
        
        assert status["agent_id"] == "initial_data_collection"
        assert status["status"] == "active"
        assert status["tools_count"] == 4
        
    def test_performance_requirement(self, agent):
        """Test requerimiento de performance < 2 segundos"""
        start_time = datetime.utcnow()
        
        result = agent.process_onboarding_email(COMPLETE_ONBOARDING_EMAIL)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        assert processing_time < 2.0  # Requerimiento de performance
        assert result.processing_time < 2.0

if __name__ == "__main__":
    # Ejecutar tests básicos
    agent = InitialDataCollectionAgent()
    print("✅ Agente inicializado correctamente")
    
    print("\n🧪 Ejecutando test básico...")
    result = agent.process_onboarding_email(COMPLETE_ONBOARDING_EMAIL)
    
    print(f"✅ Resultado: {result.success}")
    print(f"📊 Calidad: {result.data_quality_score}%")
    print(f"⏱️ Tiempo: {result.processing_time}s")
    
    if result.employee_data:
        print(f"👤 Empleado: {result.employee_data.basic_info.first_name} {result.employee_data.basic_info.last_name}")