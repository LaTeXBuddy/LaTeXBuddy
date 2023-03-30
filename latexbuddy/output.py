# LaTeXBuddy - a LaTeX checking tool
# Copyright (C) 2021-2022  LaTeXBuddy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations

from html import escape
from operator import attrgetter
from pathlib import Path

from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import Template

from latexbuddy.problem import Problem
from latexbuddy.problem import ProblemSeverity


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


def render_flask_html(
    file_name: str,
    file_text: str,
    problems: dict[str, Problem],
    path_list: Path,
    pdf_path: str,
) -> str:

    return render_general_html(
        env.get_template("flask_result.html"),
        file_name,
        file_text,
        problems,
        path_list,
        pdf_path,
    )


def render_html(
    file_name: str,
    file_text: str,
    problems: dict[str, Problem],
    path_list: Path,
    pdf_path: str,
) -> str:

    return render_general_html(
        env.get_template("result.html"),
        file_name,
        file_text,
        problems,
        path_list,
        pdf_path,
    )


def render_general_html(
    template: Template,
    file_name: str,
    file_text: str,
    problems: dict[str, Problem],
    path_list: Path,
    pdf_path: str,
) -> str:
    """Renders an HTML page based on file contents and discovered problems.

    :param template: HTML template to use for generation
    :param file_name: file name
    :param file_text: contents of the file
    :param problems: dictionary of errors returned from latexbuddy
    :param pdf_path: path of pdf file
    :param path_list: a list, containing all file paths to the checked files
    :return: generated HTML
    """

    general_problems, problem_values = sort_problems(problems)

    line_numbers = calculate_line_numbers(file_text)

    highlighted_tex = highlight(file_text, problem_values)

    final_pdf_path: str | None = pdf_path
    if Path(pdf_path).exists():
        # TODO: temporary fix, might cause issues if another "compiled"
        #  directory is in pdf_path
        cut_path = pdf_path.find("compiled")
        if cut_path > -1:
            final_pdf_path = pdf_path[pdf_path.find("compiled"):]
    else:
        final_pdf_path = None

    #  list of lines
    highlighted_tex = highlighted_tex.split("\n")

    # map line number to lines
    mapped = []
    for i in range(0, len(line_numbers)):
        mapped.append((line_numbers[i], highlighted_tex[i]))

    return template.render(
        file_name=file_name,
        file_text=mapped,
        problems=problem_values,
        general_problems=general_problems,
        paths=path_list,
        pdf_path=final_pdf_path,
    )


def sort_problems(
    problems: dict[str, Problem],
) -> tuple[list[Problem], list[Problem]]:
    problem_values = sorted(problems.values(), key=problem_key)
    general_problems = [
        problem for problem in problem_values if problem_key(problem) < 0
    ]
    problem_values = [
        problem_value
        for problem_value in problem_values
        if problem_value not in general_problems
    ]
    return general_problems, problem_values


def calculate_line_numbers(file_text: str) -> list[str]:
    split_lines = file_text.split("\n")
    line_numbers = []
    line_count = len(split_lines)
    for lineno in range(line_count):
        diff = len(str(line_count)) - len(str(lineno))

        line_numbers.append(
            "&nbsp;" * 2 * diff + str(lineno) + "." + "&nbsp;",
        )

    return line_numbers


class Interval:
    """This class describes an interval with problems.

    An interval is a section of text, defined byt its start and end
    positions, that contains :class:`~latexbuddy.problem.Problem`
    objects.

    :param problems: list of problems on the interval
    :param start: start symbol of the interval
    :param end: end symbol of the interval
    """

    def __init__(
        self,
        problems: Problem | list[Problem],
        start: int | None = None,
        end: int | None = None,
    ) -> None:

        if isinstance(problems, Problem):
            problems = [problems]

        if not problems or len(problems) == 0:
            _msg = "An interval must have at least one problem."
            raise ValueError(_msg)

        self._problems = problems

        if not start:
            for problem in self._problems:
                if problem.position is not None:
                    self._start = problem.position[1]
                    break
            else:
                self._start = 0

        self._end = end if end else self.start + problems[0].length

        if self.end < self.start:
            _msg = "End position can not be smaller than start position."
            raise ValueError(_msg)

    @property
    def problems(self) -> list[Problem]:
        return self._problems

    @property
    def start(self) -> int:
        return self._start

    @property
    def end(self) -> int:
        return self._end

    @property
    def severity(self) -> int:
        return max([problem.severity.value for problem in self.problems])

    @property
    def html_tag_title(self) -> str:
        return ", ".join(
            [
                problem.description
                if problem.description
                else f"{problem.checker}-problem ({str(problem.severity)})"
                for problem in self.problems
            ],
        )

    def intersects(self, other: Interval) -> bool:
        """Determines whether or not the other interval intersects with 'self'.

        :param other: other interval to consider
        """

        if other.start < self.start:
            return other.end > self.start

        return other.start < self.end

    def perform_intersection(self, other: Interval) -> list[Interval] | None:
        """Performs an intersection of two intervals and returns a list of new
        non-intersecting intervals to replace the two specified intervals
        'self' and 'other', if the intervals actually intersect. Should the
        intervals not intersect, None is returned, indicating that there is no
        need to replace the two intervals. The intervals in the returned list
        are sorted by their start index in ascending order.

        :param other: other interval to intersect with 'self'
        """

        if not self.intersects(other):
            return None

        # narrow down mirrored positions without loss of generality
        if other.start < self.start:
            return other.perform_intersection(self)

        new_intervals: list[Interval] = []

        if other.start > self.start:
            new_intervals.append(
                Interval(self.problems, self.start, other.start),
            )

        new_intervals.append(
            Interval(
                self.problems + other.problems,
                other.start,
                min(self.end, other.end),
            ),
        )

        if other.end < self.end:
            new_intervals.append(Interval(self.problems, other.end, self.end))

        elif other.end > self.end:
            new_intervals.append(Interval(other.problems, self.end, other.end))

        return new_intervals

    def __str__(self) -> str:
        return f"({self.start}, {self.end}, {self.severity})"


def highlight(tex: str, problems: list[Problem]) -> str:
    """Highlights the TeX code using the problems' data.

    :param tex: TeX source
    :param problems: list of problems
    :return: HTML string with highlighted errors, ready to be put inside <pre>
    """

    tex_lines: list[str] = tex.splitlines(keepends=False)
    line_intervals: list[list[Interval]] = \
        create_empty_line_interval_list(tex_lines)

    add_basic_problem_intervals(line_intervals, problems, tex_lines)

    for intervals in line_intervals:
        resolve_interval_intersections(intervals)

    mark_intervals_in_tex(tex_lines, line_intervals)

    return "\n".join(tex_lines) + "\n"


def create_empty_line_interval_list(lines: list[str]) -> list[list[Interval]]:
    """Creates and returns a list of (empty) lists of Intervals. The outer list
    will contain exactly len(tex_lines) + 1 empty lists.

    :param lines: individual lines of a .tex-file as a list of strings
    :returns: a list of empty lists that meet the specified dimensions
    """

    line_intervals: list[list[Interval]] = []
    for _ in lines:
        line_intervals.append([])

    # when parsing, yalafi often marks the n+1'th line as erroneous
    line_intervals.append([])

    return line_intervals


def add_basic_problem_intervals(
    line_intervals: list[list[Interval]],
    problems: list[Problem],
    tex_lines: list[str],
) -> None:
    """Filters out problems without a position attribute or with length zero
    and inserts the remaining ones into the line_intervals list.

    :param line_intervals: List of lists of Intervals for any given line
    :param problems: list of problems to be inserted as Intervals
    :param tex_lines: contents of the .tex-file
    """

    for problem in problems:
        # we don't care about problems with no position
        if problem.position is None:
            continue

        # we don't care about problems without length (for now)
        if problem.length == 0:
            continue

        # FIXME: split intervals, if they encompass a latex command which has
        #  been removed in the detex process (issue #58)
        line = problem.position[0] - 1
        interval = Interval(problem)

        # move the interval down the lines until their start index is actually
        # included
        while interval.start > len(tex_lines[line]):
            interval = Interval(
                problem,
                interval.start - len(tex_lines[line]),
                interval.end - len(tex_lines[line]),
            )
            line += 1

        # split the interval, if it reaches across lines
        while interval.end - 1 > len(tex_lines[line]):

            new_interval = Interval(
                problem, interval.start, len(tex_lines[line]) + 1,
            )
            line_intervals[line].append(new_interval)

            interval = Interval(
                problem,
                1,
                (interval.end - interval.start)
                - (new_interval.end - new_interval.start)
                + 1,
            )
            line += 1

        line_intervals[line].append(interval)


def resolve_interval_intersections(intervals: list[Interval]) -> None:
    """Finds any intersecting intervals and replaces them with non-
    intersecting intervals that may contain more than one problem.

    :param intervals: list of intervals in one line to be checked for
                      intersections
    """

    if len(intervals) < 2:
        return

    next_index: int = 1

    while next_index < len(intervals):

        intervals.sort(key=attrgetter("start"))

        intersect_result = intervals[next_index - 1].perform_intersection(
            intervals[next_index],
        )

        if intersect_result is not None:

            # remove both intersected intervals
            intervals.pop(next_index - 1)
            intervals.pop(next_index - 1)

            insert_index: int = next_index - 1

            for new_interval in intersect_result:
                intervals.insert(insert_index, new_interval)
                insert_index += 1

        else:
            next_index += 1


def mark_intervals_in_tex(
    lines: list[str],
    line_intervals: list[list[Interval]],
) -> None:
    """Adds HTML marker-tags for every interval in multiple lines of TeX code.

    For every line in ``lines``, and for every interval in
    ``line_intervals`` for the respective line, this method wraps it
    with ``<span>`` tags and returns the resulting line. This method
    also escapes all HTML control characters included in ``tex_line``.

    It basically calls :func:`.mark_intervals_in_tex_line`, but the
    lines are modified in-place.

    :param lines: lines from the TeX file
    :param line_intervals: list of non-intersecting intervals to be
                           highlighted for every line
    """

    for i in range(len(lines)):
        lines[i] = mark_intervals_in_tex_line(
            lines[i], line_intervals[i],
        )


def mark_intervals_in_tex_line(line: str, intervals: list[Interval]) -> str:
    """Adds HTML marker-tags for every interval in a line of TeX code.

    For every interval in ``intervals``, this method wraps it with
    ``<span>`` tags and returns the resulting line. This method also
    escapes all HTML control characters included in ``tex_line``.

    :param line: line from the TeX file
    :param intervals: list of non-intersecting intervals to be
                      highlighted in the line
    :returns: resulting line as a string, containing ``<span>`` tags
    """

    offset: int = 0
    for i, interval in enumerate(intervals):
        open_tag, close_tag = generate_wrapper_html_tags(interval)

        start: int = interval.start + offset - 1
        end: int = interval.end + offset - 1

        preface = line[:start]
        content = line[start:end]
        appendix = line[end:]

        escaped_content = escape(content)
        escaped_preface = escape(preface) if i == 0 else preface
        escaped_appendix = escape(appendix) \
            if i == len(intervals) - 1 \
            else appendix

        line = (
            f"{escaped_preface}"
            f"{open_tag}{escaped_content}{close_tag}"
            f"{escaped_appendix}"
        )

        offset += len(open_tag) + len(close_tag)
        offset += len(escaped_preface) - len(preface)
        offset += len(escaped_content) - len(content)
        offset += len(escaped_appendix) - len(appendix)

    return line


def generate_wrapper_html_tags(interval: Interval) -> tuple[str, str]:
    """Generates and returns a pair of HTML ``<span>`` tags to wrap the text in
    the specified interval.

    :param interval: interval, specifying the position and metadata of
                     the tags
    :returns: a tuple of two strings, containing an opening and
              a closing ``<span>`` tag for the specified interval object
    """

    # escape HTML control sequences and remove possible invalid linebreaks
    escaped_title = escape(interval.html_tag_title.replace("\n", ""))

    lid = interval.problems[0].uid + "List"
    opening_tag = (
        f"<span "
        f'class="under is-{str(ProblemSeverity(interval.severity))}" '
        f'title="{escaped_title}" '
        f"onclick=\"jumpTo('{lid}')\""
        f">"
    )
    closing_tag = "</span>"

    return opening_tag, closing_tag
