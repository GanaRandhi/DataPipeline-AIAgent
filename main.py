"""
Main Entry Point
================
Command-line interface for the Data Pipeline Agent.

Usage:
    python main.py --config examples/ecommerce_pipeline.yaml
    python main.py --interactive
"""

import sys
import argparse
import json
import yaml
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from src.agents.pipeline_agent import DataPipelineAgent
from src.config.settings import get_config
from src.utils.logger import setup_logging, get_logger

# Initialize
console = Console()
setup_logging()
logger = get_logger(__name__)
config = get_config()


def load_requirements(config_path: str) -> dict:
    """
    Load requirements from YAML or JSON file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        dict: Pipeline requirements
    """
    path = Path(config_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(path, 'r') as f:
        if path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        elif path.suffix == '.json':
            return json.load(f)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")


def interactive_mode():
    """Run in interactive mode to gather requirements."""
    console.print("\n[bold cyan]Data Pipeline Agent - Interactive Mode[/bold cyan]\n")
    
    # Gather basic information
    name = console.input("[yellow]Pipeline name (alphanumeric + underscores): [/yellow]")
    description = console.input("[yellow]Pipeline description: [/yellow]")
    
    # Source configuration
    console.print("\n[bold]Source Configuration[/bold]")
    source_type = console.input("[yellow]Source type (postgresql/mysql/s3/api): [/yellow]")
    source_name = console.input("[yellow]Source name: [/yellow]")
    
    sources = [{
        "type": source_type,
        "name": source_name
    }]
    
    if source_type in ['postgresql', 'mysql']:
        tables = console.input("[yellow]Tables (comma-separated): [/yellow]")
        sources[0]["tables"] = [t.strip() for t in tables.split(',')]
    
    # Transformations
    console.print("\n[bold]Transformations[/bold]")
    console.print("[dim]Enter transformations (one per line, empty line to finish):[/dim]")
    
    transformations = []
    while True:
        transform = console.input("[yellow]> [/yellow]")
        if not transform:
            break
        transformations.append(transform)
    
    # Destination
    console.print("\n[bold]Destination Configuration[/bold]")
    dest_type = console.input("[yellow]Destination type (postgresql/snowflake/s3): [/yellow]")
    dest_schema = console.input("[yellow]Schema/database name: [/yellow]")
    
    destination = {
        "type": dest_type,
        "schema": dest_schema
    }
    
    # Build requirements
    requirements = {
        "name": name,
        "description": description,
        "sources": sources,
        "transformations": transformations,
        "destination": destination,
        "mode": "batch",
        "schedule": "daily at 2am UTC"
    }
    
    return requirements


def display_results(result: dict):
    """
    Display pipeline generation results in a nice format.
    
    Args:
        result: Result dictionary from agent
    """
    console.print()
    
    # Status panel
    status_color = "green" if result["status"] == "completed" else "red"
    console.print(
        Panel(
            f"[bold {status_color}]{result['status'].upper()}[/bold {status_color}]",
            title="Pipeline Generation Status"
        )
    )
    
    # Summary table
    table = Table(title="Generation Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    
    summary = result.get("summary", {})
    table.add_row("Pipeline Name", summary.get("pipeline_name", "N/A"))
    table.add_row("Files Generated", str(result.get("generated_files", 0)))
    table.add_row("Output Directory", result.get("output_path", "N/A"))
    table.add_row("Errors", str(len(result.get("errors", []))))
    table.add_row("Warnings", str(len(result.get("warnings", []))))
    
    console.print(table)
    
    # Generated files
    if result.get("generated_files"):
        console.print("\n[bold cyan]Generated Files:[/bold cyan]")
        for file in result["generated_files"]:
            console.print(f"  📄 {file}")
    
    # Errors
    if result.get("errors"):
        console.print("\n[bold red]Errors:[/bold red]")
        for error in result["errors"]:
            console.print(f"  ❌ {error}")
    
    # Warnings
    if result.get("warnings"):
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for warning in result["warnings"]:
            console.print(f"  ⚠️  {warning}")
    
    console.print()


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="AI-Powered Data Pipeline Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --config examples/ecommerce_pipeline.yaml
  python main.py --interactive
  python main.py --config my_pipeline.json --dry-run
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to pipeline configuration file (YAML or JSON)'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Generate pipeline without executing'
    )
    
    args = parser.parse_args()
    
    try:
        # Load requirements
        if args.interactive:
            requirements = interactive_mode()
        elif args.config:
            requirements = load_requirements(args.config)
        else:
            parser.print_help()
            sys.exit(1)
        
        # Show requirements
        console.print("\n[bold]Pipeline Requirements:[/bold]")
        console.print(Panel(json.dumps(requirements, indent=2)))
        
        # Confirm
        if not console.input("\n[yellow]Proceed with generation? (y/n): [/yellow]").lower().startswith('y'):
            console.print("[red]Cancelled[/red]")
            sys.exit(0)
        
        # Initialize agent
        console.print("\n[cyan]Initializing AI Agent...[/cyan]")
        agent = DataPipelineAgent()
        
        # Build pipeline
        console.print("[cyan]Building pipeline...[/cyan]")
        with console.status("[bold green]Working...") as status:
            result = agent.build_pipeline(requirements)
        
        # Display results
        display_results(result)
        
        # Success message
        if result["status"] == "completed":
            console.print(
                f"\n[bold green]✨ Pipeline generated successfully![/bold green]"
            )
            console.print(f"[dim]Output directory: {result['output_path']}[/dim]")
        
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted by user[/red]")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()