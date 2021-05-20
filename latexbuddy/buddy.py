"""This module describes the main LaTeXBuddy instance class."""

import json
import os
import sys
import traceback

from pathlib import Path

import latexbuddy.tools as tools
from bs4 import BeautifulSoup
import re
from html import unescape
import latexbuddy.output as output
from latexbuddy import TexFile
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.problem import Problem


# TODO: make this a singleton class with static methods


class LatexBuddy:
    """The main instance of the applications that controls all the internal tools."""

    def __init__(self, config_loader: ConfigLoader, file_to_check: Path):
        """Initializes the LaTeXBuddy instance.

        :param config_loader: ConfigLoader object to manage config options
        :param file_to_check: file that will be checked
        """
        self.errors = {}  # all current errors
        self.cfg = config_loader  # configuration
        self.file_to_check = file_to_check  # .tex file that is to be error checked
        self.charmap = None  # detex charmap

        # file where the error should be saved
        self.error_file = self.cfg.get_config_option_or_default(
            "buddy", "output", Path("errors.json")
        )

        # file that represents the whitelist
        self.whitelist_file = self.cfg.get_config_option_or_default(
            "buddy", "whitelist", Path("whitelist.wlist")
        )

        # current language
        self.lang = self.cfg.get_config_option_or_default("buddy", "language", "en")
        self.check_successful = False

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

        tex_file = TexFile(self.file_to_check)

        # TODO: phase out and replace with tex_file, if possible
        detexed_file, self.charmap, detex_err = tools.yalafi_detex(self.file_to_check)
        self.check_successful = True if len(detex_err) < 1 else False

        for err in detex_err:
            self.add_error(
                # TODO: Verify this is correct and maybe implement more attributes
                Problem(
                    err[0],
                    err[1],
                    "YALaFi",
                    "latex",
                    self.file_to_check,
                )
                # TODO: old implementation for reference (remove when finished)
                # Problem(
                #    self,
                #    str(self.file_to_check),
                #    "YALaFi",
                #    "latex",
                #    "TODO",
                #    err[1],
                #    err[0],
                #    0,
                #    [],
                #    False,
                #    "TODO",
                # )
            )

        tool_loader = ToolLoader(Path("latexbuddy/modules/"))
        modules = tool_loader.load_selected_modules(self.cfg)

        for module in modules:

            try:
                errors = module.run_checks(self, tex_file)

                for error in errors:
                    self.add_error(error)

            except Exception as e:

                print(
                    f"An error occurred while executing checks for module "
                    f"'{module.__class__.__name__}':\n",
                    f"{e.__class__.__name__}: {getattr(e, 'message', e)}",
                    file=sys.stderr,
                )
                traceback.print_exc(file=sys.stderr)

        # FOR TESTING ONLY
        # self.check_whitelist()
        # keys = list(self.errors.keys())
        # for key in keys:
        #     self.add_to_whitelist(key)
        #     return

        # TODO: use tempfile.TemporaryFile instead
        os.remove(detexed_file)

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
                opening_tag = f'<mark>'
                closing_tag = f'</mark>'
                string = tex_lines[line][:start] + opening_tag + tex_lines[line][start:end] + closing_tag + tex_lines[line]
                new_len = len(string)
                tex_lines[line] = string
                offset += new_len - old_len

        return "".join(tex_lines)



    def output_html(self):

        # importing this here to avoid circular import error
        from latexbuddy.output import render_html

        # err_values = sorted(self.errors.values(), key=output.error_key)
        # html_output_path = Path(self.error_file + ".html")
        # html = self.iwas(err_values, self.file_to_check.read_text())
        # html_output_path.write_text(html)

        print(f"File output to {html_output_path}")
