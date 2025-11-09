from typing import Dict, Any, List, Optional
from datetime import datetime, date, time, timedelta
import random
import json
from .schemas import (
    CalendarSystemResponse, CalendarSimulatorConfig, CalendarAvailability,
    MeetingSchedule, Stakeholder, StakeholderRole, MeetingType
)

class CalendarSystemSimulator:
    """Simulador completo del sistema de calendario empresarial"""
    
    def __init__(self):
        self.config = self._get_default_config()
        self.active_requests = {}
        self.meeting_rooms = self._initialize_meeting_rooms()
        self.stakeholder_calendars = {}
        
    def _get_default_config(self) -> CalendarSimulatorConfig:
        """Configuración por defecto del simulador"""
        return CalendarSimulatorConfig(
            response_delay_min=60,
            response_delay_max=300,
            average_availability_percentage=0.75,
            meeting_room_availability_rate=0.85,
            conflict_rate=0.15,
            stakeholder_templates={
                "direct_manager": {
                    "availability_percentage": 0.70,
                    "preferred_times": ["09:00", "14:00", "16:00"],
                    "meeting_duration_preference": 60,
                    "response_rate": 0.95
                },
                "hr_representative": {
                    "availability_percentage": 0.80,
                    "preferred_times": ["10:00", "15:00"],
                    "meeting_duration_preference": 90,
                    "response_rate": 0.98
                },
                "it_support": {
                    "availability_percentage": 0.85,
                    "preferred_times": ["08:00", "13:00", "16:00"],
                    "meeting_duration_preference": 60,
                    "response_rate": 0.90
                },
                "project_manager": {
                    "availability_percentage": 0.65,
                    "preferred_times": ["09:00", "11:00", "15:00"],
                    "meeting_duration_preference": 60,
                    "response_rate": 0.85
                },
                "team_lead": {
                    "availability_percentage": 0.75,
                    "preferred_times": ["10:00", "14:00"],
                    "meeting_duration_preference": 60,
                    "response_rate": 0.90
                },
                "onboarding_buddy": {
                    "availability_percentage": 0.90,
                    "preferred_times": ["09:00", "11:00", "14:00", "16:00"],
                    "meeting_duration_preference": 45,
                    "response_rate": 0.95
                },
                "department_head": {
                    "availability_percentage": 0.50,
                    "preferred_times": ["11:00", "15:00"],
                    "meeting_duration_preference": 45,
                    "response_rate": 0.80
                },
                "training_coordinator": {
                    "availability_percentage": 0.80,
                    "preferred_times": ["10:00", "14:00"],
                    "meeting_duration_preference": 120,
                    "response_rate": 0.95
                }
            },
            meeting_templates={
                MeetingType.WELCOME_MEETING: {
                    "typical_duration": 60,
                    "required_room_capacity": 4,
                    "equipment_needed": ["projector", "whiteboard"],
                    "success_rate": 0.98
                },
                MeetingType.HR_ORIENTATION: {
                    "typical_duration": 120,
                    "required_room_capacity": 3,
                    "equipment_needed": ["computer", "projector"],
                    "success_rate": 0.95
                },
                MeetingType.IT_SETUP: {
                    "typical_duration": 90,
                    "required_room_capacity": 2,
                    "equipment_needed": ["computer", "network_access"],
                    "success_rate": 0.92
                },
                MeetingType.TEAM_INTRODUCTION: {
                    "typical_duration": 60,
                    "required_room_capacity": 8,
                    "equipment_needed": ["projector", "conference_phone"],
                    "success_rate": 0.90
                },
                MeetingType.PROJECT_BRIEFING: {
                    "typical_duration": 90,
                    "required_room_capacity": 6,
                    "equipment_needed": ["projector", "whiteboard", "computer"],
                    "success_rate": 0.88
                }
            }
        )
    
    def _initialize_meeting_rooms(self) -> List[Dict[str, Any]]:
        """Inicializar inventario de salas de reuniones"""
        return [
            {
                "room_id": "conf_room_001",
                "name": "Conference Room A",
                "capacity": 8,
                "location": "Floor 1",
                "equipment": ["projector", "whiteboard", "conference_phone", "computer"],
                "availability_rate": 0.85,
                "booking_priority": "high"
            },
            {
                "room_id": "conf_room_002", 
                "name": "Conference Room B",
                "capacity": 12,
                "location": "Floor 2",
                "equipment": ["projector", "whiteboard", "conference_phone", "computer", "video_conference"],
                "availability_rate": 0.75,
                "booking_priority": "high"
            },
            {
                "room_id": "meeting_room_001",
                "name": "Small Meeting Room 1",
                "capacity": 4,
                "location": "Floor 1",
                "equipment": ["whiteboard", "computer"],
                "availability_rate": 0.90,
                "booking_priority": "medium"
            },
            {
                "room_id": "meeting_room_002",
                "name": "Small Meeting Room 2", 
                "capacity": 4,
                "location": "Floor 2",
                "equipment": ["whiteboard", "computer"],
                "availability_rate": 0.90,
                "booking_priority": "medium"
            },
            {
                "room_id": "training_room_001",
                "name": "Training Room",
                "capacity": 15,
                "location": "Floor 3",
                "equipment": ["projector", "whiteboard", "computer", "microphone", "sound_system"],
                "availability_rate": 0.70,
                "booking_priority": "medium"
            },
            {
                "room_id": "executive_room_001",
                "name": "Executive Meeting Room",
                "capacity": 6,
                "location": "Floor 4",
                "equipment": ["projector", "whiteboard", "conference_phone", "computer", "video_conference", "coffee_machine"],
                "availability_rate": 0.60,
                "booking_priority": "high"
            }
        ]
    
    async def process_calendar_request(self, employee_data: Dict[str, Any], 
                                     stakeholders: List[Dict[str, Any]], 
                                     meetings: List[Dict[str, Any]]) -> CalendarSystemResponse:
        """Procesar solicitud completa de calendario"""
        request_id = f"CAL_REQ_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{employee_data.get('employee_id', 'unknown')}"
        
        # Simular tiempo de procesamiento
        processing_time = random.uniform(
            self.config.response_delay_min / 60,
            self.config.response_delay_max / 60
        )
        
        employee_id = employee_data.get("employee_id", "unknown")
        
        try:
            # 1. Generar disponibilidad de stakeholders
            calendar_availability = await self._generate_stakeholder_availability(stakeholders)
            
            # 2. Verificar disponibilidad de salas
            meeting_rooms_available = await self._check_meeting_room_availability(meetings)
            
            # 3. Detectar conflictos potenciales
            conflicts_detected = await self._detect_calendar_conflicts(meetings, calendar_availability)
            
            # 4. Crear reuniones en el sistema
            meetings_created = await self._create_calendar_meetings(meetings, stakeholders, employee_data)
            
            # 5. Enviar invitaciones
            invitations_sent = await self._send_meeting_invitations(meetings_created, stakeholders)
            
            # 6. Programar recordatorios
            reminders_scheduled = await self._schedule_meeting_reminders(meetings_created)
            
            # Registrar solicitud activa
            self.active_requests[request_id] = {
                "employee_id": employee_id,
                "status": "completed",
                "created_at": datetime.utcnow(),
                "meetings_count": len(meetings),
                "stakeholders_count": len(stakeholders)
            }
            
            return CalendarSystemResponse(
                request_id=request_id,
                employee_id=employee_id,
                status="completed",
                processing_time_minutes=processing_time,
                calendar_availability=calendar_availability,
                meeting_rooms_available=meeting_rooms_available,
                conflicts_detected=conflicts_detected,
                meetings_created=meetings_created,
                invitations_sent=invitations_sent,
                reminders_scheduled=reminders_scheduled,
                calendar_system="microsoft_outlook",
                integration_success=True,
                system_contact="calendar-admin@company.com",
                support_contact="it-support@company.com"
            )
            
        except Exception as e:
            return CalendarSystemResponse(
                request_id=request_id,
                employee_id=employee_id,
                status="failed",
                processing_time_minutes=processing_time,
                integration_success=False,
                calendar_availability={},
                meeting_rooms_available=[],
                conflicts_detected=[{"error": str(e)}],
                meetings_created=[],
                invitations_sent=[],
                reminders_scheduled=[]
            )
    
    async def _generate_stakeholder_availability(self, stakeholders: List[Dict[str, Any]]) -> Dict[str, List[CalendarAvailability]]:
        """Generar disponibilidad realista para stakeholders"""
        availability_data = {}
        
        for stakeholder_data in stakeholders:
            stakeholder_id = stakeholder_data.get("stakeholder_id")
            role = stakeholder_data.get("role", "employee")
            
            # Obtener configuración específica del rol
            role_config = self.config.stakeholder_templates.get(role, {
                "availability_percentage": 0.75,
                "preferred_times": ["10:00", "14:00"],
                "meeting_duration_preference": 60,
                "response_rate": 0.85
            })
            
            # Generar disponibilidad para próximas 4 semanas
            stakeholder_availability = []
            start_date = datetime.now().date()
            
            for day_offset in range(28):  # 4 semanas
                current_date = start_date + timedelta(days=day_offset)
                
                # Saltar fines de semana
                if current_date.weekday() >= 5:
                    continue
                
                # Generar slots disponibles y ocupados
                available_slots, busy_slots = self._generate_daily_availability(
                    current_date, role_config
                )
                
                day_availability = CalendarAvailability(
                    stakeholder_id=stakeholder_id,
                    date=current_date,
                    available_slots=available_slots,
                    busy_slots=busy_slots,
                    timezone="America/Costa_Rica"
                )
                stakeholder_availability.append(day_availability)
            
            availability_data[stakeholder_id] = stakeholder_availability
        
        return availability_data
    
    def _generate_daily_availability(self, target_date: date, role_config: Dict[str, Any]) -> tuple:
        """Generar disponibilidad diaria para un stakeholder"""
        available_slots = []
        busy_slots = []
        
        availability_rate = role_config.get("availability_percentage", 0.75)
        preferred_times = role_config.get("preferred_times", ["10:00", "14:00"])
        
        # Horario laboral: 8:00 - 18:00
        business_start = 8 * 60  # 8:00 AM en minutos
        business_end = 18 * 60   # 6:00 PM en minutos
        slot_duration = 60       # Slots de 1 hora
        
        current_time = business_start
        
        while current_time < business_end:
            time_str = f"{current_time // 60:02d}:{current_time % 60:02d}"
            end_time = current_time + slot_duration
            end_time_str = f"{end_time // 60:02d}:{end_time % 60:02d}"
            
            # Determinar si está disponible
            is_available = random.random() < availability_rate
            
            # Bonus de disponibilidad para horarios preferidos
            if time_str in preferred_times:
                is_available = random.random() < (availability_rate + 0.15)
            
            # Penalizar horarios menos deseables (muy temprano/muy tarde)
            if current_time < 9 * 60 or current_time > 16 * 60:
                is_available = random.random() < (availability_rate - 0.10)
            
            slot = {
                "start": time_str,
                "end": end_time_str
            }
            
            if is_available:
                available_slots.append(slot)
            else:
                busy_slots.append(slot)
            
            current_time += slot_duration
        
        return available_slots, busy_slots
    
    async def _check_meeting_room_availability(self, meetings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Verificar disponibilidad de salas de reuniones"""
        available_rooms = []
        
        for meeting_data in meetings:
            meeting_type = meeting_data.get("meeting_type", "general")
            duration_minutes = meeting_data.get("duration_minutes", 60)
            scheduled_date = meeting_data.get("scheduled_date")
            scheduled_time = meeting_data.get("scheduled_time")
            
            # Buscar salas apropiadas
            suitable_rooms = self._find_suitable_rooms(meeting_type, meeting_data)
            
            for room in suitable_rooms:
                # Simular disponibilidad de la sala
                is_available = random.random() < room["availability_rate"]
                
                if is_available:
                    room_availability = {
                        "room_id": room["room_id"],
                        "room_name": room["name"],
                        "capacity": room["capacity"],
                        "location": room["location"],
                        "equipment": room["equipment"],
                        "available_for_meeting": meeting_data.get("meeting_id"),
                        "booking_confirmed": True,
                        "booking_time": f"{scheduled_date} {scheduled_time}",
                        "duration_minutes": duration_minutes,
                        "setup_time_needed": 15,
                        "cleanup_time_needed": 10
                    }
                    available_rooms.append(room_availability)
                    break  # Solo necesitamos una sala por reunión
        
        return available_rooms
    
    def _find_suitable_rooms(self, meeting_type: str, meeting_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Encontrar salas apropiadas para el tipo de reunión"""
        attendees_count = len(meeting_data.get("attendees", []))
        meeting_template = self.config.meeting_templates.get(meeting_type, {})
        required_capacity = meeting_template.get("required_room_capacity", attendees_count + 1)
        equipment_needed = meeting_template.get("equipment_needed", [])
        
        suitable_rooms = []
        
        for room in self.meeting_rooms:
            # Verificar capacidad
            if room["capacity"] >= required_capacity:
                # Verificar equipamiento
                has_required_equipment = all(
                    equipment in room["equipment"] for equipment in equipment_needed
                )
                
                if has_required_equipment:
                    suitable_rooms.append(room)
        
        # Ordenar por prioridad y disponibilidad
        suitable_rooms.sort(key=lambda r: (r["booking_priority"], -r["availability_rate"]))
        
        return suitable_rooms
    
    async def _detect_calendar_conflicts(self, meetings: List[Dict[str, Any]], 
                                       availability: Dict[str, List[CalendarAvailability]]) -> List[Dict[str, Any]]:
        """Detectar conflictos de calendario"""
        conflicts = []
        
        for i, meeting1 in enumerate(meetings):
            meeting1_date = meeting1.get("scheduled_date")
            meeting1_time = meeting1.get("scheduled_time")
            meeting1_duration = meeting1.get("duration_minutes", 60)
            
            # Verificar conflictos con otros meetings
            for meeting2 in meetings[i+1:]:
                meeting2_date = meeting2.get("scheduled_date")
                meeting2_time = meeting2.get("scheduled_time")
                
                if meeting1_date == meeting2_date:
                    # Parsear tiempos
                    time1 = datetime.strptime(meeting1_time, "%H:%M").time()
                    time2 = datetime.strptime(meeting2_time, "%H:%M").time()
                    
                    # Convertir a minutos para comparación
                    time1_minutes = time1.hour * 60 + time1.minute
                    time2_minutes = time2.hour * 60 + time2.minute
                    
                    # Verificar solapamiento
                    if abs(time1_minutes - time2_minutes) < meeting1_duration:
                        conflicts.append({
                            "conflict_id": f"conflict_{meeting1.get('meeting_id')}_{meeting2.get('meeting_id')}",
                            "conflict_type": "time_overlap",
                            "meeting1_id": meeting1.get("meeting_id"),
                            "meeting2_id": meeting2.get("meeting_id"),
                            "issue": f"Meetings scheduled too close together",
                            "recommendation": "Space meetings at least 1 hour apart",
                            "severity": "medium"
                        })
            
            # Verificar disponibilidad de stakeholders
            meeting_attendees = meeting1.get("attendees", [])
            for attendee in meeting_attendees:
                stakeholder_id = attendee.get("stakeholder_id")
                
                if stakeholder_id in availability:
                    # Buscar disponibilidad para la fecha de la reunión
                    stakeholder_availability = availability[stakeholder_id]
                    day_availability = next(
                        (avail for avail in stakeholder_availability if avail.date.isoformat() == meeting1_date),
                        None
                    )
                    
                    if day_availability:
                        # Verificar si el horario está disponible
                        is_available = any(
                            slot["start"] <= meeting1_time < slot["end"]
                            for slot in day_availability.available_slots
                        )
                        
                        if not is_available:
                            conflicts.append({
                                "conflict_id": f"unavailable_{meeting1.get('meeting_id')}_{stakeholder_id}",
                                "conflict_type": "stakeholder_unavailable",
                                "meeting_id": meeting1.get("meeting_id"),
                                "stakeholder_id": stakeholder_id,
                                "stakeholder_name": attendee.get("name", "Unknown"),
                                "issue": f"Stakeholder not available at {meeting1_time} on {meeting1_date}",
                                "recommendation": "Find alternative time slot or make attendance optional",
                                "severity": "high" if stakeholder_id in meeting1.get("required_attendees", []) else "low"
                            })
        
        return conflicts
    
    async def _create_calendar_meetings(self, meetings: List[Dict[str, Any]], 
                                      stakeholders: List[Dict[str, Any]], 
                                      employee_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Crear reuniones en el sistema de calendario"""
        created_meetings = []
        
        for meeting_data in meetings:
            meeting_id = meeting_data.get("meeting_id", f"mtg_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
            
            # Simular creación exitosa
            creation_success = random.random() < 0.95  # 95% success rate
            
            if creation_success:
                created_meeting = {
                    "meeting_id": meeting_id,
                    "calendar_event_id": f"cal_event_{meeting_id}",
                    "title": meeting_data.get("title", "Onboarding Meeting"),
                    "description": meeting_data.get("description", ""),
                    "start_datetime": f"{meeting_data.get('scheduled_date')}T{meeting_data.get('scheduled_time')}:00",
                    "duration_minutes": meeting_data.get("duration_minutes", 60),
                    "timezone": "America/Costa_Rica",
                    "location": meeting_data.get("location", "Virtual Meeting"),
                    "virtual_meeting_url": meeting_data.get("virtual_meeting_url"),
                    "organizer": {
                        "name": meeting_data.get("organizer", {}).get("name", "HR Team"),
                        "email": meeting_data.get("organizer", {}).get("email", "hr@company.com")
                    },
                    "attendees": meeting_data.get("attendees", []),
                    "agenda": meeting_data.get("agenda", []),
                    "created_at": datetime.utcnow().isoformat(),
                    "status": "confirmed",
                    "reminder_settings": {
                        "email_reminders": [1440, 60, 15],  # 1 day, 1 hour, 15 minutes
                        "popup_reminders": [15]  # 15 minutes
                    }
                }
                created_meetings.append(created_meeting)
            else:
                # Simular fallo en creación
                created_meetings.append({
                    "meeting_id": meeting_id,
                    "status": "failed",
                    "error": "Calendar system temporarily unavailable",
                    "retry_recommended": True
                })
        
        return created_meetings
    
    async def _send_meeting_invitations(self, created_meetings: List[Dict[str, Any]], 
                                      stakeholders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enviar invitaciones de reuniones"""
        sent_invitations = []
        
        stakeholder_map = {s["stakeholder_id"]: s for s in stakeholders}
        
        for meeting in created_meetings:
            if meeting.get("status") == "confirmed":
                meeting_attendees = meeting.get("attendees", [])
                
                for attendee in meeting_attendees:
                    stakeholder_id = attendee.get("stakeholder_id")
                    stakeholder_info = stakeholder_map.get(stakeholder_id, {})
                    
                    # Simular envío de invitación
                    send_success = random.random() < 0.98  # 98% success rate
                    
                    invitation = {
                        "invitation_id": f"inv_{meeting['meeting_id']}_{stakeholder_id}",
                        "meeting_id": meeting["meeting_id"],
                        "stakeholder_id": stakeholder_id,
                        "stakeholder_email": attendee.get("email", "unknown@company.com"),
                        "invitation_sent": send_success,
                        "sent_at": datetime.utcnow().isoformat() if send_success else None,
                        "delivery_status": "delivered" if send_success else "failed",
                        "response_status": "pending",
                        "response_deadline": (datetime.utcnow() + timedelta(days=1)).isoformat()
                    }
                    
                    # Simular respuesta automática (algunos stakeholders responden rápido)
                    if send_success:
                        role_config = self.config.stakeholder_templates.get(
                            stakeholder_info.get("role", "employee"), {}
                        )
                        response_rate = role_config.get("response_rate", 0.85)
                        
                        if random.random() < response_rate:
                            responses = ["accepted", "tentative", "declined"]
                            weights = [0.85, 0.10, 0.05]  # 85% accept, 10% tentative, 5% decline
                            invitation["response_status"] = random.choices(responses, weights=weights)[0]
                            invitation["responded_at"] = datetime.utcnow().isoformat()
                    
                    sent_invitations.append(invitation)
        
        return sent_invitations
    
    async def _schedule_meeting_reminders(self, created_meetings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Programar recordatorios de reuniones"""
        scheduled_reminders = []
        
        for meeting in created_meetings:
            if meeting.get("status") == "confirmed":
                meeting_id = meeting["meeting_id"]
                start_datetime = datetime.fromisoformat(meeting["start_datetime"])
                
                # Schedule different types of reminders
                reminder_schedule = [
                    {"minutes_before": 1440, "type": "day_before_email"},   # 24 hours
                    {"minutes_before": 120, "type": "2_hour_email"},        # 2 hours
                    {"minutes_before": 15, "type": "popup_reminder"},       # 15 minutes
                    {"minutes_before": 5, "type": "final_popup"}            # 5 minutes
                ]
                
                for reminder_config in reminder_schedule:
                    reminder_time = start_datetime - timedelta(minutes=reminder_config["minutes_before"])
                    
                    reminder = {
                        "reminder_id": f"reminder_{meeting_id}_{reminder_config['type']}",
                        "meeting_id": meeting_id,
                        "reminder_type": reminder_config["type"],
                        "scheduled_for": reminder_time.isoformat(),
                        "recipients": [attendee.get("email") for attendee in meeting.get("attendees", [])],
                        "message_template": self._get_reminder_template(reminder_config["type"]),
                        "status": "scheduled",
                        "delivery_method": "email" if "email" in reminder_config["type"] else "popup"
                    }
                    scheduled_reminders.append(reminder)
        
        return scheduled_reminders
    
    def _get_reminder_template(self, reminder_type: str) -> str:
        """Obtener plantilla de recordatorio"""
        templates = {
            "day_before_email": "Tomorrow you have a meeting: {meeting_title} at {meeting_time}. Please confirm your attendance.",
            "2_hour_email": "Reminder: Your meeting {meeting_title} starts in 2 hours at {meeting_time}.",
            "popup_reminder": "Meeting starting in 15 minutes: {meeting_title}",
            "final_popup": "Meeting starting in 5 minutes: {meeting_title}. Join now!"
        }
        return templates.get(reminder_type, "Meeting reminder: {meeting_title}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado del sistema de calendario"""
        return {
            "system_online": True,
            "active_requests": len(self.active_requests),
            "meeting_rooms_total": len(self.meeting_rooms),
            "meeting_rooms_available": len([r for r in self.meeting_rooms if r["availability_rate"] > 0.5]),
            "average_response_time_minutes": (self.config.response_delay_min + self.config.response_delay_max) / 2 / 60,
            "system_load": random.uniform(0.2, 0.8),  # Simulated load
            "last_maintenance": (datetime.utcnow() - timedelta(days=7)).isoformat(),
            "next_maintenance": (datetime.utcnow() + timedelta(days=23)).isoformat(),
            "integration_health": {
                "outlook_connection": "healthy",
                "teams_integration": "healthy", 
                "exchange_server": "healthy",
                "notification_service": "healthy"
            }
        }
    
    def get_meeting_room_availability(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Obtener disponibilidad de salas de reuniones"""
        availability_report = {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "rooms": []
        }
        
        for room in self.meeting_rooms:
            room_availability = {
                "room_id": room["room_id"],
                "room_name": room["name"],
                "capacity": room["capacity"],
                "location": room["location"],
                "base_availability_rate": room["availability_rate"],
                "daily_availability": []
            }
            
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() < 5:  # Skip weekends
                    # Simulate daily availability
                    daily_rate = room["availability_rate"] + random.uniform(-0.1, 0.1)
                    daily_rate = max(0.0, min(1.0, daily_rate))  # Clamp between 0 and 1
                    
                    room_availability["daily_availability"].append({
                        "date": current_date.isoformat(),
                        "availability_percentage": round(daily_rate * 100, 1),
                        "busy_slots": random.randint(2, 6),
                        "available_slots": random.randint(4, 8)
                    })
                
                current_date += timedelta(days=1)
            
            availability_report["rooms"].append(room_availability)
        
        return availability_report

# Instancia global del simulador
calendar_simulator = CalendarSystemSimulator()