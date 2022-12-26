"""This module contains code for the command-line interface used to run and
manage LaTeXBuddy."""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from time import perf_counter
from typing import AnyStr
from typing import Sequence

import latexbuddy
from latexbuddy import __app_name__
from latexbuddy import __version__
from latexbuddy import colour
from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.module_loader import ModuleLoader
from latexbuddy.tools import get_abs_path
from latexbuddy.tools import get_all_paths_in_document

LOG = logging.getLogger(__name__)


def _get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="The one-stop-shop for LaTeX checking.",
        epilog="More documentation at <https://latexbuddy.readthedocs.io/>.",
    )
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"{__app_name__} v{__version__}",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Display debug output",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=Path("config.py"),
        help="Location of the config file.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Directory, in which to put the output file.",
    )

    # nargs="+" marks the beginning of a list
    parser.add_argument(
        "file",
        nargs="+",
        type=Path,
        help="File(s) that will be processed.",
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
        type=str,
        default=None,
        help="Location of the whitelist file.",
    )
    parser.add_argument(
        "--format",
        "-f",
        type=str,
        choices=["HTML", "html", "JSON", "json", "HTML_FLASK", "html_flask"],
        default=None,
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
        help="Comma-separated list of modules that should be disabled. "
        "(Every other module will be implicitly enabled!)",
    )
    return parser


def main(args: Sequence[str] | None = None) -> int:
    """Parses CLI arguments and launches the LaTeXBuddy instance."""
    start = perf_counter()

    args = args if args is not None else sys.argv[1:]
    parsed_args = _get_parser().parse_args(args)

    verbosity = parsed_args.verbose
    if os.environ.get("LATEXBUDDY_DEBUG"):
        verbosity = 2
    latexbuddy.configure_logging(
        verbosity,
    )

    sys.stderr.write(
        f"{colour.CYAN}{__app_name__}{colour.RESET_ALL} v{__version__}\n",
    )
    sys.stderr.flush()
    LOG.debug(f"Parsed CLI args: {str(parsed_args)}")

    __execute_latexbuddy_checks(parsed_args)

    LOG.debug(
        f"Execution finished in {round(perf_counter() - start, 3)} seconds",
    )
    return 0


def __execute_latexbuddy_checks(args: argparse.Namespace) -> None:
    config_loader = ConfigLoader(args)

    """ For each Tex file transferred, all paths
    are fetched and Latexbuddy is executed """

    buddy = LatexBuddy.instance
    module_loader = ModuleLoader(
        Path(
            config_loader.get_config_option_or_default(
                LatexBuddy,
                "module_dir",
                "latexbuddy/modules/",
                verify_type=AnyStr,
            ),
        ),
    )

    for p in args.file:  # args.file is a list
        p = get_abs_path(p)
        first_path = True
        paths = get_all_paths_in_document(Path(p))

        for path in paths:

            # re-initialize the buddy instance with a new path
            buddy.init(
                config_loader=config_loader,
                module_provider=module_loader,
                file_to_check=path,
                path_list=paths,  # to be used later on in render html
                compile_tex=first_path,
            )
            first_path = False

            buddy.run_tools()
            buddy.check_whitelist()
            buddy.output_file()
