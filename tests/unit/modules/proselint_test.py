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

from latexbuddy.modules.proselint_checker import ProseLint
from latexbuddy.texfile import TexFile

_DOCUMENT_CONTENTS = R"""\documentclass[12pt]{article}
\begin{document}
If this document contains errors it will be criticized in the long run.
\end{document}
"""


@pytest.fixture
def tex_file(tmp_path: Path) -> TexFile:
    document = tmp_path / "document.tex"
    document.write_text(_DOCUMENT_CONTENTS)
    return TexFile(document, compile_tex=False)


def test_run_checks(tex_file: TexFile, driver_config_loader) -> None:
    problems = ProseLint().run_checks(driver_config_loader, tex_file)

    assert len(problems) == 1
    assert "is a cliché" in problems[0].description
