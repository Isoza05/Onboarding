import random
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from .schemas import (
    ITDepartmentResponse, ITCredentials, EquipmentAssignment,
    AccessPermissions, SecuritySetup, SecurityLevel, ITSimulatorConfig
)

class ITDepartmentSimulator:
    """Simulador completo del departamento IT"""
    
    def __init__(self):
        self.config = ITSimulatorConfig()
        self._setup_default_config()
        self.active_requests = {}
        
    def _setup_default_config(self):
        """Configurar templates y configuraciones por defecto"""
        self.config.credential_templates = {
            "windows_domain": "company\\{username}",
            "email": "{first_name}.{last_name}@company.com",
            "vpn_access": "VPN-{employee_id}",
            "badge_access": "BADGE-{location}-{security_level}"
        }
        
        self.config.equipment_inventory = {
            "laptop": {"dell_latitude": 45, "hp_elitebook": 23, "macbook_pro": 12},
            "monitor": {"dell_24inch": 67, "hp_27inch": 34, "samsung_24inch": 25},
            "peripherals": {"wireless_keyboard": 89, "wireless_mouse": 92, "headset_pro": 45}
        }
        
        self.config.access_levels = {
            "basic": ["email", "intranet", "office_365", "time_tracking"],
            "standard": ["basic", "project_tools", "dev_environments", "shared_drives"],
            "elevated": ["standard", "admin_tools", "sensitive_data", "vpn_access"],
            "executive": ["elevated", "executive_dashboards", "all_systems", "remote_admin"]
        }

    async def process_it_request(self, employee_data: Dict[str, Any], 
                               equipment_specs: Dict[str, Any] = None) -> ITDepartmentResponse:
        """Procesar solicitud IT con simulación realista"""
        
        request_id = f"IT-REQ-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{employee_data.get('employee_id', 'UNK')}"
        
        # Simular tiempo de procesamiento realista
        processing_minutes = random.randint(
            self.config.response_delay_min, 
            self.config.response_delay_max
        ) / 60  # Convertir a minutos para demo rápida
        
        # Simular delay (reducido para testing)
        await self._simulate_processing_delay(processing_minutes * 10)  # 10 segundos por minuto simulado
        
        # Generar credenciales
        credentials = self._generate_credentials(employee_data)
        
        # Asignar equipamiento
        equipment = self._allocate_equipment(employee_data, equipment_specs or {})
        
        # Configurar permisos
        access_permissions = self._assign_access_permissions(employee_data)
        
        # Configurar seguridad
        security_setup = self._setup_security(employee_data)
        
        # Generar instrucciones
        setup_instructions = self._generate_setup_instructions(
            credentials, equipment, access_permissions
        )
        
        # Registrar request
        self.active_requests[request_id] = {
            "employee_id": employee_data.get("employee_id"),
            "status": "completed",
            "created_at": datetime.utcnow(),
            "processing_time": processing_minutes
        }
        
        return ITDepartmentResponse(
            request_id=request_id,
            employee_id=employee_data.get("employee_id", ""),
            processing_time_minutes=processing_minutes,
            credentials=credentials,
            equipment=equipment,
            access_permissions=access_permissions,
            security_setup=security_setup,
            setup_instructions=setup_instructions,
            completion_notes=[
                f"All credentials created successfully",
                f"Equipment allocated and configured",
                f"Security permissions applied",
                f"Ready for employee orientation"
            ]
        )

    def _generate_credentials(self, employee_data: Dict[str, Any]) -> ITCredentials:
        """Generar credenciales de usuario"""
        first_name = employee_data.get("first_name", "user").lower()
        last_name = employee_data.get("last_name", "temp").lower()
        employee_id = employee_data.get("employee_id", "EMP000")
        
        # Generar username único
        username = f"{first_name}.{last_name}"
        if len(username) > 20:
            username = f"{first_name[:3]}.{last_name[:10]}"
            
        # Email corporativo
        email = f"{username}@company.com"
        
        # Password temporal seguro
        temp_password = self._generate_secure_password()
        
        # Acceso al dominio
        domain_access = f"company\\{username}"
        
        # VPN credentials
        vpn_creds = f"VPN-{employee_id}-{datetime.utcnow().strftime('%Y%m')}"
        
        # Badge access
        office = employee_data.get("office", "main")
        security_level = employee_data.get("security_level", "standard")
        badge_access = f"BADGE-{office.upper()}-{security_level.upper()}-{employee_id}"
        
        return ITCredentials(
            username=username,
            email=email,
            temporary_password=temp_password,
            domain_access=domain_access,
            vpn_credentials=vpn_creds,
            badge_access=badge_access,
            employee_id=employee_id,
            expires_at=datetime.utcnow() + timedelta(days=90)
        )

    def _allocate_equipment(self, employee_data: Dict[str, Any], 
                          equipment_specs: Dict[str, Any]) -> EquipmentAssignment:
        """Asignar equipamiento basado en posición y especificaciones"""
        position = employee_data.get("position", "").lower()
        department = employee_data.get("department", "").lower()
        
        # Determinar tipo de laptop
        laptop_type = "dell_latitude"  # Default
        if "engineer" in position or "developer" in position:
            laptop_type = random.choice(["dell_latitude", "hp_elitebook"])
        elif "executive" in position or "manager" in position:
            laptop_type = "macbook_pro"
            
        # Asignar laptop
        laptop = {
            "type": laptop_type,
            "model": self._get_laptop_model(laptop_type),
            "serial": f"LAP-{datetime.utcnow().strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
            "specs": "16GB RAM, 512GB SSD, Windows 11 Pro" if "dell" in laptop_type or "hp" in laptop_type else "16GB RAM, 512GB SSD, macOS"
        }
        
        # Asignar monitor si es necesario
        monitor = None
        if equipment_specs.get("monitor_required", True):
            monitor_type = "dell_24inch"
            if "engineer" in position:
                monitor_type = "hp_27inch"
            monitor = {
                "type": monitor_type,
                "size": "27 inch" if "27" in monitor_type else "24 inch",
                "serial": f"MON-{datetime.utcnow().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            }
        
        # Asignar periféricos
        peripherals = [
            {
                "type": "wireless_keyboard",
                "model": "Logitech MX Keys",
                "serial": f"KEY-{random.randint(10000, 99999)}"
            },
            {
                "type": "wireless_mouse", 
                "model": "Logitech MX Master 3",
                "serial": f"MOU-{random.randint(10000, 99999)}"
            }
        ]
        
        # Headset para roles específicos
        if "engineer" in position or "support" in position:
            peripherals.append({
                "type": "headset_pro",
                "model": "Jabra Evolve2 65",
                "serial": f"HEA-{random.randint(10000, 99999)}"
            })
            
        # Software licenses
        software_licenses = ["Windows 11 Pro", "Office 365 Business"]
        if "engineer" in position or "developer" in position:
            software_licenses.extend(["Visual Studio Professional", "Git", "Docker Desktop"])
        if "data" in position:
            software_licenses.extend(["Python", "SQL Server Management Studio", "Power BI"])
            
        return EquipmentAssignment(
            laptop=laptop,
            monitor=monitor,
            peripherals=peripherals,
            software_licenses=software_licenses,
            total_items=len(peripherals) + (2 if monitor else 1)
        )

    def _assign_access_permissions(self, employee_data: Dict[str, Any]) -> AccessPermissions:
        """Asignar permisos de acceso basado en rol y departamento"""
        position = employee_data.get("position", "").lower()
        department = employee_data.get("department", "").lower()
        security_level = employee_data.get("security_level", "standard").lower()
        
        # Determinar nivel de acceso
        access_level = "basic"
        if "senior" in position or "lead" in position:
            access_level = "standard"
        if "manager" in position or "director" in position:
            access_level = "elevated"
        if "executive" in position or "ceo" in position or "cto" in position:
            access_level = "executive"
            
        base_permissions = self.config.access_levels.get(access_level, self.config.access_levels["basic"])
        
        # Sistemas específicos
        systems = ["Active Directory", "Exchange Online", "SharePoint"]
        if "engineer" in position:
            systems.extend(["Azure DevOps", "Git Repository", "Development Servers"])
        if "data" in position:
            systems.extend(["SQL Server", "Power BI", "Azure Data Factory"])
            
        # Aplicaciones
        applications = ["Office 365", "Teams", "OneDrive", "Time Tracking"]
        if access_level in ["standard", "elevated", "executive"]:
            applications.extend(["Project Management Tools", "CRM System"])
        if access_level in ["elevated", "executive"]:
            applications.extend(["Admin Portal", "Security Dashboard"])
            
        # File shares
        file_shares = [f"\\\\company\\shared", f"\\\\company\\{department}"]
        if access_level in ["elevated", "executive"]:
            file_shares.append("\\\\company\\confidential")
            
        # Network drives
        network_drives = ["H: (Home)", "S: (Shared)", f"D: ({department.title()})"]
        
        return AccessPermissions(
            systems=systems,
            applications=applications,
            file_shares=file_shares,
            network_drives=network_drives,
            vpn_access=access_level in ["standard", "elevated", "executive"],
            remote_access=access_level in ["elevated", "executive"]
        )

    def _setup_security(self, employee_data: Dict[str, Any]) -> SecuritySetup:
        """Configurar aspectos de seguridad"""
        position = employee_data.get("position", "").lower()
        office = employee_data.get("office", "main").lower()
        employee_id = employee_data.get("employee_id", "EMP000")
        
        # Determinar nivel de seguridad
        security_level = SecurityLevel.BASIC
        if "senior" in position or "lead" in position:
            security_level = SecurityLevel.STANDARD
        if "manager" in position or "director" in position:
            security_level = SecurityLevel.ELEVATED
        if "executive" in position:
            security_level = SecurityLevel.EXECUTIVE
            
        # Badge access
        badge_access = f"BADGE-{office.upper()}-{security_level.value.upper()}-{employee_id}"
        
        # Parking permit
        parking_permit = None
        if security_level in [SecurityLevel.ELEVATED, SecurityLevel.EXECUTIVE]:
            parking_permit = f"PARK-{office.upper()}-{employee_id}"
            
        # Two-factor auth
        requires_2fa = security_level in [SecurityLevel.ELEVATED, SecurityLevel.EXECUTIVE]
        
        return SecuritySetup(
            badge_access=badge_access,
            parking_permit=parking_permit,
            security_clearance=security_level,
            two_factor_auth=requires_2fa,
            security_training_required=True,
            background_check_status="verified"
        )

    def _generate_setup_instructions(self, credentials: ITCredentials, 
                                   equipment: EquipmentAssignment,
                                   access_permissions: AccessPermissions) -> List[str]:
        """Generar instrucciones de configuración"""
        instructions = [
            f"1. Initial login with username: {credentials.username}",
            f"2. Use temporary password (must be changed on first login)",
            f"3. Configure email client with: {credentials.email}",
            f"4. Join domain: {credentials.domain_access}",
            f"5. Install required software licenses: {', '.join(equipment.software_licenses[:3])}",
            f"6. Connect to VPN using: {credentials.vpn_credentials}",
            f"7. Map network drives: {', '.join(access_permissions.network_drives)}",
            f"8. Complete security training within 30 days",
            f"9. Activate badge access: {credentials.badge_access}",
            f"10. Contact IT help desk for additional setup: help@company.com"
        ]
        
        if equipment.monitor:
            instructions.insert(5, f"5a. Connect and configure external monitor: {equipment.monitor['size']}")
            
        return instructions

    def _generate_secure_password(self) -> str:
        """Generar password temporal seguro"""
        import string
        characters = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(random.choice(characters) for _ in range(12))
        return f"Temp{password}!"

    def _get_laptop_model(self, laptop_type: str) -> str:
        """Obtener modelo específico de laptop"""
        models = {
            "dell_latitude": "Dell Latitude 5530",
            "hp_elitebook": "HP EliteBook 850 G9", 
            "macbook_pro": "MacBook Pro 14-inch M2"
        }
        return models.get(laptop_type, "Standard Business Laptop")

    async def _simulate_processing_delay(self, seconds: float):
        """Simular delay de procesamiento"""
        # Para testing, usar delay muy corto
        await self._async_sleep(min(seconds, 2.0))  # Máximo 2 segundos

    async def _async_sleep(self, seconds: float):
        """Sleep asíncrono simple"""
        import asyncio
        await asyncio.sleep(seconds)

    def get_request_status(self, request_id: str) -> Dict[str, Any]:
        """Obtener estado de una solicitud"""
        if request_id in self.active_requests:
            return {
                "found": True,
                "request_id": request_id,
                **self.active_requests[request_id]
            }
        return {"found": False, "request_id": request_id}

    def get_department_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del departamento IT"""
        return {
            "active_requests": len(self.active_requests),
            "equipment_inventory": self.config.equipment_inventory,
            "average_processing_time": "4.5 minutes",
            "success_rate": "95.8%",
            "current_load": "normal"
        }