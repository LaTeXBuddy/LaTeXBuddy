import shlex

import latexbuddy.error_class as error_class
import latexbuddy.tools as tools


def run(buddy, file):
    language = buddy.get_lang()
    language = shlex.quote(language)
    langs = tools.execute("aspell", "dump dicts")
    check_language(language, langs)
    # execute aspell on given file and collect output
    error_list = tools.execute("aspell -a --lang=" + language + " < " + file)

    # format aspell output
    out = error_list[70:]
    out = out.split("\n")

    # cleanup error list
    save_errors(format_errors(out), buddy, file)


def check_language(language, langs):
    # error if language dict not installed
    if language not in langs:
        print(
            'Dict for language "'
            + language
            + '" not found - [Linux]Install via sudo apt install - check available dicts at https://ftp.gnu.org/gnu/aspell/dict/0index.html'
        )
        raise Exception("Spell check Failed")


def format_errors(out):
    cleaned_errors = []
    for error in out:
        if error == "":
            error = "x"
        if error[0] == "&":
            cleaned_errors.append(error.replace("&", "").replace("\n", "").strip())
        if error[0] == "#":
            cleaned_errors.append(error.replace("#", "").replace("\n", "").strip())
    return cleaned_errors


def save_errors(cleaned_errors, buddy, file):
    # create error instances
    for error in cleaned_errors:
        split = error.split(":")

        temp = split[0].split(" ")
        location = temp[2] if len(temp) > 2 else temp[1]
        text = temp[0]
        suggestions = split[1].strip().split(",") if len(split) > 1 else []

        error_class.Error(
            buddy,
            file.removesuffix(".detexed"),
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
