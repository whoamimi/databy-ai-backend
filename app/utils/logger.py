"""Rich logging utilities for the DataBy backend."""

from __future__ import annotations

import logging
from rich.console import Console
from rich.logging import RichHandler

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

    for logger_name in ("uvicorn", "fastapi"):
        logging.getLogger(logger_name).setLevel(log_level)

    