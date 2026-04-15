"""
Configuration Module
====================
Manages all application configurations, environment variables, and guardrails.

This module provides:
- Environment-based configuration
- Resource limits and safety thresholds
- API keys and credentials management
- Logging configuration
"""

import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GuardrailsConfig(BaseModel):
    """
    Safety guardrails and resource limits.
    
    These settings prevent the agent from consuming excessive resources
    or performing dangerous operations.
    """
    
    # Token limits
    max_input_tokens: int = Field(default=100000, description="Max tokens per input")
    max_output_tokens: int = Field(default=50000, description="Max tokens per output")
    
    # Execution limits
    max_execution_time_seconds: int = Field(default=300, description="Max execution time")
    max_retries: int = Field(default=3, description="Max retry attempts")
    
    # Resource limits
    max_memory_mb: int = Field(default=2048, description="Max memory usage in MB")
    max_file_size_mb: int = Field(default=100, description="Max file size in MB")
    max_concurrent_operations: int = Field(default=5, description="Max parallel ops")
    
    # Safety settings
    enable_dry_run: bool = Field(default=True, description="Test mode without execution")
    require_approval: bool = Field(default=True, description="Require human approval")
    enable_code_review: bool = Field(default=True, description="AI code review")
    
    # Rate limiting
    api_calls_per_minute: int = Field(default=60, description="API rate limit")
    db_queries_per_minute: int = Field(default=100, description="DB query limit")


class DatabaseConfig(BaseModel):
    """Database connection configuration."""
    
    type: str = Field(description="Database type (postgresql, mysql, etc)")
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(description="Database name")
    username: Optional[str] = None
    password: Optional[str] = None
    ssl_enabled: bool = Field(default=True)
    pool_size: int = Field(default=5)
    
    @validator('type')
    def validate_db_type(cls, v):
        """Validate supported database types."""
        allowed = ['postgresql', 'mysql', 'mongodb', 'redis', 'snowflake', 'bigquery']
        if v.lower() not in allowed:
            raise ValueError(f"Database type must be one of: {allowed}")
        return v.lower()


class AppConfig(BaseModel):
    """
    Main application configuration.
    
    Centralizes all settings for the data pipeline agent.
    """
    
    # API Keys
    anthropic_api_key: str = Field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""),
        description="Anthropic API key for Claude"
    )
    
    # Model settings
    model_name: str = Field(default="claude-sonnet-4-20250514")
    temperature: float = Field(default=0.1, ge=0.0, le=1.0)
    
    # Application settings
    app_name: str = Field(default="DataPipelineAgent")
    version: str = Field(default="1.0.0")
    environment: str = Field(default="development")
    
    # Paths
    output_dir: str = Field(default="outputs")
    log_dir: str = Field(default="logs")
    cache_dir: str = Field(default=".cache")
    
    # Guardrails
    guardrails: GuardrailsConfig = Field(default_factory=GuardrailsConfig)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    
    @validator('anthropic_api_key')
    def validate_api_key(cls, v):
        """Ensure API key is provided."""
        if not v:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        return v
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment setting."""
        allowed = ['development', 'staging', 'production']
        if v.lower() not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v.lower()


class PipelineConfig(BaseModel):
    """
    Configuration for a specific data pipeline.
    
    Defines sources, transformations, destinations, and execution parameters.
    """
    
    name: str = Field(description="Pipeline name (alphanumeric + underscores)")
    description: str = Field(description="Human-readable description")
    version: str = Field(default="1.0.0")
    
    # Sources
    sources: list[Dict[str, Any]] = Field(description="Data sources")
    
    # Transformations
    transformations: list[str] = Field(description="Transform operations")
    
    # Destination
    destination: Dict[str, Any] = Field(description="Output destination")
    
    # Execution
    mode: str = Field(default="batch", description="batch or streaming")
    schedule: Optional[str] = Field(None, description="Cron expression")
    
    # Data quality
    enable_validation: bool = Field(default=True)
    enable_profiling: bool = Field(default=True)
    
    @validator('name')
    def validate_name(cls, v):
        """Ensure pipeline name is valid."""
        if not v.replace('_', '').isalnum():
            raise ValueError("Name must contain only alphanumeric characters and underscores")
        return v
    
    @validator('mode')
    def validate_mode(cls, v):
        """Validate execution mode."""
        if v.lower() not in ['batch', 'streaming']:
            raise ValueError("Mode must be 'batch' or 'streaming'")
        return v.lower()


# Global configuration instance
config = AppConfig()


def get_config() -> AppConfig:
    """
    Get the global configuration instance.
    
    Returns:
        AppConfig: Application configuration
    """
    return config


def update_config(updates: Dict[str, Any]) -> None:
    """
    Update configuration at runtime.
    
    Args:
        updates: Dictionary of configuration updates
    """
    global config
    for key, value in updates.items():
        if hasattr(config, key):
            setattr(config, key, value)


def get_database_config(db_type: str) -> DatabaseConfig:
    """
    Get database configuration from environment.
    
    Args:
        db_type: Type of database
        
    Returns:
        DatabaseConfig: Database connection settings
    """
    prefix = f"{db_type.upper()}_"
    return DatabaseConfig(
        type=db_type,
        host=os.getenv(f"{prefix}HOST", "localhost"),
        port=int(os.getenv(f"{prefix}PORT", "5432")),
        database=os.getenv(f"{prefix}DATABASE", ""),
        username=os.getenv(f"{prefix}USERNAME"),
        password=os.getenv(f"{prefix}PASSWORD"),
        ssl_enabled=os.getenv(f"{prefix}SSL", "true").lower() == "true"
    )