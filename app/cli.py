"""
app.cli

CLI for DataBy API local development.
"""

from __future__ import annotations

import argparse
import subprocess
import sys

from .utils.logger import build_cli_panel, console
from .utils.settings import settings

class Commands:
    @staticmethod
    def run_tests(args):
        """Run pytest with coverage report."""
        console.rule("[bold cyan]🧪 Running Test Suite with Coverage[/bold cyan]")

        cmd = ["pytest", "--cov=app", "--cov-report=term-missing", "-v"]

        if args.keyword:
            cmd.extend(["-k", args.keyword])

        try:
            result = subprocess.run(cmd)
            if result.returncode == 0:
                console.print("\n[bold green] Complete Coverage Report returned. [/bold green]")
            else:
                sys.exit(result.returncode)
        except FileNotFoundError:
            sys.exit(1)

    @staticmethod
    def serve(args):
        """Start the DataBy API server."""
        try:
            import uvicorn
        except ImportError:
            console.print("[bold red]uvicorn not found![/bold red] Install with `pip install uvicorn`")
            sys.exit(1)

        if args.reload and args.workers:
            console.print("[yellow]⚠️  Warning: --workers ignored when --reload is enabled[/yellow]")

        console.print(f"[green]🚀 Starting server at[/green] http://{args.host}:{args.port}")

        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers if not args.reload else None,
            log_level="info"
        )

def mock_run():
    # TODO: REplace with main() after deleting original.
    from .utils.utils import build_parser

    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        show_welcome()
    else:
        getattr(Commands, args.func)(args)

def main():
    """Main CLI entry point."""

    parser = argparse.ArgumentParser(
        prog="databy",
        description="🔧 DataBy CLI — DataBy AI Backend Server"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start the DataBy API server")
    serve_parser.add_argument("--host", "-H", default=getattr(settings, 'app_host', '127.0.0.1'),
                             help="Host to bind to")
    serve_parser.add_argument("--port", "-p", type=int, default=8000,
                             help="Port to bind to")
    serve_parser.add_argument("--reload", "-r", action="store_true",
                             help="Enable auto-reload for development")
    serve_parser.add_argument("--workers", "-w", type=int,
                             help="Number of worker processes")
    serve_parser.set_defaults(func=Commands.serve)

    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests with coverage")
    test_parser.add_argument("-k", "--keyword",
                            help="Run only tests matching keyword")
    test_parser.set_defaults(func=Commands.run_tests)

    args = parser.parse_args()

    if not args.command:
        show_welcome()
    else:
        args.func(args)

def show_welcome():
    """Display welcome screen with available commands."""

    server = settings.agent.server

    info_lines = [
        f"[dim]Running directory: {settings.static_path}[/dim]",
        "",
        "[bold white]Agent Active Servers[/bold white]",
        f"[magenta]OLLAMA: \t\t {server.ollama}\nSANDBOX: \t\t {server.agent_sandbox}[/magenta]",
    ]

    commands = [
        ("databy serve", "Start the API server"),
        ("databy test", "Run pytest with coverage"),
        ("databy --help", "Show help message"),
    ]

    panel = build_cli_panel(
        title="🔧 DataBy Backend CLI",
        info_lines=info_lines,
        commands=commands,
    )
    console.print(panel)

if __name__ == "__main__":
    main()