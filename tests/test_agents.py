"""
Unit Tests for Data Pipeline Agent
===================================
Tests core functionality of the agentic AI system.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from src.agents.pipeline_agent import DataPipelineAgent
from src.agents.state import create_initial_state, update_state, add_message
from src.config.settings import PipelineConfig
from src.utils.validators import InputValidator, DataQualityValidator


class TestPipelineState:
    """Test state management functions."""
    
    def test_create_initial_state(self):
        """Test initial state creation."""
        requirements = {
            "name": "test_pipeline",
            "description": "Test pipeline",
            "sources": [],
            "transformations": [],
            "destination": {}
        }
        
        state = create_initial_state(requirements)
        
        assert state["status"] == "pending"
        assert state["current_step"] == "initialize"
        assert len(state["errors"]) == 0
        assert state["requires_human_approval"] == True
    
    def test_update_state(self):
        """Test state updates."""
        requirements = {"name": "test"}
        state = create_initial_state(requirements)
        
        updated_state = update_state(
            state,
            current_step="design_schema",
            schema_design={"tables": {}}
        )
        
        assert updated_state["current_step"] == "design_schema"
        assert "design_schema" in updated_state["steps_completed"]
        assert updated_state["schema_design"] is not None
    
    def test_add_message(self):
        """Test adding messages to state."""
        requirements = {"name": "test"}
        state = create_initial_state(requirements)
        
        state = add_message(state, "user", "Test message")
        
        assert len(state["messages"]) == 1
        assert state["messages"][0]["role"] == "user"
        assert state["messages"][0]["content"] == "Test message"


class TestInputValidator:
    """Test input validation and security."""
    
    def test_validate_pipeline_config_valid(self):
        """Test validation with valid config."""
        config = {
            "name": "test_pipeline",
            "description": "Test description",
            "sources": [{"type": "postgresql", "name": "db1"}],
            "transformations": ["transform1"],
            "destination": {"type": "snowflake"}
        }
        
        result = InputValidator.validate_pipeline_config(config)
        assert isinstance(result, PipelineConfig)
        assert result.name == "test_pipeline"
    
    def test_validate_pipeline_config_invalid_name(self):
        """Test validation with invalid name."""
        config = {
            "name": "test-pipeline!",  # Invalid characters
            "description": "Test",
            "sources": [],
            "transformations": [],
            "destination": {}
        }
        
        with pytest.raises(Exception):
            InputValidator.validate_pipeline_config(config)
    
    def test_sanitize_sql_safe(self):
        """Test SQL sanitization with safe query."""
        safe_query = "SELECT * FROM users WHERE id = %s"
        result = InputValidator.sanitize_sql(safe_query)
        assert result == safe_query
    
    def test_sanitize_sql_dangerous(self):
        """Test SQL sanitization with dangerous query."""
        dangerous_query = "SELECT * FROM users; DROP TABLE users;"
        
        with pytest.raises(Exception):
            InputValidator.sanitize_sql(dangerous_query)
    
    def test_validate_file_path_safe(self):
        """Test file path validation with safe path."""
        safe_path = "outputs/pipeline_123/file.py"
        result = InputValidator.validate_file_path(safe_path)
        assert result == safe_path
    
    def test_validate_file_path_dangerous(self):
        """Test file path validation with dangerous path."""
        dangerous_path = "../../../etc/passwd"
        
        with pytest.raises(Exception):
            InputValidator.validate_file_path(dangerous_path)
    
    def test_check_resource_limits_within(self):
        """Test resource limits within bounds."""
        result = InputValidator.check_resource_limits(
            data_size_mb=50.0,
            estimated_memory_mb=1024.0
        )
        assert result == True
    
    def test_check_resource_limits_exceeded(self):
        """Test resource limits exceeded."""
        with pytest.raises(Exception):
            InputValidator.check_resource_limits(
                data_size_mb=500.0,  # Exceeds default max
                estimated_memory_mb=1024.0
            )


class TestDataQualityValidator:
    """Test data quality validation."""
    
    def test_check_null_percentage_acceptable(self):
        """Test null percentage within threshold."""
        result = DataQualityValidator.check_null_percentage(
            null_count=10,
            total_count=100,
            threshold=0.2
        )
        assert result == True
    
    def test_check_null_percentage_exceeded(self):
        """Test null percentage exceeds threshold."""
        with pytest.raises(Exception):
            DataQualityValidator.check_null_percentage(
                null_count=50,
                total_count=100,
                threshold=0.2
            )
    
    def test_check_data_freshness_fresh(self):
        """Test data freshness within limit."""
        result = DataQualityValidator.check_data_freshness(
            last_updated_hours=12.0,
            max_age_hours=24.0
        )
        assert result == True
    
    def test_check_data_freshness_stale(self):
        """Test stale data detection."""
        with pytest.raises(Exception):
            DataQualityValidator.check_data_freshness(
                last_updated_hours=48.0,
                max_age_hours=24.0
            )
    
    def test_check_record_count_valid(self):
        """Test record count validation."""
        result = DataQualityValidator.check_record_count(
            record_count=100,
            min_records=1,
            max_records=1000
        )
        assert result == True
    
    def test_check_record_count_below_minimum(self):
        """Test record count below minimum."""
        with pytest.raises(Exception):
            DataQualityValidator.check_record_count(
                record_count=0,
                min_records=1
            )


@pytest.fixture
def mock_agent():
    """Create a mock agent for testing."""
    with patch('src.agents.pipeline_agent.ChatAnthropic'):
        agent = DataPipelineAgent()
        return agent


class TestDataPipelineAgent:
    """Test the main agent functionality."""
    
    def test_agent_initialization(self, mock_agent):
        """Test agent initializes correctly."""
        assert mock_agent.schema_tool is not None
        assert mock_agent.code_tool is not None
        assert mock_agent.validation_tool is not None
        assert mock_agent.doc_tool is not None
    
    def test_build_pipeline_success(self, mock_agent):
        """Test successful pipeline build."""
        requirements = {
            "name": "test_pipeline",
            "description": "Test pipeline",
            "sources": [{"type": "postgresql", "name": "db1"}],
            "transformations": ["Calculate daily metrics"],
            "destination": {"type": "snowflake", "schema": "analytics"}
        }
        
        # Mock the graph execution
        with patch.object(mock_agent.graph, 'invoke') as mock_invoke:
            mock_invoke.return_value = {
                "status": "completed",
                "output_directory": "outputs/test_pipeline",
                "generated_files": ["test_pipeline.py"],
                "errors": [],
                "warnings": [],
                "result_summary": {"files_generated": 1}
            }
            
            result = mock_agent.build_pipeline(requirements)
            
            assert result["status"] == "completed"
            assert len(result["generated_files"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])