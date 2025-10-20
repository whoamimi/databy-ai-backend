"""
app.agent.outbounds.aws.utils

Utility functions for running AWS setup and management scripts.
"""
import subprocess
from typing import Optional, Dict, Any

from ....utils.settings import settings

SCRIPTS_DIR = settings.root_dir / "app" / "agent" / "outbounds" / "aws" / "scripts"

def run_script(script_name: str, *args, cwd: Optional[str] = None) -> Dict[str, Any]:
    """
    Run a bash script with optional arguments.

    Args:
        script_name: Name of the script file (e.g., "on_start.sh")
        *args: Variable number of arguments to pass to the script
        cwd: Optional working directory (defaults to scripts directory)

    Returns:
        Dict with keys: 'success' (bool), 'stdout' (str), 'stderr' (str), 'returncode' (int)

    Raises:
        FileNotFoundError: If script doesn't exist
    """
    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    # Build the command
    command = ["bash", str(script_path), *[str(arg) for arg in args]]

    # Set working directory
    working_dir = cwd or str(SCRIPTS_DIR)

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=working_dir,
            check=False  # Don't raise on non-zero exit
        )

        success = result.returncode == 0

        if success:
            print("✓ Script completed successfully")
        else:
            print(f"✗ Script failed with exit code {result.returncode}")

        if result.stdout:
            print("\nOutput:")
            print(result.stdout)

        if result.stderr:
            print("\nErrors/Warnings:")
            print(result.stderr)

        return {
            'success': success,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }

    except Exception as e:
        print(f"Error running script: {e}")
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }
