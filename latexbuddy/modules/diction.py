from pathlib import Path

import latexbuddy.tools as tools
from latexbuddy.problem import Problem, ProblemSeverity


def run_checks(buddy, file: Path):
    lang = "de"
    errors = tools.execute(f"diction --suggest --language {lang} {str(file)}")
    errors = errors[:len(errors) - 35]
    errors= errors.split("\n")

    offsets = tools.calculate_line_offsets(file)

    cleaned_errors = []
    for error in errors:
        if len(error) > 0:
            cleaned_errors.append(error.strip())

    for error in cleaned_errors:
        print(error)

    print("-----------")

    problems = []

    for error in cleaned_errors:
        print(error)
        src, location, sugg = error.split(":", maxsplit=2)
        print(f"src={src}, loc={location}, sugg={sugg}")

        line = location.split(".")[0]
        print("line=" + line)
        num = location.split(".")[1].split("-")[0]
        print("num=" + num)

        char = int(offsets[line+2]) + int(num)

        problems.append(
            Problem(
                position=(line, num),
                text=sugg,
                checker="diction",
                cid="0",
                file=file,
                severity=ProblemSeverity.INFO,
                category="wording/ phrasing",
                suggestions=sugg,
                key="diction_" + "wip",
            )
        )
