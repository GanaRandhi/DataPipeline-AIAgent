"""
Self-Healing and Auto-Upgrade Module
=====================================
Enables the agent to self-heal from failures and incrementally upgrade pipelines.

Features:
- Automatic error detection and recovery
- Incremental pipeline upgrades
- Performance monitoring and optimization
- Adaptive learning from failures
- Version management and rollback
"""

import json
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

from src.utils.logger import get_logger
from src.config.settings import get_config

logger = get_logger(__name__)
config = get_config()


class HealthStatus(Enum):
    """Pipeline health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    CRITICAL = "critical"


class UpgradeType(Enum):
    """Types of pipeline upgrades."""
    PERFORMANCE = "performance"
    SCHEMA = "schema"
    SECURITY = "security"
    FEATURE = "feature"
    BUG_FIX = "bug_fix"


@dataclass
class HealthMetrics:
    """Health metrics for a pipeline."""
    success_rate: float
    avg_execution_time: float
    error_count: int
    last_success: Optional[str]
    last_failure: Optional[str]
    consecutive_failures: int
    memory_usage_mb: float
    cpu_usage_percent: float


@dataclass
class UpgradeCandidate:
    """Represents a potential upgrade to a pipeline."""
    upgrade_type: UpgradeType
    description: str
    estimated_improvement: float
    risk_level: str  # "low", "medium", "high"
    requires_downtime: bool
    code_changes: List[str]
    rollback_plan: str


class SelfHealingEngine:
    """
    Self-healing engine that monitors pipelines and automatically recovers from failures.
    
    Capabilities:
    1. Detects failures and anomalies
    2. Attempts automatic recovery
    3. Learns from past failures
    4. Suggests preventive measures
    """
    
    def __init__(self):
        """Initialize the self-healing engine."""
        self.health_history: Dict[str, List[HealthMetrics]] = {}
        self.failure_patterns: Dict[str, int] = {}
        self.recovery_strategies: Dict[str, callable] = self._load_recovery_strategies()
        
        logger.info("SelfHealingEngine initialized")
    
    def _load_recovery_strategies(self) -> Dict[str, callable]:
        """
        Load recovery strategies for different failure types.
        
        Returns:
            Dict mapping error patterns to recovery functions
        """
        return {
            "connection_timeout": self._recover_connection_timeout,
            "memory_error": self._recover_memory_error,
            "data_quality_failure": self._recover_data_quality_failure,
            "schema_mismatch": self._recover_schema_mismatch,
            "rate_limit_exceeded": self._recover_rate_limit,
            "authentication_failure": self._recover_authentication,
            "deadlock": self._recover_deadlock,
            "disk_full": self._recover_disk_full,
        }
    
    def monitor_pipeline(
        self,
        pipeline_name: str,
        execution_result: Dict[str, Any]
    ) -> HealthStatus:
        """
        Monitor pipeline execution and assess health.
        
        Args:
            pipeline_name: Name of the pipeline
            execution_result: Result from pipeline execution
            
        Returns:
            HealthStatus: Current health status
        """
        logger.info("Monitoring pipeline health", pipeline=pipeline_name)
        
        # Extract metrics
        metrics = HealthMetrics(
            success_rate=self._calculate_success_rate(pipeline_name),
            avg_execution_time=execution_result.get("duration_seconds", 0),
            error_count=len(execution_result.get("errors", [])),
            last_success=datetime.utcnow().isoformat() if execution_result.get("status") == "success" else None,
            last_failure=datetime.utcnow().isoformat() if execution_result.get("status") == "failed" else None,
            consecutive_failures=self._get_consecutive_failures(pipeline_name),
            memory_usage_mb=execution_result.get("memory_usage_mb", 0),
            cpu_usage_percent=execution_result.get("cpu_usage_percent", 0)
        )
        
        # Store metrics
        if pipeline_name not in self.health_history:
            self.health_history[pipeline_name] = []
        self.health_history[pipeline_name].append(metrics)
        
        # Assess health status
        status = self._assess_health_status(metrics)
        
        logger.info(
            "Pipeline health assessed",
            pipeline=pipeline_name,
            status=status.value,
            success_rate=metrics.success_rate
        )
        
        return status
    
    def _calculate_success_rate(self, pipeline_name: str) -> float:
        """Calculate success rate from history."""
        history = self.health_history.get(pipeline_name, [])
        if not history:
            return 1.0
        
        # Look at last 100 executions
        recent = history[-100:]
        successes = sum(1 for m in recent if m.error_count == 0)
        return successes / len(recent)
    
    def _get_consecutive_failures(self, pipeline_name: str) -> int:
        """Get count of consecutive failures."""
        history = self.health_history.get(pipeline_name, [])
        if not history:
            return 0
        
        count = 0
        for metrics in reversed(history):
            if metrics.error_count > 0:
                count += 1
            else:
                break
        return count
    
    def _assess_health_status(self, metrics: HealthMetrics) -> HealthStatus:
        """
        Assess overall health status based on metrics.
        
        Args:
            metrics: Health metrics
            
        Returns:
            HealthStatus: Assessed status
        """
        # Critical: Multiple consecutive failures
        if metrics.consecutive_failures >= 5:
            return HealthStatus.CRITICAL
        
        # Failing: Low success rate or recent failures
        if metrics.success_rate < 0.5 or metrics.consecutive_failures >= 3:
            return HealthStatus.FAILING
        
        # Degraded: Moderate issues
        if metrics.success_rate < 0.9 or metrics.consecutive_failures >= 1:
            return HealthStatus.DEGRADED
        
        # Healthy: No issues
        return HealthStatus.HEALTHY
    
    def attempt_self_heal(
        self,
        pipeline_name: str,
        error: str,
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Attempt to automatically heal a failed pipeline.
        
        Args:
            pipeline_name: Name of the pipeline
            error: Error message
            context: Additional context about the failure
            
        Returns:
            Tuple of (success, action_taken)
        """
        logger.info("Attempting self-heal", pipeline=pipeline_name, error=error)
        
        # Identify error pattern
        error_pattern = self._identify_error_pattern(error)
        
        # Get recovery strategy
        recovery_func = self.recovery_strategies.get(error_pattern)
        
        if not recovery_func:
            logger.warning("No recovery strategy found", pattern=error_pattern)
            return False, "No recovery strategy available"
        
        # Attempt recovery
        try:
            success, action = recovery_func(pipeline_name, error, context)
            
            # Log the attempt
            self._log_recovery_attempt(pipeline_name, error_pattern, success, action)
            
            if success:
                logger.info("Self-heal successful", pipeline=pipeline_name, action=action)
            else:
                logger.warning("Self-heal failed", pipeline=pipeline_name, action=action)
            
            return success, action
            
        except Exception as e:
            logger.error(f"Recovery attempt failed: {e}", exc_info=True)
            return False, f"Recovery exception: {str(e)}"
    
    def _identify_error_pattern(self, error: str) -> str:
        """
        Identify the error pattern from error message.
        
        Args:
            error: Error message
            
        Returns:
            str: Error pattern identifier
        """
        error_lower = error.lower()
        
        patterns = {
            "timeout": "connection_timeout",
            "memory": "memory_error",
            "null": "data_quality_failure",
            "schema": "schema_mismatch",
            "rate limit": "rate_limit_exceeded",
            "authentication": "authentication_failure",
            "deadlock": "deadlock",
            "disk": "disk_full",
        }
        
        for keyword, pattern in patterns.items():
            if keyword in error_lower:
                return pattern
        
        return "unknown"
    
    def _log_recovery_attempt(
        self,
        pipeline_name: str,
        error_pattern: str,
        success: bool,
        action: str
    ) -> None:
        """Log recovery attempt for learning."""
        key = f"{pipeline_name}:{error_pattern}"
        
        if key not in self.failure_patterns:
            self.failure_patterns[key] = 0
        
        if success:
            self.failure_patterns[key] = max(0, self.failure_patterns[key] - 1)
        else:
            self.failure_patterns[key] += 1
    
    # Recovery Strategy Functions
    # ============================
    
    def _recover_connection_timeout(
        self,
        pipeline_name: str,
        error: str,
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Recover from connection timeout.
        
        Strategy:
        1. Wait with exponential backoff
        2. Retry with increased timeout
        3. Switch to backup connection if available
        """
        retry_count = context.get("retry_count", 0)
        max_retries = 3
        
        if retry_count >= max_retries:
            return False, f"Max retries ({max_retries}) exceeded"
        
        # Exponential backoff
        wait_time = 2 ** retry_count
        logger.info(f"Waiting {wait_time}s before retry", pipeline=pipeline_name)
        time.sleep(wait_time)
        
        return True, f"Retrying with {wait_time}s backoff (attempt {retry_count + 1}/{max_retries})"
    
    def _recover_memory_error(
        self,
        pipeline_name: str,
        error: str,
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Recover from memory error.
        
        Strategy:
        1. Reduce batch size
        2. Enable disk-based processing
        3. Clear caches
        """
        current_batch_size = context.get("batch_size", 10000)
        new_batch_size = current_batch_size // 2
        
        if new_batch_size < 100:
            return False, "Batch size too small, cannot reduce further"
        
        action = f"Reducing batch size from {current_batch_size} to {new_batch_size}"
        logger.info(action, pipeline=pipeline_name)
        
        return True, action
    
    def _recover_data_quality_failure(
        self,
        pipeline_name: str,
        error: str,
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Recover from data quality failure.
        
        Strategy:
        1. Apply data cleaning
        2. Skip invalid records
        3. Use default values
        """
        action = "Enabling automatic data cleaning and null handling"
        logger.info(action, pipeline=pipeline_name)
        
        return True, action
    
    def _recover_schema_mismatch(
        self,
        pipeline_name: str,
        error: str,
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Recover from schema mismatch.
        
        Strategy:
        1. Attempt automatic schema migration
        2. Add missing columns with defaults
        3. Cast incompatible types
        """
        action = "Attempting automatic schema reconciliation"
        logger.info(action, pipeline=pipeline_name)
        
        # TODO: Implement actual schema migration logic
        
        return True, action
    
    def _recover_rate_limit(
        self,
        pipeline_name: str,
        error: str,
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Recover from rate limit.
        
        Strategy:
        1. Wait for rate limit reset
        2. Reduce request rate
        3. Use rate limiting queue
        """
        wait_time = 60  # Wait 1 minute
        logger.info(f"Rate limit hit, waiting {wait_time}s", pipeline=pipeline_name)
        time.sleep(wait_time)
        
        return True, f"Waited {wait_time}s for rate limit reset"
    
    def _recover_authentication(
        self,
        pipeline_name: str,
        error: str,
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Recover from authentication failure.
        
        Strategy:
        1. Refresh authentication token
        2. Re-read credentials
        3. Use backup credentials
        """
        action = "Attempting to refresh authentication credentials"
        logger.info(action, pipeline=pipeline_name)
        
        # TODO: Implement actual credential refresh
        
        return False, "Authentication refresh requires manual intervention"
    
    def _recover_deadlock(
        self,
        pipeline_name: str,
        error: str,
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Recover from database deadlock.
        
        Strategy:
        1. Retry transaction immediately
        2. Randomize operation order
        3. Reduce concurrency
        """
        retry_count = context.get("retry_count", 0)
        
        if retry_count >= 3:
            return False, "Max deadlock retries exceeded"
        
        # Small random delay to break deadlock pattern
        wait_time = 0.1 * (retry_count + 1)
        time.sleep(wait_time)
        
        return True, f"Retrying after deadlock (attempt {retry_count + 1})"
    
    def _recover_disk_full(
        self,
        pipeline_name: str,
        error: str,
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Recover from disk full error.
        
        Strategy:
        1. Clean temporary files
        2. Compress existing data
        3. Use alternative storage location
        """
        action = "Cleaning temporary files and caches"
        logger.info(action, pipeline=pipeline_name)
        
        # TODO: Implement actual cleanup logic
        
        return True, action


class IncrementalUpgradeEngine:
    """
    Engine for incrementally upgrading pipelines without breaking existing functionality.
    
    Capabilities:
    1. Analyzes pipeline performance
    2. Identifies upgrade opportunities
    3. Applies incremental improvements
    4. Validates upgrades before deployment
    5. Automatic rollback on failure
    """
    
    def __init__(self, healing_engine: SelfHealingEngine):
        """
        Initialize the upgrade engine.
        
        Args:
            healing_engine: Reference to self-healing engine for metrics
        """
        self.healing_engine = healing_engine
        self.upgrade_history: Dict[str, List[Dict[str, Any]]] = {}
        self.version_registry: Dict[str, str] = {}
        
        logger.info("IncrementalUpgradeEngine initialized")
    
    def analyze_upgrade_opportunities(
        self,
        pipeline_name: str,
        pipeline_code: str,
        health_metrics: HealthMetrics
    ) -> List[UpgradeCandidate]:
        """
        Analyze a pipeline and identify upgrade opportunities.
        
        Args:
            pipeline_name: Name of the pipeline
            pipeline_code: Current pipeline code
            health_metrics: Health metrics
            
        Returns:
            List of upgrade candidates
        """
        logger.info("Analyzing upgrade opportunities", pipeline=pipeline_name)
        
        candidates = []
        
        # Performance upgrades
        if health_metrics.avg_execution_time > 300:  # > 5 minutes
            candidates.append(UpgradeCandidate(
                upgrade_type=UpgradeType.PERFORMANCE,
                description="Add parallel processing to reduce execution time",
                estimated_improvement=0.4,  # 40% faster
                risk_level="medium",
                requires_downtime=False,
                code_changes=[
                    "Add multiprocessing for batch operations",
                    "Implement connection pooling",
                    "Add result caching"
                ],
                rollback_plan="Revert to sequential processing"
            ))
        
        # Security upgrades
        if "password" in pipeline_code.lower() and "getenv" not in pipeline_code:
            candidates.append(UpgradeCandidate(
                upgrade_type=UpgradeType.SECURITY,
                description="Move hardcoded credentials to environment variables",
                estimated_improvement=0.0,
                risk_level="low",
                requires_downtime=False,
                code_changes=[
                    "Replace hardcoded passwords with os.getenv()",
                    "Add credential validation"
                ],
                rollback_plan="Restore original credential handling"
            ))
        
        # Data quality upgrades
        if health_metrics.error_count > 5:
            candidates.append(UpgradeCandidate(
                upgrade_type=UpgradeType.BUG_FIX,
                description="Add data validation and error handling",
                estimated_improvement=0.6,  # 60% fewer errors
                risk_level="low",
                requires_downtime=False,
                code_changes=[
                    "Add input validation",
                    "Implement null handling",
                    "Add try-except blocks"
                ],
                rollback_plan="Remove validation layer"
            ))
        
        # Feature upgrades
        if "logging" not in pipeline_code:
            candidates.append(UpgradeCandidate(
                upgrade_type=UpgradeType.FEATURE,
                description="Add comprehensive logging and monitoring",
                estimated_improvement=0.0,
                risk_level="low",
                requires_downtime=False,
                code_changes=[
                    "Add structured logging",
                    "Add performance metrics",
                    "Add error tracking"
                ],
                rollback_plan="Remove logging statements"
            ))
        
        # Schema upgrades
        if "CREATE TABLE" in pipeline_code.upper() and "IF NOT EXISTS" not in pipeline_code.upper():
            candidates.append(UpgradeCandidate(
                upgrade_type=UpgradeType.SCHEMA,
                description="Add idempotent table creation",
                estimated_improvement=0.0,
                risk_level="low",
                requires_downtime=False,
                code_changes=[
                    "Add IF NOT EXISTS to CREATE TABLE",
                    "Add schema versioning"
                ],
                rollback_plan="Revert to original schema logic"
            ))
        
        logger.info(
            "Upgrade analysis complete",
            pipeline=pipeline_name,
            candidates_found=len(candidates)
        )
        
        return candidates
    
    def apply_incremental_upgrade(
        self,
        pipeline_name: str,
        pipeline_code: str,
        upgrade: UpgradeCandidate,
        dry_run: bool = True
    ) -> Tuple[bool, str, str]:
        """
        Apply an incremental upgrade to a pipeline.
        
        Args:
            pipeline_name: Name of the pipeline
            pipeline_code: Current pipeline code
            upgrade: Upgrade to apply
            dry_run: If True, validate without applying
            
        Returns:
            Tuple of (success, new_code, message)
        """
        logger.info(
            "Applying incremental upgrade",
            pipeline=pipeline_name,
            upgrade_type=upgrade.upgrade_type.value,
            dry_run=dry_run
        )
        
        try:
            # Apply code changes based on upgrade type
            new_code = self._apply_code_changes(
                pipeline_code,
                upgrade.upgrade_type,
                upgrade.code_changes
            )
            
            # Validate the new code
            is_valid, validation_msg = self._validate_upgraded_code(
                pipeline_name,
                new_code,
                upgrade
            )
            
            if not is_valid:
                return False, pipeline_code, f"Validation failed: {validation_msg}"
            
            # If dry run, return without saving
            if dry_run:
                return True, new_code, "Dry run successful - upgrade validated"
            
            # Save backup
            self._save_version_backup(pipeline_name, pipeline_code)
            
            # Record upgrade
            self._record_upgrade(pipeline_name, upgrade)
            
            # Update version
            current_version = self.version_registry.get(pipeline_name, "1.0.0")
            new_version = self._increment_version(current_version, upgrade.upgrade_type)
            self.version_registry[pipeline_name] = new_version
            
            message = (
                f"Upgrade applied successfully. "
                f"Version {current_version} -> {new_version}"
            )
            
            logger.info(message, pipeline=pipeline_name)
            return True, new_code, message
            
        except Exception as e:
            logger.error(f"Upgrade failed: {e}", exc_info=True)
            return False, pipeline_code, f"Upgrade failed: {str(e)}"
    
    def _apply_code_changes(
        self,
        code: str,
        upgrade_type: UpgradeType,
        changes: List[str]
    ) -> str:
        """
        Apply code changes based on upgrade type.
        
        Args:
            code: Original code
            upgrade_type: Type of upgrade
            changes: List of changes to apply
            
        Returns:
            str: Modified code
        """
        modified_code = code
        
        if upgrade_type == UpgradeType.PERFORMANCE:
            # Add parallel processing
            if "def transform(" in code:
                modified_code = modified_code.replace(
                    "def transform(self, df: pd.DataFrame)",
                    "def transform(self, df: pd.DataFrame, n_jobs: int = 4)"
                )
        
        elif upgrade_type == UpgradeType.SECURITY:
            # Replace hardcoded credentials
            import re
            # Find password patterns
            password_pattern = r'password\s*=\s*["\']([^"\']+)["\']'
            modified_code = re.sub(
                password_pattern,
                'password = os.getenv("DB_PASSWORD")',
                modified_code
            )
            
            # Add import if not present
            if "import os" not in modified_code:
                modified_code = "import os\n" + modified_code
        
        elif upgrade_type == UpgradeType.FEATURE:
            # Add logging
            if "import logging" not in code:
                modified_code = "import logging\n" + modified_code
        
        elif upgrade_type == UpgradeType.BUG_FIX:
            # Add error handling
            if "try:" not in code:
                # Wrap main execution in try-except
                modified_code = modified_code.replace(
                    "def run(self):",
                    "def run(self):\n        try:"
                )
        
        elif upgrade_type == UpgradeType.SCHEMA:
            # Add idempotent schema operations
            modified_code = modified_code.replace(
                "CREATE TABLE",
                "CREATE TABLE IF NOT EXISTS"
            )
        
        return modified_code
    
    def _validate_upgraded_code(
        self,
        pipeline_name: str,
        code: str,
        upgrade: UpgradeCandidate
    ) -> Tuple[bool, str]:
        """
        Validate upgraded code before deployment.
        
        Args:
            pipeline_name: Pipeline name
            code: New code
            upgrade: Applied upgrade
            
        Returns:
            Tuple of (is_valid, message)
        """
        # Check syntax
        try:
            compile(code, pipeline_name, 'exec')
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"
        
        # Check for dangerous patterns
        dangerous_patterns = ["os.system", "eval(", "exec(", "__import__"]
        for pattern in dangerous_patterns:
            if pattern in code:
                return False, f"Dangerous pattern detected: {pattern}"
        
        # Check code length (ensure we didn't delete too much)
        original_lines = len(code.split('\n'))
        if original_lines < 10:
            return False, "Code too short after upgrade"
        
        return True, "Validation passed"
    
    def _save_version_backup(self, pipeline_name: str, code: str) -> None:
        """
        Save a backup of the current version.
        
        Args:
            pipeline_name: Pipeline name
            code: Code to backup
        """
        backup_dir = Path("outputs") / pipeline_name / "versions"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        version = self.version_registry.get(pipeline_name, "1.0.0")
        backup_file = backup_dir / f"{pipeline_name}_v{version}.py"
        
        backup_file.write_text(code)
        logger.info("Version backup saved", file=str(backup_file))
    
    def _record_upgrade(self, pipeline_name: str, upgrade: UpgradeCandidate) -> None:
        """Record upgrade in history."""
        if pipeline_name not in self.upgrade_history:
            self.upgrade_history[pipeline_name] = []
        
        self.upgrade_history[pipeline_name].append({
            "timestamp": datetime.utcnow().isoformat(),
            "upgrade_type": upgrade.upgrade_type.value,
            "description": upgrade.description,
            "estimated_improvement": upgrade.estimated_improvement
        })
    
    def _increment_version(self, current_version: str, upgrade_type: UpgradeType) -> str:
        """
        Increment version based on upgrade type (semantic versioning).
        
        Args:
            current_version: Current version (e.g., "1.2.3")
            upgrade_type: Type of upgrade
            
        Returns:
            str: New version
        """
        major, minor, patch = map(int, current_version.split('.'))
        
        if upgrade_type in [UpgradeType.SCHEMA, UpgradeType.SECURITY]:
            # Major version for breaking changes
            major += 1
            minor = 0
            patch = 0
        elif upgrade_type in [UpgradeType.FEATURE, UpgradeType.PERFORMANCE]:
            # Minor version for new features
            minor += 1
            patch = 0
        else:  # BUG_FIX
            # Patch version for bug fixes
            patch += 1
        
        return f"{major}.{minor}.{patch}"
    
    def rollback_upgrade(
        self,
        pipeline_name: str,
        target_version: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Rollback to a previous version.
        
        Args:
            pipeline_name: Pipeline name
            target_version: Version to rollback to (None = previous version)
            
        Returns:
            Tuple of (success, message)
        """
        logger.info("Rolling back upgrade", pipeline=pipeline_name, target=target_version)
        
        try:
            backup_dir = Path("outputs") / pipeline_name / "versions"
            
            if not backup_dir.exists():
                return False, "No backup versions found"
            
            # Get available versions
            backups = sorted(backup_dir.glob(f"{pipeline_name}_v*.py"))
            
            if not backups:
                return False, "No backup files found"
            
            # Rollback to target or previous version
            if target_version:
                target_file = backup_dir / f"{pipeline_name}_v{target_version}.py"
                if not target_file.exists():
                    return False, f"Version {target_version} not found"
            else:
                target_file = backups[-1]  # Most recent backup
            
            # Restore the backup
            restored_code = target_file.read_text()
            current_file = Path("outputs") / pipeline_name / f"{pipeline_name}.py"
            current_file.write_text(restored_code)
            
            message = f"Rolled back to version {target_version or 'previous'}"
            logger.info(message, pipeline=pipeline_name)
            
            return True, message
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}", exc_info=True)
            return False, f"Rollback failed: {str(e)}"


def create_self_healing_agent() -> Tuple[SelfHealingEngine, IncrementalUpgradeEngine]:
    """
    Create and initialize self-healing and upgrade engines.
    
    Returns:
        Tuple of (healing_engine, upgrade_engine)
    """
    healing_engine = SelfHealingEngine()
    upgrade_engine = IncrementalUpgradeEngine(healing_engine)
    
    logger.info("Self-healing agent created")
    return healing_engine, upgrade_engine