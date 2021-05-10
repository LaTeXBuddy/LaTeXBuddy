import json
import os

import latexbuddy.aspell as aspell
import latexbuddy.chktex as chktex
import latexbuddy.languagetool as languagetool
import latexbuddy.tools as tools


# TODO: rename this file to stop PyCharm throwing warnings
# TODO: some comments

class LatexBuddy:
    def __init__(self, error_file, whitelist_file, file_to_check, lang):
        self.errors = {}
        self.error_file = error_file
        self.whitelist_file = whitelist_file
        self.file_to_check = file_to_check
        self.lang = lang

    def add_error(self, error):
        self.errors[error.get_uid()] = error

    def parse_to_json(self):
        if os.path.isfile(self.error_file):
            os.remove(self.error_file)
        for uid in self.errors:
            self.parse_error(self.errors[uid])

    def parse_error(self, error):
        with open(self.error_file, "a") as file:
            json.dump(error.dict, file, indent=4)

    """
    should be working
    """

    def check_whitelist(self):
        with open(self.whitelist_file, "r") as file:
            whitelist = file.read().split('\n')

        for whitelist_element in whitelist:
            for uid in self.errors.keys():
                if self.errors[uid].compare_with_other_comp_id(whitelist_element):
                    self.errors.pop(uid)

    """
    should be working
    """

    def add_to_whitelist(self, uid):
        if uid not in self.errors.keys():
            raise  # exception

        # write error in whitelist
        with open(self.whitelist_file, "a") as file:
            # json.dump(self.errors[uid], file)
            file.write(self.errors[uid].get_comp_id())
            file.write("\n")

        # delete error & check errors with whitelist again
        self.errors.pop(uid)
        # TODO: check errors with this error object alone to avoid having to check
        #  with the entire whitelist
        self.check_whitelist()

    # TODO: implement rest
    def check_errors(self):
        self.check_whitelist()
        # self.check_config()
        # self.check_parameters()

    def run_tools(self):
        chktex.run(self, self.file_to_check)
        detexed_file = tools.detex(self.file_to_check)
        aspell.run(self, detexed_file)
        languagetool.run(self, detexed_file)
        os.remove(detexed_file)

    def get_lang(self):
        return self.lang
