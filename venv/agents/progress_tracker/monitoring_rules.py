from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .schemas import (
    PipelineStage, QualityGate, SLAConfiguration, EscalationRule,
    QualityGateStatus, SLAStatus, EscalationLevel, EscalationType
)

class MonitoringRulesEngine:
    """Motor de reglas para monitoreo del pipeline"""
    
    def __init__(self):
        self.quality_gates = self._load_quality_gates()
        self.sla_configurations = self._load_sla_configurations()
        self.escalation_rules = self._load_escalation_rules()
        self.dynamic_thresholds = self._load_dynamic_thresholds()
    
    def _load_quality_gates(self) -> Dict[PipelineStage, QualityGate]:
        """Cargar configuraciones de quality gates"""
        return {
            # ADD: Quality gate para DATA_COLLECTION
            PipelineStage.DATA_COLLECTION: QualityGate(
                gate_id="data_collection_quality_gate",
                stage=PipelineStage.DATA_COLLECTION,
                gate_name="Data Collection Quality Gate",
                description="Validates initial data collection completion",
                required_fields=[
                    "initial_data_collected",
                    "confirmation_completed", 
                    "documentation_validated"
                ],
                quality_thresholds={
                    "collection_completeness": 85.0,
                    "data_quality_score": 75.0
                },
                validation_rules=[
                    {
                        "type": "min_value",
                        "config": {"field": "collection_completeness", "min_value": 85.0},
                        "severity": "warning",
                        "description": "Data collection should be at least 85% complete"
                    }
                ],
                is_mandatory=True,
                can_bypass=True,
                failure_action="warning",
                retry_allowed=True,
                max_retries=2
            ),
            
            PipelineStage.DATA_AGGREGATION: QualityGate(
                gate_id="data_aggregation_quality_gate",
                stage=PipelineStage.DATA_AGGREGATION,
                gate_name="Data Aggregation Quality Gate",
                description="Validates data consolidation and quality before sequential pipeline",
                required_fields=[
                    "aggregation_completed",
                    "overall_quality_score", 
                    "validation_passed",
                    "ready_for_sequential"
                ],
                quality_thresholds={
                    "overall_quality_score": 70.0,
                    "completeness_score": 80.0,
                    "consistency_score": 85.0,
                    "reliability_score": 75.0
                },
                validation_rules=[
                    {
                        "type": "min_value",
                        "config": {"field": "overall_quality_score", "min_value": 70.0},
                        "severity": "error",
                        "description": "Overall quality must be at least 70%"
                    },
                    {
                        "type": "required_boolean",
                        "config": {"field": "validation_passed", "expected_value": True},
                        "severity": "error",
                        "description": "Data validation must pass"
                    },
                    {
                        "type": "min_value",
                        "config": {"field": "completeness_score", "min_value": 80.0},
                        "severity": "warning",
                        "description": "Data completeness should be at least 80%"
                    }
                ],
                is_mandatory=True,
                can_bypass=False,
                failure_action="block",
                retry_allowed=True,
                max_retries=2
            ),
            
            PipelineStage.IT_PROVISIONING: QualityGate(
                gate_id="it_provisioning_quality_gate",
                stage=PipelineStage.IT_PROVISIONING,
                gate_name="IT Provisioning Quality Gate",
                description="Validates IT setup completion and security compliance",
                required_fields=[
                    "credentials_created",
                    "system_access_configured",
                    "equipment_assigned",
                    "security_clearance_assigned"
                ],
                quality_thresholds={
                    "provisioning_success_rate": 90.0,
                    "security_compliance_score": 95.0,
                    "setup_completion_percentage": 85.0
                },
                validation_rules=[
                    {
                        "type": "required_boolean",
                        "config": {"field": "credentials_created", "expected_value": True},
                        "severity": "error",
                        "description": "IT credentials must be created"
                    },
                    {
                        "type": "required_boolean", 
                        "config": {"field": "equipment_assigned", "expected_value": True},
                        "severity": "error",
                        "description": "Equipment must be assigned"
                    },
                    {
                        "type": "min_value",
                        "config": {"field": "security_compliance_score", "min_value": 95.0},
                        "severity": "error",
                        "description": "Security compliance must be at least 95%"
                    }
                ],
                is_mandatory=True,
                can_bypass=True,
                bypass_authorization_level="it_manager",
                failure_action="escalate",
                retry_allowed=True,
                max_retries=3
            ),
            
            PipelineStage.CONTRACT_MANAGEMENT: QualityGate(
                gate_id="contract_management_quality_gate",
                stage=PipelineStage.CONTRACT_MANAGEMENT,
                gate_name="Contract Management Quality Gate", 
                description="Validates contract generation, legal compliance, and signature process",
                required_fields=[
                    "contract_generated",
                    "legal_validation_passed",
                    "signature_process_complete",
                    "document_archived"
                ],
                quality_thresholds={
                    "compliance_score": 90.0,
                    "legal_validation_score": 95.0,
                    "contract_completeness": 100.0
                },
                validation_rules=[
                    {
                        "type": "required_boolean",
                        "config": {"field": "contract_generated", "expected_value": True},
                        "severity": "error",
                        "description": "Contract must be generated"
                    },
                    {
                        "type": "required_boolean",
                        "config": {"field": "legal_validation_passed", "expected_value": True},
                        "severity": "error", 
                        "description": "Legal validation must pass"
                    },
                    {
                        "type": "required_boolean",
                        "config": {"field": "signature_process_complete", "expected_value": True},
                        "severity": "error",
                        "description": "Signature process must be completed"
                    },
                    {
                        "type": "min_value",
                        "config": {"field": "compliance_score", "min_value": 90.0},
                        "severity": "error",
                        "description": "Compliance score must be at least 90%"
                    }
                ],
                is_mandatory=True,
                can_bypass=False,
                failure_action="block",
                retry_allowed=True,
                max_retries=2
            ),
            
            PipelineStage.MEETING_COORDINATION: QualityGate(
                gate_id="meeting_coordination_quality_gate",
                stage=PipelineStage.MEETING_COORDINATION,
                gate_name="Meeting Coordination Quality Gate",
                description="Validates meeting scheduling and stakeholder engagement",
                required_fields=[
                    "stakeholders_engaged",
                    "meetings_scheduled_successfully",
                    "calendar_integration_active",
                    "reminder_system_setup"
                ],
                quality_thresholds={
                    "stakeholder_engagement_score": 80.0,
                    "scheduling_efficiency_score": 75.0,
                    "timeline_optimization_score": 70.0
                },
                validation_rules=[
                    {
                        "type": "min_value",
                        "config": {"field": "stakeholders_engaged", "min_value": 3},
                        "severity": "error",
                        "description": "At least 3 stakeholders must be engaged"
                    },
                    {
                        "type": "min_value",
                        "config": {"field": "meetings_scheduled_successfully", "min_value": 3},
                        "severity": "error",
                        "description": "At least 3 meetings must be scheduled"
                    },
                    {
                        "type": "required_boolean",
                        "config": {"field": "calendar_integration_active", "expected_value": True},
                        "severity": "warning",
                        "description": "Calendar integration should be active"
                    },
                    {
                        "type": "min_value",
                        "config": {"field": "stakeholder_engagement_score", "min_value": 80.0},
                        "severity": "warning",
                        "description": "Stakeholder engagement should be at least 80%"
                    }
                ],
                is_mandatory=True,
                can_bypass=True,
                bypass_authorization_level="hr_manager",
                failure_action="warning",
                retry_allowed=True,
                max_retries=3
            )
        }

    def _load_sla_configurations(self) -> Dict[PipelineStage, SLAConfiguration]:
        """Cargar configuraciones de SLA"""
        return {
            # ADD: SLA para DATA_COLLECTION  
            PipelineStage.DATA_COLLECTION: SLAConfiguration(
                sla_id="data_collection_sla",
                stage=PipelineStage.DATA_COLLECTION,
                agent_id="data_collection_orchestrator",
                target_duration_minutes=20,
                warning_threshold_minutes=15,
                critical_threshold_minutes=25,
                breach_threshold_minutes=30,
                business_hours_only=False,
                exclude_weekends=False,
                auto_escalate_on_warning=False,
                auto_escalate_on_critical=True,
                escalation_contacts=[
                    "data_collection_team@company.com",
                    "system_admin@company.com"
                ],
                extension_allowed=True,
                max_extensions=1,
                extension_duration_minutes=10
            ),
            
            PipelineStage.DATA_AGGREGATION: SLAConfiguration(
                sla_id="data_aggregation_sla",
                stage=PipelineStage.DATA_AGGREGATION,
                agent_id="data_aggregator_agent",
                target_duration_minutes=5,
                warning_threshold_minutes=4,
                critical_threshold_minutes=6,
                breach_threshold_minutes=8,
                business_hours_only=False,  # Data aggregation can run 24/7
                exclude_weekends=False,
                auto_escalate_on_warning=False,
                auto_escalate_on_critical=True,
                escalation_contacts=[
                    "data_team_lead@company.com",
                    "system_admin@company.com"
                ],
                extension_allowed=True,
                max_extensions=1,
                extension_duration_minutes=3
            ),
            
            PipelineStage.IT_PROVISIONING: SLAConfiguration(
                sla_id="it_provisioning_sla",
                stage=PipelineStage.IT_PROVISIONING,
                agent_id="it_provisioning_agent",
                target_duration_minutes=10,
                warning_threshold_minutes=8,
                critical_threshold_minutes=12,
                breach_threshold_minutes=15,
                business_hours_only=True,  # IT provisioning during business hours
                exclude_weekends=True,
                auto_escalate_on_warning=True,
                auto_escalate_on_critical=True,
                escalation_contacts=[
                    "it_manager@company.com",
                    "security_team@company.com",
                    "hr_coordinator@company.com"
                ],
                extension_allowed=True,
                max_extensions=2,
                extension_duration_minutes=5
            ),
            
            PipelineStage.CONTRACT_MANAGEMENT: SLAConfiguration(
                sla_id="contract_management_sla",
                stage=PipelineStage.CONTRACT_MANAGEMENT,
                agent_id="contract_management_agent",
                target_duration_minutes=15,
                warning_threshold_minutes=12,
                critical_threshold_minutes=18,
                breach_threshold_minutes=20,
                business_hours_only=True,  # Legal processes during business hours
                exclude_weekends=True,
                auto_escalate_on_warning=False,
                auto_escalate_on_critical=True,
                escalation_contacts=[
                    "legal_team@company.com",
                    "hr_manager@company.com",
                    "compliance_officer@company.com"
                ],
                extension_allowed=True,
                max_extensions=2,
                extension_duration_minutes=10
            ),
            
            PipelineStage.MEETING_COORDINATION: SLAConfiguration(
                sla_id="meeting_coordination_sla",
                stage=PipelineStage.MEETING_COORDINATION,
                agent_id="meeting_coordination_agent",
                target_duration_minutes=8,
                warning_threshold_minutes=6,
                critical_threshold_minutes=10,
                breach_threshold_minutes=12,
                business_hours_only=True,  # Meeting coordination during business hours
                exclude_weekends=True,
                auto_escalate_on_warning=False,
                auto_escalate_on_critical=True,
                escalation_contacts=[
                    "hr_coordinator@company.com",
                    "calendar_admin@company.com"
                ],
                extension_allowed=True,
                max_extensions=1,
                extension_duration_minutes=5
            )
        }
    def _load_escalation_rules(self) -> List[EscalationRule]:
        """Cargar reglas de escalación"""
        return [
            # Regla 1: SLA Breach crítico
            EscalationRule(
                rule_id="critical_sla_breach",
                rule_name="Critical SLA Breach Alert",
                escalation_type=EscalationType.SLA_BREACH,
                escalation_level=EscalationLevel.CRITICAL,
                trigger_conditions={
                    "sla_status": "breached",
                    "stage_criticality": "high",
                    "breach_duration_minutes": 5
                },
                notification_recipients=[
                    "pipeline_manager@company.com",
                    "hr_director@company.com",
                    "it_director@company.com"
                ],
                automatic_actions=[
                    "pause_pipeline",
                    "create_incident_ticket",
                    "notify_management"
                ],
                escalation_message_template="CRITICAL SLA BREACH: Employee {employee_id} pipeline stage {stage} has breached SLA by {breach_duration} minutes. Immediate intervention required.",
                cooldown_minutes=15,
                max_escalations_per_session=3,
                requires_acknowledgment=True
            ),
            
            # Regla 2: Quality Gate Failure repetido
            EscalationRule(
                rule_id="repeated_quality_failure",
                rule_name="Repeated Quality Gate Failure",
                escalation_type=EscalationType.QUALITY_FAILURE,
                escalation_level=EscalationLevel.WARNING,
                trigger_conditions={
                    "quality_gate_status": "failed",
                    "retry_attempts": 2,
                    "failure_pattern": "repeated"
                },
                notification_recipients=[
                    "quality_assurance@company.com",
                    "data_team_lead@company.com",
                    "hr_coordinator@company.com"
                ],
                automatic_actions=[
                    "flag_for_manual_review",
                    "create_quality_ticket",
                    "pause_stage"
                ],
                escalation_message_template="Quality gate failure for {employee_id} in {stage}. Multiple retry attempts failed. Manual review required.",
                cooldown_minutes=20,
                max_escalations_per_session=2,
                requires_acknowledgment=False
            ),
            
            # Regla 3: Agent Failure con recuperación automática
            EscalationRule(
                rule_id="agent_failure_recovery",
                rule_name="Agent Failure with Auto Recovery",
                escalation_type=EscalationType.AGENT_FAILURE,
                escalation_level=EscalationLevel.CRITICAL,
                trigger_conditions={
                    "agent_status": "failed",
                    "error_count": 3,
                    "consecutive_failures": True
                },
                notification_recipients=[
                    "devops_team@company.com",
                    "system_admin@company.com",
                    "pipeline_support@company.com"
                ],
                automatic_actions=[
                    "restart_agent",
                    "clear_agent_cache",
                    "create_support_ticket",
                    "log_failure_pattern"
                ],
                escalation_message_template="Agent {agent_id} has failed multiple times for employee {employee_id}. Auto-recovery initiated. System team notified.",
                cooldown_minutes=10,
                max_escalations_per_session=5,
                requires_acknowledgment=True
            ),
            
            # Regla 4: Multiple stages at risk
            EscalationRule(
                rule_id="multiple_stages_at_risk",
                rule_name="Multiple Pipeline Stages At Risk",
                escalation_type=EscalationType.SLA_BREACH,
                escalation_level=EscalationLevel.WARNING,
                trigger_conditions={
                    "stages_at_risk": 2,
                    "overall_pipeline_risk": "high"
                },
                notification_recipients=[
                    "pipeline_coordinator@company.com",
                    "hr_manager@company.com"
                ],
                automatic_actions=[
                    "increase_monitoring_frequency",
                    "prepare_contingency_plan",
                    "notify_stakeholders"
                ],
                escalation_message_template="Multiple pipeline stages at risk for employee {employee_id}. Enhanced monitoring activated.",
                cooldown_minutes=30,
                max_escalations_per_session=2,
                requires_acknowledgment=False
            ),
            
            # Regla 5: System overload detection
            EscalationRule(
                rule_id="system_overload_detection",
                rule_name="System Overload Detection",
                escalation_type=EscalationType.SYSTEM_ERROR,
                escalation_level=EscalationLevel.EMERGENCY,
                trigger_conditions={
                    "concurrent_pipelines": 10,
                    "system_load": 0.9,
                    "error_rate": 0.3
                },
                notification_recipients=[
                    "cto@company.com",
                    "infrastructure_team@company.com",
                    "incident_commander@company.com"
                ],
                automatic_actions=[
                    "throttle_new_pipelines",
                    "scale_resources",
                    "create_emergency_ticket",
                    "activate_incident_response"
                ],
                escalation_message_template="SYSTEM EMERGENCY: High load detected. {concurrent_pipelines} concurrent pipelines, {system_load}% load, {error_rate}% error rate.",
                cooldown_minutes=5,
                max_escalations_per_session=1,
                requires_acknowledgment=True
            ),
            
            # Regla 6: Business hours violation
            EscalationRule(
                rule_id="business_hours_violation",
                rule_name="Processing Outside Business Hours",
                escalation_type=EscalationType.MANUAL_INTERVENTION,
                escalation_level=EscalationLevel.WARNING,
                trigger_conditions={
                    "outside_business_hours": True,
                    "requires_human_interaction": True,
                    "stage_type": "manual_dependent"
                },
                notification_recipients=[
                    "after_hours_support@company.com",
                    "hr_emergency@company.com"
                ],
                automatic_actions=[
                    "queue_for_next_business_day",
                    "notify_employee_delay",
                    "update_expected_completion"
                ],
                escalation_message_template="Pipeline for {employee_id} requires manual intervention outside business hours. Queued for next business day.",
                cooldown_minutes=60,
                max_escalations_per_session=1,
                requires_acknowledgment=False
            )
        ]
    
    def _load_dynamic_thresholds(self) -> Dict[str, Any]:
        """Cargar umbrales dinámicos basados en patrones históricos"""
        return {
            "adaptive_sla_adjustment": {
                "enabled": True,
                "adjustment_factor": 0.1,  # 10% adjustment based on history
                "min_historical_data": 10,  # Minimum samples for adjustment
                "confidence_threshold": 0.8
            },
            "quality_trend_analysis": {
                "enabled": True,
                "trend_window_hours": 24,
                "degradation_threshold": 0.15,  # 15% quality degradation
                "improvement_threshold": 0.10   # 10% quality improvement
            },
            "load_based_thresholds": {
                "enabled": True,
                "low_load_multiplier": 0.8,    # Tighter SLAs when load is low
                "high_load_multiplier": 1.3,   # Relaxed SLAs when load is high
                "load_threshold_low": 0.3,
                "load_threshold_high": 0.8
            },
            "time_based_adjustments": {
                "enabled": True,
                "peak_hours": ["09:00-11:00", "14:00-16:00"],
                "peak_adjustment_factor": 1.2,
                "off_peak_adjustment_factor": 0.9
            }
        }
    
    def get_quality_gate(self, stage: PipelineStage) -> Optional[QualityGate]:
        """Obtener quality gate para una etapa"""
        return self.quality_gates.get(stage)
    
    def get_sla_configuration(self, stage: PipelineStage) -> Optional[SLAConfiguration]:
        """Obtener configuración SLA para una etapa"""
        return self.sla_configurations.get(stage)
    
    def get_applicable_escalation_rules(self, escalation_type: EscalationType = None) -> List[EscalationRule]:
        """Obtener reglas de escalación aplicables"""
        if escalation_type:
            return [rule for rule in self.escalation_rules if rule.escalation_type == escalation_type]
        return self.escalation_rules
    
    def adjust_sla_thresholds(self, stage: PipelineStage, historical_data: Dict[str, Any]) -> SLAConfiguration:
        """Ajustar umbrales SLA basado en datos históricos"""
        base_config = self.get_sla_configuration(stage)
        if not base_config or not self.dynamic_thresholds["adaptive_sla_adjustment"]["enabled"]:
            return base_config
        
        # Crear copia para modificar
        adjusted_config = SLAConfiguration(**base_config.dict())
        
        # Analizar datos históricos
        avg_processing_time = historical_data.get("average_processing_time_minutes", base_config.target_duration_minutes)
        success_rate = historical_data.get("success_rate", 1.0)
        sample_count = historical_data.get("sample_count", 0)
        
        # Solo ajustar si hay suficientes datos históricos
        min_samples = self.dynamic_thresholds["adaptive_sla_adjustment"]["min_historical_data"]
        if sample_count >= min_samples:
            adjustment_factor = self.dynamic_thresholds["adaptive_sla_adjustment"]["adjustment_factor"]
            
            # Ajustar basado en tiempo promedio histórico
            if avg_processing_time > base_config.target_duration_minutes:
                # Si históricamente toma más tiempo, relajar un poco los SLAs
                multiplier = 1 + (adjustment_factor * (avg_processing_time / base_config.target_duration_minutes - 1))
            else:
                # Si históricamente es más rápido, mantener o endurecer ligeramente
                multiplier = 1 - (adjustment_factor * 0.5)
            
            # Ajustar basado en tasa de éxito
            if success_rate < 0.9:
                # Baja tasa de éxito, relajar SLAs
                multiplier *= 1 + (adjustment_factor * (1 - success_rate))
            
            # Aplicar ajustes
            adjusted_config.target_duration_minutes = int(base_config.target_duration_minutes * multiplier)
            adjusted_config.warning_threshold_minutes = int(base_config.warning_threshold_minutes * multiplier)
            adjusted_config.critical_threshold_minutes = int(base_config.critical_threshold_minutes * multiplier)
            adjusted_config.breach_threshold_minutes = int(base_config.breach_threshold_minutes * multiplier)
        
        return adjusted_config
    
    def evaluate_quality_trend(self, stage: PipelineStage, recent_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluar tendencias de calidad"""
        if not self.dynamic_thresholds["quality_trend_analysis"]["enabled"] or not recent_results:
            return {"trend": "stable", "confidence": 0.0, "recommendation": "insufficient_data"}
        
        # Extraer scores de calidad
        quality_scores = []
        for result in recent_results:
            score = result.get("overall_quality_score", result.get("quality_score", 0))
            if score > 0:
                quality_scores.append(score)
        
        if len(quality_scores) < 3:
            return {"trend": "stable", "confidence": 0.0, "recommendation": "insufficient_data"}
        
        # Calcular tendencia simple
        recent_avg = sum(quality_scores[-3:]) / 3  # Últimos 3
        older_avg = sum(quality_scores[:-3]) / max(1, len(quality_scores) - 3) if len(quality_scores) > 3 else recent_avg
        
        change_ratio = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
        
        degradation_threshold = self.dynamic_thresholds["quality_trend_analysis"]["degradation_threshold"]
        improvement_threshold = self.dynamic_thresholds["quality_trend_analysis"]["improvement_threshold"]
        
        if change_ratio < -degradation_threshold:
            trend = "degrading"
            recommendation = "investigate_quality_issues"
        elif change_ratio > improvement_threshold:
            trend = "improving"
            recommendation = "maintain_current_practices"
        else:
            trend = "stable"
            recommendation = "monitor_continuously"
        
        confidence = min(1.0, len(quality_scores) / 10)  # Higher confidence with more data
        
        return {
            "trend": trend,
            "change_ratio": change_ratio,
            "confidence": confidence,
            "recent_average": recent_avg,
            "historical_average": older_avg,
            "recommendation": recommendation,
            "sample_count": len(quality_scores)
        }
    
    def get_load_adjusted_sla(self, stage: PipelineStage, current_load: float) -> SLAConfiguration:
        """Obtener SLA ajustado por carga del sistema"""
        base_config = self.get_sla_configuration(stage)
        if not base_config or not self.dynamic_thresholds["load_based_thresholds"]["enabled"]:
            return base_config
        
        # Crear copia para modificar
        adjusted_config = SLAConfiguration(**base_config.dict())
        
        load_config = self.dynamic_thresholds["load_based_thresholds"]
        
        # Determinar multiplier basado en carga
        if current_load <= load_config["load_threshold_low"]:
            multiplier = load_config["low_load_multiplier"]
        elif current_load >= load_config["load_threshold_high"]:
            multiplier = load_config["high_load_multiplier"]
        else:
            # Interpolación lineal entre low y high
            low_threshold = load_config["load_threshold_low"]
            high_threshold = load_config["load_threshold_high"]
            low_multiplier = load_config["low_load_multiplier"]
            high_multiplier = load_config["high_load_multiplier"]
            
            ratio = (current_load - low_threshold) / (high_threshold - low_threshold)
            multiplier = low_multiplier + ratio * (high_multiplier - low_multiplier)
        
        # Aplicar ajuste
        adjusted_config.target_duration_minutes = int(base_config.target_duration_minutes * multiplier)
        adjusted_config.warning_threshold_minutes = int(base_config.warning_threshold_minutes * multiplier)
        adjusted_config.critical_threshold_minutes = int(base_config.critical_threshold_minutes * multiplier)
        adjusted_config.breach_threshold_minutes = int(base_config.breach_threshold_minutes * multiplier)
        
        return adjusted_config
    
    def validate_rule_consistency(self) -> List[str]:
        """Validar consistencia de reglas de monitoreo"""
        issues = []
        
        # Verificar que todas las etapas tengan quality gates
        for stage in PipelineStage:
            if stage not in [PipelineStage.ONBOARDING_EXECUTION, PipelineStage.COMPLETED]:
                if stage not in self.quality_gates:
                    issues.append(f"Missing quality gate for stage: {stage.value}")
                
                if stage not in self.sla_configurations:
                    issues.append(f"Missing SLA configuration for stage: {stage.value}")
        
        # Verificar coherencia en umbrales SLA
        for stage, sla_config in self.sla_configurations.items():
            if sla_config.warning_threshold_minutes >= sla_config.critical_threshold_minutes:
                issues.append(f"SLA warning threshold >= critical threshold for stage: {stage.value}")
            
            if sla_config.critical_threshold_minutes >= sla_config.breach_threshold_minutes:
                issues.append(f"SLA critical threshold >= breach threshold for stage: {stage.value}")
        
        # Verificar escalation rules tienen contactos válidos
        for rule in self.escalation_rules:
            if not rule.notification_recipients:
                issues.append(f"Escalation rule {rule.rule_id} has no notification recipients")
            
            if rule.cooldown_minutes <= 0:
                issues.append(f"Escalation rule {rule.rule_id} has invalid cooldown period")
        
        return issues

# Instancia global del motor de reglas
monitoring_rules_engine = MonitoringRulesEngine()

# Funciones auxiliares para uso en el agente
def get_quality_gate_for_stage(stage: PipelineStage) -> Optional[QualityGate]:
    """Obtener quality gate para una etapa específica"""
    return monitoring_rules_engine.get_quality_gate(stage)

def get_sla_config_for_stage(stage: PipelineStage) -> Optional[SLAConfiguration]:
    """Obtener configuración SLA para una etapa específica"""
    return monitoring_rules_engine.get_sla_configuration(stage)

def get_escalation_rules_by_type(escalation_type: EscalationType) -> List[EscalationRule]:
    """Obtener reglas de escalación por tipo"""
    return monitoring_rules_engine.get_applicable_escalation_rules(escalation_type)

def validate_monitoring_configuration() -> List[str]:
    """Validar configuración completa de monitoreo"""
    return monitoring_rules_engine.validate_rule_consistency()