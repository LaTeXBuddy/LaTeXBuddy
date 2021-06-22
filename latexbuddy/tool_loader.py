import importlib
import importlib.util as importutil
import inspect

from pathlib import Path
from types import ModuleType
from typing import List

import latexbuddy.tools as tools

from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules import Module


class ToolLoader:
    """This class encapsulates all features necessary to load LaTeXBuddy modules from
    a specified directory."""

    def __init__(self, directory: Path):
        """Initializes the ToolLoader for a specific directory.

        :param directory: the path of the directory to load tools from
        """
        self.directory = directory

    def load_modules(self) -> List[Module]:
        """This method loads every module that is found in the ToolLoader's directory.

        :return: a list of instances of classes implementing the Module API
        """

        imported_py_modules = ToolLoader.import_py_files(self.find_py_files())
        modules = []

        for module in imported_py_modules:

            classes = [
                cls_obj
                for cls_name, cls_obj in inspect.getmembers(module, inspect.isclass)
                if cls_obj.__module__ == module.__name__ and Module in cls_obj.mro()
            ]

            for class_obj in classes:
                modules.append(class_obj())

        return modules

    def load_selected_modules(self, cfg: ConfigLoader) -> List[Module]:
        """This method loads every module that is found in the ToolLoader's directory
            and only returns instances of modules that are enabled in the specified
            configuration context.

        :param cfg: ConfigLoader instance containing config options for
                    enabled/disabled tools
        :return: a list of instances of classes implementing the Module API which have
                 been enabled in the specified configuration context
        """

        modules = self.load_modules()

        selected = [
            module
            for module in modules
            if cfg.get_config_option_or_default(
                module.__class__.__name__,
                "enabled",
                cfg.get_config_option_or_default(
                    "buddy", "enable-modules-by-default", True
                ),
            )
        ]

        return selected

    @staticmethod
    def import_py_files(py_files: List[Path]) -> List[ModuleType]:
        """This method loads a python module from the specified file path for a list
            of file paths.

        :param py_files: python module files to be loaded
        :return: a list of python modules ready to be used
        """

        loaded_modules = []

        for py_file in py_files:

            def lambda_function() -> None:

                module_path = str(py_file.with_suffix("")).replace("/", ".")
                module = importlib.import_module(module_path)

                loaded_modules.append(module)

            tools.execute_no_exceptions(
                lambda_function,
                f"An error occurred while loading module file at {str(py_file)}",
            )

        return loaded_modules

    def find_py_files(self) -> List[Path]:
        """This method finds all .py files within the ToolLoader's directory or any
            subdirectories and returns a list of their paths.

        :return: a list of all .py files in the ToolLoader's directory (or subfolders)
        """

        if not self.directory.is_dir():
            return []

        return sorted(self.directory.rglob("*.py"))
