from typing import List

import proselint

from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules import Module
from latexbuddy.problem import Problem, ProblemSeverity
from latexbuddy.texfile import TexFile


class ProseLint(Module):
    def __init__(self):

        self.tool_name = "ProseLintModule"
        self.problem_type = "grammar"

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:

        lang = config.get_config_option_or_default(LatexBuddy, "language", None)

        if lang != "en":
            self.logger.info("Proselint only supports documents written in English.")
            return []

        suggestions = proselint.tools.lint(file.plain)

        result = self.format_errors(suggestions, file)

        return result

    def format_errors(self, suggestions: List, file: TexFile):
        problems = []
        for suggestion in suggestions:
            p_type = suggestion[0]
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
            key = self.tool_name + delimiter + p_type
            problems.append(
                Problem(
                    position=position,
                    text=text,
                    checker=ProseLint,
                    p_type=p_type,
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
