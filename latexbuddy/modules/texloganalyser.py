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
from tempfile import mkdtemp


class TexLogAnalyser(Module):
    __logger = root_logger.getChild('texloganalyser.pl')

    def __init__(self):
        self.tool_name = "texloganalyser.pl"
        self.tex_mf = ''

    def avoid_linebreak(self):
        """
        This method makes the log file be written correctly
        """
        # https://tex.stackexchange.com/questions/52988/avoid-linebreaks-in-latex-console-log-output-or-increase-columns-in-terminal
        # https://tex.stackexchange.com/questions/410592/texlive-personal-texmf-cnf
        text = '\n'.join(['max_print_line=1000', 'error_line=254', 'half_error_line=238'])
        cnf_file = 'texmf.cnf'
        cnf_dir = mkdtemp(prefix='texloganalyser.pl')
        cnf_path = Path(cnf_dir)/cnf_file
        cnf_path.write_text(text)
        self.tex_mf = cnf_dir

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:
        try:
            tools.find_executable('perl')
        except FileNotFoundError:
            self.__logger.error(not_found('perl', 'perl'))

        logfile = self.compile_tex(file.tex_file)
        self.avoid_linebreak()
        problems = []
        warning_problems = self.check_warnings(logfile, file)
        for problem in warning_problems:
            problems.append(problem)
        return problems

    def check_warnings(self, logfile) -> List[Problem]:
        problems = []
        raw_output = tools.execute('texloganalyser', '-wpn', logfile).splitlines()
        for line in raw_output:
            warning_match = warning_line_re.match(line)
            if warning_match:
                raw_error = warning_match.group("error")
            else:
                faulty_box_match = faulty_box_re.match(line)

                if not faulty_box_match:
                    continue

            raw_error = faulty_box_match.group("error")
            lineno_match = lineno_re.match(raw_error)
            if lineno_match:
                lineno = int(lineno_match.group("lineno"))
            else:
                lineno = None

            problem_text = raw_error.rsplit('on input line', 1)[0].strip()
            position = (lineno, None) if lineno else None

            problem = Problem(
                position=position,
                text=problem_text,
                checker="texloganalyser",
                cid="",  # TODO
                file=self.

            )
            problems.append(problem)

        return []

    def compile_tex(self, tex_file: Path) -> Path:
        try:
            tools.find_executable('latex')
        except FileNotFoundError:
            self.__logger.error(not_found('latex', 'texlive-core'))

        directory = 'texlogs'
        path = os.path.join(os.getcwd(), directory)
        os.mkdir(path)
        tools.execute_background(f'TEXMFCNF="{self.tex_mf}";', 'latex',
                                 str(tex_file), f'-output-directory={path}')
        return Path(os.path.join(path, tex_file.stem + '.log'))
