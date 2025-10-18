"""Rich logging utilities for the DataBy backend."""

from __future__ import annotations

import logging
from typing import Iterable, Sequence

from rich import box
from rich.console import Console, Group
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def setup_logging(debug: bool = False) -> None:
    """Configure logging using Rich's handler."""

    log_level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )

    for logger_name in ("uvicorn", "fastapi", "databy"):
        logging.getLogger(logger_name).setLevel(log_level)


def build_cli_panel(
    *,
    title: str,
    info_lines: Iterable[str],
    commands: Sequence[tuple[str, str]],
    border_style: str = "magenta",
) -> Panel:
    """Create a Rich ``Panel`` combining status lines and command table."""

    info_text = Text.from_markup("\n".join(line.rstrip() for line in info_lines if line is not None))
    table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
    table.add_column("Command", style="green", width=20)
    table.add_column("Description", style="white")

    for command, description in commands:
        table.add_row(command, description)

    content = Group(info_text, Text(""), table)

    return Panel(
        content,
        title=f"[bold magenta]{title}[/bold magenta]",
        border_style=border_style,
        padding=(1, 2),
    )


__all__ = ["console", "setup_logging", "build_cli_panel"]