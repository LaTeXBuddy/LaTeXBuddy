import json
import os

import latexbuddy.aspell as aspell
import latexbuddy.chktex as chktex
import latexbuddy.languagetool as languagetool
import latexbuddy.tools as tools


# TODO: rename this file to stop PyCharm throwing warnings


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
            json.dump(error.__dict__, file, indent=4)

    """
    not working
    """

    def check_whitelist(self):
        with open(self.whitelist_file, "r") as file:
            whitelist = json.load(file)
        for whitelist_error in whitelist:
            for uid in self.errors.keys():
                # if whitelist_error.__eq__(errors[uid]):
                self.errors.pop(uid)

    """
    not working
    """

    def add_to_whitelist(self, uid):
        if uid not in self.errors.keys():
            raise  # exception

        # write error in whitelist
        with open(self.whitelist_file, "a") as file:
            # json.dump(self.errors[uid], file)
            file.write("\n")
            file.write(self.errors[uid].get_hash(self.lang))

        # delete error
        self.errors.pop(uid)

    def run_tools(self):
        chktex.run(self, self.file_to_check)
        detexed_file = tools.detex(self.file_to_check)
        aspell.run(self, detexed_file)
        languagetool.run(self, detexed_file)
        os.remove(detexed_file)

    def get_lang(self):
        return self.lang
