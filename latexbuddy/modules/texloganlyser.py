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
    __logger = root_logger.getChild('texloganalyser')

    def __init__(self):
        self.tool_name = "texloganalyser"
        self.tex_mf = ''

    def avoid_linebreak(self):
        """
        This method makes the log file be written correctly
        """
        # https://tex.stackexchange.com/questions/52988/avoid-linebreaks-in-latex-console-log-output-or-increase-columns-in-terminal
        # https://tex.stackexchange.com/questions/410592/texlive-personal-texmf-cnf
        text = ['max_print_line=1000', 'error_line=254', 'half_error_line=238']
        cnf_file = 'texmf.cnf'
        cnf_dir = os.getcwd()
        cnf_path = os.path.join(cnf_dir, cnf_file)
        for cfg in text:
            tools.execute(f'{cfg} >> {cnf_path}')
        self.tex_mf = cnf_dir

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:
        try:
            tools.find_executable('perl')
        except FileNotFoundError:
            self.__logger.error(not_found('perl', 'perl'))

        logfile = self.compile_tex(file.tex_file)
        self.avoid_linebreak()
        problems = []
        font_problems = self.check_fonts(logfile)
        for problem in font_problems:
            problems.append(problem)
        return problems

    def check_fonts(self, logfile) -> List[Problem]:
        raw_output = tools.execute().split('\n')
        return []

    def compile_tex(self, tex_file: Path) -> Path:
        try:
            tools.find_executable('latex')
        except FileNotFoundError:
            self.__logger.error(not_found('latex', 'texlive-core'))

        directory = 'texlogs'
        path = os.path.join(os.getcwd(), directory)
        os.mkdir(path)
        tools.execute_background(f'export TEXMFCNF="{self.tex_mf}";', 'latex',
                                 str(tex_file), f'-output-directory={path}')
        return Path(os.path.join(path, tex_file.stem + '.log'))
