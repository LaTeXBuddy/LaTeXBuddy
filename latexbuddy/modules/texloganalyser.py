import re

import latexbuddy.tools as tools

from typing import List
from pathlib import Path
from latexbuddy.modules import Module
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.problem import Problem, ProblemSeverity
from latexbuddy.texfile import TexFile
from latexbuddy import __logger as root_logger
from latexbuddy.messages import not_found
from tempfile import mkdtemp, mkstemp

# ^Page \d+: (Overfull \\hbox .* in paragraph at lines (\d+--\d+))$

warning_line_re = re.compile(r'^.*(?P<severity>Warning|Error):\s(?P<error>.*)$')
faulty_box_re = re.compile(r'(?P<error>(Under|Over)full.*)')
lineno_re = re.compile(r'on input line (?P<lineno>\d+)\.$')
box_lineno_re = re.compile(r'at lines (?P<lineno>\d+)--\d+$')


class TexLogAnalyser(Module):
    __logger = root_logger.getChild('texloganalyser.pl')

    def __init__(self):
        self.tool_name = "texloganalyser"

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:
        try:
            tools.find_executable('perl')
        except FileNotFoundError:
            self.__logger.error(not_found('perl', 'Perl'))

        log_path, pdf_path = tools.compile_tex(self, file.tex_file)
        warning_problems = self.check_warnings(log_path, file)
        return warning_problems

    def check_warnings(self, log_path: Path, file: TexFile) -> List[Problem]:
        problems = []
        raw_output = tools.execute('texloganalyser', '-wpnhv',
                                   str(log_path)).splitlines()
        i = 0
        for line in raw_output:
            print(i, line)
            i += 1
            self.__logger.debug(f"Processing line: {line}")
            warning_match = warning_line_re.match(line)
            if warning_match:
                raw_error = warning_match.group("error")

                lineno_match = lineno_re.match(raw_error)
            else:
                faulty_box_match = faulty_box_re.match(line)

                if not faulty_box_match:
                    continue

                raw_error = faulty_box_match.group("error")

                lineno_match = box_lineno_re.match(raw_error)

            if lineno_match:
                lineno = int(lineno_match.group("lineno"))
            else:
                lineno = None

            problem_text = raw_error.rsplit('on input line', 1)[0].strip()
            position = (lineno, 0) if lineno else (0, 0)  # TODO: Change to None
            severity_str = warning_match.group(
                "severity").upper() if warning_match else "ERROR"
            severity = ProblemSeverity[severity_str]

            problem = Problem(
                position=position,  # TODO: update type if None
                text=problem_text,
                checker=self.tool_name,
                p_type="warning",  # TODO
                file=file.tex_file,
                severity=severity,
                category="latex",
                key=self.tool_name + '_' + 'warning'  # TODO
            )
            problems.append(problem)

        return problems
