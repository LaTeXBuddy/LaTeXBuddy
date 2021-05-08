import argparse

from latexbuddy.latexbuddy import LatexBuddy


parser = argparse.ArgumentParser(description="The one-stop-shop for LaTeX checking.")
parser.add_argument("file", help="File that will be processed.")
parser.add_argument(
    "--language", "-l", default="en", help="Target language of the file."
)
parser.add_argument(
    "--whitelist",
    "-w",
    default="whitelist.json",
    help="Location of the whitelist file.",
)
parser.add_argument(
    "--output", "-o", default="errors.json", help="Where to output the errors file."
)


def main():
    args = parser.parse_args()
    buddy = LatexBuddy(
        error_file=args.output,
        whitelist_file=args.whitelist,
        file_to_check=args.file,
        lang=args.language,
    )
    buddy.run_tools()
    buddy.parse_to_json()
