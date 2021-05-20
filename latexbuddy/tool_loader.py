import importlib.util as importutil
import inspect
import sys
import traceback

from pathlib import Path
from typing import List

from latexbuddy.abs_module import Module


class ToolLoader:
    def __init__(self, directory: Path):
        self.directory = directory

    def load_modules(self) -> List[Module]:

        imported_py_files = ToolLoader.import_py_files(self.find_py_files())
        modules = []

        for module in imported_py_files:

            classes = [
                cls_obj
                for cls_name, cls_obj in inspect.getmembers(module, inspect.isclass)
                if cls_obj.__module__ == module.__name__ and Module in cls_obj.mro()
            ]

            for class_obj in classes:
                modules.append(class_obj())

        return modules

    @staticmethod
    def import_py_files(py_files: List[Path]) -> List:

        loaded_modules = []

        for py_file in py_files:

            try:

                spec = importutil.spec_from_file_location(py_file.stem, py_file)
                module = importutil.module_from_spec(spec)
                spec.loader.exec_module(module)

                loaded_modules.append(module)

            except Exception as e:

                print(
                    f"An error occurred while loading module file at "
                    f"'{str(py_file)}':\n",
                    f"{e.__class__.__name__}: {getattr(e, 'message', e)}",
                    file=sys.stderr,
                )
                traceback.print_exc(file=sys.stderr)

        return loaded_modules

    def find_py_files(self) -> List[Path]:

        if not self.directory.is_dir():
            return []

        return sorted(self.directory.rglob("*.py"))
