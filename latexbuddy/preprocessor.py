import re

from abc import ABC, abstractmethod
from typing import List, Optional, Type

from latexbuddy import TexFile
from latexbuddy import __logger as root_logger
from latexbuddy.problem import Problem, ProblemSeverity


# forward-declare
class ProblemFilter(ABC):
    pass


class Preprocessor:
    __logger = root_logger.getChild("Preprocessor")

    __COMMAND_PATTERN = re.compile(
        r"%(\s?)buddy (ignore-next|begin-ignore|end-ignore)( (\S+))*"
    )

    def __init__(self):
        self.filters: List[ProblemFilter] = []

    def parse_preprocessor_comments(self, file: TexFile):

        line_num = 0  # lines are 1-based
        for line in file.tex.splitlines():

            line_num += 1  # lines are 1-based

            if not Preprocessor.__COMMAND_PATTERN.match(line):
                continue

            args = re.sub(r"%(\s?)buddy ", "", line).split(" ")

            resulting_filter = self.__parse_cmd_args_to_filter(args, line_num)

            if resulting_filter is None:
                continue

            self.filters.append(resulting_filter)

    def __parse_cmd_args_to_filter(
        self, args: List[str], line: int
    ) -> Optional[ProblemFilter]:

        if len(args) < 1:
            return None

        command = args.pop(0)

        # % buddy begin-ignore [module[s] <module_class_name> [module_class_name ...] | severet[y|ies] <severity-level> [severity-level ...] | whitelist-key[s] <key> [key ...]]
        #   -> begins ignoring all problems (of a given module, severity level or with a given whitelist key)

        # % buddy end-ignore [module[s] <module_name> [module_name ...] | severet[y|ies] <severity-level> [severity-level ...] | whitelist-key[s] <key> [key ...]]
        #   -> ends ignoring all problems (of a given module, severity level or with a given whitelist key)

        if command == "ignore-next":
            # Syntax:
            # % buddy ignore-next [[1] line | <N> lines]

            if len(args) < 1:

                Preprocessor.__logger.debug(f"Created LineProblemFilter from line {line + 1} to {line + 1}")
                return LineProblemFilter(line + 1, line + 1)

            elif len(args) == 1 and not args[0].isnumeric() and args[0] == "line":

                Preprocessor.__logger.debug(f"Created LineProblemFilter from line {line + 1} to {line + 1}")
                return LineProblemFilter(line + 1, line + 1)

            elif len(args) == 2 and args[0].isnumeric() and (args[1] == "line" or args[1] == "lines"):

                Preprocessor.__logger.debug(
                    f"Created LineProblemFilter from line {line + 1} to {line + int(args[0])}"
                )

                return LineProblemFilter(line + 1, line + int(args[0]))

            else:
                Preprocessor.__logger.warning(
                    f"SyntaxError: Could not create ProblemFilter from comment in line {line}. "
                    f"Usage: buddy ignore-next [[1] line | <N> lines]"
                )
                return None

        elif command == "begin-ignore":
            # Syntax:
            # % buddy begin-ignore [
            #       module[s] <module_class_name> [module_class_name ...] |
            #       severit[y|ies] <severity-level> [severity-level ...] |
            #       whitelist-key[s] <key> [key ...]
            #   ]

            if len(args) < 1:

                open_ended_filter = self.__get_open_ended_filter(LineProblemFilter(0))

                if open_ended_filter is not None:
                    return None
                else:
                    return LineProblemFilter(line + 1)

            elif len(args) >= 2:

                category = args.pop(0)

                if category == "module" or category == "modules":

                    for module in args:

                        open_ended_filter = self.__get_open_ended_filter(ModuleProblemFilter(module, 0))

                        if open_ended_filter is not None:
                            return None
                        else:
                            return ModuleProblemFilter(module, line + 1)

                elif category == "severity" or category == "severities":

                    for severity in args:

                        try:
                            enum_severity = ProblemSeverity[severity.upper()]

                            open_ended_filter = self.__get_open_ended_filter(
                                SeverityProblemFilter(enum_severity, 0)
                            )

                            if open_ended_filter is not None:
                                return None
                            else:
                                return SeverityProblemFilter(enum_severity, line + 1)
                        except KeyError:
                            pass

                elif category == "whitelist-key" or category == "whitelist-keys":

                    pass

                else:
                    return None

            else:
                return None

        elif command == "end-ignore":

            return None

        else:
            return None

    def __get_open_ended_filter(self, reference_filter: ProblemFilter) -> Optional[ProblemFilter]:

        for f in self.filters:
            if f.end_line is None and f.custom_parameters_equal(reference_filter):
                return f

        return None

    def matches_preprocessor_filter(self, problem: Problem) -> bool:

        for f in self.filters:
            if f.match(problem):
                return False
        return True

    def apply_preprocessor_filter(self, problems: List[Problem]) -> List[Problem]:

        return list(filter(self.matches_preprocessor_filter, problems))


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

    def _match_line(self, problem: Problem) -> bool:

        if self.end_line is None:
            return self.start_line <= problem.position[0]
        else:
            return self.start_line <= problem.position[0] <= self.end_line

    @abstractmethod
    def match(self, problem: Problem) -> bool:
        pass

    @abstractmethod
    def custom_parameters_equal(self, other: ProblemFilter) -> bool:
        pass


class LineProblemFilter(ProblemFilter):
    def __init__(self, start_line: int, end_line: Optional[int] = None):
        super().__init__(start_line, end_line)

    def match(self, problem: Problem) -> bool:

        return self._match_line(problem)

    def custom_parameters_equal(self, other: ProblemFilter) -> bool:

        return type(other) == LineProblemFilter


class ModuleProblemFilter(ProblemFilter):
    def __init__(
        self, module_name: str, start_line: int, end_line: Optional[int] = None
    ):
        super().__init__(start_line, end_line)
        self.module_name = module_name

    def match(self, problem: Problem) -> bool:

        return self._match_line(problem) and problem.checker == self.module_name

    def custom_parameters_equal(self, other: ProblemFilter) -> bool:

        return type(other) == ModuleProblemFilter and other.module_name == self.module_name


class SeverityProblemFilter(ProblemFilter):
    def __init__(
        self, severity: ProblemSeverity, start_line: int, end_line: Optional[int] = None
    ):
        super().__init__(start_line, end_line)
        self.severity = severity

    def match(self, problem: Problem) -> bool:

        return self._match_line(problem) and problem.severity == self.severity

    def custom_parameters_equal(self, other: ProblemFilter) -> bool:

        return type(other) == SeverityProblemFilter and other.severity == self.severity


class WhitelistKeyProblemFilter(ProblemFilter):
    def __init__(self, wl_key: str, start_line: int, end_line: Optional[int] = None):
        super().__init__(start_line, end_line)
        self.wl_key = wl_key

    def match(self, problem: Problem) -> bool:

        return self._match_line(problem) and problem.key == self.wl_key

    def custom_parameters_equal(self, other: ProblemFilter) -> bool:

        return type(other) == WhitelistKeyProblemFilter and other.wl_key == self.wl_key
