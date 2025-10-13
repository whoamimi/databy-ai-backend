"""Console script for DataBy API using argparse and uvicorn."""

import uvicorn
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from .utils.settings import settings

console = Console()

def run_checks(args):
    """ TODO: Runs build tests / checks and validate if workspace is ready to prod. """
    pass

def check_servers(args):
    """ TODO: Check if the servers are active, warns user (me). """
    pass

def serve(args):
    """Start the DataBy API server with uvicorn-style logging."""

    # Create a beautiful startup panel
    startup_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
    startup_table.add_column(style="cyan bold", justify="right")
    startup_table.add_column(style="white")

    startup_table.add_row("Host", f"[green]{args.host}[/green]")
    startup_table.add_row("Port", f"[green]{args.port}[/green]")
    startup_table.add_row("Reload", f"[{'green' if args.reload else 'dim'}]{args.reload}[/]")
    startup_table.add_row("Workers", f"[green]{args.workers if args.workers else 'auto'}[/]")

    panel = Panel(
        startup_table,
        title="[bold cyan]🚀 Starting DataBy API Server[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(panel)

    if args.reload and args.workers:
        console.print(
            "[bold yellow]⚠️  Warning:[/bold yellow] --workers ignored when --reload is enabled",
            style="yellow"
        )
        console.print()

    try:
        from uvicorn.config import LOGGING_CONFIG
        log_config = LOGGING_CONFIG.copy()
    except ImportError:
        log_config = uvicorn.Config("app.main:app").log_config

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_config=log_config,
        log_level=settings.debug,
        use_colors=True,
    )


def main():
    parser = argparse.ArgumentParser(
        prog="databy",
        description="🔧 DataBy CLI — DataBy AI Backend Server.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start the DataBy API server")
    serve_parser.add_argument(
        "--host", "-H",
        default=settings.app_host,
        help="Host to bind to (default from settings)",
    )
    serve_parser.add_argument(
        "--port", "-p", type=int, default=8000, help="Port to bind to (default: 8000)"
    )
    serve_parser.add_argument(
        "--reload", "-r", action="store_true", help="Enable auto-reload for development"
    )
    serve_parser.add_argument(
        "--workers", "-w", type=int, help="Number of worker processes"
    )
    serve_parser.set_defaults(func=serve)

    args = parser.parse_args()

    if not args.command:
        # Create welcome panel
        welcome_text = f"""
        [dim]Running directory:\t{settings.root_dir}
        Static Path:\t\t{settings.static_path}[/dim]

        [bold white]AgentHub Servers[/bold white]
        [magenta]{settings.agent.server}[/magenta]
        """

        panel = Panel(
            welcome_text,
            title="[bold magenta]🔧 DataBy Backend CLI[/bold magenta]",
            border_style="magenta",
            padding=(1, 2)
        )
        console.print(panel)
        console.print()

        # Create commands table
        commands_table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
        commands_table.add_column("Command", style="green", width=20)
        commands_table.add_column("Description", style="white")

        commands_table.add_row(
            "databy serve",
            "Start the API server"
        )
        commands_table.add_row(
            "databy --help",
            "Show all available commands"
        )

        console.print(commands_table)
        console.print()
    else:
        args.func(args)


if __name__ == "__main__":
    main()