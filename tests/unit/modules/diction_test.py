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
from latexbuddy.modules.diction import Diction
from latexbuddy.texfile import TexFile

pytestmark = pytest.mark.skipif(
    shutil.which("diction") is None,
    reason="GNU Diction is not installed",
)

_DOCUMENT_CONTENTS = R"""This Sentence cause a double double Word Error.

This Sentence causes a Error, thats why its important.

This text is only written to test serval modules for Buddy.
"""

_CONFIG_CONTENTS = R"""main = {
    "language": "en",
}"""


@pytest.fixture
def tex_file(tmp_path: Path) -> TexFile:
    document = tmp_path / "document.tex"
    document.write_text(_DOCUMENT_CONTENTS)
    return TexFile(document, compile_tex=False)


@pytest.mark.xfail(
    reason="Diction has unstable API, and the whole module should be rewritten",
)
def test_run_checks(tex_file: TexFile, driver_config_loader):
    output_problems = Diction().run_checks(driver_config_loader, tex_file)

    assert len(output_problems) == 3
    assert output_problems[0].text \
        == "This Sentence cause a double double Word Error."
    assert output_problems[1].text \
        == "This Sentence causes a Error, thats why its important."
