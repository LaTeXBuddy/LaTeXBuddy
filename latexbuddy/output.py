from functools import reduce
from html import escape
from typing import Dict, List, Set, Tuple

from jinja2 import Environment, PackageLoader

from latexbuddy.problem import Problem, ProblemSeverity


env = Environment(loader=PackageLoader("latexbuddy"))


def problem_key(problem: Problem) -> int:
    """Returns a number for each problem to be able to sort them.

    This puts YaLaFi's problems on top, followed by errors without location.

    :param problem: problem object
    :return: error's "rating" for sorting
    """
    if problem.checker.lower() == "yalafi":
        return -3
    if not problem.position:
        return -2
    if not isinstance(problem.position, tuple):
        return -1

    return problem.position[0]


def render_html(file_name: str, file_text: str, problems: Dict[str, Problem]) -> str:
    """Renders an HTML page based on file contents and discovered problems.

    :param file_name: file name
    :param file_text: contents of the file
    :param problems: dictionary of errors returned from latexbuddy
    :return: generated HTML
    """
    problem_values = sorted(problems.values(), key=problem_key)
    template = env.get_template("result.html")
    highlighted = highlight(file_text, problem_values)
    return template.render(
        file_name=file_name, file_text=highlighted, problems=problem_values
    )


class MarkedInterval:
    def __init__(self, problem: Problem) -> None:
        self.start = problem.position[1] - 1
        self.end = problem.position[1] + problem.length - 1
        self.problem = problem

    def intersects(self, other: "MarkedInterval") -> bool:
        return (
            other.start <= self.end <= other.end
            or self.start <= other.end <= self.end
            or (self.start <= other.start and other.end <= self.end)
            or (other.start <= self.start and self.end <= other.end)
        )

    def merge(self, other: "MarkedInterval") -> "List[MarkedInterval]":
        if not self.intersects(other):
            return [self, other]

        if self.problem.severity < other.problem.severity:
            return [other]

        return [self]

    def __str__(self) -> str:
        return f"{self.start}:{self.end}"

    def __repr__(self):
        return f"<{str(self)}>"


def highlight(tex: str, problems: List[Problem]) -> str:
    line_intervals: List[List[MarkedInterval]] = []
    tex_lines = tex.splitlines(keepends=True)
    for _ in tex_lines:
        line_intervals.append([])
    line_intervals.append([])

    for problem in problems:
        if problem.position == (0, 0):
            continue
        lin = problem.position[0] - 1
        p_int = MarkedInterval(problem)

        if p_int.problem.length == 0:
            continue

        line_intervals[lin].append(p_int)

    def reducer(mil: List[MarkedInterval], mi2: MarkedInterval):
        if len(mil) == 0:
            return [mi2]

        result = []
        for mi1 in mil:
            merge_res = mi1.merge(mi2)
            result += merge_res
            if mi2 in merge_res:
                break

        return result

    for i in range(len(line_intervals)):
        line = line_intervals[i]
        if len(line) == 0:
            continue

        reduced_line = reduce(reducer, line, [])

        offset = 0
        for interval in reduced_line:
            old_len = len(tex_lines[i])
            start = offset + interval.start
            end = offset + interval.end
            opening_tag = f'<span class="under is-{str(interval.problem.severity)}" title="{escape(interval.problem.description or "")}">'
            closing_tag = f"</span>"
            string = (
                tex_lines[i][:start]
                + opening_tag
                + tex_lines[i][start:end]
                + closing_tag
                + tex_lines[i][end:]
            )
            new_len = len(string)
            tex_lines[i] = string
            offset += new_len - old_len

    return "".join(tex_lines)
