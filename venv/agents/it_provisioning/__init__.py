"""
IT Provisioning Agent Package

Agente especializado en provisioning completo de IT para nuevos empleados.
Incluye generación de credenciales, asignación de equipamiento, 
configuración de permisos y simulación del departamento IT.
"""

from .agent import ITProvisioningAgent
from .schemas import (
    ITProvisioningRequest, ITProvisioningResult, ITCredentials,
    EquipmentAssignment, AccessPermissions, SecuritySetup, SecurityLevel
)
from .it_simulator import ITDepartmentSimulator

__all__ = [
    "ITProvisioningAgent",
    "ITProvisioningRequest", 
    "ITProvisioningResult",
    "ITCredentials",
    "EquipmentAssignment", 
    "AccessPermissions",
    "SecuritySetup",
    "SecurityLevel",
    "ITDepartmentSimulator"
]