"""This module contains code for the command-line interface used to run and manage
LaTeXBuddy."""

import argparse

from pathlib import Path
from time import perf_counter

from latexbuddy import __logger as root_logger
from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.log import __setup_root_logger


parser = argparse.ArgumentParser(description="The one-stop-shop for LaTeX checking.")

parser.add_argument("file", type=Path, help="File that will be processed.")
parser.add_argument(
    "--config",
    "-c",
    type=Path,
    default=Path("config.py"),
    help="Location of the config file.",
)

parser.add_argument(
    "--language",
    "-l",
    type=str,
    default=None,
    help="Target language of the file.",
)
parser.add_argument(
    "--whitelist",
    "-w",
    type=Path,
    default=None,
    help="Location of the whitelist file.",
)
parser.add_argument(
    "--output",
    "-o",
    type=Path,
    default=None,
    help="Directory, in which to put the output file.",
)
parser.add_argument(
    "--format",
    "-f",
    type=str,
    choices=["HTML", "html", "JSON", "json"],
    default="HTML",
    help="Format of the output file (either HTML or JSON).",
)

module_selection = parser.add_mutually_exclusive_group()
module_selection.add_argument(
    "--enable-modules",
    type=str,
    default=None,
    help="Comma-separated list of module names that should be executed. "
    "(Any other module will be implicitly disabled!)",
)
module_selection.add_argument(
    "--disable-modules",
    type=str,
    default=None,
    help="Comma-separated list of module names that should not be executed."
    "(Every other module will be implicitly enabled!)",
)


def main():
    """Parses CLI arguments and launches the LaTeXBuddy instance."""
    start = perf_counter()

    args = parser.parse_args()

    __setup_root_logger(root_logger)
    logger = root_logger.getChild("cli")

    logger.debug(f"Parsed CLI args: {str(args)}")

    config_loader = ConfigLoader(args)

    buddy = LatexBuddy(
        config_loader=config_loader,
        file_to_check=args.file,
    )

    buddy.run_tools()
    buddy.check_whitelist()
    buddy.output_file()

    logger.debug(f"Execution finished in {round(perf_counter()-start, 2)}s")
