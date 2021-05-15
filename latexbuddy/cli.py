import argparse

from pathlib import Path

from latexbuddy.config_loader import ConfigLoader
from latexbuddy.latexbuddy import LatexBuddy


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
    help="Where to output the errors file.",
)


def main():
    args = parser.parse_args()

    config_loader = ConfigLoader(args)

    buddy = LatexBuddy(
        config_loader=config_loader,
        file_to_check=args.file,
    )

    buddy.run_tools()
    buddy.check_whitelist()
    buddy.parse_to_json()
