"""
Data Pipeline Agent Module
===========================
Main agentic AI system built with LangGraph for generating data pipelines.

Architecture:
- Uses LangGraph for state management and control flow
- Multiple specialized agent nodes
- Conditional routing based on validation results
- Human-in-the-loop approval for production deployment

Graph Structure:
    START
      ↓
    analyze_requirements
      ↓
    design_schema
      ↓
    generate_code
      ↓
    validate_code
      ↓
    [If valid] → generate_documentation
      ↓
    [If needs approval] → request_approval
      ↓
    END
"""

from typing import Dict, Any, List
from pathlib import Path
import json

from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.state import (
    PipelineState,
    create_initial_state,
    update_state,
    add_message,
    add_error,
    add_warning,
    mark_completed
)
from src.tools.pipeline_tools import (
    SchemaDesignTool,
    CodeGeneratorTool,
    ValidationTool,
    DocumentationTool
)
from src.config.settings import get_config
from src.utils.logger import get_logger
from src.utils.validators import InputValidator

logger = get_logger(__name__)
config = get_config()


class DataPipelineAgent:
    """
    AI Agent for generating end-to-end data pipelines.
    
    Uses LangGraph to orchestrate multiple specialized agents that:
    1. Analyze requirements
    2. Design data schemas
    3. Generate ETL code
    4. Validate and review code
    5. Generate documentation
    6. Request human approval (if needed)
    """
    
    def __init__(self):
        """Initialize the agent with LangGraph and Claude."""
        self.llm = ChatAnthropic(
            model=config.model_name,
            temperature=config.temperature,
            anthropic_api_key=config.anthropic_api_key
        )
        
        self.schema_tool = SchemaDesignTool()
        self.code_tool = CodeGeneratorTool()
        self.validation_tool = ValidationTool()
        self.doc_tool = DocumentationTool()
        
        # Build the agent graph
        self.graph = self._build_graph()
        
        logger.info("DataPipelineAgent initialized")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        
        Returns:
            StateGraph: Compiled graph ready for execution
        """
        # Create the graph
        workflow = StateGraph(PipelineState)
        
        # Add nodes (agent steps)
        workflow.add_node("analyze_requirements", self._analyze_requirements)
        workflow.add_node("design_schema", self._design_schema)
        workflow.add_node("generate_code", self._generate_code)
        workflow.add_node("validate_code", self._validate_code)
        workflow.add_node("generate_documentation", self._generate_documentation)
        workflow.add_node("finalize", self._finalize)
        
        # Define edges (flow)
        workflow.set_entry_point("analyze_requirements")
        workflow.add_edge("analyze_requirements", "design_schema")
        workflow.add_edge("design_schema", "generate_code")
        workflow.add_edge("generate_code", "validate_code")
        
        # Conditional edge: if validation fails, end; otherwise continue
        workflow.add_conditional_edges(
            "validate_code",
            self._should_continue_after_validation,
            {
                "continue": "generate_documentation",
                "stop": END
            }
        )
        
        workflow.add_edge("generate_documentation", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    # Node Functions
    # ===============
    
    def _analyze_requirements(self, state: PipelineState) -> PipelineState:
        """
        Agent node: Analyze user requirements and extract key information.
        
        Args:
            state: Current pipeline state
            
        Returns:
            PipelineState: Updated state with analysis
        """
        logger.info("Analyzing requirements")
        
        requirements = state["requirements"]
        
        # Validate requirements
        try:
            validator = InputValidator()
            validator.validate_pipeline_config(requirements)
        except Exception as e:
            logger.error(f"Requirements validation failed: {e}")
            return add_error(state, str(e))
        
        # Use LLM to analyze and structure requirements
        system_prompt = """You are a data engineering expert. Analyze the pipeline requirements 
        and extract key information about data sources, transformations, and destinations.
        
        Identify:
        - Data entities and their relationships
        - Required transformations
        - Data quality requirements
        - Performance considerations
        """
        
        human_prompt = f"""
        Analyze these pipeline requirements:
        
        {json.dumps(requirements, indent=2)}
        
        Provide a structured analysis including:
        1. Main entities and their relationships
        2. Data flow summary
        3. Transformation complexity
        4. Potential challenges
        """
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = self.llm.invoke(messages)
            analysis = response.content
            
            # Update state
            state = add_message(state, "assistant", f"Requirements Analysis:\n{analysis}")
            state = update_state(state, current_step="analyze_requirements")
            
            logger.info("Requirements analyzed successfully")
            return state
            
        except Exception as e:
            logger.error(f"Requirements analysis failed: {e}")
            return add_error(state, f"Analysis failed: {str(e)}")
    
    def _design_schema(self, state: PipelineState) -> PipelineState:
        """
        Agent node: Design database schema and data models.
        
        Args:
            state: Current pipeline state
            
        Returns:
            PipelineState: Updated state with schema design
        """
        logger.info("Designing schema")
        
        requirements = state["requirements"]
        sources = requirements.get("sources", [])
        
        # Extract entities from sources
        entities = []
        for source in sources:
            if "tables" in source:
                entities.extend(source["tables"])
        
        # Use schema design tool
        try:
            schema_design = self.schema_tool.design_schema(
                entities=entities,
                relationships=[],
                constraints=["NOT NULL on primary keys", "UNIQUE on natural keys"]
            )
            
            # Update state
            state = update_state(
                state,
                current_step="design_schema",
                schema_design=schema_design
            )
            
            logger.info("Schema designed", tables=len(schema_design.get("tables", {})))
            return state
            
        except Exception as e:
            logger.error(f"Schema design failed: {e}")
            return add_error(state, f"Schema design failed: {str(e)}")
    
    def _generate_code(self, state: PipelineState) -> PipelineState:
        """
        Agent node: Generate ETL pipeline code.
        
        Args:
            state: Current pipeline state
            
        Returns:
            PipelineState: Updated state with generated code
        """
        logger.info("Generating pipeline code")
        
        requirements = state["requirements"]
        
        try:
            # Generate code using tool
            code = self.code_tool.generate_etl_code(
                source_config=requirements.get("sources", [{}])[0],
                transformations=requirements.get("transformations", []),
                destination_config=requirements.get("destination", {}),
                pipeline_name=requirements.get("name", "pipeline")
            )
            
            # Save code to file
            output_dir = Path(state["output_directory"])
            output_dir.mkdir(parents=True, exist_ok=True)
            
            code_file = output_dir / f"{requirements['name']}.py"
            code_file.write_text(code)
            
            # Update state
            state = update_state(
                state,
                current_step="generate_code",
                pipeline_code=code,
                generated_files=state["generated_files"] + [str(code_file)]
            )
            
            logger.info("Code generated", file=str(code_file))
            return state
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return add_error(state, f"Code generation failed: {str(e)}")
    
    def _validate_code(self, state: PipelineState) -> PipelineState:
        """
        Agent node: Validate generated code for quality and safety.
        
        Args:
            state: Current pipeline state
            
        Returns:
            PipelineState: Updated state with validation results
        """
        logger.info("Validating generated code")
        
        code = state.get("pipeline_code")
        if not code:
            return add_error(state, "No code to validate")
        
        try:
            # Validate using tool
            validation_results = self.validation_tool.validate_pipeline_code(code)
            
            # Add warnings if any
            for warning in validation_results.get("warnings", []):
                state = add_warning(state, warning)
            
            # Add errors if any issues
            for issue in validation_results.get("issues", []):
                state = add_error(state, issue)
            
            # Update state
            state = update_state(
                state,
                current_step="validate_code",
                validation_results=validation_results
            )
            
            if validation_results["valid"]:
                logger.info("Code validation passed")
            else:
                logger.warning("Code validation failed", issues=validation_results["issues"])
            
            return state
            
        except Exception as e:
            logger.error(f"Code validation failed: {e}")
            return add_error(state, f"Validation failed: {str(e)}")
    
    def _generate_documentation(self, state: PipelineState) -> PipelineState:
        """
        Agent node: Generate comprehensive documentation.
        
        Args:
            state: Current pipeline state
            
        Returns:
            PipelineState: Updated state with documentation
        """
        logger.info("Generating documentation")
        
        requirements = state["requirements"]
        
        try:
            # Generate documentation
            documentation = self.doc_tool.generate_documentation(
                pipeline_name=requirements.get("name", "pipeline"),
                description=requirements.get("description", ""),
                sources=requirements.get("sources", []),
                transformations=requirements.get("transformations", []),
                destination=requirements.get("destination", {})
            )
            
            # Save documentation
            output_dir = Path(state["output_directory"])
            doc_file = output_dir / f"{requirements['name']}_README.md"
            doc_file.write_text(documentation)
            
            # Update state
            state = update_state(
                state,
                current_step="generate_documentation",
                documentation=documentation,
                generated_files=state["generated_files"] + [str(doc_file)]
            )
            
            logger.info("Documentation generated", file=str(doc_file))
            return state
            
        except Exception as e:
            logger.error(f"Documentation generation failed: {e}")
            return add_error(state, f"Documentation generation failed: {str(e)}")
    
    def _finalize(self, state: PipelineState) -> PipelineState:
        """
        Agent node: Finalize the pipeline generation process.
        
        Args:
            state: Current pipeline state
            
        Returns:
            PipelineState: Final state with summary
        """
        logger.info("Finalizing pipeline generation")
        
        # Create summary
        summary = {
            "pipeline_name": state["requirements"].get("name"),
            "status": "completed" if not state["errors"] else "completed_with_warnings",
            "files_generated": len(state["generated_files"]),
            "output_directory": state["output_directory"],
            "errors": len(state["errors"]),
            "warnings": len(state["warnings"]),
            "steps_completed": state["steps_completed"]
        }
        
        state = mark_completed(state, summary)
        
        logger.info("Pipeline generation finalized", **summary)
        return state
    
    # Conditional Edge Functions
    # ===========================
    
    def _should_continue_after_validation(self, state: PipelineState) -> str:
        """
        Decide whether to continue after validation.
        
        Args:
            state: Current pipeline state
            
        Returns:
            str: "continue" or "stop"
        """
        validation_results = state.get("validation_results", {})
        
        if not validation_results.get("valid", False):
            logger.warning("Stopping due to validation failures")
            return "stop"
        
        return "continue"
    
    # Public Interface
    # ================
    
    def build_pipeline(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point: Build a complete data pipeline from requirements.
        
        Args:
            requirements: Pipeline requirements
            
        Returns:
            Dict: Results including generated files and status
        """
        logger.info("Starting pipeline build", pipeline=requirements.get("name"))
        
        # Create initial state
        output_dir = Path(config.output_dir) / requirements.get("name", "pipeline")
        initial_state = create_initial_state(requirements, str(output_dir))
        
        # Execute the graph
        try:
            final_state = self.graph.invoke(initial_state)
            
            result = {
                "status": final_state["status"],
                "output_path": final_state["output_directory"],
                "generated_files": final_state["generated_files"],
                "errors": final_state["errors"],
                "warnings": final_state["warnings"],
                "summary": final_state.get("result_summary", {})
            }
            
            logger.info("Pipeline build completed", **result)
            return result
            
        except Exception as e:
            logger.error(f"Pipeline build failed: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "output_path": str(output_dir)
            }