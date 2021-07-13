"""This module contains code for the command-line interface used to run and manage
LaTeXBuddy."""

import argparse
import logging
import os

from pathlib import Path
from time import perf_counter
from typing import AnyStr

from colorama import Fore

from latexbuddy import __app_name__
from latexbuddy import __logger as root_logger
from latexbuddy import __name__ as name
from latexbuddy import __version__
from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.log import __setup_root_logger
from latexbuddy.module_loader import ModuleLoader
from latexbuddy.tools import get_all_paths_in_document, perform_whitelist_operations


parser = argparse.ArgumentParser(
    prog=name, description="The one-stop-shop for LaTeX checking."
)
parser.add_argument(
    "--version", "-V", action="version", version=f"{__app_name__} v{__version__}"
)
# nargs="+" marks the beginning of a list
parser.add_argument(
    "file", nargs="+", type=Path, help="File(s) that will be processed."
)
parser.add_argument(
    "--config",
    "-c",
    type=Path,
    default=Path("config.py"),
    help="Location of the config file.",
)
parser.add_argument(
    "--verbose",
    "-v",
    action="store_true",
    default=False,
    help="Display debug output",
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
    "--output",
    "-o",
    type=str,
    default=None,
    help="Directory, in which to put the output file.",
)
parser.add_argument(
    "--format",
    "-f",
    type=str,
    choices=["HTML", "html", "JSON", "json"],
    default=None,
    help="Format of the output file (either HTML or JSON).",
)

# TODO changer parser so no file is required when adding words/ keys to whitelist
parser.add_argument(
    "--wl_add_keys",
    "-ak",
    nargs="+",
    metavar="KEY",
    default=None,
    help="Arguments are valid keys that should be added to whitelist. Ideally"
    " the keys are copied from LaTeXBuddy HTML Output",
)
parser.add_argument(
    "--wl_from_wordlist",
    "-awl",
    metavar=("WORD_LIST", "LANGUAGE"),
    nargs=2,
    default=None,
    help="First argument is a file containing a single word per line, "
    "second argument is the language of the words."
    " The words get parsed to keys and the keys get added to the whitelist as "
    "spelling errors that will be ignored by LaTeXBuddy",
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

    display_debug = args.verbose or os.environ.get("LATEXBUDDY_DEBUG", False)

    __setup_root_logger(root_logger, logging.DEBUG if display_debug else logging.INFO)
    logger = root_logger.getChild("cli")

    print(f"{Fore.CYAN}{__app_name__}{Fore.RESET} v{__version__}")

    logger.debug(f"Parsed CLI args: {str(args)}")

    if args.wl_add_keys or args.wl_from_wordlist:

        perform_whitelist_operations(args)
        return

    config_loader = ConfigLoader(args)

    """ For each Tex file transferred, all paths
    are fetched and Latexbuddy is executed """

    buddy = LatexBuddy.instance
    module_loader = ModuleLoader(
        Path(
            config_loader.get_config_option_or_default(
                LatexBuddy, "module_dir", "latexbuddy/modules/", verify_type=AnyStr
            )
        )
    )

    for p in args.file:  # args.file is a list
        paths, problems = get_all_paths_in_document(p)

        for path in paths:

            # re-initialize the buddy instance with a new path
            buddy.init(
                config_loader=config_loader,
                module_provider=module_loader,
                file_to_check=path,
                path_list=paths,  # to be used later on in render html
            )

            # TODO: Moved this here, so added Problems are not immediately deleted
            #  anymore. Please acknowledge by removing this comment.
            for problem in problems:
                buddy.add_error(problem)

            buddy.run_tools()
            buddy.check_whitelist()
            buddy.output_file()

    logger.debug(f"Execution finished in {round(perf_counter() - start, 2)}s")
