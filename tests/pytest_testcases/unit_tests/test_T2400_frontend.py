from __future__ import annotations

import os
from pathlib import Path
from random import sample

import pytest

from latexbuddy.modules.aspell import Aspell
from latexbuddy.output import Interval
from latexbuddy.output import render_html
from latexbuddy.problem import Problem
from latexbuddy.problem import ProblemSeverity


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_unit_frontend_render_html(script_dir):
    file_name = "/home/lenni/Desktop/test.tex"  # this is not a real file_path
    file_path = Path(file_name)
    file_text = (
        "\\begin{document} \nHello, how are you? \n I am fine, and you? \n "
        "\\end{document} "
    )

    problems = {
        "uid": Problem(
            position=None,
            text="test_error",
            checker=Aspell,
            file=file_path,
            severity=ProblemSeverity.INFO,
            p_type="123",
            category="spelling",
            suggestions=["lel", "lol", "lul"],
            key="aspell_check",
        ),
    }
    path_list = [file_path]  # this is static!
    pdf_path = script_dir + "/resources/test_T2400_pdf.pdf"

    path = Path("test_T2400_output.html")
    path.write_text(
        render_html(file_name, file_text, problems, path_list, pdf_path),
    )


def generate_test_problem(
    position: tuple[int, int],
    length: int,
    description: str,
) -> Problem:

    return Problem(
        position,
        generate_random_text(length),
        Aspell,
        Path("./"),
        description=description,
    )


def generate_random_text(length: int) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    text = ""

    for i in range(length):
        text += sample(alphabet, 1)[0]

    return text


def parse_interval_list(
    interval_data: list[tuple[tuple[int, int], int, str]] | None,
) -> list[Interval] | None:

    if interval_data is None:
        return None

    result = []

    for result_interval in interval_data:
        result.append(
            Interval(
                generate_test_problem(
                    result_interval[0],
                    result_interval[1],
                    result_interval[2],
                ),
            ),
        )

    return result


def interval_equals(first: Interval, second: Interval) -> bool:
    return (
        first.start == second.start
        and first.end == second.end
        and first.severity == second.severity
        and sorted(first.html_tag_title.split(", "))
        == sorted(second.html_tag_title.split(", "))
    )


def interval_lists_equal(
    first: list[Interval] | None,
    second: list[Interval] | None,
) -> bool:

    if first is None or second is None:
        return first is None and second is None

    if len(first) != len(second):
        return False

    if len(first) == 0:
        return True

    for interval0 in first:
        equal_found = False

        for interval1 in second:
            if interval_equals(interval0, interval1):
                equal_found = True
                break

        if not equal_found:
            return False

    return True


@pytest.mark.parametrize(
    "position, length, description",
    [
        ((0, 3), 5, "description_0"),
        ((1, 5), 6, "description_1"),
        ((42, 55), 15, "description_2"),
    ],
)
def test_interval_creation(position, length, description):
    problem = generate_test_problem(position, length, description)
    interval = Interval(problem)

    assert interval.start == position[1]
    assert interval.end == position[1] + length
    assert interval.problems == [problem]
    assert interval.severity == problem.severity.value
    assert interval.html_tag_title == problem.description


@pytest.mark.parametrize(
    "interval_data_in, result_interval_data",
    [
        (
            [
                ((5, 3), 4, "description_0"),
                ((5, 5), 6, "description_1"),
            ],
            [
                ((5, 3), 2, "description_0"),
                ((5, 5), 2, "description_0, description_1"),
                ((5, 7), 4, "description_1"),
            ],
        ),
        (
            [
                ((4, 4), 7, "description_2"),
                ((4, 6), 3, "description_3"),
            ],
            [
                ((4, 4), 2, "description_2"),
                ((4, 6), 3, "description_2, description_3"),
                ((4, 9), 2, "description_2"),
            ],
        ),
        (
            [
                ((45, 2), 5, "description_4"),
                ((45, 4), 3, "description_5"),
            ],
            [
                ((45, 2), 2, "description_4"),
                ((45, 4), 3, "description_4, description_5"),
            ],
        ),
        (
            [
                ((46, 2), 5, "description_6"),
                ((46, 2), 3, "description_7"),
            ],
            [
                ((46, 2), 3, "description_6, description_7"),
                ((46, 5), 2, "description_6"),
            ],
        ),
        (
            [
                ((6, 8), 4, "description_8"),
                ((6, 14), 3, "description_9"),
            ],
            None,
        ),
    ],
)
def test_interval_intersection(
    interval_data_in: list[tuple[tuple[int, int], int, str]],
    result_interval_data: list[tuple[tuple[int, int], int, str]] | None,
):

    intervals_in = parse_interval_list(interval_data_in)
    assert intervals_in is not None and len(intervals_in) == 2

    i0 = intervals_in[0]
    i1 = intervals_in[1]

    result_intervals = i0.perform_intersection(i1)
    assert interval_lists_equal(result_intervals, i1.perform_intersection(i0))

    expected_result = parse_interval_list(result_interval_data)
    assert interval_lists_equal(result_intervals, expected_result)
