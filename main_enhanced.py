"""
Main Entry Point - Enhanced with Self-Healing
==============================================
Command-line interface for the Self-Healing Data Pipeline Agent.

New Commands:
    python main.py --config examples/ecommerce_pipeline.yaml --enable-healing
    python main.py --upgrade pipeline_name --type performance
    python main.py --rollback pipeline_name --version 1.0.0
    python main.py --history pipeline_name
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

from src.agents.enhanced_agent import SelfHealingPipelineAgent
from src.config.settings import get_config
from src.utils.logger import setup_logging, get_logger

# Initialize
console = Console()
setup_logging()
logger = get_logger(__name__)
config = get_config()


def load_requirements(config_path: str) -> dict:
    """Load requirements from YAML or JSON file."""
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
    """Display pipeline generation results in a nice format."""
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
    table.add_row("Files Generated", str(len(result.get("generated_files", []))))
    table.add_row("Output Directory", result.get("output_path", "N/A"))
    table.add_row("Errors", str(len(result.get("errors", []))))
    table.add_row("Warnings", str(len(result.get("warnings", []))))
    
    # Add health status if available
    if "health_status" in result:
        table.add_row("Health Status", result["health_status"])
    
    # Add healing attempts if any
    if "healing_attempts" in result:
        table.add_row("Healing Attempts", str(result["healing_attempts"]))
    
    console.print(table)
    
    # Suggested upgrades
    if result.get("suggested_upgrades"):
        console.print("\n[bold cyan]Suggested Upgrades:[/bold cyan]")
        upgrade_table = Table()
        upgrade_table.add_column("Type", style="yellow")
        upgrade_table.add_column("Description", style="white")
        upgrade_table.add_column("Improvement", style="green")
        upgrade_table.add_column("Risk", style="red")
        
        for upgrade in result["suggested_upgrades"]:
            upgrade_table.add_row(
                upgrade["type"],
                upgrade["description"],
                f"{upgrade['improvement']*100:.0f}%",
                upgrade["risk"]
            )
        
        console.print(upgrade_table)
        console.print("\n[dim]Apply upgrades with: python main.py --upgrade <pipeline_name> --type <upgrade_type>[/dim]")
    
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


def upgrade_pipeline(pipeline_name: str, upgrade_type: str, dry_run: bool):
    """Upgrade an existing pipeline."""
    console.print(f"\n[cyan]Upgrading pipeline: {pipeline_name}[/cyan]")
    console.print(f"[cyan]Upgrade type: {upgrade_type}[/cyan]")
    
    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be saved[/yellow]\n")
    
    agent = SelfHealingPipelineAgent(enable_auto_upgrade=True)
    
    with console.status("[bold green]Analyzing and applying upgrade...") as status:
        result = agent.apply_upgrade(pipeline_name, upgrade_type, dry_run=dry_run)
    
    # Display result
    if result["status"] == "completed":
        console.print(f"\n[bold green]✨ Upgrade successful![/bold green]")
        console.print(f"[cyan]Type:[/cyan] {result['upgrade_type']}")
        console.print(f"[cyan]Description:[/cyan] {result['description']}")
        console.print(f"[cyan]Estimated improvement:[/cyan] {result['estimated_improvement']*100:.0f}%")
        
        if not dry_run:
            console.print(f"\n[green]Updated file:[/green] {result['updated_file']}")
    else:
        console.print(f"\n[bold red]❌ Upgrade failed[/bold red]")
        console.print(f"[red]Error:[/red] {result.get('error', 'Unknown error')}")


def rollback_pipeline(pipeline_name: str, target_version: str = None):
    """Rollback a pipeline to previous version."""
    console.print(f"\n[cyan]Rolling back pipeline: {pipeline_name}[/cyan]")
    if target_version:
        console.print(f"[cyan]Target version: {target_version}[/cyan]")
    else:
        console.print("[cyan]Target: Previous version[/cyan]")
    
    agent = SelfHealingPipelineAgent()
    
    with console.status("[bold green]Rolling back...") as status:
        result = agent.rollback_pipeline(pipeline_name, target_version)
    
    if result["status"] == "completed":
        console.print(f"\n[bold green]✨ Rollback successful![/bold green]")
        console.print(f"[green]{result['message']}[/green]")
    else:
        console.print(f"\n[bold red]❌ Rollback failed[/bold red]")
        console.print(f"[red]{result['message']}[/red]")


def show_pipeline_history(pipeline_name: str):
    """Show upgrade and health history for a pipeline."""
    console.print(f"\n[cyan]History for pipeline: {pipeline_name}[/cyan]\n")
    
    agent = SelfHealingPipelineAgent()
    history = agent.get_pipeline_history(pipeline_name)
    
    # Current version
    console.print(f"[bold]Current Version:[/bold] {history['current_version']}\n")
    
    # Upgrade history
    if history["upgrade_history"]:
        console.print("[bold cyan]Upgrade History:[/bold cyan]")
        upgrade_table = Table()
        upgrade_table.add_column("Timestamp", style="yellow")
        upgrade_table.add_column("Type", style="cyan")
        upgrade_table.add_column("Description", style="white")
        upgrade_table.add_column("Improvement", style="green")
        
        for upgrade in history["upgrade_history"]:
            upgrade_table.add_row(
                upgrade["timestamp"][:19],
                upgrade["upgrade_type"],
                upgrade["description"],
                f"{upgrade['estimated_improvement']*100:.0f}%"
            )
        
        console.print(upgrade_table)
    else:
        console.print("[dim]No upgrade history[/dim]")
    
    # Health history
    if history["health_history"]:
        console.print("\n[bold cyan]Health Metrics (Last 5):[/bold cyan]")
        health_table = Table()
        health_table.add_column("Success Rate", style="green")
        health_table.add_column("Avg Time (s)", style="yellow")
        health_table.add_column("Errors", style="red")
        
        for metrics in history["health_history"][-5:]:
            health_table.add_row(
                f"{metrics['success_rate']*100:.1f}%",
                f"{metrics['avg_execution_time']:.2f}",
                str(metrics['error_count'])
            )
        
        console.print(health_table)
    else:
        console.print("\n[dim]No health history[/dim]")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="AI-Powered Self-Healing Data Pipeline Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build a new pipeline with self-healing
  python main.py --config examples/ecommerce_pipeline.yaml --enable-healing
  
  # Build in interactive mode
  python main.py --interactive --enable-healing
  
  # Upgrade an existing pipeline
  python main.py --upgrade ecommerce_analytics --type performance
  
  # Dry run an upgrade
  python main.py --upgrade ecommerce_analytics --type security --dry-run
  
  # Rollback to previous version
  python main.py --rollback ecommerce_analytics
  
  # Rollback to specific version
  python main.py --rollback ecommerce_analytics --version 1.2.0
  
  # View pipeline history
  python main.py --history ecommerce_analytics
        """
    )
    
    # Build pipeline arguments
    parser.add_argument('--config', type=str, help='Path to pipeline configuration file')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    parser.add_argument('--enable-healing', action='store_true', help='Enable self-healing')
    parser.add_argument('--enable-upgrades', action='store_true', help='Enable auto-upgrades')
    
    # Upgrade arguments
    parser.add_argument('--upgrade', type=str, help='Upgrade an existing pipeline')
    parser.add_argument('--type', type=str, help='Upgrade type (performance/security/bug_fix/feature/schema)')
    
    # Rollback arguments
    parser.add_argument('--rollback', type=str, help='Rollback a pipeline')
    parser.add_argument('--version', type=str, help='Target version for rollback')
    
    # History arguments
    parser.add_argument('--history', type=str, help='Show pipeline history')
    
    # Other options
    parser.add_argument('--dry-run', action='store_true', help='Test without executing')
    
    args = parser.parse_args()
    
    try:
        # Handle upgrade command
        if args.upgrade:
            if not args.type:
                console.print("[red]Error: --type required for upgrade[/red]")
                sys.exit(1)
            upgrade_pipeline(args.upgrade, args.type, args.dry_run)
            return
        
        # Handle rollback command
        if args.rollback:
            rollback_pipeline(args.rollback, args.version)
            return
        
        # Handle history command
        if args.history:
            show_pipeline_history(args.history)
            return
        
        # Build pipeline
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
        
        # Initialize agent with self-healing capabilities
        console.print("\n[cyan]Initializing Self-Healing AI Agent...[/cyan]")
        agent = SelfHealingPipelineAgent(
            enable_self_healing=args.enable_healing,
            enable_auto_upgrade=args.enable_upgrades
        )
        
        if args.enable_healing:
            console.print("[green]✓ Self-healing enabled[/green]")
        if args.enable_upgrades:
            console.print("[green]✓ Auto-upgrades enabled[/green]")
        
        # Build pipeline
        console.print("\n[cyan]Building pipeline...[/cyan]")
        with console.status("[bold green]Working...") as status:
            result = agent.build_pipeline(requirements)
        
        # Display results
        display_results(result)
        
        # Success message
        if result["status"] == "completed":
            console.print(f"\n[bold green]✨ Pipeline generated successfully![/bold green]")
            console.print(f"[dim]Output directory: {result['output_path']}[/dim]")
            
            if result.get("healing_attempts", 0) > 0:
                console.print(f"\n[yellow]Note: {result['healing_attempts']} self-healing attempt(s) were made[/yellow]")
        
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted by user[/red]")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()