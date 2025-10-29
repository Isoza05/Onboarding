from datetime import datetime
from agents.initial_data_collection.schemas import RawEmailData

# Email de prueba con datos completos
COMPLETE_ONBOARDING_EMAIL = RawEmailData(
    subject="New collaborator entry - Juan Carlos Pérez",
    sender="hr@encora.com",
    received_at=datetime.utcnow(),
    body="""
New collaborator entry - San Carlos

Employee Information:
Id Card | 123456789
Type of Hire | New Hire  
Type of information | New collaborator entry
Passport | AB123456
First Name | Juan
Middle Name | Carlos
Name of Preference | JC
Last Name | Pérez
Mother's Lastname | González
Gender | Male
English level | B2
Birth date | 1989-08-12
University | Tecnológico de Costa Rica
Career | Ingeniería en Computación
Country of birth | Costa Rica
Marital status | Married
Children | 0
Nationality | Costarricense
District | Ciudad Quesada
Start Date | 2025-10-13

Position Details:
Customer | Encora Inc
Client Interview | No
Position | Data Engineer
Position Area | Production
Technology | Data Engineering

Project Information:
Project Manager | María López
Office | Costa Rica
Collaborator Type | Production
Billable Type | Billable
Contracting Type | Payroll
Contracting Time | Long term
Contracting office | CRC
Reference Market | General
GM Total | 43.0%
Partner name | BCM
Project Need | Windows standard
The user will provide Windows Laptop | No

Address Details:
Country | Costa Rica
City | San José
Current Address | Av Central 123, San José
Email | juan.perez@email.com

Comments | Nuevo empleado con excelente perfil técnico
    """,
    message_id="msg_001"
)

# Email con datos incompletos
INCOMPLETE_ONBOARDING_EMAIL = RawEmailData(
    subject="New collaborator entry - María",
    sender="hr@encora.com", 
    received_at=datetime.utcnow(),
    body="""
New collaborator entry

Employee Information:
Id Card | 987654321
First Name | María
Last Name | Rodríguez
Position | Software Engineer
Start Date | 2025-11-01
    """,
    message_id="msg_002"
)

# Email con formato incorrecto
MALFORMED_EMAIL = RawEmailData(
    subject="Nuevo empleado",
    sender="test@test.com",
    received_at=datetime.utcnow(), 
    body="""
Información del nuevo empleado:
Nombre: Pedro
Apellido: García
Email: email-invalido
Fecha: fecha-invalida
    """,
    message_id="msg_003"
)