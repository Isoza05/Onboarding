from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date, time
from enum import Enum
from shared.models import Priority

class MeetingType(str, Enum):
    """Tipos de reuniones de onboarding"""
    WELCOME_MEETING = "welcome_meeting"
    HR_ORIENTATION = "hr_orientation"
    IT_SETUP = "it_setup"
    TEAM_INTRODUCTION = "team_introduction"
    MANAGER_CHECKIN = "manager_checkin"
    TRAINING_SESSION = "training_session"
    PROJECT_BRIEFING = "project_briefing"
    BUDDY_ASSIGNMENT = "buddy_assignment"

class MeetingPriority(str, Enum):
    """Prioridades de reuniones"""
    CRITICAL = "critical"  # Day 1 essentials
    HIGH = "high"         # Week 1
    MEDIUM = "medium"     # Week 2-4
    LOW = "low"          # Month 1+

class MeetingStatus(str, Enum):
    """Estados de reuniones"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"

class RecurrenceType(str, Enum):
    """Tipos de recurrencia"""
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"

class StakeholderRole(str, Enum):
    """Roles de stakeholders"""
    DIRECT_MANAGER = "direct_manager"
    HR_REPRESENTATIVE = "hr_representative"
    IT_SUPPORT = "it_support"
    TEAM_LEAD = "team_lead"
    PROJECT_MANAGER = "project_manager"
    ONBOARDING_BUDDY = "onboarding_buddy"
    DEPARTMENT_HEAD = "department_head"
    TRAINING_COORDINATOR = "training_coordinator"

class Stakeholder(BaseModel):
    """Stakeholder del proceso de onboarding"""
    stakeholder_id: str
    name: str
    email: str
    role: StakeholderRole
    department: str
    availability_hours: str = "9:00-17:00"  # Default business hours
    timezone: str = "America/Costa_Rica"
    phone: Optional[str] = None
    preferred_meeting_duration: int = 60  # minutes
    meeting_preferences: Dict[str, Any] = Field(default_factory=dict)

class MeetingSchedule(BaseModel):
    """Programación de una reunión"""
    meeting_id: str = Field(default_factory=lambda: f"MTG-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    meeting_type: MeetingType
    title: str
    description: str
    
    # Timing
    scheduled_date: date
    scheduled_time: time
    duration_minutes: int = 60
    timezone: str = "America/Costa_Rica"
    
    # Participants
    organizer: Stakeholder
    attendees: List[Stakeholder] = Field(default_factory=list)
    required_attendees: List[str] = Field(default_factory=list)  # stakeholder_ids
    optional_attendees: List[str] = Field(default_factory=list)
    
    # Meeting details
    location: Optional[str] = None
    virtual_meeting_url: Optional[str] = None
    meeting_platform: str = "Microsoft Teams"  # Teams, Zoom, Meet
    agenda: List[str] = Field(default_factory=list)
    materials: List[str] = Field(default_factory=list)
    
    # Status and tracking
    status: MeetingStatus = MeetingStatus.SCHEDULED
    priority: MeetingPriority = MeetingPriority.MEDIUM
    recurrence: RecurrenceType = RecurrenceType.NONE
    
    # Integration data
    calendar_event_id: Optional[str] = None
    reminder_settings: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class OnboardingTimeline(BaseModel):
    """Timeline completo de onboarding"""
    employee_id: str
    start_date: date
    
    # Day 1 meetings
    day_1_meetings: List[MeetingSchedule] = Field(default_factory=list)
    
    # Week 1 meetings
    week_1_meetings: List[MeetingSchedule] = Field(default_factory=list)
    
    # Month 1 meetings
    month_1_meetings: List[MeetingSchedule] = Field(default_factory=list)
    
    # Recurring meetings
    recurring_meetings: List[MeetingSchedule] = Field(default_factory=list)
    
    # Milestones
    onboarding_milestones: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Summary
    total_meetings: int = 0
    estimated_total_hours: float = 0.0
    critical_meetings_count: int = 0

class MeetingCoordinationRequest(BaseModel):
    """Solicitud de coordinación de reuniones"""
    employee_id: str
    session_id: str
    
    # Input data from Contract Management Agent
    personal_data: Dict[str, Any]
    position_data: Dict[str, Any]
    contractual_data: Dict[str, Any]
    it_credentials: Dict[str, Any]
    contract_details: Dict[str, Any]
    
    # Meeting coordination configuration
    priority: Priority = Priority.MEDIUM
    onboarding_start_date: date
    department_preferences: Dict[str, Any] = Field(default_factory=dict)
    special_requirements: List[str] = Field(default_factory=list)
    
    # Calendar constraints
    business_hours: str = "9:00-17:00"
    excluded_dates: List[date] = Field(default_factory=list)
    preferred_meeting_duration: int = 60
    
    # Integration settings
    calendar_system: str = "microsoft_outlook"
    notification_preferences: Dict[str, Any] = Field(default_factory=dict)

class CalendarAvailability(BaseModel):
    """Disponibilidad de calendario"""
    stakeholder_id: str
    date: date
    available_slots: List[Dict[str, str]] = Field(default_factory=list)  # [{"start": "09:00", "end": "10:00"}]
    busy_slots: List[Dict[str, str]] = Field(default_factory=list)
    timezone: str = "America/Costa_Rica"
    
class ConflictResolution(BaseModel):
    """Resolución de conflictos de calendario"""
    conflict_id: str
    conflicted_meeting: MeetingSchedule
    alternative_slots: List[Dict[str, Any]] = Field(default_factory=list)
    resolution_strategy: str  # "reschedule", "split_meeting", "change_attendees"
    resolved: bool = False
    resolution_notes: List[str] = Field(default_factory=list)

class MeetingCoordinationResult(BaseModel):
    """Resultado del Meeting Coordination Agent"""
    success: bool
    employee_id: str
    session_id: str
    coordination_id: str = Field(default_factory=lambda: f"COORD-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    
    # Main result
    onboarding_timeline: Optional[OnboardingTimeline] = None
    scheduled_meetings: List[MeetingSchedule] = Field(default_factory=list)
    
    # Stakeholder management
    identified_stakeholders: List[Stakeholder] = Field(default_factory=list)
    stakeholder_mapping: Dict[str, List[str]] = Field(default_factory=dict)  # role -> stakeholder_ids
    
    # Calendar integration
    calendar_integration_active: bool = False
    calendar_events_created: int = 0
    calendar_conflicts_detected: int = 0
    conflict_resolutions: List[ConflictResolution] = Field(default_factory=list)
    
    # Reminder and notification system
    reminder_system_setup: bool = False
    notifications_scheduled: int = 0
    stakeholder_notifications_sent: int = 0
    
    # Processing metrics
    processing_time: float = 0.0
    meetings_scheduled_successfully: int = 0
    stakeholders_engaged: int = 0
    
    # Quality metrics
    scheduling_efficiency_score: float = Field(ge=0.0, le=100.0, default=0.0)
    stakeholder_satisfaction_predicted: float = Field(ge=0.0, le=100.0, default=0.0)
    timeline_optimization_score: float = Field(ge=0.0, le=100.0, default=0.0)
    
    # Status and next steps
    ready_for_onboarding_execution: bool = False
    onboarding_process_status: str = "meetings_coordinated"
    next_actions: List[str] = Field(default_factory=list)
    requires_manual_review: bool = False
    
    # Error handling
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Integration results
    integration_status: Dict[str, Any] = Field(default_factory=dict)

class CalendarSystemResponse(BaseModel):
    """Respuesta simulada del sistema de calendario"""
    request_id: str
    employee_id: str
    status: str = "completed"
    processing_time_minutes: float
    
    # Calendar data
    calendar_availability: Dict[str, List[CalendarAvailability]] = Field(default_factory=dict)
    meeting_rooms_available: List[Dict[str, Any]] = Field(default_factory=list)
    conflicts_detected: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Meeting creation results
    meetings_created: List[Dict[str, Any]] = Field(default_factory=list)
    invitations_sent: List[Dict[str, Any]] = Field(default_factory=list)
    reminders_scheduled: List[Dict[str, Any]] = Field(default_factory=list)
    
    # System integration
    calendar_system: str = "microsoft_outlook"
    integration_success: bool = True
    
    # Contact information
    system_contact: str = "calendar-admin@company.com"
    support_contact: str = "it-support@company.com"

class CalendarSimulatorConfig(BaseModel):
    """Configuración del simulador de calendario"""
    response_delay_min: int = 60   # 1 minuto
    response_delay_max: int = 300  # 5 minutos
    
    # Availability simulation
    average_availability_percentage: float = 0.75  # 75% availability
    meeting_room_availability_rate: float = 0.85   # 85% room availability
    conflict_rate: float = 0.15                    # 15% chance of conflicts
    
    # Stakeholder templates
    stakeholder_templates: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Meeting room inventory
    meeting_rooms: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Business rules
    business_hours: Dict[str, str] = Field(default_factory=lambda: {
        "start": "08:00",
        "end": "18:00",
        "timezone": "America/Costa_Rica"
    })
    
    # Default meeting templates
    meeting_templates: Dict[MeetingType, Dict[str, Any]] = Field(default_factory=dict)

# Meeting templates for different types
MEETING_TEMPLATES = {
    MeetingType.WELCOME_MEETING: {
        "duration_minutes": 60,
        "required_roles": [StakeholderRole.DIRECT_MANAGER, StakeholderRole.HR_REPRESENTATIVE],
        "agenda": [
            "Welcome and introductions",
            "Company overview and culture",
            "Role expectations and goals",
            "First week schedule review",
            "Q&A session"
        ],
        "priority": MeetingPriority.CRITICAL,
        "day_offset": 0  # Day 1
    },
    MeetingType.HR_ORIENTATION: {
        "duration_minutes": 120,
        "required_roles": [StakeholderRole.HR_REPRESENTATIVE],
        "agenda": [
            "Employee handbook review",
            "Benefits enrollment",
            "Policies and procedures",
            "Compliance training",
            "Payroll and timekeeping"
        ],
        "priority": MeetingPriority.CRITICAL,
        "day_offset": 0  # Day 1
    },
    MeetingType.IT_SETUP: {
        "duration_minutes": 90,
        "required_roles": [StakeholderRole.IT_SUPPORT],
        "agenda": [
            "Equipment setup and configuration",
            "Account access verification",
            "Security protocols training",
            "Software installation",
            "IT support resources"
        ],
        "priority": MeetingPriority.CRITICAL,
        "day_offset": 0  # Day 1
    },
    MeetingType.TEAM_INTRODUCTION: {
        "duration_minutes": 60,
        "required_roles": [StakeholderRole.TEAM_LEAD, StakeholderRole.PROJECT_MANAGER],
        "agenda": [
            "Team member introductions",
            "Current projects overview",
            "Team dynamics and communication",
            "Collaboration tools and processes",
            "Team goals and objectives"
        ],
        "priority": MeetingPriority.HIGH,
        "day_offset": 1  # Day 2
    },
    MeetingType.PROJECT_BRIEFING: {
        "duration_minutes": 90,
        "required_roles": [StakeholderRole.PROJECT_MANAGER],
        "agenda": [
            "Project scope and objectives",
            "Current project status",
            "Role in project team",
            "Project timeline and milestones",
            "Tools and methodologies"
        ],
        "priority": MeetingPriority.HIGH,
        "day_offset": 2  # Day 3
    },
    MeetingType.BUDDY_ASSIGNMENT: {
        "duration_minutes": 30,
        "required_roles": [StakeholderRole.ONBOARDING_BUDDY],
        "agenda": [
            "Buddy program introduction",
            "Informal company culture discussion",
            "Office tour and logistics",
            "Social integration",
            "Open questions and support"
        ],
        "priority": MeetingPriority.MEDIUM,
        "day_offset": 1  # Day 2
    }
}

# Default stakeholder configurations
DEFAULT_STAKEHOLDER_CONFIGS = {
    StakeholderRole.DIRECT_MANAGER: {
        "meeting_preferences": {
            "preferred_duration": 60,
            "preferred_times": ["09:00", "14:00"],
            "meeting_frequency": "weekly"
        }
    },
    StakeholderRole.HR_REPRESENTATIVE: {
        "meeting_preferences": {
            "preferred_duration": 90,
            "preferred_times": ["10:00", "15:00"],
            "meeting_frequency": "as_needed"
        }
    },
    StakeholderRole.IT_SUPPORT: {
        "meeting_preferences": {
            "preferred_duration": 60,
            "preferred_times": ["08:00", "16:00"],
            "meeting_frequency": "as_needed"
        }
    }
}