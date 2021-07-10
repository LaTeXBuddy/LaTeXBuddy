import os

import pytest

from latexbuddy.modules.aspell import Aspell
from latexbuddy.output import render_html, Interval
from latexbuddy.problem import Problem, ProblemSeverity
from pathlib import Path


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_unit_frontend_render_html(script_dir):

    file_name = "/home/lenni/Desktop/test.tex"  # this is not a real file_path
    file_path = Path(file_name)
    file_text = "\\begin{document} \nHello, how are you? \n I am fine, and you? \n " \
                "\\end{document} "

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
        )
    }
    path_list = [file_path]  # this is static!
    pdf_path = script_dir + "/resources/test_T2400_pdf.pdf"

    path = Path("test_T2400_output.html")
    path.write_text(
        render_html(file_name, file_text, problems, path_list, pdf_path)
    )


def test_interval_intersection():
    i1 = Interval(Problem((1, 3), "blub", Aspell, Path("./"), description="descr"))
    i2 = Interval(Problem((1, 5), "blubbb", Aspell, Path("./"), description="descr"))

    assert i1.start == 3 and i1.end == 7
    assert i2.start == 5 and i2.end == 11

    assert i1.intersects(i2)
    assert i2.intersects(i1)

    result = i1.perform_intersection(i2)

    assert len(result) == 3
    assert len(i2.perform_intersection(i1)) == 3

    assert result[0].start == 3 and result[0].end == 5 and len(result[0].problems) == 1
    assert result[1].start == 5 and result[1].end == 7 and len(result[1].problems) == 2
    assert result[2].start == 7 and result[2].end == 11 and len(result[2].problems) == 1
