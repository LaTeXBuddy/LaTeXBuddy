# LaTeXBuddy - a LaTeX checking tool
# Copyright (C) 2021-2022  LaTeXBuddy
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

import importlib
import inspect
import logging
import sys
from abc import ABC
from abc import abstractmethod
from pathlib import Path
from types import ModuleType
from typing import Callable

import latexbuddy.tools
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules import Module


LOG = logging.getLogger(__name__)


class ModuleProvider(ABC):
    """This interface class defines all methods necessary to provide a list of
    instances of modules that implement the Module API, which is required in
    order for the instances to be executed by the main LatexBuddy instance."""

    @abstractmethod
    def load_selected_modules(self, cfg: ConfigLoader) -> list[Module]:
        """This method loads every module that is found in the ModuleLoader's
        directory and only returns instances of modules that are enabled in the
        specified configuration context.

        :param cfg: ConfigLoader instance containing config options for
                    enabled/disabled tools
        :return: a list of instances of classes implementing the Module
                 API which have been enabled in the specified
                 configuration context
        """


class ModuleLoader(ModuleProvider):
    """This class encapsulates all features necessary to load LaTeXBuddy
    modules from a specified directory."""

    def __init__(self, directory: Path):
        """Initializes the ModuleLoader for a specific directory.

        :param directory: the path of the directory to load modules from
        """
        self.directory = directory

    def load_selected_modules(self, cfg: ConfigLoader) -> list[Module]:
        # importing this here to avoid circular import error
        from latexbuddy.buddy import LatexBuddy

        modules = self.load_modules()

        return [
            module
            for module in modules
            if cfg.get_config_option_or_default(
                module,
                "enabled",
                cfg.get_config_option_or_default(
                    LatexBuddy,
                    "enable-modules-by-default",
                    default_value=True,
                ),
            )
        ]

    def load_modules(self) -> list[Module]:
        """This method loads every module that is found in the ModuleLoader's
        directory.

        :return: a list of instances of classes implementing the Module API
        """

        imported_py_modules = self.import_py_files()

        modules = []

        for module in imported_py_modules:

            classes = [
                cls_obj
                for cls_name, cls_obj
                in inspect.getmembers(module, inspect.isclass)
                if cls_obj.__module__ == module.__name__
                and Module in cls_obj.mro()
            ]

            for class_obj in classes:
                modules.append(class_obj())

        return modules

    def import_py_files(self) -> list[ModuleType]:
        """This method loads a python module from the specified file path for a
        list of file paths.

        :return: a list of python modules ready to be used
        """

        py_files = self.find_py_files()
        sys.path.append(str(self.directory))

        loaded_modules = []

        def make_lambda(file: Path) -> Callable[[], None]:
            def lambda_function() -> None:
                module_path = str(file.stem)

                LOG.debug(
                    f"Attempting to load module from '{module_path}'",
                )
                module = importlib.import_module(module_path)

                loaded_modules.append(module)
            return lambda_function

        for py_file in py_files:
            latexbuddy.tools.execute_no_exceptions(
                make_lambda(py_file),
                f"An error occurred while loading module file at "
                f"{str(py_file)}",
            )

        return loaded_modules

    def find_py_files(self) -> list[Path]:
        """This method finds all .py files within the ModuleLoader's directory
        or any subdirectories and returns a list of their paths.

        :return: a list of all Python files in the ModuleLoader's
                 directory (or subfolders)
        """

        if not self.directory.is_dir():
            LOG.warning(
                f"{str(self.directory.resolve())} is not a directory. "
                f"No modules could be loaded.",
            )
            return []

        LOG.debug(
            f"Searching for Python files inside "
            f"'{str(self.directory.resolve())}'",
        )

        files = sorted(self.directory.rglob("*.py"))

        LOG.debug(
            f"Found the following .py-files in directory "
            f"'{str(self.directory.resolve())}': {str(files)}",
        )

        return files
