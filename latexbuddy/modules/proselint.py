from typing import List

import proselint

from latexbuddy import __logger as root_logger
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules import Module
from latexbuddy.problem import Problem, ProblemSeverity
from latexbuddy.texfile import TexFile


class ProseLintModule(Module):
    __logger = root_logger.getChild("ProseLintModule")

    def __init__(self):
        self.tool_name = "proselint"
        self.problem_type = "grammar"

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:

        lang = config.get_config_option_or_default("buddy", "language", None)

        if lang != "en":
            return []

        suggestions = proselint.tools.lint(file.plain)

        result = self.format_errors(suggestions, file)

        return result

    def format_errors(self, suggestions: List, file: TexFile):
        problems = []
        for suggestion in suggestions:
            cid = suggestion[0]
            description = suggestion[1]
            # line, col = (suggestion[2] + 1, suggestion[3] + 1)
            start_char = suggestion[4] - 1
            position = file.get_position_in_tex(start_char)
            length = suggestion[6]
            text = self.get_text(start_char, length, file)
            severity_map = {
                "warning": ProblemSeverity.WARNING,
                "error": ProblemSeverity.ERROR,
                "suggestion": ProblemSeverity.INFO,
            }
            severity = severity_map[suggestion[7]]
            replacements = suggestion[8]
            if replacements is None:
                replacements = []
            delimiter = "_"
            key = self.tool_name + delimiter + cid
            problems.append(
                Problem(
                    position=position,
                    text=text,
                    checker=self.tool_name,
                    cid=cid,
                    file=file.tex_file,
                    severity=severity,
                    category=self.problem_type,
                    description=description,
                    suggestions=replacements,
                    key=key,
                    length=length,
                )
            )
        return problems

    @staticmethod
    def get_text(start_char: int, length: int, file: TexFile):
        text = file.plain
        return text[start_char : start_char + length]
