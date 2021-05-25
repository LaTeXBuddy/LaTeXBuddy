"""This module contains code for the command-line interface used to run and manage
LaTeXBuddy."""

import argparse

from pathlib import Path

from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.tools import add_whitelist_console, add_whitelist_from_file


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
    # Not JSON so I removed file ending.
    type=Path,
    default=None,
    help="Location of the whitelist file.",
)
parser.add_argument(
    "--output",
    "-o",
    type=Path,
    default=None,
    help="Where to output the errors file.",
)
parser.add_argument(
    "--wl_add_word",
    "-ww",
    type=str,
    default=None,
    help="TODO"
)
parser.add_argument(
    "--wl_from_file",
    "-wf",
    type=Path,
    default=None,
    help="TODO"
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
    args = parser.parse_args()

    # if we want to add word(s) to the whitelist only do that. Don't check.
    # TODO: no file has to be specified in the call in the next block
    if args.wl_add_word or args.wl_from_file:
        if args.whitelist:
            wl_file = Path(args.whitelist)
        else:
            wl_file = Path("whitelist")
        if args.wl_add_word:
            add_whitelist_console(wl_file, args.wl_add_word)
        if args.wl_from_file:
            add_whitelist_from_file(wl_file, Path(args.wl_from_file))
        return

    config_loader = ConfigLoader(args)

    buddy = LatexBuddy(
        config_loader=config_loader,
        file_to_check=args.file,
    )

    buddy.run_tools()
    buddy.check_whitelist()
    buddy.parse_to_json()
    buddy.output_html()
