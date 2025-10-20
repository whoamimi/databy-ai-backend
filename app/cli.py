"""
app.cli

CLI for DataBy API local development.
"""

from __future__ import annotations

import sys
import argparse
import subprocess

from .utils.logger import console

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

def main():
    from .utils.utils import build_parser

    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Map command names to Command methods
    command_map = {
        'serve': Commands.serve,
        'test': Commands.run_tests,
    }

    if args.command in command_map:
        command_map[args.command](args)
    else:
        console.print(f"[red]Unknown command: {args.command}[/red]")
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()