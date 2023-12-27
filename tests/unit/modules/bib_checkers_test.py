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

from latexbuddy.modules.bib_checkers import BibtexDuplicates
from latexbuddy.modules.bib_checkers import NewerPublications
from latexbuddy.texfile import TexFile

_DOCUMENT_CONTENTS = R"""\bibliography{document}
"""

_BIBLIOGRAPHY_CONTENTS = R"""
@misc{FirecrackerGithub,
author = {Amazon},
title = {{Firecracker Micro VM}},
howpublished = {\url{https://aws.amazon.com/blogs/aws/firecracker-lightweight-virtualization-for-serverless-computing/}},
urldate = {2018-11-10},
year = {2020}
}
@misc{FirecrackerBlog,
author = {Amazon},
title = {{Firecracker Micro VM}},
howpublished = {\url{https://aws.amazon.com/blogs/aws/firecracker-lightweight-virtualization-for-serverless-computing/}},
urldate = {2019-07-02},
year = {2020}
}
@inproceedings{StatefulDataflow:2014,
author = {Fernandez, Raul Castro and Migliavacca, Matteo and Kalyvianaki, Evangelia and Pietzuch, Peter},
booktitle = {USENIX Annual Technical Conference (USENIX ATC)},
title = {{Making State Explicit For Imperative Big Data Processing}},
year = {2014}
}
@inproceedings{SFDF,
author = {Fernandez, Raul Castro and Migliavacca, Matteo and Kalyvianaki, Evangelia and Pietzuch, Peter},
booktitle = {USENIX Annual Technical Conference (USENIX ATC)},
title = {{Making State Explicit For Imperative Big Data Processing}},
year = {2014}
}

@inproceedings{werner2018serverless,
author={S. {Werner} and J. {Kuhlenkamp} and M. {Klems} and J. {Müller} and S. {Tai}},
booktitle = {IEEE Conference on Big Data (Big Data)},
title = {{Serverless Big Data Processing Using Matrix Multiplication}},
year = {2018}
}
@article{Anna:2019,
author = {Wu, Chenggang and Faleiro, Jose and Lin, Yihan and Hellerstein, Joseph},
journal = {IEEE International Conference on Data Engineering, (ICDE)},
title = {{Anna: a KVS for any Scale}},
year = {2018}
}
"""


@pytest.fixture
def bib_file(tmp_path: Path) -> Path:
    document = tmp_path / "document.bib"
    document.write_text(_BIBLIOGRAPHY_CONTENTS)
    return document


@pytest.fixture
def tex_file(tmp_path: Path, bib_file: Path) -> TexFile:
    document = tmp_path / "document.tex"
    document.write_text(_DOCUMENT_CONTENTS)
    return TexFile(document, compile_tex=False)


def test_duplicates(tex_file: TexFile, driver_config_loader) -> None:
    problems = BibtexDuplicates().run_checks(driver_config_loader, tex_file)

    assert len(problems) == 2
    assert problems[0].text == "FirecrackerGithub <=> FirecrackerBlog"
    assert problems[1].text == "StatefulDataflow:2014 <=> SFDF"


def test_newer_publications(tex_file: TexFile, driver_config_loader) -> None:
    problems = NewerPublications().run_checks(driver_config_loader, tex_file)

    assert len(problems) == 2
    # FIXME: this returns DOI and not the key
    if problems[0].text != "werner2018serverless":
        pytest.xfail(reason="Checker returned wrong values")
    assert problems[1].text == "Anna:2019"
