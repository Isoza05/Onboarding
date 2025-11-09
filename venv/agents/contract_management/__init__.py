"""
Contract Management Agent Package

Agente especializado en generación, validación y firma de contratos legales.
Incluye templates legales, compliance verification y HR Department Simulator.
"""

from .agent import ContractManagementAgent
from .schemas import (
    ContractGenerationRequest, ContractManagementResult, ContractDocument,
    ContractType, ContractStatus, ComplianceLevel
)
from .hr_simulator import HRDepartmentSimulator

__all__ = [
    "ContractManagementAgent",
    "ContractGenerationRequest", 
    "ContractManagementResult",
    "ContractDocument",
    "ContractType",
    "ContractStatus", 
    "ComplianceLevel",
    "HRDepartmentSimulator"
]