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

import shutil
from pathlib import Path

import pytest

from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules.aspell import Aspell
from latexbuddy.texfile import TexFile

pytestmark = pytest.mark.skipif(
    shutil.which("aspell") is None,
    reason="GNU Aspell is not installed",
)

_DOCUMENT_CONTENTS = R"""I was about to leave the restaurant when my friends arrived.

Let's go have a look.

May I speeek to Mrs. Smith please?

Please tike me to this address.

Thank you vary much.

Would you take a mesage please?
"""


@pytest.fixture
def tex_file(tmp_path: Path) -> TexFile:
    document = tmp_path / "document.tex"
    document.write_text(_DOCUMENT_CONTENTS)
    return TexFile(document, compile_tex=False)


def test_run_checks(tex_file: TexFile, driver_config_loader) -> None:
    output_problems = Aspell().run_checks(driver_config_loader, tex_file)

    assert len(output_problems) == 3
    assert output_problems[0].text == "speeek"
    assert output_problems[1].text == "tike"
    assert output_problems[2].text == "mesage"
