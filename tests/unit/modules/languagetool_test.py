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
from latexbuddy.modules.languagetool import LanguageTool
from latexbuddy.texfile import TexFile

pytestmark = pytest.mark.skipif(
    shutil.which("languagetool-commandline.jar") is None,
    reason="LanguageTool not installed",
)

_DOCUMENT_CONTENTS = R"""Dear Jane,

I was delighted to read you're letter last week. Its always a pleasure to recieve the latest news and to here that you and your family had a great summer.

We spent last week at the beach and had so much fun on the sand and in the water exploring the coast we weren't prepared for the rains that came at the end of the vacation. The best parts of the trip was the opportunities to sightsee and relax.

My kids are back in school to. I find their are less things to worry about now that the kids are at school all day. There is plenty of fun things to do in the summer, but by August, I've running out of ideas. I've excepted the fact that we'll have to think up brand-new activities next summer; hoping to round up some creative ideas soon.

Thanks again for your letter!

Sincerely,
Karen
"""


@pytest.fixture
def tex_file(tmp_path: Path) -> TexFile:
    document = tmp_path / "document.tex"
    document.write_text(_DOCUMENT_CONTENTS)
    return TexFile(document, compile_tex=False)


def test_run_checks(tex_file: TexFile, driver_config_loader) -> None:
    problems = LanguageTool().run_checks(driver_config_loader, tex_file)

    assert len(problems) == 16
    assert str(problems[0]) \
        == "Grammar error on 15:43:   : Whitespace repetition (bad formatting)."
    assert str(problems[1]) == 'Grammar error on 19:276: ": Smart quotes (“”).'
    assert str(problems[2]) == 'Grammar error on 19:286: ": Smart quotes (“”).'
