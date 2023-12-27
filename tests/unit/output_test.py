#  LaTeXBuddy - a LaTeX checking tool
#  Copyright (c) 2023  LaTeXBuddy
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations

import random
from pathlib import Path
from string import ascii_lowercase

import pytest

from latexbuddy.modules.aspell import Aspell
from latexbuddy.output import Interval
from latexbuddy.output import render_html
from latexbuddy.problem import Problem
from latexbuddy.problem import ProblemSeverity

_DOCUMENT_CONTENTS = R"""\begin{document}
Hello, how are you?
I am fine, and you?
\end{document}
"""


def test_render_html(tmp_path: Path, resources_dir: Path) -> None:
    file = tmp_path / "document.tex"  # not a real document
    file_text = _DOCUMENT_CONTENTS

    from latexbuddy.problem import Problem
    problems = {
        "problem1": Problem(
            position=None,
            text="test_error",
            checker=Aspell,
            file=file,
            severity=ProblemSeverity.INFO,
            p_type="123",
            category="spelling",
            suggestions=["foo", "bar", "baz"],
            key="aspell_check",
        ),
    }

    # TODO: check the output
    render_html(
        str(file),
        file_text,
        problems,
        [file],
        str(resources_dir / "output" / "document.pdf"),
    )


def test_interval(tmp_path):
    problem = Problem(
        position=(0, 5),
        text="foo bar",
        checker=Aspell,
        file=tmp_path / "document.tex",
        description="some error",
    )

    interval = Interval(problem)

    assert interval.start == 5
    assert interval.end == 12
    assert interval.problems == [problem]
    assert interval.severity == 2  # WARNING by default
    assert interval.html_tag_title == "some error"


@pytest.mark.xfail(reason="Interval doesn't work, see #128", strict=False)
@pytest.mark.parametrize(
    ("input_tuples", "expected"),
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
    input_tuples: list[tuple[tuple[int, int], int, str]],
    expected: list[tuple[tuple[int, int], int, str]] | None,
):
    intervals = _parse_interval_tuples(input_tuples)

    intersection = intervals[0].perform_intersection(intervals[1])
    back_intersection = intervals[1].perform_intersection(intervals[0])
    assert _interval_lists_equal(
        intersection, back_intersection,
    )

    expected_intersecion = _parse_interval_tuples(expected)
    assert _interval_lists_equal(intersection, expected_intersecion)


def _interval_equals(first: Interval, second: Interval) -> bool:
    return (
        first.start == second.start
        and first.end == second.end
        and first.severity == second.severity
        and sorted(first.html_tag_title.split(", "))
        == sorted(second.html_tag_title.split(", "))
    )


def _interval_lists_equal(
    first: list[Interval] | None,
    second: list[Interval] | None,
) -> bool:
    if first is None or second is None:
        return first is None and second is None

    if len(first) != len(second):
        return False

    if len(first) == 0:
        return True

    for i0, i1 in zip(first, second):
        if not _interval_equals(i0, i1):
            return False

    return True


def _parse_interval_tuples(
    interval_tuples: list[tuple[tuple[int, int], int, str]] | None,
) -> list[Interval] | None:
    if interval_tuples is None:
        return None

    return [
        Interval(
            Problem(
                interval[0],
                ''.join(
                    random.choice(ascii_lowercase) for _ in range(
                        interval[1],
                    )
                ),
                Aspell,
                Path("./"),
                description=(interval[2]),
            ),
        )
        for interval in interval_tuples
    ]
