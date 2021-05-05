import shlex
import tools
import error_class


def run(buddy, file):
    language = "de"
    language = shlex.quote(language)
    langs = tools.execute("aspell", "dump dicts")

    # error if language dict not installed
    if language not in langs:
        print(
            "Dict for language \"" + language + "\" not found - [Linux]Install via sudo apt install - check available dicts at https://ftp.gnu.org/gnu/aspell/dict/0index.html")
        raise Exception("Spell check Failed")

    # execute aspell on given file and collect output
    error_list = tools.execute("aspell -a --lang=" + language + " < " + file)

    # format aspell output
    out = error_list[70:]
    out = out.split("\n")

    # cleanup error list
    cleaned_errors = []
    for error in out:
        if error == "":
            error = "x"
        if error[0] == '&':
            cleaned_errors.append(error.replace("&", "").replace("\n", "").strip())
        if error[0] == '#':
            cleaned_errors.append(error.replace("#", "").replace("\n", "").strip())

    # create error instances
    for error in cleaned_errors:
        print(error)
        split = error.split(":")

        temp = split[0].split(" ")
        location = temp[2] if len(temp) > 2 else temp[1]
        text = temp[0]
        sugg = split[1].strip() if len(split) > 1 else ""

        error_class.Error(
            buddy,
            file,
            "aspell",
            "spelling",
            "0",
            text,
            location,
            len(text),
            sugg,
            False,
        )
