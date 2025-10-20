"""
app.utils.utils

Project utilities / helper functions.

"""

import os
import yaml
import argparse

from pathlib import Path

ROOT_DIR_NAME = 'backend'

def setup_dev_workspace(root_folder_name: str = ROOT_DIR_NAME):
    """ Call in files / notebooks if running workspace in sub-directory path. """

    if Path.cwd().stem == root_folder_name:
        print(f'Path already set to default root directory: {Path.cwd()}')
        return Path.cwd()
    else:
        print('Initialized workspace currently at directory: %s', Path.cwd())

    current = Path().resolve()
    for parent in [current, *current.parents]:
        if parent.name == root_folder_name:
            os.chdir(parent)  # change working directory
            print(f"📂 Working directory set to: {parent}")
            return parent # Exit after changing directory

    raise FileNotFoundError(f"Root folder '{root_folder_name}' cannot be found from current dir: {Path.cwd()} ")

def build_parser():
    from ..utils.settings import settings

    with open(settings.cli_path, "r") as f:
        config = yaml.safe_load(f)

    parser = argparse.ArgumentParser(
        prog=config["program"]["name"],
        description=config["program"]["description"]
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    for cmd_name, cmd_def in config["commands"].items():
        sub = subparsers.add_parser(cmd_name, help=cmd_def.get("help", ""))
        for arg_name, arg_opts in cmd_def.get("args", {}).items():
            flags = arg_opts.get("flags", [f"--{arg_name}"])
            kwargs = {}

            if "help" in arg_opts:
                kwargs["help"] = arg_opts["help"]

            if "type" in arg_opts:
                # Map YAML string type to Python type
                type_map = {"int": int, "str": str, "float": float, "bool": bool}
                kwargs["type"] = type_map.get(arg_opts["type"], str)

            if "default" in arg_opts:
                # Support pulling defaults from settings dynamically
                default_value = getattr(settings, f"app_{arg_name}", arg_opts["default"])
                kwargs["default"] = default_value

            if "action" in arg_opts:
                kwargs["action"] = arg_opts["action"]

            sub.add_argument(*flags, **kwargs)

        # Dynamically assign function by name
        func_name = cmd_def.get("func")
        if func_name:
            sub.set_defaults(func=globals().get(func_name))

    return parser