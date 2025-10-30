"""
Data Aggregator Agent - Consolida y valida datos del DATA COLLECTION HUB.

Este agente recibe los resultados de:
- Initial Data Collection Agent
- Confirmation Data Agent  
- Documentation Agent

Y produce datos consolidados, validados y listos para:
- IT Provisioning Agent
- Contract Management Agent
- Meeting Coordination Agent
"""

from .agent import DataAggregatorAgent
from .schemas import (
    AggregationRequest, AggregationResult, ConsolidatedEmployeeData,
    ValidationLevel, DataConsistencyStatus, FieldValidationStatus
)

__all__ = [
    'DataAggregatorAgent',
    'AggregationRequest',
    'AggregationResult', 
    'ConsolidatedEmployeeData',
    'ValidationLevel',
    'DataConsistencyStatus',
    'FieldValidationStatus'
]