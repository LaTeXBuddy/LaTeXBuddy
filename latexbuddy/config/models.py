#  LaTeXBuddy - a LaTeX checking tool
#  Copyright (c) 2022  LaTeXBuddy
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

import enum
from pathlib import Path

from pydantic import BaseSettings
from pydantic import Field
from pydantic.types import DirectoryPath
from pydantic.types import FilePath


class OutputFormat(enum.Enum):
    html = "HTML"
    json = "JSON"
    html_flask = "HTML_Flask"


class MainConfig(BaseSettings):
    # TODO: consider a separate field type, for example, `Locale`
    language: str | None = Field(
        default=None,
        max_length=2,
        description="Target language of the file.",
    )
    language_country: str | None = Field(
        default=None,
        max_length=2,
        description="Country of the language.",
    )
    module_dir: DirectoryPath = Field(
        default=Path(__file__) / ".." / "modules",
        description="Directory to load the modules from.",
    )
    whitelist: FilePath | None = Field(
        default=None,
        description="Location of the whitelist file.",
    )
    output: Path = Field(
        default=Path.cwd() / "latexbuddy_html",
        description="Directory, in which to put the output file.",
    )
    format: OutputFormat = Field(
        default=OutputFormat.json,
        description="Format of the output file.",
    )
    enable_modules_by_default: bool = Field(
        default=True,
        description="Whether to enable all found modules by default.",
    )
    pdf: bool = Field(
        default=True,
        description="Whether to compile the PDF by default.",
    )


MainConfig.update_forward_refs()
