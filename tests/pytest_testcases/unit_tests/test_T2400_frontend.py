import os

import pytest

from latexbuddy.modules.aspell import Aspell
from latexbuddy.output import render_html
from latexbuddy.problem import Problem
from pathlib import Path


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_render_html(script_dir):

    file_name = "/home/lenni/Desktop/test.tex"  # this is static!
    file_text = "\\begin{document} \nHello, how are you? \n I am fine, and you? \n " \
                "\\end{document} "

    aspell = Aspell()
    problems = {
        "uid": Problem(
            position=None,
            text="test_error",
            checker=aspell,
            file=None,
            severity="INFO",
            p_type="123",
            category="spelling",
            suggestions=["lel", "lol", "lul"],
            key="aspell_check",
        )
    }
    path_list = [Path("/home/lenni/Desktop/test.tex")]  # this is static!
    pdf_path = script_dir + "/resources/test_T2400_pdf.pdf"

    path = Path("test_T2400_output.html")
    path.write_text(
        render_html(file_name, file_text, problems, path_list, pdf_path)
    )
