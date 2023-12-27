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

from pathlib import Path

import pytest

from latexbuddy.modules.own_checkers import EmptySections
from latexbuddy.modules.own_checkers import NativeUseOfRef
from latexbuddy.modules.own_checkers import SiUnitx
from latexbuddy.modules.own_checkers import UnreferencedFigures
from latexbuddy.modules.own_checkers import URLCheck
from latexbuddy.texfile import TexFile

_DOCUMENT_CONTENTS = R"""\begin{figure}[ht]
\centering
\includegraphics[width=\textwidth]{VorlagenSEP2021/figures/gantt.pdf}
\caption{Gantt-Diagramm}
\label{gantt}
\end{figure}

%error for si unit
2002 km

%EmptySections
\section{}
\subsection{}

%url
https://www.tu-braunschweig.de/

%NativeUseOfRef
\ref{}
"""


@pytest.fixture
def tex_file(tmp_path: Path) -> TexFile:
    document = tmp_path / "document.tex"
    document.write_text(_DOCUMENT_CONTENTS)
    return TexFile(document, compile_tex=False)


def test_unreferenced_figures(tex_file: TexFile, driver_config_loader) -> None:
    problems = UnreferencedFigures().run_checks(driver_config_loader, tex_file)

    assert len(problems) == 1
    assert "Figure gantt not referenced" in str(problems[0])


@pytest.mark.xfail(reason="Checker returns more problems than expected")
def test_siunitx(tex_file: TexFile, driver_config_loader) -> None:
    problems = SiUnitx().run_checks(driver_config_loader, tex_file)

    # FIXME: checker returns more problems
    assert len(problems) == 3
    assert R"For number 2021 \num from siunitx may be used" in str(problems[0])
    assert R"For number 2022 \num from siunitx may be used" in str(problems[1])


def test_empty_sections(tex_file: TexFile, driver_config_loader) -> None:
    problems = EmptySections().run_checks(driver_config_loader, tex_file)

    assert len(problems) == 1
    assert "Sections may not be empty" in str(problems[0])


@pytest.mark.xfail(reason="Checker returns more problems than expected")
def test_url_check(tex_file: TexFile, driver_config_loader) -> None:
    problems = URLCheck().run_checks(driver_config_loader, tex_file)

    # FIXME: checker returns more problems
    assert len(problems) == 1
    assert problems[0].text == "https://www.tu-braunschweig.de/"


def test_native_use_of_ref(tex_file: TexFile, driver_config_loader) -> None:
    problems = NativeUseOfRef().run_checks(driver_config_loader, tex_file)

    assert len(problems) == 1
    assert R"Instead of \ref{} use a more precise command" in str(problems[0])
