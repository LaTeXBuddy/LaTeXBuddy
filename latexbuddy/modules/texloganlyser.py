import latexbuddy.tools as tools
import os

from typing import List
from pathlib import Path
from latexbuddy.modules import Module
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.problem import Problem, ProblemSeverity
from latexbuddy.texfile import TexFile
from latexbuddy import __logger as root_logger
from latexbuddy.messages import not_found


class TexLogAnalyser(Module):

    def __init__(self):
        self.tool_name = "texloganalyser"

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:
        return []

    def compile_tex(self, tex_file: Path) -> Path:
        try:
            tools.find_executable('latex')
        except FileNotFoundError:
            self.__logger.error(not_found('latex', 'texlive-core'))

        directory = 'texlogs'
        path = os.path.join(os.getcwd(), directory)
        os.mkdir(path)
        tools.execute_background('latex', str(tex_file), f'-output-directory={path}')
        return Path(os.path.join(path, tex_file.stem + '.log'))
