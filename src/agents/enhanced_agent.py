"""
Enhanced Data Pipeline Agent with Self-Healing
===============================================
Extends the base pipeline agent with self-healing and auto-upgrade capabilities.

New Features:
- Automatic failure recovery
- Incremental upgrades
- Performance monitoring
- Adaptive learning
"""

from typing import Dict, Any, Optional
from pathlib import Path

from src.agents.pipeline_agent import DataPipelineAgent
from src.agents.self_healing import (
    SelfHealingEngine,
    IncrementalUpgradeEngine,
    HealthStatus,
    UpgradeType
)
from src.agents.state import PipelineState, add_error, add_warning
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SelfHealingPipelineAgent(DataPipelineAgent):
    """
    Enhanced pipeline agent with self-healing and auto-upgrade capabilities.
    
    Extends DataPipelineAgent with:
    - Automatic error recovery
    - Incremental pipeline upgrades
    - Performance optimization
    - Continuous improvement
    """
    
    def __init__(self, enable_self_healing: bool = True, enable_auto_upgrade: bool = True):
        """
        Initialize the self-healing agent.
        
        Args:
            enable_self_healing: Enable automatic error recovery
            enable_auto_upgrade: Enable automatic upgrades
        """
        super().__init__()
        
        self.enable_self_healing = enable_self_healing
        self.enable_auto_upgrade = enable_auto_upgrade
        
        # Initialize healing and upgrade engines
        self.healing_engine = SelfHealingEngine()
        self.upgrade_engine = IncrementalUpgradeEngine(self.healing_engine)
        
        logger.info(
            "SelfHealingPipelineAgent initialized",
            self_healing=enable_self_healing,
            auto_upgrade=enable_auto_upgrade
        )
    
    def build_pipeline(
        self,
        requirements: Dict[str, Any],
        max_healing_attempts: int = 3
    ) -> Dict[str, Any]:
        """
        Build a pipeline with self-healing capabilities.
        
        Args:
            requirements: Pipeline requirements
            max_healing_attempts: Maximum self-healing attempts
            
        Returns:
            Dict: Results including healing and upgrade information
        """
        logger.info("Building pipeline with self-healing", pipeline=requirements.get("name"))
        
        healing_attempts = 0
        last_error = None
        
        while healing_attempts <= max_healing_attempts:
            # Attempt to build pipeline
            result = super().build_pipeline(requirements)
            
            # Check if successful
            if result["status"] == "completed":
                # Monitor health
                health_status = self._check_pipeline_health(result)
                result["health_status"] = health_status.value
                
                # Suggest upgrades if enabled
                if self.enable_auto_upgrade:
                    upgrades = self._suggest_upgrades(requirements, result)
                    result["suggested_upgrades"] = [
                        {
                            "type": u.upgrade_type.value,
                            "description": u.description,
                            "improvement": u.estimated_improvement,
                            "risk": u.risk_level
                        }
                        for u in upgrades
                    ]
                
                logger.info("Pipeline built successfully with health monitoring")
                return result
            
            # Pipeline failed - attempt self-healing
            if not self.enable_self_healing or healing_attempts >= max_healing_attempts:
                logger.error("Pipeline build failed, self-healing disabled or max attempts reached")
                return result
            
            # Extract error
            errors = result.get("errors", [])
            if not errors:
                logger.error("Pipeline failed but no error details available")
                return result
            
            last_error = errors[0]
            healing_attempts += 1
            
            logger.info(
                "Attempting self-heal",
                attempt=healing_attempts,
                max_attempts=max_healing_attempts,
                error=last_error
            )
            
            # Attempt to heal
            success, action = self.healing_engine.attempt_self_heal(
                pipeline_name=requirements.get("name", "unknown"),
                error=last_error,
                context={"retry_count": healing_attempts}
            )
            
            if success:
                logger.info("Self-heal action taken", action=action)
                # Modify requirements based on healing action
                requirements = self._apply_healing_adjustments(requirements, action)
            else:
                logger.warning("Self-heal unsuccessful", action=action)
                result["healing_failed"] = True
                result["healing_attempts"] = healing_attempts
                return result
        
        # Max attempts reached
        logger.error("Max healing attempts reached", attempts=healing_attempts)
        return {
            "status": "failed",
            "error": last_error,
            "healing_attempts": healing_attempts,
            "max_attempts_reached": True
        }
    
    def _check_pipeline_health(self, result: Dict[str, Any]) -> HealthStatus:
        """
        Check the health of a generated pipeline.
        
        Args:
            result: Pipeline build result
            
        Returns:
            HealthStatus: Health assessment
        """
        # Mock execution result for health check
        execution_result = {
            "status": result["status"],
            "duration_seconds": 0,  # Not executed yet
            "errors": result.get("errors", []),
            "memory_usage_mb": 0,
            "cpu_usage_percent": 0
        }
        
        pipeline_name = result.get("output_path", "").split("/")[-1]
        health_status = self.healing_engine.monitor_pipeline(pipeline_name, execution_result)
        
        return health_status
    
    def _suggest_upgrades(
        self,
        requirements: Dict[str, Any],
        result: Dict[str, Any]
    ) -> list:
        """
        Analyze pipeline and suggest upgrades.
        
        Args:
            requirements: Original requirements
            result: Build result
            
        Returns:
            List of upgrade candidates
        """
        # Read generated code
        code_file = result.get("generated_files", [None])[0]
        if not code_file:
            return []
        
        try:
            code = Path(code_file).read_text()
        except Exception as e:
            logger.warning(f"Could not read code for upgrade analysis: {e}")
            return []
        
        # Mock health metrics
        from src.agents.self_healing import HealthMetrics
        health_metrics = HealthMetrics(
            success_rate=1.0,
            avg_execution_time=0,
            error_count=len(result.get("errors", [])),
            last_success=None,
            last_failure=None,
            consecutive_failures=0,
            memory_usage_mb=0,
            cpu_usage_percent=0
        )
        
        # Analyze upgrades
        pipeline_name = requirements.get("name", "pipeline")
        upgrades = self.upgrade_engine.analyze_upgrade_opportunities(
            pipeline_name,
            code,
            health_metrics
        )
        
        return upgrades
    
    def _apply_healing_adjustments(
        self,
        requirements: Dict[str, Any],
        healing_action: str
    ) -> Dict[str, Any]:
        """
        Apply adjustments to requirements based on healing action.
        
        Args:
            requirements: Original requirements
            healing_action: Description of healing action taken
            
        Returns:
            Dict: Modified requirements
        """
        modified_reqs = requirements.copy()
        
        # Parse healing action and adjust requirements
        if "batch size" in healing_action.lower():
            # Extract new batch size if mentioned
            import re
            match = re.search(r'(\d+)', healing_action)
            if match:
                batch_size = int(match.group(1))
                modified_reqs["batch_size"] = batch_size
        
        elif "timeout" in healing_action.lower():
            # Increase timeout
            current_timeout = modified_reqs.get("timeout_minutes", 60)
            modified_reqs["timeout_minutes"] = current_timeout * 2
        
        elif "memory" in healing_action.lower():
            # Enable disk-based processing
            modified_reqs["use_disk_cache"] = True
        
        return modified_reqs
    
    def apply_upgrade(
        self,
        pipeline_name: str,
        upgrade_type: str,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Apply an upgrade to an existing pipeline.
        
        Args:
            pipeline_name: Name of pipeline to upgrade
            upgrade_type: Type of upgrade ("performance", "security", etc.)
            dry_run: If True, validate without applying
            
        Returns:
            Dict: Upgrade result
        """
        logger.info("Applying upgrade", pipeline=pipeline_name, type=upgrade_type, dry_run=dry_run)
        
        # Read current pipeline code
        code_file = Path("outputs") / pipeline_name / f"{pipeline_name}.py"
        
        if not code_file.exists():
            return {
                "status": "failed",
                "error": f"Pipeline file not found: {code_file}"
            }
        
        try:
            current_code = code_file.read_text()
        except Exception as e:
            return {
                "status": "failed",
                "error": f"Could not read pipeline code: {e}"
            }
        
        # Get upgrade candidates
        from src.agents.self_healing import HealthMetrics
        mock_metrics = HealthMetrics(
            success_rate=0.8,
            avg_execution_time=400,  # Trigger performance upgrade
            error_count=10,  # Trigger bug fix upgrade
            last_success=None,
            last_failure=None,
            consecutive_failures=0,
            memory_usage_mb=512,
            cpu_usage_percent=60
        )
        
        candidates = self.upgrade_engine.analyze_upgrade_opportunities(
            pipeline_name,
            current_code,
            mock_metrics
        )
        
        # Find matching upgrade
        upgrade_type_enum = UpgradeType[upgrade_type.upper()]
        matching_upgrades = [u for u in candidates if u.upgrade_type == upgrade_type_enum]
        
        if not matching_upgrades:
            return {
                "status": "failed",
                "error": f"No {upgrade_type} upgrade available for this pipeline"
            }
        
        # Apply the first matching upgrade
        upgrade = matching_upgrades[0]
        success, new_code, message = self.upgrade_engine.apply_incremental_upgrade(
            pipeline_name,
            current_code,
            upgrade,
            dry_run=dry_run
        )
        
        result = {
            "status": "completed" if success else "failed",
            "message": message,
            "upgrade_type": upgrade.upgrade_type.value,
            "description": upgrade.description,
            "estimated_improvement": upgrade.estimated_improvement,
            "dry_run": dry_run
        }
        
        # If not dry run and successful, save the new code
        if success and not dry_run:
            code_file.write_text(new_code)
            result["updated_file"] = str(code_file)
        
        logger.info("Upgrade result", **result)
        return result
    
    def rollback_pipeline(
        self,
        pipeline_name: str,
        target_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Rollback a pipeline to a previous version.
        
        Args:
            pipeline_name: Pipeline name
            target_version: Version to rollback to (None = previous)
            
        Returns:
            Dict: Rollback result
        """
        logger.info("Rolling back pipeline", pipeline=pipeline_name, target=target_version)
        
        success, message = self.upgrade_engine.rollback_upgrade(
            pipeline_name,
            target_version
        )
        
        return {
            "status": "completed" if success else "failed",
            "message": message,
            "pipeline": pipeline_name,
            "target_version": target_version or "previous"
        }
    
    def get_pipeline_history(self, pipeline_name: str) -> Dict[str, Any]:
        """
        Get upgrade and health history for a pipeline.
        
        Args:
            pipeline_name: Pipeline name
            
        Returns:
            Dict: History information
        """
        return {
            "upgrade_history": self.upgrade_engine.upgrade_history.get(pipeline_name, []),
            "current_version": self.upgrade_engine.version_registry.get(pipeline_name, "1.0.0"),
            "health_history": [
                {
                    "success_rate": m.success_rate,
                    "avg_execution_time": m.avg_execution_time,
                    "error_count": m.error_count
                }
                for m in self.healing_engine.health_history.get(pipeline_name, [])
            ]
        }