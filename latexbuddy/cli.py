"""This module contains code for the command-line interface used to run and manage
LaTeXBuddy."""

import argparse
from pathlib import Path

from latexbuddy.latexbuddy import LatexBuddy


parser = argparse.ArgumentParser(description="The one-stop-shop for LaTeX checking.")
parser.add_argument("file", help="File that will be processed.")
parser.add_argument(
    "--language", "-l", default="en", help="Target language of the file."
)
parser.add_argument(
    "--whitelist",
    "-w",
    # TODO: why a new file format? if it's JSON, use .json. If not, don't use one.
    default="whitelist.wlist",
    help="Location of the whitelist file.",
)
parser.add_argument(
    "--output", "-o", default="errors.json", help="Where to output the errors file."
)


def main():
    """Parses CLI arguments and launches the LaTeXBuddy instance."""
    args = parser.parse_args()
    buddy = LatexBuddy(
        error_file=args.output,
        whitelist_file=args.whitelist,
        file_to_check=Path(args.file),
        lang=args.language,
    )
    buddy.run_tools()
    buddy.check_whitelist()
    buddy.parse_to_json()
    buddy.output_html()
