"""This module describes the main LaTeXBuddy instance class."""

import json
import os
import sys
import traceback

from pathlib import Path

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

    def output_html(self):

        # importing this here to avoid circular import error
        from latexbuddy.output import render_html

        html_output_path = Path(self.error_file + ".html")
        html_output_path.write_text(
            render_html(
                str(self.tex_file.tex_file),
                self.tex_file.tex,
                self.errors,
            )
        )

        print(f"File output to {html_output_path}")