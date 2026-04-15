"""
Validation Utility Module
=========================
Provides input validation and guardrail enforcement.

Features:
- Input sanitization
- Resource limit checks
- Security validation
- Data quality checks
"""

import re
import json
from typing import Any, Dict, List, Optional
from pydantic import ValidationError
from src.config.settings import get_config, PipelineConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()


class ValidationError(Exception):
    """Custom validation error."""
    pass


class InputValidator:
    """
    Validates user inputs and enforces safety guardrails.
    
    Prevents:
    - SQL injection
    - Code injection
    - Resource exhaustion
    - Malicious configurations
    """
    
    @staticmethod
    def validate_pipeline_config(config_dict: Dict[str, Any]) -> PipelineConfig:
        """
        Validate pipeline configuration against schema.
        
        Args:
            config_dict: Pipeline configuration dictionary
            
        Returns:
            PipelineConfig: Validated configuration
            
        Raises:
            ValidationError: If configuration is invalid
        """
        try:
            pipeline_config = PipelineConfig(**config_dict)
            logger.info("Pipeline configuration validated", pipeline=pipeline_config.name)
            return pipeline_config
        except ValidationError as e:
            logger.error("Invalid pipeline configuration", errors=str(e))
            raise ValidationError(f"Configuration validation failed: {e}")
    
    @staticmethod
    def sanitize_sql(query: str) -> str:
        """
        Sanitize SQL query to prevent injection attacks.
        
        Args:
            query: SQL query string
            
        Returns:
            str: Sanitized query
            
        Raises:
            ValidationError: If query contains dangerous patterns
        """
        # Check for dangerous SQL patterns
        dangerous_patterns = [
            r';\s*drop\s+table',
            r';\s*delete\s+from',
            r';\s*truncate',
            r'xp_cmdshell',
            r'exec\s*\(',
            r'execute\s*\(',
        ]
        
        query_lower = query.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, query_lower):
                raise ValidationError(f"Dangerous SQL pattern detected: {pattern}")
        
        return query
    
    @staticmethod
    def validate_file_path(path: str) -> str:
        """
        Validate and sanitize file paths.
        
        Args:
            path: File path string
            
        Returns:
            str: Sanitized path
            
        Raises:
            ValidationError: If path is dangerous
        """
        # Prevent directory traversal
        if '..' in path or path.startswith('/'):
            raise ValidationError("Directory traversal detected in path")
        
        # Only allow safe characters
        if not re.match(r'^[a-zA-Z0-9_\-./]+$', path):
            raise ValidationError("Invalid characters in file path")
        
        return path
    
    @staticmethod
    def check_resource_limits(data_size_mb: float, estimated_memory_mb: float) -> bool:
        """
        Check if operation is within resource limits.
        
        Args:
            data_size_mb: Size of data in MB
            estimated_memory_mb: Estimated memory usage in MB
            
        Returns:
            bool: True if within limits
            
        Raises:
            ValidationError: If limits exceeded
        """
        guardrails = config.guardrails
        
        if data_size_mb > guardrails.max_file_size_mb:
            raise ValidationError(
                f"Data size ({data_size_mb}MB) exceeds limit "
                f"({guardrails.max_file_size_mb}MB)"
            )
        
        if estimated_memory_mb > guardrails.max_memory_mb:
            raise ValidationError(
                f"Estimated memory ({estimated_memory_mb}MB) exceeds limit "
                f"({guardrails.max_memory_mb}MB)"
            )
        
        return True
    
    @staticmethod
    def validate_connection_string(conn_str: str, db_type: str) -> bool:
        """
        Validate database connection string format.
        
        Args:
            conn_str: Connection string
            db_type: Database type
            
        Returns:
            bool: True if valid
            
        Raises:
            ValidationError: If format is invalid
        """
        patterns = {
            'postgresql': r'^postgresql://[^:]+:[^@]+@[^:]+:\d+/\w+$',
            'mysql': r'^mysql://[^:]+:[^@]+@[^:]+:\d+/\w+$',
            'mongodb': r'^mongodb(\+srv)?://[^:]+:[^@]+@[^/]+/\w+$',
        }
        
        pattern = patterns.get(db_type)
        if not pattern:
            raise ValidationError(f"Unsupported database type: {db_type}")
        
        if not re.match(pattern, conn_str):
            raise ValidationError(f"Invalid {db_type} connection string format")
        
        return True
    
    @staticmethod
    def validate_cron_expression(cron: str) -> bool:
        """
        Validate cron expression format.
        
        Args:
            cron: Cron expression string
            
        Returns:
            bool: True if valid
            
        Raises:
            ValidationError: If format is invalid
        """
        # Basic cron validation (5 or 6 fields)
        parts = cron.split()
        if len(parts) not in [5, 6]:
            raise ValidationError("Cron expression must have 5 or 6 fields")
        
        return True
    
    @staticmethod
    def validate_json_schema(data: Any, schema: Dict[str, Any]) -> bool:
        """
        Validate data against JSON schema.
        
        Args:
            data: Data to validate
            schema: JSON schema
            
        Returns:
            bool: True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        from jsonschema import validate as json_validate
        from jsonschema.exceptions import ValidationError as JsonValidationError
        
        try:
            json_validate(instance=data, schema=schema)
            return True
        except JsonValidationError as e:
            raise ValidationError(f"JSON schema validation failed: {e.message}")


class DataQualityValidator:
    """
    Validates data quality metrics.
    
    Checks:
    - Null percentages
    - Data types
    - Value ranges
    - Uniqueness constraints
    """
    
    @staticmethod
    def check_null_percentage(
        null_count: int,
        total_count: int,
        threshold: float = 0.2
    ) -> bool:
        """
        Check if null percentage is acceptable.
        
        Args:
            null_count: Number of null values
            total_count: Total number of values
            threshold: Maximum acceptable null percentage (default 20%)
            
        Returns:
            bool: True if acceptable
            
        Raises:
            ValidationError: If threshold exceeded
        """
        if total_count == 0:
            return True
        
        null_pct = null_count / total_count
        if null_pct > threshold:
            raise ValidationError(
                f"Null percentage ({null_pct:.1%}) exceeds threshold ({threshold:.1%})"
            )
        
        return True
    
    @staticmethod
    def check_data_freshness(
        last_updated_hours: float,
        max_age_hours: float = 24.0
    ) -> bool:
        """
        Check if data is fresh enough.
        
        Args:
            last_updated_hours: Hours since last update
            max_age_hours: Maximum acceptable age
            
        Returns:
            bool: True if fresh enough
            
        Raises:
            ValidationError: If data is stale
        """
        if last_updated_hours > max_age_hours:
            raise ValidationError(
                f"Data is stale ({last_updated_hours:.1f}h old, "
                f"max {max_age_hours:.1f}h)"
            )
        
        return True
    
    @staticmethod
    def check_record_count(
        record_count: int,
        min_records: int = 1,
        max_records: Optional[int] = None
    ) -> bool:
        """
        Validate record count is within acceptable range.
        
        Args:
            record_count: Number of records
            min_records: Minimum acceptable records
            max_records: Maximum acceptable records (optional)
            
        Returns:
            bool: True if acceptable
            
        Raises:
            ValidationError: If count is out of range
        """
        if record_count < min_records:
            raise ValidationError(
                f"Record count ({record_count}) below minimum ({min_records})"
            )
        
        if max_records and record_count > max_records:
            raise ValidationError(
                f"Record count ({record_count}) exceeds maximum ({max_records})"
            )
        
        return True