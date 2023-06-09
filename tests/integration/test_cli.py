# LaTeXBuddy tests
# Copyright (C) 2022  LaTeXBuddy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations

from pathlib import Path

import pytest

import latexbuddy.cli

_CONFIG_FILE_CONTENTS = r"""main = {
    "language": "en",
    "language_country": "GB",
    "module_dir": "<DRIVERS>",
    "output": "./latexbuddy_html/",
    "format": "HTML",
    "enable-modules-by-default": False,
    "pdf": True,
}

modules = {
    "FirstDriver": {
        "enabled": True,
    },
    "SecondDriver": {
        "enabled": True,
    },
}
"""

_DOCUMENT_CONTENTS = r"""\documentclass{article}

\begin{document}
First document. This is a simple example, with no
extra parameters or packages included.
\end{document}
"""


@pytest.fixture
def config_file(tmp_path: Path, resources_dir: Path) -> Path:
    config_file = tmp_path / "config.py"
    config_file.write_text(
        _CONFIG_FILE_CONTENTS.replace(
            "<DRIVERS>",
            str((resources_dir / "driver_modules").resolve()),
        ),
    )
    return config_file


@pytest.fixture
def document(tmp_path: Path) -> Path:
    document = tmp_path / "document.tex"
    document.write_text(_DOCUMENT_CONTENTS)
    return document


def test_running_cli(
    caplog,
    config_file,
    empty_whitelist_file,
    document,
    output_dir: Path,
):
    """Tests that running the main command succeeds.

    This is a basic test that checks that, under "normal circumstances",
    the command is getting ran, the modules run, too, and the output
    gets written.
    """
    args = [
        "--config",
        str(config_file.resolve()),
        "--whitelist",
        str(empty_whitelist_file.resolve()),
        "--output",
        str(output_dir.resolve()),
        str(document.resolve()),
    ]

    return_code = latexbuddy.cli.main(args)
    assert return_code == 0

    # asserting that both driver modules have been executed correctly
    # FIXME: this is not being output as of now
    # assert "FirstDriver started checks" in caplog.text
    # assert "SecondDriver started checks" in caplog.text
    # assert "FirstDriver finished after" in caplog.text
    # assert "SecondDriver finished after" in caplog.text

    # asserting that the whitelist-check has been executed correctly
    assert "Beginning whitelist-check..." in caplog.text
    assert "Finished whitelist-check in" in caplog.text

    # asserting that the output file was saved correctly
    assert "Output saved to " in caplog.text
