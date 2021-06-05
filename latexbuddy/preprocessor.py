import re

from abc import ABC, abstractmethod
from typing import List, Optional

from latexbuddy import TexFile
from latexbuddy.problem import Problem, ProblemSeverity


class ProblemFilter(ABC):
    def __init__(self, start_line: int, end_line: Optional[int] = None):
        self.start_line = start_line
        self.end_line = end_line

    def end(self, end_line: int) -> bool:

        if self.end_line is None:
            self.end_line = end_line
            return True
        else:
            return False

    def __match_line(self, problem: Problem) -> bool:

        if self.end_line is None:
            return self.start_line <= problem.position[0]
        else:
            return self.start_line <= problem.position[0] <= self.end_line

    @abstractmethod
    def match(self, problem: Problem) -> bool:
        pass


class Preprocessor:
    def __init__(self):
        self.filters: List[ProblemFilter] = []

    command_pattern = re.compile(
        "%(\\s?)buddy\\s(ignore-next|begin-ignore|end-ignore)(\\s(\\S)+)*(\\s*)"
    )

    def parse_preprocessor_comments(self, file: TexFile):

        line_num = 1
        for line in file.tex.splitlines():

            if Preprocessor.command_pattern.match(line):
                pass

            line_num += 1

    def matches_preprocessor_filter(self, problem: Problem) -> bool:

        for f in self.filters:
            if f.match(problem):
                return False
        return True

    def apply_preprocessor_filter(self, problems: List[Problem]) -> List[Problem]:

        return list(filter(self.matches_preprocessor_filter, problems))


class LineProblemFilter(ProblemFilter):
    def __init__(self, start_line: int, end_line: Optional[int] = None):
        super().__init__(start_line, end_line)

    def match(self, problem: Problem) -> bool:

        return self.__match_line(problem)


class ModuleProblemFilter(ProblemFilter):
    def __init__(
        self, module_name: str, start_line: int, end_line: Optional[int] = None
    ):
        super().__init__(start_line, end_line)
        self.module_name = module_name

    def match(self, problem: Problem) -> bool:

        return self.__match_line(problem) and problem.checker == self.module_name


class SeverityProblemFilter(ProblemFilter):
    def __init__(
        self, severity: ProblemSeverity, start_line: int, end_line: Optional[int] = None
    ):
        super().__init__(start_line, end_line)
        self.severity = severity

    def match(self, problem: Problem) -> bool:

        return self.__match_line(problem) and problem.severity == self.severity


class WhitelistKeyProblemFilter(ProblemFilter):
    def __init__(self, wl_key: str, start_line: int, end_line: Optional[int] = None):
        super().__init__(start_line, end_line)
        self.wl_key = wl_key

    def match(self, problem: Problem) -> bool:

        return self.__match_line(problem) and problem.key == self.wl_key


# % buddy ignore-next [[1] line | <N> lines]
#   -> ignores all problems in the given line(s)

# % buddy begin-ignore [module[s] <module_class_name> [module_class_name ...] | severet[y|ies] <severity-level> [severity-level ...] | whitelist-key[s] <key> [key ...]]
#   -> begins ignoring all problems (of a given module, severity level or with a given whitelist key)

# % buddy end-ignore [module[s] <module_name> [module_name ...] | severet[y|ies] <severity-level> [severity-level ...] | whitelist-key[s] <key> [key ...]]
#   -> ends ignoring all problems (of a given module, severity level or with a given whitelist key)
