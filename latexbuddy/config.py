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
"""Configuration module for LaTeXBuddy.

This module implements the configuration management. Our configuration
encompasses three different formats, each of which have to be parsed
differently:

- **Command-line arguments.** These can be specified per call, and thus
  they are prioritized over other options. We use :py:mod:`argparse` to
  parse the arguments from :py:obj:`sys.argv`.

- **Environment variables.** We parse those variables, who have the
  ``LATEXBUDDY_`` prefix and whose names (prefix excluded) match the
  configuration parameters' names. Matching is case-insensitive, and
  dashes are replaced with underscores. Environment variables can be set
  for a prolonged period of time, but raely forever; they take
  precedence over the config file.

- **Config file.**

  .. warning::
     This option is unstable and will be changed later.

  Early versions of LaTeXBuddy used a Python file as a config file. We
  are considering different file formats to simplify the configuration
  process and to mitigate the risk of code injection attacks.

.. versionadded:: 0.5.0
"""
from __future__ import annotations

import enum
from pathlib import Path
from typing import Any
from typing import Iterable
from typing import TYPE_CHECKING
from typing import TypeVar

from pydantic import BaseSettings
from pydantic import create_model

if TYPE_CHECKING:
    import argparse


class Config:
    """LaTeXBuddy config class.

    This is a custom configuration class that combines a Pydantic model
    with an :py:class:`argparse.ArgumentParser`. LaTeXBuddy uses it to
    define its configuration, while plugin developers can use it to
    extend said configuration with their custom fields.

    :param parser:
        Argument parser to populate with the options
    :param title:
        Title of the option group. Should not contain the words
        'config' or 'plugin'
    :param description:
        Description of the option group. Will only be shown in the
        command-line help.
    """

    def __init__(
        self,
        parser: argparse.ArgumentParser,
        title: str,
        description: str | None = None,
    ) -> None:
        """Create a config class.

        Creates an empty config class that represents an option group
        within the global configuration.
        """
        self._model_kwargs: dict[str, tuple[type[Any], Any]] = {}
        self._parser = parser.add_argument_group(
            title=title,
            description=description,
        )
        self.title = title
        self.description = description

    @property
    def model(self) -> type[BaseSettings]:
        """Return the Pydantic settings model."""
        return create_model(
            f"{''.join(self.title.capitalize().split())}Config",
            __base__=BaseSettings,
            **self._model_kwargs,
        )  # type: ignore

    T = TypeVar("T")

    def add_option(
        self,
        name: str,
        option_type: type[T],
        *,
        action: str = "store",
        default: T | None = None,
        alias: str | None = None,
        description: str | None = None,
        metavar: str | None = None,
        choices: Iterable[T] | None = None,
    ) -> None:
        """Add a configuration option.

        :param name:
            Option name. Can be kebab-case or snake_case.
        :param option_type:
            Type of the option.
        :param action:
            :external:ref:`Action` of the option's command-line argument
        :param default:
            Default value of the option.
        :param alias:
            Option short name for the command-line argument. Should be
            only one character.
        :param description:
            Option description.
        :param metavar:
            Option metavar for the command-line argument. Defaults to
            option name in UPPER_SNAKE_CASE.
        :param choices:
            :external:ref:`Choices` (possible values) of the option.
        """
        self._parser.add_argument(
            *[
                f"--{n.replace('_', '-')}"
                if len(n) > 1
                else f"-{n.replace('_', '-')}"
                for n in [name, alias]
                if n
            ],
            action=action,
            default=default,
            type=option_type,
            help=description,
            metavar=metavar or name.replace("-", "_").upper(),
            choices=choices,
        )
        self._model_kwargs[name.replace("-", "_")] = (option_type, default)


class OutputFormat(enum.Enum):
    """Possible output file formats.

    HTML
       This will produce a single HTML page with all problems arranged
       in an editor-like interface

    JSON
       This will output a machine-readable JSON

    HTML_Flask
       This is similar to HTML, but it will output the HTML page
       suitable for being a response of the Flask-based server
    """

    html = "HTML"
    json = "JSON"
    html_flask = "HTML_Flask"


def get_core_config(parser: argparse.ArgumentParser) -> Config:
    """Build a parser and a config model for LaTeXBuddy.

    This method will populate the parser with the arguments and return
    the config model (based on Pydantic's BaseSettings) that can be used
    for configuration.

    :param parser: The parser to get populated with the config options
    :return: The generated config model class
    """
    config = Config(
        parser,
        "Core",
    )
    config.add_option(
        "language",
        str,
        default="en",
        alias="l",
        description="Target language of the file.",
    )
    config.add_option(
        "module_dir",
        Path,
        default=Path(__file__) / ".." / "modules",
        description="Directory to load the modules from.",
    )
    config.add_option(
        "whitelist",
        Path,
        default=None,
        alias="w",
        description="Location of the whitelist file.",
    )
    config.add_option(
        "output",
        Path,
        default=Path.cwd(),
        alias="o",
        description="Directory, in which to put the output file.",
    )
    config.add_option(
        "format",
        OutputFormat,
        default=OutputFormat.json,
        alias="f",
        description="Format of the output file.",
        choices=list(OutputFormat),
    )
    config.add_option(
        "compile-pdf",
        bool,
        default=False,
        description="Whether to compile the PDF by default.",
    )

    return config
