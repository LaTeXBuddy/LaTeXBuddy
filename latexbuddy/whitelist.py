from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


def add_to_whitelist(whitelist: Path, keys: list[str]) -> None:
    """Adds a list of keys to the whitelist.

    Keys should be valid keys, ideally copied from LaTeXBuddy HTML
    output.

    :param whitelist: path to the whitelist file
    :param keys: list of keys
    """
    whitelist.touch(exist_ok=True)
    entries = {*(whitelist.read_text().splitlines(keepends=False)), *keys}

    with whitelist.open("w") as file:
        file.write("\n".join(entries))
        file.write("\n")


def fill_whitelist_from_wordlist(
    whitelist: Path, wordlist: Path, language: str,
) -> None:
    """Adds keys to the whitelist based on a list of words.

    Words in the wordlist should all be from the same language. Each
    line should be a single word.

    :param whitelist: path to the whitelist file
    :param wordlist: path to the wordlist file
    :param language: language of the words in the wordlist
    """
    wordlist_entries = [
        f"{language}_spelling_{line}"
        for line in Path(wordlist).read_text().splitlines(keepends=False)
        if line
    ]

    whitelist.touch(exist_ok=True)
    entries = {
        *(whitelist.read_text().splitlines(keepends=False)),
        *wordlist_entries,
    }

    with whitelist.open("w") as file:
        file.write("\n".join(entries))
        file.write("\n")


def _get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="latexbuddy-whitelist",
        description="Perform whitelist operations.",
    )
    parser.add_argument(
        "--whitelist",
        "-w",
        type=Path,
        default="./whitelist",
        help="Location of the whitelist file.",
    )
    subparsers = parser.add_subparsers(help="available operations")

    add_parser = subparsers.add_parser(
        "add",
        help="Add keys to the whitelist.",
    )
    add_parser.add_argument(
        "keys",
        metavar="KEY",
        nargs="+",
        type=str,
        help="Keys that should be added to whitelist. Ideally, they should "
             "have been copied from the HTML output",
    )

    wordlist_parser = subparsers.add_parser(
        "from-wordlist",
        help="Read allowed words and add them to whitelist.",
    )
    wordlist_parser.add_argument(
        "wordlist",
        metavar="WORD_LIST",
        type=Path,
        help="Path to the wordlist file. It should contain one word per line.",
    )
    wordlist_parser.add_argument(
        "language",
        metavar="LANGUAGE",
        type=str,
        help="Language of the words in the wordlist",
    )
    return parser


def main(args: Sequence[str] | None = None) -> int:
    args = args if args is not None else sys.argv[1:]
    parsed_args = _get_parser().parse_args(args)

    if "keys" in parsed_args:
        add_to_whitelist(parsed_args.whitelist, parsed_args.keys)
        return 0

    if "wordlist" in parsed_args and "language" in parsed_args:
        fill_whitelist_from_wordlist(
            parsed_args.whitelist,
            parsed_args.wordlist,
            parsed_args.language,
        )

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
