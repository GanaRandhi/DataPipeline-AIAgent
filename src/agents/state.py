"""
Pipeline Agent State Module
============================
Defines the state structure for the LangGraph agent.

The state holds all information as it flows through the agent graph:
- User requirements
- Generated artifacts (schema, code, docs)
- Validation results
- Current processing step
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
from datetime import datetime
import operator


class PipelineState(TypedDict):
    """
    State object that flows through the agent graph.
    
    Each node in the graph reads from and writes to this state.
    The 'messages' field uses the operator.add reducer to append messages.
    """
    
    # User input and requirements
    requirements: Dict[str, Any]
    
    # Agent conversation and reasoning
    messages: Annotated[List[Dict[str, str]], operator.add]
    
    # Generated artifacts
    schema_design: Optional[Dict[str, Any]]
    pipeline_code: Optional[str]
    documentation: Optional[str]
    test_cases: Optional[List[Dict[str, Any]]]
    
    # Validation and quality checks
    validation_results: Optional[Dict[str, Any]]
    code_review_results: Optional[Dict[str, Any]]
    
    # Execution metadata
    current_step: str
    steps_completed: List[str]
    errors: List[str]
    warnings: List[str]
    
    # Output paths
    output_directory: str
    generated_files: List[str]
    
    # Execution control
    requires_human_approval: bool
    approved: bool
    dry_run: bool
    
    # Timestamps
    started_at: str
    completed_at: Optional[str]
    
    # Final result
    status: str  # "pending", "in_progress", "completed", "failed"
    result_summary: Optional[Dict[str, Any]]


def create_initial_state(requirements: Dict[str, Any], output_dir: str = "outputs") -> PipelineState:
    """
    Create initial state for a new pipeline generation.
    
    Args:
        requirements: User requirements for the pipeline
        output_dir: Directory for output files
        
    Returns:
        PipelineState: Initialized state
    """
    return PipelineState(
        requirements=requirements,
        messages=[],
        schema_design=None,
        pipeline_code=None,
        documentation=None,
        test_cases=None,
        validation_results=None,
        code_review_results=None,
        current_step="initialize",
        steps_completed=[],
        errors=[],
        warnings=[],
        output_directory=output_dir,
        generated_files=[],
        requires_human_approval=True,
        approved=False,
        dry_run=True,
        started_at=datetime.utcnow().isoformat(),
        completed_at=None,
        status="pending",
        result_summary=None
    )


def update_state(
    state: PipelineState,
    current_step: Optional[str] = None,
    **updates
) -> PipelineState:
    """
    Update state with new values.
    
    Args:
        state: Current state
        current_step: New current step (optional)
        **updates: Key-value pairs to update
        
    Returns:
        PipelineState: Updated state
    """
    new_state = state.copy()
    
    if current_step:
        new_state["current_step"] = current_step
        new_state["steps_completed"].append(current_step)
    
    for key, value in updates.items():
        if key in new_state:
            new_state[key] = value
    
    return new_state


def add_message(state: PipelineState, role: str, content: str) -> PipelineState:
    """
    Add a message to the state's message history.
    
    Args:
        state: Current state
        role: Message role ("user", "assistant", "system")
        content: Message content
        
    Returns:
        PipelineState: Updated state
    """
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    new_state = state.copy()
    new_state["messages"] = state["messages"] + [message]
    return new_state


def add_error(state: PipelineState, error: str) -> PipelineState:
    """
    Add an error to the state.
    
    Args:
        state: Current state
        error: Error message
        
    Returns:
        PipelineState: Updated state
    """
    new_state = state.copy()
    new_state["errors"] = state["errors"] + [error]
    new_state["status"] = "failed"
    return new_state


def add_warning(state: PipelineState, warning: str) -> PipelineState:
    """
    Add a warning to the state.
    
    Args:
        state: Current state
        warning: Warning message
        
    Returns:
        PipelineState: Updated state
    """
    new_state = state.copy()
    new_state["warnings"] = state["warnings"] + [warning]
    return new_state


def mark_completed(state: PipelineState, summary: Dict[str, Any]) -> PipelineState:
    """
    Mark the pipeline generation as completed.
    
    Args:
        state: Current state
        summary: Result summary
        
    Returns:
        PipelineState: Updated state
    """
    new_state = state.copy()
    new_state["status"] = "completed"
    new_state["completed_at"] = datetime.utcnow().isoformat()
    new_state["result_summary"] = summary
    return new_state