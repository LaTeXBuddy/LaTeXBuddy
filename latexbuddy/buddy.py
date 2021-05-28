"""This module describes the main LaTeXBuddy instance class."""

import json
import os
import re
import sys
import traceback

from html import unescape
from pathlib import Path

from bs4 import BeautifulSoup

import latexbuddy.output as output
import latexbuddy.tools as tools

from latexbuddy import TexFile
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.problem import Problem, ProblemSeverity


# TODO: make this a singleton class with static methods


class LatexBuddy:
    """The main instance of the applications that controls all the internal tools."""

    def __init__(self, config_loader: ConfigLoader, file_to_check: Path):
        """Initializes the LaTeXBuddy instance.

        :param config_loader: ConfigLoader object to manage config options
        :param file_to_check: file that will be checked
        """
        self.errors = {}  # all current errors
        self.cfg: ConfigLoader = config_loader  # configuration
        self.file_to_check = file_to_check  # .tex file that is to be error checked
        self.tex_file: TexFile = TexFile(file_to_check)

        # file where the error should be saved
        self.error_file = self.cfg.get_config_option_or_default(
            "buddy", "output", Path("errors.json")
        )

        # file that represents the whitelist
        # TODO: why a new file format? if it's JSON, use .json. If not, don't use one.
        self.whitelist_file = self.cfg.get_config_option_or_default(
            "buddy", "whitelist", Path("whitelist.wlist")
        )

        # current language
        self.lang = self.cfg.get_config_option_or_default("buddy", "language", "en")

    def add_error(self, error: Problem):
        """Adds the error to the errors dictionary.

        UID is used as key, the error object is used as value.

        :param error: error to add to the dictionary
        """

        self.errors[error.uid] = error

    # TODO: rename method. Parse = read; this method writes
    # TODO: maybe remove the method completely
    def parse_to_json(self):
        """Writes all the current error objects into the error file."""

        # TODO: extend JSONEncoder to get rid of such hacks
        with open(self.error_file, "w+") as file:
            file.write("[")
            uids = list(self.errors.keys())
            for uid in uids:

                # TODO: clean up this temporary workaround by properly reworking the
                #   JSON encoding process (Path and Enum are not JSON serializable)
                err_data = self.errors[uid].__dict__
                if "file" in err_data:
                    err_data["file"] = str(err_data["file"])
                if "severity" in err_data:
                    err_data["severity"] = str(err_data["severity"])

                json.dump(err_data, file, indent=4)
                if not uid == uids[-1]:
                    file.write(",")

            file.write("]")

    def check_whitelist(self):
        """Remove errors that are whitelisted."""
        if not os.path.isfile(self.whitelist_file):
            return  # if no whitelist yet, don't have to check

        with open(self.whitelist_file, "r") as file:
            whitelist = file.read().split("\n")

        for whitelist_element in whitelist:
            uids = list(self.errors.keys())
            for uid in uids:
                if self.errors[uid].compare_with_other_comp_id(whitelist_element):
                    del self.errors[uid]

    def add_to_whitelist(self, uid):
        """Adds the error identified by the given UID to the whitelist

        Afterwards this method deletes all other errors that are the same as the one
        just whitelisted.

        :param uid: the UID of the error to be deleted
        """

        if uid not in self.errors.keys():
            print(
                "Error: invalid UID, error object with ID: "
                + uid
                + "not found and not added to whitelist"
            )
            return

        # write error in whitelist
        with open(self.whitelist_file, "a+") as file:
            file.write(self.errors[uid].get_comp_id())
            file.write("\n")

        # delete error and save comp_id for further check
        compare_id = self.errors[uid].get_comp_id()
        del self.errors[uid]

        # check if there are other errors equal to the one just added to the whitelist
        uids = list(self.errors.keys())
        for curr_uid in uids:
            if self.errors[curr_uid].compare_with_other_comp_id(compare_id):
                del self.errors[curr_uid]

    # TODO: implement
    # def add_to_whitelist_manually(self):
    #     return

    def run_tools(self):
        """Runs all tools in the LaTeXBuddy toolchain"""

        # importing this here to avoid circular import error
        from latexbuddy.tool_loader import ToolLoader

        # check_preprocessor
        # check_config

        if self.tex_file.is_faulty:
            for raw_err in self.tex_file._parse_problems:
                self.add_error(
                    Problem(
                        position=raw_err[0],
                        text=raw_err[1],
                        checker="YaLafi",
                        cid="tex2txt",
                        file=self.tex_file.tex_file,
                        severity=ProblemSeverity.ERROR,
                        category="latex",
                    )
                )

        tool_loader = ToolLoader(Path("latexbuddy/modules/"))
        modules = tool_loader.load_selected_modules(self.cfg)

        for module in modules:

            def lambda_function() -> None:
                errors = module.run_checks(self, self.tex_file)

                for error in errors:
                    self.add_error(error)

            tools.execute_no_exceptions(
                lambda_function,
                f"An error occurred while executing checks for module "
                f"'{module.__class__.__name__}'",
            )

        # FOR TESTING ONLY
        # self.check_whitelist()
        # keys = list(self.errors.keys())
        # for key in keys:
        #     self.add_to_whitelist(key)
        #     return

    # TODO: why does this exist? Use direct access
    def get_lang(self) -> str:
        """Returns the set LaTeXBuddy language.

        :returns: language code
        """
        return self.lang

    def iwas(self, problems: list[Problem], tex: str):
        intervals = {}

        for problem in problems:
            line = problem.position[0]
            new_interval = set(
                range(problem.position[1], problem.position[1] + problem.length)
            )
            new_severity = problem.severity

            if line not in intervals:
                intervals[line] = [[new_interval, new_severity]]
                continue

            for lst in intervals[line]:
                if len(new_interval.intersection(lst[0])) > 0:
                    if lst[1] < new_severity:
                        lst[0] = new_interval
                        lst[1] = new_severity
                        break

        # zu diesem Zeitpunkt sieht intervals so aus:
        #
        # {
        #    1: {
        #      [3,4,5,6,...]: "warning"
        #    }
        # }

        tex_lines = tex.splitlines(keepends=True)
        for line, intervals_set in intervals:
            offset = 0
            for i, s in intervals_set:
                old_len = len(tex_lines[line])
                start = offset + min(i)
                end = start + max(i)
                opening_tag = f"<mark>"
                closing_tag = f"</mark>"
                string = (
                    tex_lines[line][:start]
                    + opening_tag
                    + tex_lines[line][start:end]
                    + closing_tag
                    + tex_lines[line]
                )
                new_len = len(string)
                tex_lines[line] = string
                offset += new_len - old_len

        return "".join(tex_lines)

    def output_html(self):

        # importing this here to avoid circular import error
        from latexbuddy.output import render_html

        html_output_path = Path(str(self.error_file) + ".html")
        html_output_path.write_text(
            render_html(
                str(self.tex_file.tex_file),
                self.tex_file.tex,
                self.errors,
            )
        )
        html_output_path.write_text(html)

        print(f"File output to {html_output_path}")

    def mark_output(self, file, text, problems) -> str:
        html = output.render_html(file, text, self.errors)  # gets html
        lines_problems = self.get_line_problems(
            problems, text
        )  # gets problems per line
        lines = text.split("\n")
        line_count = len(lines)
        charmap = self.generate_charmap(line_count, lines_problems)
        lines = self.mark_text(line_count, lines_problems, lines, charmap)
        content = ""
        for line in lines:
            content += line + "\n"

        soup = BeautifulSoup(html, "html.parser")
        new_code = soup.new_tag("code")
        new_code.string = unescape(content)
        soup.find("section", id="file-contents").pre.code.replace_with(new_code)
        new_soup = BeautifulSoup(unescape(str(soup)), "html.parser")

        return unescape(str(new_soup))
        # return unescape(str(soup))

    def mark_text(
        self,
        line_count: int,
        lines_problems: dict,
        lines: list[str],
        charmap: list[dict],
    ) -> list[str]:
        for line in range(line_count):
            for problem in lines_problems[line]:
                # removes unwanted problems
                if (
                    problem.checker == "aspell"
                    or problem.category is None
                    or problem.category == ""
                ):
                    continue
                # gets new start, end based on original position
                original_start = problem.position[1] - 1
                original_end = original_start + problem.length
                print(str(line), ":", original_start, original_end)
                print(charmap)
                print(line_count)
                print(len(charmap))
                start, end = charmap[line + 1][(original_start, original_end)]

                tag, end_tag = self.get_tag(problem)

                # replaces string with string wrapped in tag
                left = lines[line][:start]
                middle = tag + lines[line][start:end] + end_tag
                right = lines[line][end:]
                lines[line] = left + middle + right
                charmap = self.update_charmap(charmap, tag, end_tag, line, start, end)

        return lines

    @staticmethod
    def update_charmap(
        charmap: list[dict],
        tag: str,
        end_tag: str,
        line: int,
        changed_start: int,
        changed_end: int,
    ) -> list[dict]:
        line_map = charmap[line]
        s_offset = len(tag)
        e_offset = len(end_tag)
        offset = s_offset + e_offset
        for old in line_map:
            original_start, original_end = (old[0], old[1])
            start, end = line_map[(original_start, original_end)]
            if (changed_end + e_offset + s_offset) <= start:
                start += offset
                end += offset
            elif changed_start + s_offset <= start <= changed_end + offset <= end:
                start += s_offset
                end += offset
            elif changed_start + s_offset <= start and end <= changed_end + offset:
                start += s_offset
                end += s_offset
            elif start <= changed_start + s_offset <= end <= changed_end + offset:
                end += s_offset
            elif start <= changed_start + s_offset and changed_end + offset <= end:
                end += offset
            charmap[line][(original_start, original_end)] = (start, end)

        return charmap

    @staticmethod
    def generate_charmap(line_count: int, lines_problems: dict) -> list[dict]:
        charmap = [{}]
        # maps each position to itself in charmap
        for line in range(line_count):
            dict = {}
            for problem in lines_problems[line]:
                start = problem.position[1] - 1
                end = start + problem.length
                dict[(start, end)] = (start, end)
            charmap.append(dict)

        return charmap

    @staticmethod
    def get_line_problems(problems, text) -> dict[int, list[Problem]]:
        problem_dict = {}
        line_count = len(text.split("\n"))
        for line in range(line_count):
            problem_dict[line] = []

        for problem in problems:
            if problem.checker == "aspell":
                continue
            problem_dict[problem.position[0] - 1].append(problem)

        return problem_dict

    @staticmethod
    def get_tag(problem) -> tuple:
        tag = "span"
        if problem.category == "spelling":
            tag = "u"
        elif problem.category == "grammar":
            tag = "mark"
        elif problem.category == "latex":
            tag = "span"
        return unescape("<" + tag + ' class="' + problem.category + '">'), unescape(
            "</" + tag + ">"
        )
