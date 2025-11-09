from typing import Dict, Any, List, Optional
from langchain.tools import BaseTool
from datetime import datetime, date, time, timedelta
import json
import random
from .schemas import (
    MeetingCoordinationRequest, Stakeholder, StakeholderRole, MeetingSchedule,
    MeetingType, MeetingPriority, OnboardingTimeline, CalendarAvailability,
    ConflictResolution, MEETING_TEMPLATES, DEFAULT_STAKEHOLDER_CONFIGS
)

class StakeholderFinderTool(BaseTool):
    """Herramienta para identificar stakeholders relevantes"""
    name: str = "stakeholder_finder_tool"
    description: str = "Identifica y mapea stakeholders clave para el proceso de onboarding basado en rol, departamento y proyecto"

    def _run(self, employee_data: Dict[str, Any], position_data: Dict[str, Any], contract_details: Dict[str, Any]) -> Dict[str, Any]:
        """Identificar stakeholders relevantes"""
        try:
            stakeholders = []
            stakeholder_mapping = {}
            
            # Extract key information
            department = position_data.get("department", "General")
            position = position_data.get("position", "Employee")
            project_manager = position_data.get("project_manager", "")
            office = position_data.get("office", "Costa Rica")
            
            # 1. DIRECT MANAGER (Always required)
            manager_name = contract_details.get("employment_terms", {}).get("reporting_manager", "Manager TBD")
            direct_manager = Stakeholder(
                stakeholder_id=f"mgr_{employee_data.get('employee_id', 'unknown')}",
                name=manager_name,
                email=self._generate_email(manager_name, "manager"),
                role=StakeholderRole.DIRECT_MANAGER,
                department=department,
                **DEFAULT_STAKEHOLDER_CONFIGS[StakeholderRole.DIRECT_MANAGER]
            )
            stakeholders.append(direct_manager)
            stakeholder_mapping[StakeholderRole.DIRECT_MANAGER.value] = [direct_manager.stakeholder_id]
            
            # 2. HR REPRESENTATIVE (Always required)
            hr_rep = Stakeholder(
                stakeholder_id=f"hr_{office.lower().replace(' ', '_')}",
                name=f"HR Representative - {office}",
                email=f"hr.{office.lower().replace(' ', '_')}@company.com",
                role=StakeholderRole.HR_REPRESENTATIVE,
                department="Human Resources",
                **DEFAULT_STAKEHOLDER_CONFIGS[StakeholderRole.HR_REPRESENTATIVE]
            )
            stakeholders.append(hr_rep)
            stakeholder_mapping[StakeholderRole.HR_REPRESENTATIVE.value] = [hr_rep.stakeholder_id]
            
            # 3. IT SUPPORT (Always required)
            it_support = Stakeholder(
                stakeholder_id=f"it_{office.lower().replace(' ', '_')}",
                name=f"IT Support - {office}",
                email=f"it.support.{office.lower().replace(' ', '_')}@company.com",
                role=StakeholderRole.IT_SUPPORT,
                department="Information Technology",
                **DEFAULT_STAKEHOLDER_CONFIGS[StakeholderRole.IT_SUPPORT]
            )
            stakeholders.append(it_support)
            stakeholder_mapping[StakeholderRole.IT_SUPPORT.value] = [it_support.stakeholder_id]
            
            # 4. PROJECT MANAGER (If specified)
            if project_manager and project_manager != "TBD":
                proj_mgr = Stakeholder(
                    stakeholder_id=f"pm_{project_manager.lower().replace(' ', '_')}",
                    name=project_manager,
                    email=self._generate_email(project_manager, "pm"),
                    role=StakeholderRole.PROJECT_MANAGER,
                    department=department
                )
                stakeholders.append(proj_mgr)
                stakeholder_mapping[StakeholderRole.PROJECT_MANAGER.value] = [proj_mgr.stakeholder_id]
            
            # 5. TEAM LEAD (Based on department and seniority)
            if "senior" in position.lower() or "lead" in position.lower():
                team_lead = Stakeholder(
                    stakeholder_id=f"tl_{department.lower().replace(' ', '_')}",
                    name=f"Team Lead - {department}",
                    email=f"team.lead.{department.lower().replace(' ', '_')}@company.com",
                    role=StakeholderRole.TEAM_LEAD,
                    department=department
                )
                stakeholders.append(team_lead)
                stakeholder_mapping[StakeholderRole.TEAM_LEAD.value] = [team_lead.stakeholder_id]
            
            # 6. ONBOARDING BUDDY (Always assign)
            buddy = Stakeholder(
                stakeholder_id=f"buddy_{employee_data.get('employee_id', 'unknown')}",
                name=f"Onboarding Buddy - {department}",
                email=f"buddy.{department.lower().replace(' ', '_')}@company.com",
                role=StakeholderRole.ONBOARDING_BUDDY,
                department=department
            )
            stakeholders.append(buddy)
            stakeholder_mapping[StakeholderRole.ONBOARDING_BUDDY.value] = [buddy.stakeholder_id]
            
            # 7. DEPARTMENT HEAD (For senior positions)
            if "senior" in position.lower() or "manager" in position.lower():
                dept_head = Stakeholder(
                    stakeholder_id=f"head_{department.lower().replace(' ', '_')}",
                    name=f"Department Head - {department}",
                    email=f"head.{department.lower().replace(' ', '_')}@company.com",
                    role=StakeholderRole.DEPARTMENT_HEAD,
                    department=department
                )
                stakeholders.append(dept_head)
                stakeholder_mapping[StakeholderRole.DEPARTMENT_HEAD.value] = [dept_head.stakeholder_id]
            
            # 8. TRAINING COORDINATOR (If training required)
            training_coord = Stakeholder(
                stakeholder_id=f"training_{office.lower().replace(' ', '_')}",
                name=f"Training Coordinator - {office}",
                email=f"training.{office.lower().replace(' ', '_')}@company.com",
                role=StakeholderRole.TRAINING_COORDINATOR,
                department="Learning & Development"
            )
            stakeholders.append(training_coord)
            stakeholder_mapping[StakeholderRole.TRAINING_COORDINATOR.value] = [training_coord.stakeholder_id]
            
            return {
                "success": True,
                "stakeholders_identified": stakeholders,
                "stakeholder_mapping": stakeholder_mapping,
                "total_stakeholders": len(stakeholders),
                "critical_stakeholders": len([s for s in stakeholders if s.role in [
                    StakeholderRole.DIRECT_MANAGER, 
                    StakeholderRole.HR_REPRESENTATIVE, 
                    StakeholderRole.IT_SUPPORT
                ]]),
                "identification_notes": [
                    f"Identified {len(stakeholders)} stakeholders for {position} in {department}",
                    f"Critical stakeholders: Manager, HR, IT Support",
                    f"Optional stakeholders based on role seniority and requirements"
                ]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error identifying stakeholders: {str(e)}",
                "stakeholders_identified": [],
                "stakeholder_mapping": {}
            }
    
    def _generate_email(self, name: str, role_prefix: str) -> str:
        """Generate email from name"""
        clean_name = name.lower().replace(" ", ".").replace("-", ".")
        return f"{clean_name}@company.com"

class CalendarAnalyzerTool(BaseTool):
    """Herramienta para analizar disponibilidad de calendarios"""
    name: str = "calendar_analyzer_tool"
    description: str = "Analiza disponibilidad de calendarios de stakeholders y detecta conflictos potenciales"

    def _run(self, stakeholders: List[Dict[str, Any]], start_date: str, business_hours: str = "9:00-17:00") -> Dict[str, Any]:
        """Analizar disponibilidad de calendarios"""
        try:
            start_date_obj = datetime.fromisoformat(start_date).date()
            analysis_period_days = 30  # Analyze next 30 days
            
            stakeholder_availability = {}
            conflicts_detected = []
            optimal_slots = []
            
            # Generate availability for each stakeholder
            for stakeholder_data in stakeholders:
                stakeholder_id = stakeholder_data.get("stakeholder_id")
                role = stakeholder_data.get("role")
                
                # Generate realistic availability
                availability = self._generate_stakeholder_availability(
                    stakeholder_id, 
                    start_date_obj, 
                    analysis_period_days,
                    role
                )
                stakeholder_availability[stakeholder_id] = availability
            
            # Find optimal meeting slots
            for day_offset in range(14):  # First 2 weeks
                analysis_date = start_date_obj + timedelta(days=day_offset)
                
                # Skip weekends
                if analysis_date.weekday() >= 5:
                    continue
                
                daily_slots = self._find_daily_optimal_slots(
                    stakeholder_availability, 
                    analysis_date,
                    business_hours
                )
                optimal_slots.extend(daily_slots)
            
            # Detect potential conflicts
            conflicts = self._detect_scheduling_conflicts(optimal_slots, stakeholder_availability)
            
            # Calculate availability metrics
            availability_metrics = self._calculate_availability_metrics(stakeholder_availability)
            
            return {
                "success": True,
                "analysis_period_start": start_date,
                "analysis_period_days": analysis_period_days,
                "stakeholder_availability": stakeholder_availability,
                "optimal_meeting_slots": optimal_slots[:20],  # Top 20 slots
                "conflicts_detected": conflicts,
                "availability_metrics": availability_metrics,
                "scheduling_recommendations": [
                    "Schedule critical meetings (Welcome, HR, IT) on Day 1",
                    "Distribute team meetings across first week",
                    "Reserve flexible slots for follow-up meetings",
                    f"Best meeting times: {availability_metrics.get('optimal_hours', ['10:00', '14:00'])}"
                ]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error analyzing calendar availability: {str(e)}",
                "stakeholder_availability": {},
                "optimal_meeting_slots": []
            }
    
    def _generate_stakeholder_availability(self, stakeholder_id: str, start_date: date, days: int, role: str) -> List[CalendarAvailability]:
        """Generate realistic availability for a stakeholder"""
        availability = []
        
        # Different availability patterns by role
        availability_patterns = {
            "direct_manager": 0.7,      # 70% available
            "hr_representative": 0.8,   # 80% available
            "it_support": 0.85,         # 85% available
            "project_manager": 0.65,    # 65% available
            "team_lead": 0.75,          # 75% available
            "onboarding_buddy": 0.9,    # 90% available
            "department_head": 0.5,     # 50% available (busy)
            "training_coordinator": 0.8  # 80% available
        }
        
        base_availability = availability_patterns.get(role, 0.75)
        
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            
            # Skip weekends
            if current_date.weekday() >= 5:
                continue
            
            # Generate available slots
            available_slots = []
            busy_slots = []
            
            # Business hours: 9:00-17:00 (8 hours = 480 minutes)
            total_minutes = 480
            available_minutes = int(total_minutes * base_availability)
            
            # Create realistic time slots
            current_time = 9 * 60  # 9:00 AM in minutes
            end_time = 17 * 60     # 5:00 PM in minutes
            
            while current_time < end_time:
                slot_duration = random.choice([30, 60, 90, 120])  # Random meeting durations
                
                if random.random() < base_availability:
                    # Available slot
                    available_slots.append({
                        "start": f"{current_time // 60:02d}:{current_time % 60:02d}",
                        "end": f"{(current_time + slot_duration) // 60:02d}:{(current_time + slot_duration) % 60:02d}"
                    })
                else:
                    # Busy slot
                    busy_slots.append({
                        "start": f"{current_time // 60:02d}:{current_time % 60:02d}",
                        "end": f"{(current_time + slot_duration) // 60:02d}:{(current_time + slot_duration) % 60:02d}"
                    })
                
                current_time += slot_duration
            
            day_availability = CalendarAvailability(
                stakeholder_id=stakeholder_id,
                date=current_date,
                available_slots=available_slots,
                busy_slots=busy_slots
            )
            availability.append(day_availability)
        
        return availability
    
    def _find_daily_optimal_slots(self, all_availability: Dict[str, List], target_date: date, business_hours: str) -> List[Dict[str, Any]]:
        """Find optimal meeting slots for a specific day"""
        daily_slots = []
        
        # Common meeting times to check
        common_times = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
        
        for meeting_time in common_times:
            slot_quality = self._evaluate_slot_quality(all_availability, target_date, meeting_time)
            
            if slot_quality["score"] > 60:  # Good enough slot
                daily_slots.append({
                    "date": target_date.isoformat(),
                    "time": meeting_time,
                    "quality_score": slot_quality["score"],
                    "available_stakeholders": slot_quality["available_count"],
                    "conflicts": slot_quality["conflicts"]
                })
        
        # Sort by quality score
        daily_slots.sort(key=lambda x: x["quality_score"], reverse=True)
        return daily_slots
    
    def _evaluate_slot_quality(self, all_availability: Dict, target_date: date, meeting_time: str) -> Dict[str, Any]:
        """Evaluate quality of a specific time slot"""
        available_count = 0
        total_stakeholders = len(all_availability)
        conflicts = []
        
        for stakeholder_id, availability_list in all_availability.items():
            # Find availability for target date
            day_availability = next((a for a in availability_list if a.date == target_date), None)
            
            if day_availability:
                # Check if meeting time is available
                time_available = any(
                    slot["start"] <= meeting_time <= slot["end"] 
                    for slot in day_availability.available_slots
                )
                
                if time_available:
                    available_count += 1
                else:
                    conflicts.append(stakeholder_id)
        
        score = (available_count / total_stakeholders) * 100 if total_stakeholders > 0 else 0
        
        return {
            "score": score,
            "available_count": available_count,
            "total_stakeholders": total_stakeholders,
            "conflicts": conflicts
        }
    
    def _detect_scheduling_conflicts(self, optimal_slots: List, stakeholder_availability: Dict) -> List[Dict[str, Any]]:
        """Detect potential scheduling conflicts"""
        conflicts = []
        
        # Simple conflict detection - overlapping high-priority meetings
        for i, slot1 in enumerate(optimal_slots[:10]):  # Check top 10 slots
            for slot2 in optimal_slots[i+1:i+6]:  # Check next 5 slots
                if slot1["date"] == slot2["date"]:
                    time_diff = abs(
                        int(slot1["time"].split(":")[0]) - int(slot2["time"].split(":")[0])
                    )
                    
                    if time_diff < 2:  # Less than 2 hours apart
                        conflicts.append({
                            "conflict_type": "close_timing",
                            "slot1": slot1,
                            "slot2": slot2,
                            "issue": f"Meetings too close together ({time_diff} hour(s))",
                            "recommendation": "Space meetings at least 2 hours apart"
                        })
        
        return conflicts
    
    def _calculate_availability_metrics(self, stakeholder_availability: Dict) -> Dict[str, Any]:
        """Calculate overall availability metrics"""
        if not stakeholder_availability:
            return {}
        
        total_slots = 0
        available_slots = 0
        optimal_hours = []
        
        # Count available vs total slots
        for stakeholder_id, availability_list in stakeholder_availability.items():
            for day_avail in availability_list:
                total_slots += len(day_avail.available_slots) + len(day_avail.busy_slots)
                available_slots += len(day_avail.available_slots)
                
                # Track popular times
                for slot in day_avail.available_slots:
                    hour = slot["start"].split(":")[0]
                    optimal_hours.append(hour)
        
        # Find most common available hours
        from collections import Counter
        hour_counts = Counter(optimal_hours)
        best_hours = [f"{hour}:00" for hour, count in hour_counts.most_common(3)]
        
        availability_percentage = (available_slots / total_slots * 100) if total_slots > 0 else 0
        
        return {
            "overall_availability_percentage": round(availability_percentage, 1),
            "total_time_slots_analyzed": total_slots,
            "available_time_slots": available_slots,
            "optimal_hours": best_hours,
            "scheduling_difficulty": "Easy" if availability_percentage > 70 else "Moderate" if availability_percentage > 50 else "Challenging"
        }

class SchedulerOptimizerTool(BaseTool):
    """Herramienta para optimizar programación de reuniones"""
    name: str = "scheduler_optimizer_tool"
    description: str = "Optimiza la programación de reuniones considerando prioridades, dependencias y preferencias"

    def _run(self, stakeholders: List[Dict[str, Any]], optimal_slots: List[Dict[str, Any]], 
             employee_data: Dict[str, Any], start_date: str) -> Dict[str, Any]:
        """Optimizar programación de reuniones"""
        try:
            start_date_obj = datetime.fromisoformat(start_date).date()
            optimized_schedule = []
            stakeholder_map = {s["stakeholder_id"]: s for s in stakeholders}
            
            # Create onboarding timeline
            timeline = OnboardingTimeline(
                employee_id=employee_data.get("employee_id", "unknown"),
                start_date=start_date_obj
            )
            
            # Schedule Day 1 critical meetings
            day_1_meetings = self._schedule_critical_meetings(
                stakeholder_map, optimal_slots, start_date_obj, employee_data
            )
            timeline.day_1_meetings = day_1_meetings
            optimized_schedule.extend(day_1_meetings)
            
            # Schedule Week 1 meetings
            week_1_meetings = self._schedule_week_1_meetings(
                stakeholder_map, optimal_slots, start_date_obj, employee_data
            )
            timeline.week_1_meetings = week_1_meetings
            optimized_schedule.extend(week_1_meetings)
            
            # Schedule Month 1 meetings
            month_1_meetings = self._schedule_month_1_meetings(
                stakeholder_map, optimal_slots, start_date_obj, employee_data
            )
            timeline.month_1_meetings = month_1_meetings
            optimized_schedule.extend(month_1_meetings)
            
            # Calculate timeline metrics
            timeline.total_meetings = len(optimized_schedule)
            timeline.estimated_total_hours = sum(m.duration_minutes for m in optimized_schedule) / 60
            timeline.critical_meetings_count = len([m for m in optimized_schedule if m.priority == MeetingPriority.CRITICAL])
            
            # Add milestones
            timeline.onboarding_milestones = [
                {
                    "milestone": "Day 1 Setup Complete",
                    "date": start_date_obj.isoformat(),
                    "meetings": len(day_1_meetings),
                    "status": "scheduled"
                },
                {
                    "milestone": "Week 1 Integration",
                    "date": (start_date_obj + timedelta(days=7)).isoformat(),
                    "meetings": len(week_1_meetings),
                    "status": "scheduled"
                },
                {
                    "milestone": "Month 1 Assessment",
                    "date": (start_date_obj + timedelta(days=30)).isoformat(),
                    "meetings": len(month_1_meetings),
                    "status": "scheduled"
                }
            ]
            
            # Calculate optimization metrics
            optimization_metrics = self._calculate_optimization_metrics(optimized_schedule, optimal_slots)
            
            return {
                "success": True,
                "onboarding_timeline": timeline,
                "optimized_meetings": optimized_schedule,
                "optimization_metrics": optimization_metrics,
                "scheduling_summary": {
                    "total_meetings_scheduled": len(optimized_schedule),
                    "day_1_meetings": len(day_1_meetings),
                    "week_1_meetings": len(week_1_meetings),
                    "month_1_meetings": len(month_1_meetings),
                    "estimated_total_hours": timeline.estimated_total_hours,
                    "critical_meetings": timeline.critical_meetings_count
                },
                "optimization_recommendations": [
                    "Day 1 focused on essential setup and welcome",
                    "Week 1 emphasizes team integration and project briefing",
                    "Month 1 includes progress reviews and development planning",
                    f"Total time investment: {timeline.estimated_total_hours:.1f} hours over first month"
                ]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error optimizing schedule: {str(e)}",
                "onboarding_timeline": None,
                "optimized_meetings": []
            }
    
    def _schedule_critical_meetings(self, stakeholder_map: Dict, optimal_slots: List, 
                                  start_date: date, employee_data: Dict) -> List[MeetingSchedule]:
        """Schedule Day 1 critical meetings"""
        critical_meetings = []
        day_1_slots = [slot for slot in optimal_slots if slot["date"] == start_date.isoformat()]
        
        # Sort by quality score
        day_1_slots.sort(key=lambda x: x["quality_score"], reverse=True)
        
        # 1. Welcome Meeting (9:00 AM - highest priority)
        if day_1_slots:
            welcome_slot = day_1_slots[0]
            welcome_meeting = self._create_meeting_from_template(
                MeetingType.WELCOME_MEETING,
                stakeholder_map,
                employee_data,
                start_date,
                welcome_slot["time"]
            )
            critical_meetings.append(welcome_meeting)
        
        # 2. HR Orientation (10:30 AM)
        if len(day_1_slots) > 1:
            hr_slot = day_1_slots[1]
            hr_meeting = self._create_meeting_from_template(
                MeetingType.HR_ORIENTATION,
                stakeholder_map,
                employee_data,
                start_date,
                "10:30"
            )
            critical_meetings.append(hr_meeting)
        
        # 3. IT Setup (2:00 PM)
        it_meeting = self._create_meeting_from_template(
            MeetingType.IT_SETUP,
            stakeholder_map,
            employee_data,
            start_date,
            "14:00"
        )
        critical_meetings.append(it_meeting)
        
        return critical_meetings
    
    def _schedule_week_1_meetings(self, stakeholder_map: Dict, optimal_slots: List,
                                start_date: date, employee_data: Dict) -> List[MeetingSchedule]:
        """Schedule Week 1 meetings"""
        week_1_meetings = []
        
        # Day 2: Team Introduction
        day_2 = start_date + timedelta(days=1)
        team_meeting = self._create_meeting_from_template(
            MeetingType.TEAM_INTRODUCTION,
            stakeholder_map,
            employee_data,
            day_2,
            "10:00"
        )
        week_1_meetings.append(team_meeting)
        
        # Day 2: Buddy Assignment
        buddy_meeting = self._create_meeting_from_template(
            MeetingType.BUDDY_ASSIGNMENT,
            stakeholder_map,
            employee_data,
            day_2,
            "15:00"
        )
        week_1_meetings.append(buddy_meeting)
        
        # Day 3: Project Briefing
        day_3 = start_date + timedelta(days=2)
        project_meeting = self._create_meeting_from_template(
            MeetingType.PROJECT_BRIEFING,
            stakeholder_map,
            employee_data,
            day_3,
            "09:00"
        )
        week_1_meetings.append(project_meeting)
        
        return week_1_meetings
    
    def _schedule_month_1_meetings(self, stakeholder_map: Dict, optimal_slots: List,
                                 start_date: date, employee_data: Dict) -> List[MeetingSchedule]:
        """Schedule Month 1 recurring and follow-up meetings"""
        month_1_meetings = []
        
        # Week 2: Manager Check-in
        week_2_date = start_date + timedelta(days=7)
        manager_checkin = MeetingSchedule(
            meeting_type=MeetingType.MANAGER_CHECKIN,
            title="Weekly Manager Check-in",
            description="Regular check-in with direct manager to discuss progress and address any questions",
            scheduled_date=week_2_date,
            scheduled_time=time(14, 0),  # 2:00 PM
            duration_minutes=30,
            organizer=self._find_stakeholder_by_role(stakeholder_map, StakeholderRole.DIRECT_MANAGER),
            attendees=[self._find_stakeholder_by_role(stakeholder_map, StakeholderRole.DIRECT_MANAGER)],
            priority=MeetingPriority.HIGH
        )
        month_1_meetings.append(manager_checkin)
        
        # Week 3: Training Session
        week_3_date = start_date + timedelta(days=14)
        training_session = MeetingSchedule(
            meeting_type=MeetingType.TRAINING_SESSION,
            title="Role-specific Training Session",
            description="Specialized training for role responsibilities and company processes",
            scheduled_date=week_3_date,
            scheduled_time=time(10, 0),  # 10:00 AM
            duration_minutes=120,
            organizer=self._find_stakeholder_by_role(stakeholder_map, StakeholderRole.TRAINING_COORDINATOR),
            attendees=[self._find_stakeholder_by_role(stakeholder_map, StakeholderRole.TRAINING_COORDINATOR)],
            priority=MeetingPriority.MEDIUM
        )
        month_1_meetings.append(training_session)
        
        return month_1_meetings
    
    def _create_meeting_from_template(self, meeting_type: MeetingType, stakeholder_map: Dict,
                                    employee_data: Dict, meeting_date: date, meeting_time: str) -> MeetingSchedule:
        """Create meeting from template"""
        template = MEETING_TEMPLATES[meeting_type]
        
        # Find required attendees
        attendees = []
        required_attendees = []
        
        for role in template["required_roles"]:
            stakeholder = self._find_stakeholder_by_role(stakeholder_map, role)
            if stakeholder:
                attendees.append(stakeholder)
                required_attendees.append(stakeholder.stakeholder_id)
        
        # Set organizer (first required attendee)
        organizer = attendees[0] if attendees else None
        
        # Parse time
        hour, minute = map(int, meeting_time.split(":"))
        
        meeting = MeetingSchedule(
            meeting_type=meeting_type,
            title=f"{meeting_type.value.replace('_', ' ').title()} - {employee_data.get('first_name', 'New Employee')}",
            description=f"Onboarding {meeting_type.value.replace('_', ' ')} for {employee_data.get('first_name', 'New Employee')}",
            scheduled_date=meeting_date,
            scheduled_time=time(hour, minute),
            duration_minutes=template["duration_minutes"],
            organizer=organizer,
            attendees=attendees,
            required_attendees=required_attendees,
            agenda=template["agenda"],
            priority=template["priority"],
            virtual_meeting_url=f"https://teams.microsoft.com/meet/{meeting_type.value}_{employee_data.get('employee_id', 'unknown')}"
        )
        
        return meeting
    
    def _find_stakeholder_by_role(self, stakeholder_map: Dict, role: StakeholderRole) -> Optional[Stakeholder]:
        """Find stakeholder by role"""
        for stakeholder_data in stakeholder_map.values():
            if stakeholder_data.get("role") == role.value:
                return Stakeholder(**stakeholder_data)
        return None
    
    def _calculate_optimization_metrics(self, meetings: List[MeetingSchedule], optimal_slots: List) -> Dict[str, Any]:
        """Calculate optimization quality metrics"""
        if not meetings:
            return {}
        
        # Calculate metrics
        total_meetings = len(meetings)
        critical_meetings = len([m for m in meetings if m.priority == MeetingPriority.CRITICAL])
        average_duration = sum(m.duration_minutes for m in meetings) / total_meetings
        
        # Spacing quality (meetings well distributed)
        meeting_dates = [m.scheduled_date for m in meetings]
        unique_dates = len(set(meeting_dates))
        spacing_score = (unique_dates / total_meetings) * 100 if total_meetings > 0 else 0
        
        # Time slot utilization
        used_optimal_slots = len([m for m in meetings if any(
            slot["date"] == m.scheduled_date.isoformat() and 
            slot["time"] == m.scheduled_time.strftime("%H:%M")
            for slot in optimal_slots
        )])
        slot_utilization = (used_optimal_slots / len(optimal_slots)) * 100 if optimal_slots else 0
        
        return {
            "total_meetings_optimized": total_meetings,
            "critical_meetings_percentage": (critical_meetings / total_meetings) * 100,
            "average_meeting_duration_minutes": round(average_duration, 1),
            "spacing_optimization_score": round(spacing_score, 1),
            "optimal_slot_utilization": round(slot_utilization, 1),
            "overall_optimization_score": round((spacing_score + slot_utilization) / 2, 1),
            "optimization_quality": "Excellent" if slot_utilization > 80 else "Good" if slot_utilization > 60 else "Needs Improvement"
        }

class InvitationManagerTool(BaseTool):
    """Herramienta para gestionar invitaciones y notificaciones"""
    name: str = "invitation_manager_tool"
    description: str = "Gestiona envío de invitaciones, recordatorios y configuración de notificaciones para reuniones"

    def _run(self, meetings: List[Dict[str, Any]], stakeholders: List[Dict[str, Any]], 
             employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gestionar invitaciones y notificaciones"""
        try:
            invitation_results = []
            notification_results = []
            stakeholder_engagement = {}
            
            # Create stakeholder map for easy lookup
            stakeholder_map = {s["stakeholder_id"]: s for s in stakeholders}
            
            # Process each meeting
            for meeting_data in meetings:
                meeting_id = meeting_data.get("meeting_id", f"meeting_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
                
                # Create calendar invitations
                invitation_result = self._create_calendar_invitations(meeting_data, stakeholder_map, employee_data)
                invitation_results.append(invitation_result)
                
                # Setup meeting reminders
                reminder_result = self._setup_meeting_reminders(meeting_data, stakeholder_map)
                notification_results.extend(reminder_result)
                
                # Track stakeholder engagement
                attendees = meeting_data.get("attendees", [])
                for attendee_data in attendees:
                    stakeholder_id = attendee_data.get("stakeholder_id")
                    if stakeholder_id:
                        if stakeholder_id not in stakeholder_engagement:
                            stakeholder_engagement[stakeholder_id] = {
                                "name": attendee_data.get("name", "Unknown"),
                                "meetings_invited": 0,
                                "notifications_sent": 0,
                                "engagement_score": 0
                            }
                        stakeholder_engagement[stakeholder_id]["meetings_invited"] += 1
            
            # Calculate engagement scores
            for stakeholder_id, engagement in stakeholder_engagement.items():
                base_score = engagement["meetings_invited"] * 20  # Base score per meeting
                notification_bonus = engagement["notifications_sent"] * 5  # Bonus for notifications
                engagement["engagement_score"] = min(100, base_score + notification_bonus)
            
            # Generate stakeholder notifications
            stakeholder_notifications = self._generate_stakeholder_notifications(
                stakeholder_engagement, employee_data
            )
            
            # Setup reminder system
            reminder_system = self._setup_reminder_system(meetings, stakeholders)
            
            return {
                "success": True,
                "invitations_processed": len(invitation_results),
                "invitations_sent": len([r for r in invitation_results if r["success"]]),
                "invitation_results": invitation_results,
                "notifications_scheduled": len(notification_results),
                "notification_results": notification_results,
                "stakeholder_engagement": stakeholder_engagement,
                "stakeholder_notifications": stakeholder_notifications,
                "reminder_system": reminder_system,
                "engagement_summary": {
                    "stakeholders_engaged": len(stakeholder_engagement),
                    "average_engagement_score": round(
                        sum(e["engagement_score"] for e in stakeholder_engagement.values()) / len(stakeholder_engagement), 1
                    ) if stakeholder_engagement else 0,
                    "highly_engaged_stakeholders": len([
                        e for e in stakeholder_engagement.values() if e["engagement_score"] > 80
                    ])
                },
                "invitation_success_rate": (
                    len([r for r in invitation_results if r["success"]]) / len(invitation_results) * 100
                ) if invitation_results else 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error managing invitations: {str(e)}",
                "invitations_processed": 0,
                "notifications_scheduled": 0
            }
    
    def _create_calendar_invitations(self, meeting_data: Dict, stakeholder_map: Dict, employee_data: Dict) -> Dict[str, Any]:
        """Create calendar invitations for a meeting"""
        try:
            meeting_id = meeting_data.get("meeting_id")
            meeting_title = meeting_data.get("title", "Onboarding Meeting")
            meeting_date = meeting_data.get("scheduled_date")
            meeting_time = meeting_data.get("scheduled_time")
            duration = meeting_data.get("duration_minutes", 60)
            
            # Generate invitation content
            invitation_content = self._generate_invitation_content(meeting_data, employee_data)
            
            # Process attendees
            attendee_invitations = []
            attendees = meeting_data.get("attendees", [])
            
            for attendee_data in attendees:
                attendee_invitation = {
                    "attendee_id": attendee_data.get("stakeholder_id"),
                    "attendee_name": attendee_data.get("name"),
                    "attendee_email": attendee_data.get("email"),
                    "invitation_status": "sent",
                    "invitation_sent_at": datetime.utcnow().isoformat(),
                    "response_required": attendee_data.get("stakeholder_id") in meeting_data.get("required_attendees", [])
                }
                attendee_invitations.append(attendee_invitation)
            
            return {
                "success": True,
                "meeting_id": meeting_id,
                "invitation_title": meeting_title,
                "invitation_content": invitation_content,
                "attendee_invitations": attendee_invitations,
                "calendar_event_created": True,
                "calendar_event_id": f"cal_event_{meeting_id}",
                "virtual_meeting_url": meeting_data.get("virtual_meeting_url"),
                "invitations_sent_count": len(attendee_invitations)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error creating calendar invitation: {str(e)}",
                "meeting_id": meeting_data.get("meeting_id", "unknown")
            }
    
    def _generate_invitation_content(self, meeting_data: Dict, employee_data: Dict) -> str:
        """Generate invitation email content"""
        employee_name = f"{employee_data.get('first_name', 'New')} {employee_data.get('last_name', 'Employee')}"
        meeting_title = meeting_data.get("title", "Onboarding Meeting")
        meeting_type = meeting_data.get("meeting_type", "meeting")
        agenda = meeting_data.get("agenda", [])
        
        content = f"""
Subject: {meeting_title}

Dear Team,

You are invited to participate in an onboarding meeting for our new team member, {employee_name}.

Meeting Details:
- Type: {meeting_type.replace('_', ' ').title()}
- Date: {meeting_data.get('scheduled_date', 'TBD')}
- Time: {meeting_data.get('scheduled_time', 'TBD')}
- Duration: {meeting_data.get('duration_minutes', 60)} minutes
- Location: {meeting_data.get('location', 'Virtual Meeting')}

Meeting Link: {meeting_data.get('virtual_meeting_url', 'Will be provided')}

Agenda:
"""
        
        for i, agenda_item in enumerate(agenda, 1):
            content += f"{i}. {agenda_item}\n"
        
        content += f"""

Please confirm your attendance. This meeting is important for {employee_name}'s successful integration into our team.

Best regards,
HR Team
"""
        
        return content.strip()
    
    def _setup_meeting_reminders(self, meeting_data: Dict, stakeholder_map: Dict) -> List[Dict[str, Any]]:
        """Setup automated reminders for meeting"""
        reminders = []
        meeting_id = meeting_data.get("meeting_id")
        meeting_date = meeting_data.get("scheduled_date")
        attendees = meeting_data.get("attendees", [])
        
        # Different reminder schedules
        reminder_schedule = [
            {"days_before": 7, "type": "initial_notification"},
            {"days_before": 1, "type": "day_before_reminder"},
            {"hours_before": 2, "type": "same_day_reminder"},
            {"minutes_before": 15, "type": "final_reminder"}
        ]
        
        for reminder_config in reminder_schedule:
            for attendee_data in attendees:
                reminder = {
                    "reminder_id": f"reminder_{meeting_id}_{attendee_data.get('stakeholder_id')}_{reminder_config['type']}",
                    "meeting_id": meeting_id,
                    "attendee_id": attendee_data.get("stakeholder_id"),
                    "attendee_email": attendee_data.get("email"),
                    "reminder_type": reminder_config["type"],
                    "scheduled_for": self._calculate_reminder_time(meeting_date, reminder_config),
                    "content": self._generate_reminder_content(meeting_data, reminder_config["type"]),
                    "status": "scheduled"
                }
                reminders.append(reminder)
        
        return reminders
    
    def _calculate_reminder_time(self, meeting_date: str, reminder_config: Dict) -> str:
        """Calculate when to send reminder"""
        try:
            meeting_datetime = datetime.fromisoformat(meeting_date)
            
            if "days_before" in reminder_config:
                reminder_time = meeting_datetime - timedelta(days=reminder_config["days_before"])
            elif "hours_before" in reminder_config:
                reminder_time = meeting_datetime - timedelta(hours=reminder_config["hours_before"])
            elif "minutes_before" in reminder_config:
                reminder_time = meeting_datetime - timedelta(minutes=reminder_config["minutes_before"])
            else:
                reminder_time = meeting_datetime - timedelta(days=1)  # Default
            
            return reminder_time.isoformat()
        except:
            # Fallback
            return datetime.utcnow().isoformat()
    
    def _generate_reminder_content(self, meeting_data: Dict, reminder_type: str) -> str:
        """Generate reminder message content"""
        meeting_title = meeting_data.get("title", "Onboarding Meeting")
        
        content_templates = {
            "initial_notification": f"Upcoming meeting scheduled: {meeting_title}. Please save the date.",
            "day_before_reminder": f"Reminder: You have {meeting_title} tomorrow. Please confirm your attendance.",
            "same_day_reminder": f"Today's meeting reminder: {meeting_title} in 2 hours. Meeting link attached.",
            "final_reminder": f"Final reminder: {meeting_title} starts in 15 minutes. Join now."
        }
        
        return content_templates.get(reminder_type, f"Meeting reminder: {meeting_title}")
    
    def _generate_stakeholder_notifications(self, stakeholder_engagement: Dict, employee_data: Dict) -> List[Dict[str, Any]]:
        """Generate notifications for stakeholders about new employee"""
        notifications = []
        employee_name = f"{employee_data.get('first_name', 'New')} {employee_data.get('last_name', 'Employee')}"
        
        for stakeholder_id, engagement in stakeholder_engagement.items():
            notification = {
                "notification_id": f"stakeholder_notify_{stakeholder_id}",
                "stakeholder_id": stakeholder_id,
                "stakeholder_name": engagement["name"],
                "notification_type": "new_employee_introduction",
                "subject": f"Welcome {employee_name} - Your Role in Onboarding",
                "content": f"""
Hello {engagement['name']},

We're excited to introduce {employee_name}, who will be joining our team.

You have been identified as a key stakeholder in the onboarding process, with {engagement['meetings_invited']} scheduled meetings.

Your participation is crucial for ensuring a smooth integration experience.

Meeting schedule and details will be sent separately.

Thank you for your support in welcoming our new team member.

Best regards,
HR Team
                """.strip(),
                "scheduled_for": datetime.utcnow().isoformat(),
                "priority": "high" if engagement["engagement_score"] > 80 else "medium",
                "status": "scheduled"
            }
            notifications.append(notification)
        
        return notifications
    
    def _setup_reminder_system(self, meetings: List[Dict], stakeholders: List[Dict]) -> Dict[str, Any]:
        """Setup comprehensive reminder system"""
        return {
            "system_active": True,
            "total_meetings_monitored": len(meetings),
            "total_stakeholders": len(stakeholders),
            "reminder_channels": ["email", "calendar", "teams"],
            "reminder_schedule": {
                "week_before": True,
                "day_before": True,
                "2_hours_before": True,
                "15_minutes_before": True
            },
            "escalation_rules": {
                "no_response_after_24h": "send_followup",
                "no_response_after_48h": "escalate_to_manager",
                "meeting_missed": "reschedule_automatically"
            },
            "system_configuration": {
                "timezone": "America/Costa_Rica",
                "business_hours": "08:00-18:00",
                "weekend_reminders": False,
                "auto_reschedule": True
            }
        }

# Export tools
stakeholder_finder_tool = StakeholderFinderTool()
calendar_analyzer_tool = CalendarAnalyzerTool()
scheduler_optimizer_tool = SchedulerOptimizerTool()
invitation_manager_tool = InvitationManagerTool()