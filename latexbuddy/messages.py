"""This module defines standard messages that are to be printed to the command line
as well as builders for those.
"""
from pathlib import Path


def not_found(executable: str, to_install: str) -> str:
    # importing this here to avoid circular import error
    from latexbuddy import __app_name__

    return (
        f"'{executable}' not found! "
        f"Make sure you've installed {to_install} correctly. "
        f"Refer to the {__app_name__} manual for help."
    )


def error_occurred_in_module(module_name: str) -> str:
    return (
        f"An error occurred while executing checks for module '{module_name}' "
        f"resulting in the module stopping execution and not providing any results"
    )


def texfile_error(msg: str) -> str:
    return f"An error occurred while compiling the tex file:" f"{msg}"


def path_not_found(error_occasion: str, path: Path) -> str:
    return (
        f"An error occurred during {error_occasion}: "
        f"No such file or directory: {str(path)}."
    )
