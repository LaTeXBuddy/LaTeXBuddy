import re

from abc import ABC, abstractmethod
from typing import List, Optional, Callable

from latexbuddy import TexFile
from latexbuddy import __logger as root_logger
from latexbuddy.problem import Problem, ProblemSeverity


# forward-declare
class ProblemFilter(ABC):
    """forward-declaring ProblemFilter because type hints will break otherwise"""
    pass


class ProblemFilter(ABC):
    """
    Describes the base class for any filter for Problem objects.
    ProblemFilter provides functionality to define a start and end line and to match a
    problem based on its line position.

    ProblemFilters can be created open-ended by omitting the end_line parameter
    resulting in the filter matching any Problem located at or below the start line.
    Open-ended filters can later be closed by supplying an end line to the end() method.

    For more diverse filters ProblemFilter provides the following abstract methods which
    must be implemented by all subclasses:

        - custom_match: Matches a problem based on custom parameters. This method is
                        only called, if a given problem is located within the filter's
                        line boundaries

        - custom_parameters_equal: determines whether another custom filter is of the
                                   same type and has all equal custom parameters as the
                                   current one
    """

    def __init__(self, start_line: int, end_line: Optional[int] = None):
        """
        Initializes a new ProblemFilter with a start_line and possibly an end_line.

        :param start_line: beginning of the filter's area
        :param end_line: end of the filter's area (open-ended, if omitted)
        """
        self.start_line = start_line
        self.end_line = end_line

    def end(self, end_line: int) -> bool:
        """
        Sets the end line of ProblemFilter, if not already done.

        :param end_line: line number of the filter's end
        :return: true if end_line was set; false otherwise
        """
        if self.end_line is None:
            self.end_line = end_line
            return True
        else:
            return False

    def __match_line(self, problem: Problem) -> bool:
        """
        Determines, whether a given problem is located within the ProblemFilter's
        line boundaries.

        :param problem: Problem object to examine
        :return: True, if the problem is located in the area covered by the
                 ProblemFilter, False otherwise
        """

        if self.end_line is None:
            return self.start_line <= problem.position[0]
        else:
            return self.start_line <= problem.position[0] <= self.end_line

    def match(self, problem: Problem) -> bool:
        """
        Determines, whether a given problem is located within the ProblemFilter's
        line boundaries and matches all custom requirements that the subclass
        implementation imposes.

        :param problem: Problem object to examine
        :return: True, if the problem is located in the area covered by the
                 ProblemFilter and matches all custom requirements, False otherwise
        """

        return self.__match_line(problem) and self.custom_match(problem)

    @abstractmethod
    def custom_match(self, problem: Problem) -> bool:
        """
        Matches a given Problem object based on custom parameters of the subclass
        implementation.

        :param problem: Problem object to be examined
        :return: True, if the problem matches all custom requirements, False otherwise
        """
        pass

    @abstractmethod
    def custom_parameters_equal(self, other: ProblemFilter) -> bool:
        """
        Determines, if two custom ProblemFilters are:
            - of the same type
            - equal in terms of their custom parameters

        This method explicitly DOES NOT CHECK the equality of start_line and end_line!

        :param other: second custom ProblemFilter to be compared with the current one
        :return: True, if the other custom ProblemFilter is equal to the current one
                 with respect to its type and custom parameters, False otherwise
        """
        pass


class LineProblemFilter(ProblemFilter):
    """
    ProblemFilter implementation that only considers a problem's line position.
    """

    def __init__(self, start_line: int, end_line: Optional[int] = None):
        """
        Initializes a new LineProblemFilter with no custom parameters.

        :param start_line: beginning of the filter's area
        :param end_line: end of the filter's area
        """

        super().__init__(start_line, end_line)

    def custom_match(self, problem: Problem) -> bool:

        return True

    def custom_parameters_equal(self, other: ProblemFilter) -> bool:

        return type(other) == LineProblemFilter


class ModuleProblemFilter(ProblemFilter):
    """
    ProblemFilter implementation that filters problems, if they have been created by a
    specified LaTeXBuddy module.
    """

    def __init__(
        self, module_name: str, start_line: int, end_line: Optional[int] = None
    ):
        """
        Initializes a new ModuleProblemFilter with a string representation of a module
        name as its custom parameter.

        :param module_name: name of the module which created a problem object
        :param start_line: beginning of the filter's area
        :param end_line: end of the filter's area
        """

        super().__init__(start_line, end_line)
        self.module_name = module_name

    def custom_match(self, problem: Problem) -> bool:

        return problem.checker == self.module_name

    def custom_parameters_equal(self, other: ProblemFilter) -> bool:

        return (
            type(other) == ModuleProblemFilter and other.module_name == self.module_name
        )


class SeverityProblemFilter(ProblemFilter):
    """
    ProblemFilter implementation that filters problems, if they have been created with a
    specified ProblemSeverity.
    """

    def __init__(
        self, severity: ProblemSeverity, start_line: int, end_line: Optional[int] = None
    ):
        """
        Initializes a new SeverityProblemFilter with a string representation of a
        ProblemSeverity level as its custom parameter.

        :param severity: ProblemSeverity level of a problem
        :param start_line: beginning of the filter's area
        :param end_line: end of the filter's area
        """

        super().__init__(start_line, end_line)
        self.severity = severity

    def custom_match(self, problem: Problem) -> bool:

        return problem.severity == self.severity

    def custom_parameters_equal(self, other: ProblemFilter) -> bool:

        return type(other) == SeverityProblemFilter and other.severity == self.severity


class WhitelistKeyProblemFilter(ProblemFilter):
    """
    WhitelistKeyProblemFilter implementation that filters problems, if they have been
    created with a specified whitelist key.
    """

    def __init__(self, wl_key: str, start_line: int, end_line: Optional[int] = None):
        """
        Initializes a new WhitelistKeyProblemFilter with a whitelist key as its custom
        parameter.

        :param wl_key: whitelist key of a problem
        :param start_line: beginning of the filter's area
        :param end_line: end of the filter's area
        """

        super().__init__(start_line, end_line)
        self.wl_key = wl_key

    def custom_match(self, problem: Problem) -> bool:

        return problem.key == self.wl_key

    def custom_parameters_equal(self, other: ProblemFilter) -> bool:

        return type(other) == WhitelistKeyProblemFilter and other.wl_key == self.wl_key


class Preprocessor:
    """
    This class represents the LaTeXBuddy in-file preprocessor.
    the Preprocessor is capable of parsing buddy commands disguised as LaTeX comments
    from a TexFile object using regexes and is able to filter any given Problem or list
    of Problems accordingly.
    """

    __logger = root_logger.getChild("Preprocessor")

    __COMMAND_PATTERN = re.compile(
        r"%\s?buddy (ignore-next|begin-ignore|end-ignore)( (\S+))*"
    )

    __COMMAND_PATTERN_IGNORE_NEXT_ONE_LINE = re.compile(
        r"%\s?buddy ignore-next(?:(?: 1)? line)?"
    )
    __COMMAND_PATTERN_IGNORE_NEXT_N_LINES = re.compile(
        r"%\s?buddy ignore-next (\d+) lines"
    )

    __COMMAND_PATTERN_BEGIN_IGNORE_ANYTHING = re.compile(r"%\s?buddy begin-ignore")
    __COMMAND_PATTERN_BEGIN_IGNORE_MODULES = re.compile(
        r"%\s?buddy begin-ignore (modules?)((?: \S+)+)"
    )
    __COMMAND_PATTERN_BEGIN_IGNORE_SEVERITIES = re.compile(
        r"%\s?buddy begin-ignore (?:severity|severities)((?: \S+)+)"
    )
    __COMMAND_PATTERN_BEGIN_IGNORE_WL_KEYS = re.compile(
        r"%\s?buddy begin-ignore (whitelist-keys?)((?: \S+)+)"
    )

    __COMMAND_PATTERN_END_IGNORE_ANYTHING = re.compile(r"%\s?buddy end-ignore")
    __COMMAND_PATTERN_END_IGNORE_MODULES = re.compile(
        r"%\s?buddy end-ignore (modules?)((?: \S+)+)"
    )
    __COMMAND_PATTERN_END_IGNORE_SEVERITIES = re.compile(
        r"%\s?buddy end-ignore (?:severity|severities)((?: \S+)+)"
    )
    __COMMAND_PATTERN_END_IGNORE_WL_KEYS = re.compile(
        r"%\s?buddy end-ignore (whitelist-keys?)((?: \S+)+)"
    )

    def __init__(self):
        """
        Initializes a new Preprocessor instance with an empty list of filters.
        """

        self.filters: List[ProblemFilter] = []

    def regex_parse_preprocessor_comments(self, file: TexFile) -> None:
        """
        This method takes in a TexFile object and parses all contained preprocessor
        commands resulting in a set of ProblemFilters which are added to this instance's
        list of filters to be applied to any given problem.

        :param file: TexFile object containing the LaTeX sourcecode to be parsed
        """

        line_num = 0  # lines are 1-based
        for line in file.tex.splitlines():

            line_num += 1  # lines are 1-based

            if not Preprocessor.__COMMAND_PATTERN.fullmatch(line):
                continue

            resulting_filters = self.__regex_parse_cmd_args_to_filter(line, line_num)

            for resulting_filter in resulting_filters:
                self.filters.append(resulting_filter)

    def __regex_parse_cmd_args_to_filter(
        self, line: str, line_num: int
    ) -> List[ProblemFilter]:
        """
        Parses a single preprocessor command resulting in a list of zero or more
        ProblemFilters which are returned.

        :param line: the LaTeX code line which contains the preprocessor command to be
                     parsed
        :param line_num: line number of the LaTeX code line to be parsed
        :return: a list of zero or more ProblemFilters resulting from the preprocessor
                 command
        """

        matchers: List[Callable[[str, int], Optional[List[ProblemFilter]]]] = [
            self.__regex_match_command_pattern_ignore_next_one_line,
            self.__regex_match_command_pattern_ignore_next_n_lines,
            self.__regex_match_command_pattern_begin_ignore_anything,
            self.__regex_match_command_pattern_begin_ignore_modules,
            self.__regex_match_command_pattern_begin_ignore_severities,
            self.__regex_match_command_pattern_begin_ignore_wl_keys,
            self.__regex_match_command_pattern_end_ignore_anything,
            self.__regex_match_command_pattern_end_ignore_modules,
            self.__regex_match_command_pattern_end_ignore_severities,
            self.__regex_match_command_pattern_end_ignore_wl_keys,
        ]

        for matcher in matchers:

            match = matcher(line, line_num)
            if match is not None:
                return match

        Preprocessor.__logger.warning(
            f"Invalid Syntax: Could not parse preprocessing command "
            f"in line {line_num}: \n{line}"
        )
        return []

    def __regex_match_command_pattern_ignore_next_one_line(
        self, line: str, line_num: int
    ) -> Optional[List[ProblemFilter]]:
        """
        Checks, if the provided command matches the regex pattern
        and creates LineProblemFilters beginning and ending at line_num + 1.

        :param line: inserted command from .tex file
        :param line_num: line number of command occurrence
        :return: LineProblemFilter as a list, None if regex not matching
        """

        match = Preprocessor.__COMMAND_PATTERN_IGNORE_NEXT_ONE_LINE.fullmatch(line)
        if match is not None:
            Preprocessor.__logger.debug(
                f"Created LineProblemFilter from line {line_num + 1} to {line_num + 1}"
            )
            return [LineProblemFilter(line_num + 1, line_num + 1)]

        return None

    def __regex_match_command_pattern_ignore_next_n_lines(
        self, line: str, line_num: int
    ) -> Optional[List[ProblemFilter]]:
        """
        Checks, if the provided command matches the regex pattern
        and creates a LineProblemFilter beginning at line_num + 1
        and ending at line_num + n.
        The number of lines to ignore (n) is drawn from the command.

        :param line: inserted command from .tex file
        :param line_num: line number of command occurrence
        :return: LineProblemFilter as a list, None if regex not matching
        """

        match = Preprocessor.__COMMAND_PATTERN_IGNORE_NEXT_N_LINES.fullmatch(line)
        if match is not None:
            n = int(match.group(1))
            Preprocessor.__logger.debug(
                f"Created LineProblemFilter from line {line_num + 1} to {line_num + n}"
            )
            return [LineProblemFilter(line_num + 1, line_num + n)]

        return None

    def __regex_match_command_pattern_begin_ignore_anything(
        self, line: str, line_num: int
    ) -> Optional[List[ProblemFilter]]:
        """
        Checks, if the provided command matches the regex pattern
        and creates a LineProblemFilter beginning at line_num + 1.

        :param line: inserted command from .tex file
        :param line_num: line number of command occurrence
        :return: open-ended LineProblemFilter as a list, None if regex not matching
        """

        match = Preprocessor.__COMMAND_PATTERN_BEGIN_IGNORE_ANYTHING.fullmatch(line)
        if match is not None:

            open_ended_filter = self.__get_open_ended_filter(LineProblemFilter(0))

            if open_ended_filter is not None:
                Preprocessor.__logger.info(
                    f"Ignored duplicate command 'begin-ignore' in line {line_num}"
                )
                return []
            else:
                Preprocessor.__logger.debug(
                    f"Created open-ended LineProblemFilter "
                    f"beginning in line {line_num + 1}"
                )
                return [LineProblemFilter(line_num + 1)]

        return None

    def __regex_match_command_pattern_begin_ignore_modules(
        self, line: str, line_num: int
    ) -> Optional[List[ProblemFilter]]:
        """
        Checks, if the provided command matches the regex pattern
        and creates ModuleProblemFilters corresponding to the provided
        module names beginning at line_num + 1.

        :param line: inserted command from .tex file
        :param line_num: line number of command occurrence
        :return: list of open-ended ModuleProblemFilters to match the provided modules,
                None if regex not matching
        """

        match = Preprocessor.__COMMAND_PATTERN_BEGIN_IGNORE_MODULES.fullmatch(line)
        if match is not None:
            modules = match.group(1).strip().split(" ")

            filters = []
            for module in modules:

                open_ended_filter = self.__get_open_ended_filter(
                    ModuleProblemFilter(module, 0)
                )

                if open_ended_filter is not None:
                    Preprocessor.__logger.info(
                        f"Ignored duplicate command 'begin-ignore' "
                        f"for module '{module}' in line {line_num}"
                    )
                else:
                    Preprocessor.__logger.debug(
                        f"Created open-ended ModuleProblemFilter "
                        f"for module '{module}' beginning in line {line_num + 1}"
                    )
                    filters.append(ModuleProblemFilter(module, line_num + 1))

            return filters

        return None

    def __regex_match_command_pattern_begin_ignore_severities(
        self, line: str, line_num: int
    ) -> Optional[List[ProblemFilter]]:
        """
        Checks, if the provided command matches the regex pattern
        and creates SeverityProblemFilters corresponding to the provided severities
        beginning at line_num + 1.

        :param line: inserted command from .tex file
        :param line_num: line number of command occurrence
        :return: list of open-ended SeverityProblemFilters
                 to match the provided severities, None if regex not matching
        """

        match = Preprocessor.__COMMAND_PATTERN_BEGIN_IGNORE_SEVERITIES.fullmatch(line)
        if match is not None:
            severities = match.group(1).strip().split(" ")

            filters = []
            for severity in severities:

                try:
                    enum_severity = ProblemSeverity[severity.upper()]

                    open_ended_filter = self.__get_open_ended_filter(
                        SeverityProblemFilter(enum_severity, 0)
                    )

                    if open_ended_filter is not None:
                        Preprocessor.__logger.info(
                            f"Ignored duplicate command 'begin-ignore' "
                            f"for severity '{severity}' in line {line_num}"
                        )
                    else:
                        Preprocessor.__logger.debug(
                            f"Created open-ended ModuleProblemFilter for severity "
                            f"'{str(enum_severity)}' beginning in line {line_num + 1}"
                        )
                        filters.append(
                            SeverityProblemFilter(enum_severity, line_num + 1)
                        )
                except KeyError:
                    Preprocessor.__logger.warning(
                        f"Invalid syntax: Unknown ProblemSeverity '{severity}' "
                        f"in line {line_num}"
                    )

            return filters

        return None

    def __regex_match_command_pattern_begin_ignore_wl_keys(
        self, line: str, line_num: int
    ) -> Optional[List[ProblemFilter]]:
        """
        Checks, if the provided command matches the regex pattern
        and creates WhitelistKeyProblemFilters corresponding to the provided
        whitelist keys beginning at line_num + 1.

        :param line: inserted command from .tex file
        :param line_num: line number of command occurrence
        :return: list of open-ended WhitelistKeyProblemFilters
                 to match the provided whitelist keys, None if regex not matching
        """

        match = Preprocessor.__COMMAND_PATTERN_BEGIN_IGNORE_WL_KEYS.fullmatch(line)
        if match is not None:
            keys = match.group(1).strip().split(" ")

            filters = []
            for key in keys:

                open_ended_filter = self.__get_open_ended_filter(
                    WhitelistKeyProblemFilter(key, 0)
                )

                if open_ended_filter is not None:
                    Preprocessor.__logger.info(
                        f"Ignored duplicate command 'begin-ignore' "
                        f"for whitelist-key '{key}' in line {line_num}"
                    )
                else:
                    Preprocessor.__logger.debug(
                        f"Created open-ended WhitelistKeyProblemFilter "
                        f"for whitelist-key '{key}' beginning in line {line_num + 1}"
                    )
                    filters.append(WhitelistKeyProblemFilter(key, line_num + 1))

            return filters

        return None

    def __regex_match_command_pattern_end_ignore_anything(
        self, line: str, line_num: int
    ) -> Optional[List[ProblemFilter]]:
        """
        Checks, if the provided command (line) matches the regex pattern
        and sets the end line for the matching open-ended ProblemFilter.

        :param line: inserted command from .tex file
        :param line_num: line number of command occurrence
        :return: empty list, if successful; None otherwise
        """

        match = Preprocessor.__COMMAND_PATTERN_END_IGNORE_ANYTHING.fullmatch(line)
        if match is not None:

            open_ended_filter = self.__get_open_ended_filter(LineProblemFilter(0))

            if open_ended_filter is None:
                Preprocessor.__logger.info(
                    f"Ignored duplicate command 'end-ignore' in line {line_num}"
                )
            else:
                Preprocessor.__logger.debug(
                    f"Ended existing open-ended LineProblemFilter in line {line_num}"
                )
                open_ended_filter.end(line_num)

            return []

        return None

    def __regex_match_command_pattern_end_ignore_modules(
        self, line: str, line_num: int
    ) -> Optional[List[ProblemFilter]]:
        """
        Checks, if the provided command (line) matches the regex pattern
        and sets the end line for the matching open-ended ProblemFilter.

        :param line: inserted command from .tex file
        :param line_num: line number of command occurrence
        :return: empty list, if successful; None otherwise
        """

        match = Preprocessor.__COMMAND_PATTERN_END_IGNORE_MODULES.fullmatch(line)
        if match is not None:
            modules = match.group(1).strip().split(" ")

            for module in modules:

                open_ended_filter = self.__get_open_ended_filter(
                    ModuleProblemFilter(module, 0)
                )

                if open_ended_filter is None:
                    Preprocessor.__logger.info(
                        f"Ignored duplicate command 'end-ignore' for module '{module}' "
                        f"in line {line_num}"
                    )
                else:
                    Preprocessor.__logger.debug(
                        f"Ended existing open-ended ModuleProblemFilter "
                        f"for module '{module}' in line {line_num + 1}"
                    )
                    open_ended_filter.end(line_num)

            return []

        return None

    def __regex_match_command_pattern_end_ignore_severities(
        self, line: str, line_num: int
    ) -> Optional[List[ProblemFilter]]:
        """
        Checks, if the provided command (line) matches the regex pattern
        and sets the end line for the matching open-ended ProblemFilter.

        :param line: inserted command from .tex file
        :param line_num: line number of command occurrence
        :return: empty list, if successful; None otherwise
        """

        match = Preprocessor.__COMMAND_PATTERN_END_IGNORE_SEVERITIES.fullmatch(line)
        if match is not None:
            severities = match.group(1).strip().split(" ")

            for severity in severities:

                try:
                    enum_severity = ProblemSeverity[severity.upper()]

                    open_ended_filter = self.__get_open_ended_filter(
                        SeverityProblemFilter(enum_severity, 0)
                    )

                    if open_ended_filter is None:
                        Preprocessor.__logger.info(
                            f"Ignored duplicate command 'end-ignore' "
                            f"for severity '{severity}' in line {line_num}"
                        )
                    else:
                        Preprocessor.__logger.debug(
                            f"Ended existing open-ended SeverityProblemFilter for "
                            f"severity '{str(enum_severity)}' in line {line_num + 1}"
                        )
                        open_ended_filter.end(line_num)
                except KeyError:
                    Preprocessor.__logger.warning(
                        f"Invalid syntax: Unknown ProblemSeverity '{severity}' "
                        f"in line {line_num}"
                    )

            return []

        return None

    def __regex_match_command_pattern_end_ignore_wl_keys(
        self, line: str, line_num: int
    ) -> Optional[List[ProblemFilter]]:
        """
        Checks, if the provided command (line) matches the regex pattern
        and sets the end line for the matching open-ended ProblemFilter.

        :param line: inserted command from .tex file
        :param line_num: line number of command occurrence
        :return: empty list, if successful; None otherwise
        """

        match = Preprocessor.__COMMAND_PATTERN_END_IGNORE_WL_KEYS.fullmatch(line)
        if match is not None:
            keys = match.group(1).strip().split(" ")

            for key in keys:

                open_ended_filter = self.__get_open_ended_filter(
                    WhitelistKeyProblemFilter(key, 0)
                )

                if open_ended_filter is None:
                    Preprocessor.__logger.info(
                        f"Ignored duplicate command 'end-ignore' "
                        f"for whitelist-key '{key}' in line {line_num}"
                    )
                else:
                    Preprocessor.__logger.debug(
                        f"Ended existing open-ended WhitelistKeyProblemFilter "
                        f"for whitelist-key '{key}' in line {line_num + 1}"
                    )
                    open_ended_filter.end(line_num)

            return []

        return None

    def __get_open_ended_filter(
        self, reference_filter: ProblemFilter
    ) -> Optional[ProblemFilter]:
        """
        Searches for any open-ended (no end set) ProblemFilter matching
        the provided reference ProblemFilter.

        :param reference_filter: reference to find matching open-ended filter
        :return: matching open-ended filter, if found
        """

        for f in self.filters:
            if f.end_line is None and f.custom_parameters_equal(reference_filter):
                return f

        return None

    def matches_preprocessor_filter(self, problem: Problem) -> bool:
        """
        Checks, if the provided Problem matches any filter.

        :param problem: Problem to check
        :return: false if matching; true otherwise
        """
        for f in self.filters:
            if f.match(problem):
                return False
        return True

    def apply_preprocessor_filter(self, problems: List[Problem]) -> List[Problem]:
        """
        Applies all parsed ProblemFilters and returns all non-matching Problems.

        :param problems: list of Problems to filter
        :return: filtered list of Problems
        """
        return list(filter(self.matches_preprocessor_filter, problems))
