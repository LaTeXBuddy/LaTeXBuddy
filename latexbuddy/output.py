from html import escape
from operator import attrgetter
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

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


def render_html(
    file_name: str,
    file_text: str,
    problems: Dict[str, Problem],
    path_list: Path,
    pdf_path: str,
) -> str:
    """Renders an HTML page based on file contents and discovered problems.

    :param file_name: file name
    :param file_text: contents of the file
    :param problems: dictionary of errors returned from latexbuddy
    :param pdf_path: path of pdf file
    :param path_list: a list, containing all file paths to the checked files
    :return: generated HTML
    """
    problem_values = sorted(problems.values(), key=problem_key)
    general_problems = [
        problem for problem in problem_values if problem_key(problem) < 0
    ]
    problem_values = [
        problem_value
        for problem_value in problem_values
        if problem_value not in general_problems
    ]
    template = env.get_template("result.html")

    # calculate amount of whitespaces needed for line numbers to be indented correctly
    split_lines = file_text.split("\n")
    line_numbers = []
    i = 1
    line_count = len(split_lines)
    for line in split_lines:
        diff = len(str(line_count)) - len(str(i))
        new_line = ""

        # add whitespaces
        for x in range(0, diff):
            new_line += "&nbsp;" + "&nbsp;"
        new_line += str(i) + "." + "&nbsp;"

        line_numbers.append(new_line)
        i += 1

    highlighted_tex = highlight(file_text, problem_values)

    if not Path(pdf_path).exists():
        pdf_path = None
    else:
        # TODO: temporary fix, might cause issues if another "compiled" directory
        #  is in pdf_path
        cut_path = pdf_path.find("compiled")
        if -1 < cut_path:
            pdf_path = pdf_path[pdf_path.find("compiled") :]

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
        pdf_path=pdf_path,
    )


class Interval:
    """forward declaration to enable type-hinting within class"""

    @property
    def start(self) -> int:
        return -1

    @property
    def end(self) -> int:
        return -1

    @property
    def severity(self) -> int:
        return -1

    @property
    def problems(self):
        return []

    def intersects(self, other):
        return False

    def perform_intersection(self, other):
        return None


class Interval:
    def __init__(
        self,
        problems: Union[Problem, List[Problem]],
        start: Optional[int] = None,
        end: Optional[int] = None,
    ) -> None:

        if isinstance(problems, Problem):
            problems = [problems]

        if not problems or len(problems) == 0:
            raise ValueError("An interval must have at least one problem!")

        self._problems = problems

        self._start = start if start else problems[0].position[1]
        self._end = end if end else self.start + problems[0].length

    @property
    def problems(self):
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
            ]
        )

    def intersects(self, other: Interval) -> bool:
        """
        Determines whether or not the other interval intersects with 'self'

        :param other: other interval to consider
        """

        if other.start < self.start:
            return other.end > self.start
        else:
            return other.start < self.end

    def perform_intersection(self, other: Interval) -> Optional[List[Interval]]:
        """
        Performs an intersection of two intervals and returns a list of new
        non-intersecting intervals to replace the two specified intervals 'self' and
        'other', if the intervals actually intersect. Should the intervals not
        intersect, None is returned, indicating that there is no need to replace the
        two intervals.
        The intervals in the returned list are sorted by their start index in ascending
        order.

        :param other: other interval to intersect with 'self'
        """

        if not self.intersects(other):
            return None

        # narrow down mirrored positions without restricting the input space
        if other.start < self.start:
            return other.perform_intersection(self)

        new_intervals: List[Interval] = []

        if other.start > self.start:
            new_intervals.append(Interval(self.problems, self.start, other.start))

        new_intervals.append(
            Interval(
                self.problems + other.problems, other.start, min(self.end, other.end)
            )
        )

        if other.end < self.end:
            new_intervals.append(Interval(self.problems, other.end, self.end))

        elif other.end > self.end:
            new_intervals.append(Interval(other.problems, self.end, other.end))

        return new_intervals

    def __str__(self) -> str:
        return f"({self.start}, {self.end}, {self.severity})"


def highlight(tex: str, problems: List[Problem]) -> str:
    """Highlights the TeX code using the problems' data.

    :param tex: TeX source
    :param problems: list of problems
    :return: HTML string with highlighted errors, ready to be put inside <pre>
    """

    tex_lines: List[str] = tex.splitlines(keepends=False)
    line_intervals: List[List[Interval]] = create_empty_line_interval_list(tex_lines)

    add_basic_problem_intervals(line_intervals, problems)

    # old_highlighting(line_intervals, tex_lines)
    for intervals in line_intervals:
        resolve_interval_intersections(intervals)

    mark_intervals_in_tex(tex_lines, line_intervals)

    return "\n".join(tex_lines) + "\n"


def create_empty_line_interval_list(tex_lines: List[str]) -> List[List[Interval]]:
    """
    Creates and returns a list of (empty) lists of Intervals. The outer list will
    contain exactly len(tex_lines) + 1 empty lists.

    :param tex_lines: individual lines of a .tex-file as a list of strings
    :returns: a list of empty lists that meet the specified dimensions
    """

    line_intervals: List[List[Interval]] = []
    for _ in tex_lines:
        line_intervals.append([])

    # when parsing, yalafi often marks the n+1'th line as erroneous
    line_intervals.append([])

    return line_intervals


def add_basic_problem_intervals(
    line_intervals: List[List[Interval]], problems: List[Problem]
) -> None:
    """
    Filters out problems without a position attribute or with length zero and inserts
    the remaining ones into the line_intervals list.

    :param line_intervals: List of lists of Intervals for any given line
    :param problems: list of problems to be inserted as Intervals
    """

    for problem in problems:
        # we don't care about problems with no position
        if problem.position is None:
            continue

        # we don't care about problems without length (for now)
        if problem.length == 0:
            continue

        # TODO: add more intervals for Problems that encompass multiple lines
        # FIXME: split intervals, if they encompass a latex command which has been
        #  removed in the detex process (issue #58)
        line = problem.position[0] - 1
        line_intervals[line].append(Interval(problem))


def resolve_interval_intersections(intervals: List[Interval]) -> None:
    """
    Finds any intersecting intervals and replaces them with non-intersecting intervals
    that may contain more than one problem.

    :param intervals: list of intervals in one line to be checked for intersections
    """

    if len(intervals) < 2:
        return

    next_index: int = 1

    while next_index < len(intervals):

        intervals.sort(key=attrgetter("start"))

        intersect_result = intervals[next_index - 1].perform_intersection(
            intervals[next_index]
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
    tex_lines: List[str], line_intervals: List[List[Interval]]
) -> None:
    """
    Adds HTML marker-tags (span) for every interval in line_intervals to the respective
    line in tex_lines and escapes all HTML control characters in tex_lines.

    :param tex_lines: text lines from the .tex-file
    :param line_intervals: list of non-intersecting intervals to be marked for every
                           line in tex_lines
    """

    for i in range(len(tex_lines)):
        tex_lines[i] = mark_intervals_in_tex_line(tex_lines[i], line_intervals[i])


def mark_intervals_in_tex_line(tex_line: str, intervals: List[Interval]) -> str:
    """
    Adds HTML marker-tags (span) for every interval in intervals to the respective
    tex_line string and returns the resulting line. This method also escapes all HTML
    control characters included in tex_line.

    :param tex_line: line from the .tex-file
    :param intervals: list of non-intersecting intervals to be highlighted in the line
    :returns: resulting line as a string, containing HTML span tags
    """

    offset: int = 0
    for interval in intervals:
        open_tag, close_tag = generate_wrapper_html_tags(interval)

        start: int = interval.start + offset - 1
        end: int = interval.end + offset - 1

        # TODO: figure out HTML escaping
        tex_line = (
            f"{tex_line[:start]}"
            f"{open_tag}{tex_line[start:end]}{close_tag}"
            f"{tex_line[end:]}"
        )

        offset += len(open_tag) + len(close_tag)

    return tex_line


def generate_wrapper_html_tags(interval: Interval) -> Tuple[str, str]:
    """
    Generates and returns a pair of HTML span tags to wrap the text in the specified
    interval.

    :param interval: interval, specifying the position and metadata of the tags
    :returns: a tuple of two strings, containing an opening and a closing span tag for
              the specified interval object
    """

    opening_tag = (
        f"<span "
        f'class="under is-{str(ProblemSeverity(interval.severity))}" '
        f'title="{escape(interval.html_tag_title)}"'
        f">"
    )
    closing_tag = f"</span>"

    return opening_tag, closing_tag
