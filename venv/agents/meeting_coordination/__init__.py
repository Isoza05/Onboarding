"""
Meeting Coordination Agent Module

Este módulo contiene el agente especializado en coordinación de reuniones y gestión
de calendarios para el proceso de onboarding automatizado.
"""

from .agent import MeetingCoordinationAgent
from .schemas import (
    MeetingCoordinationRequest,
    MeetingCoordinationResult,
    OnboardingTimeline,
    MeetingSchedule,
    Stakeholder,
    StakeholderRole,
    MeetingType,
    MeetingPriority
)
from .tools import (
    stakeholder_finder_tool,
    calendar_analyzer_tool,
    scheduler_optimizer_tool,
    invitation_manager_tool
)
from .calendar_simulator import calendar_simulator

__all__ = [
    "MeetingCoordinationAgent",
    "MeetingCoordinationRequest",
    "MeetingCoordinationResult", 
    "OnboardingTimeline",
    "MeetingSchedule",
    "Stakeholder",
    "StakeholderRole",
    "MeetingType",
    "MeetingPriority",
    "stakeholder_finder_tool",
    "calendar_analyzer_tool",
    "scheduler_optimizer_tool",
    "invitation_manager_tool",
    "calendar_simulator"
]