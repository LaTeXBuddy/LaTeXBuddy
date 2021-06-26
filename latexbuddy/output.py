from copy import deepcopy
from html import escape
from operator import attrgetter
from typing import Dict, List

from jinja2 import Environment, PackageLoader

from latexbuddy.problem import Problem


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


def render_html(file_name: str, file_text: str, problems: Dict[str, Problem], pdf_path: str) -> str:
    """Renders an HTML page based on file contents and discovered problems.

    :param file_name: file name
    :param file_text: contents of the file
    :param problems: dictionary of errors returned from latexbuddy
    :param pdf_path: path of pdf file
    :return: generated HTML
    """
    problem_values = sorted(problems.values(), key=problem_key)
    template = env.get_template("result.html")

    highlighted_tex = highlight(file_text, problem_values)

    # add line numbers
    splitted_text = highlighted_tex.splitlines(keepends=True)
    new_text = []
    i = 1
    line_count = len(splitted_text)
    for line in splitted_text:
        # calculate amount of whitespaces needed for correct indentation
        diff = len(str(line_count)) - len(str(i))
        new_line = str(i) + "    "

        # add diff whitespaces
        for x in range(0, diff):
            new_line += " "

        new_line += line
        new_text.append(new_line)
        i += 1
    new_text = "".join(new_text)

    return template.render(
        pdf_path=pdf_path,
        file_name=file_name,
        file_text=new_text,
        problems=problem_values,
    )


class Interval:
    def __init__(self, problem: Problem) -> None:
        self.problem = problem

    @property
    def start(self) -> int:
        return self.problem.position[1]

    @property
    def end(self) -> int:
        return self.start + self.problem.length

    @property
    def severity(self) -> int:
        return self.problem.severity.value

    def __str__(self) -> str:
        return f"({self.start}, {self.end}, {self.severity})"


def find_best_intervals(intervals: List[Interval]) -> List[Interval]:
    """Returns a list of non-overlapping intervals with the maximal sum of severities.

    In other words, it filters out less important intervals to find the most optimal set
    of non-overlapping intervals that are to be highlighted.

    Dynamic programming algorithm composed by David Meyer <da.meyer@tu-braunsschweig.de>

    :param intervals: original list of (possibly overlapping) intervals
    :return: list of non-overlapping intervals
    """
    if len(intervals) == 0:
        return []

    if len(intervals) == 1:
        return intervals

    sorted_intervals = sorted(intervals, key=attrgetter("end"))
    n = len(sorted_intervals)

    def find_predecessor(idx: int) -> int:
        """Calculates the index of the closest predecessor to the interval with index i.

        :param idx: index of the inspected interval
        :return: index of the closest predecessor
        """
        i_start = sorted_intervals[idx].start
        j = idx - 1
        while j >= 0:
            if sorted_intervals[j].end <= i_start:
                return j  # j'th interval is the closest predecessor
            j -= 1

        return -1  # no predecessor exists

    # dictionary for storing intermediate results
    calculated = {-1: ([], 0)}

    for i in range(n):
        if i == 0:
            # always add first interval
            calculated[i] = (
                [sorted_intervals[i]],
                sorted_intervals[i].severity,
            )
            continue

        pred_i = find_predecessor(i)
        if calculated[i - 1][1] > calculated[pred_i][1] + sorted_intervals[i].severity:
            calculated[i] = calculated[i - 1]
        else:
            copy_tuples = deepcopy(calculated[pred_i][0])
            copy_tuples.append(sorted_intervals[i])
            calculated[i] = (
                copy_tuples,
                calculated[pred_i][1] + sorted_intervals[i].severity,
            )

    return calculated[n - 1][0]


def highlight(tex: str, problems: List[Problem]) -> str:
    """Highlights the TeX code using the problems' data.

    :param tex: TeX source
    :param problems: list of problems
    :return: HTML string with highlighted errors, ready to be put inside <pre>
    """
    line_intervals: List[List[Interval]] = []
    tex_lines = tex.splitlines(keepends=True)
    for _ in tex_lines:
        line_intervals.append([])

    # when parsing, yalafi often marks the n+1'th line as erroneous
    line_intervals.append([])

    for problem in problems:
        # we don't care about problems with no position
        if problem.position is None:
            continue

        # we don't care about problems without length (for now)
        if problem.length == 0:
            continue

        lin = problem.position[0] - 1
        line_intervals[lin].append(Interval(problem))

    for i in range(len(line_intervals)):
        intervals = line_intervals[i]
        if len(intervals) == 0:
            continue

        best_intervals = find_best_intervals(intervals)

        offset = 0
        for interval in best_intervals:
            old_len = len(tex_lines[i])
            start = offset + interval.start - 1
            end = offset + interval.end - 1
            opening_tag = (
                f"<span "
                f'class="under is-{str(interval.problem.severity)}" '
                f'title="{escape(interval.problem.description or "")}"'
                f">"
            )
            closing_tag = f"</span>"

            # TODO: figure out HTML escaping
            string = (
                f"{tex_lines[i][:start]}"
                f"{opening_tag}"
                f"{tex_lines[i][start:end]}"
                f"{closing_tag}"
                f"{tex_lines[i][end:]}"
            )
            tex_lines[i] = string
            offset += len(string) - old_len

    return "".join(tex_lines)
