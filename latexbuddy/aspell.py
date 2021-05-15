import shlex

from pathlib import PurePath

import latexbuddy.error_class as error_class
import latexbuddy.tools as tools


def run(buddy, file):
    language = buddy.get_lang()
    language = shlex.quote(language)
    langs = tools.execute("aspell", "dump dicts")
    check_language(language, langs)
    # execute aspell on given file and collect output
    error_list = tools.execute(f"cat {file} | aspell -a --lang={language}")

    # format aspell output
    out = error_list.splitlines()[1:]  # the first line specifies aspell version

    # cleanup error list
    format_errors(out, buddy, file)


def check_language(language, langs):
    # error if language dict not installed
    if language not in langs:
        print(
            'Dict for language "'
            + language
            + '" not found - [Linux]Install via sudo apt install - check available dicts at https://ftp.gnu.org/gnu/aspell/dict/0index.html'
        )
        raise Exception("Spell check Failed")


def format_errors(out, buddy, file):
    line_number = 1
    line_lengths = tools.calculate_line_lengths(file)
    line_offsets = tools.calculate_line_offsets(file)

    for error in out:
        if error.strip() == "":
            # this is a line separator
            line_number += 1
            continue

        if error[0] in ("&", "#"):
            meta_str, suggestions_str = error[1:].strip().split(": ", 1)

            # & original count offset
            # # original
            meta = meta_str.split(" ")

            text = meta[0]
            suggestions = []

            if error[0] == "&":  # there are suggestions
                location = int(meta[2])  # meta[1] is suggestion count
                suggestions = suggestions_str.split(", ")
            else:  # there are no suggestions
                location = int(meta[1])

            print(f"Word is {text}")
            print(f"Offset in line is {location}")
            print(f"Line {line_number} begins at character {line_offsets[line_number]}")

            # TODO: do something with line_number
            # location = str(tools.start_char(line_number, location, line_lengths))
            location = str(line_offsets[line_number] + location)

            print(f"Offset in file is {location}")

            error_class.Error(
                buddy,
                PurePath(file).stem,
                "aspell",
                "spelling",
                "0",
                text,
                location,
                len(text),
                suggestions,
                False,
                "spelling_" + text,
            )
