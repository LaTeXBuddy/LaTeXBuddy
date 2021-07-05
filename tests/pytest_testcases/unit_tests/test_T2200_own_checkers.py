import pytest
import os

from pathlib import Path
from latexbuddy.modules.own_checkers import UnreferencedFigures
from latexbuddy.modules.own_checkers import SiUnitx
from latexbuddy.modules.own_checkers import EmptySections
from latexbuddy.modules.own_checkers import URLCheck
from latexbuddy.modules.own_checkers import NativeUseOfRef
from latexbuddy.texfile import TexFile
from tests.pytest_testcases.unit_tests.resources.driver_config_loader import ConfigLoader as DriverCL


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_run_checks_unreferenced_figures(script_dir):

    ERROR_COUNT = 1
    document_path = script_dir + "/resources/T2200.tex"
    checker_instance = UnreferencedFigures()

    test_file = TexFile(Path(document_path))

    output_problems = checker_instance.run_checks(DriverCL(), test_file)

    assert len(output_problems) == ERROR_COUNT
    assert str(output_problems[0]) == "Latex info on 2:1: gantt: Figure gantt not referenced.."


def test_run_checks_si_unit(script_dir):

    ERROR_COUNT = 3
    document_path = script_dir + "/resources/T2200.tex"
    checker_instance = SiUnitx()

    test_file = TexFile(Path(document_path))

    output_problems = checker_instance.run_checks(DriverCL(), test_file)

    assert len(output_problems) == ERROR_COUNT
    assert str(output_problems[0]) == "Latex info on 4:47: 2021: For number 2021 \\num from siunitx may be used.."
    assert str(output_problems[1]) == "Latex info on 10:1: 2002: For number 2002 \\num from siunitx may be used.."


def test_run_checks_empty_sections(script_dir):

    ERROR_COUNT = 1
    document_path = script_dir + "/resources/T2200.tex"
    checker_instance = EmptySections()

    test_file = TexFile(Path(document_path))

    output_problems = checker_instance.run_checks(DriverCL(), test_file)

    assert len(output_problems) == ERROR_COUNT
    assert str(output_problems[0]) == "Latex info on 13:1: : Sections may not be empty.."


def test_run_checks_url_check(script_dir):

    ERROR_COUNT = 1
    document_path = script_dir + "/resources/T2200.tex"
    checker_instance = URLCheck()

    test_file = TexFile(Path(document_path))

    output_problems = checker_instance.run_checks(DriverCL(), test_file)

    assert len(output_problems) == ERROR_COUNT
    assert output_problems[0].text == "https://www.tu-braunschweig.de/"


def test_run_checks_native_use_of_ref(script_dir):

    ERROR_COUNT = 1
    document_path = script_dir + "/resources/T2200.tex"
    checker_instance = NativeUseOfRef()

    test_file = TexFile(Path(document_path))

    output_problems = checker_instance.run_checks(DriverCL(), test_file)

    assert len(output_problems) == ERROR_COUNT
    assert str(output_problems[0]) == "Latex info on 20:1: \\ref{: Instead of \\ref{} use a more precise command e.g. \cref{}."
