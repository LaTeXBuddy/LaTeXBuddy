import json
import os

import latexbuddy.aspell as aspell
import latexbuddy.chktex as chktex
import latexbuddy.languagetool as languagetool
import latexbuddy.tools as tools

# TODO: rename this file to stop PyCharm throwing warnings. ?


class LatexBuddy:
    def __init__(self, error_file, whitelist_file, file_to_check, lang):
        self.errors = {}  # all current errors
        self.error_file = error_file  # file where the error should be saved
        self.whitelist_file = whitelist_file  # file that represents the whitelist
        self.file_to_check = file_to_check  # .tex file that is to be error checked
        self.lang = lang  # current language

    """
    Adds an error to the dict with UID as key and the error object as value
    """

    def add_error(self, error):
        self.errors[error.get_uid()] = error

    """
    Writes all the current error objects into the error file
    """

    def parse_to_json(self):
        items = list(self.errors.values())
        with open(self.error_file, "w+") as file:
            file.write("[")
            uids = list(self.errors.keys())
            for uid in uids:
                json.dump(self.errors[uid].__dict__, file, indent=4)
                if not uid == uids[-1]:
                    file.write(",")

            file.write("]")

    """
    Checks the errors if any match an element in the whitelist and if so deletes it
    """

    def check_whitelist(self):
        if not os.path.isfile(self.whitelist_file):
            return  # if no whitelist yet, don't have to check

        with open(self.whitelist_file, "r") as file:
            whitelist = file.read().split("\n")

        for whitelist_element in whitelist:
            uids = list(self.errors.keys())
            for uid in uids:
                if self.errors[uid].compare_with_other_comp_id(whitelist_element):
                    del self.errors[uid]

    """
    Adds the error identified by the given UID to the whitelist, afterwards deletes all
    other errors that are the same as the one just added
    """

    def add_to_whitelist(self, uid):
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
    def add_to_whitelist_manually(self):
        return

    def run_tools(self):
        # check_preprocessor
        # check_config

        chktex.run(self, self.file_to_check)
        detexed_file = tools.detex(self.file_to_check)
        # aspell.run(self, detexed_file)
        languagetool.run(self, self.file_to_check)

        # FOR TESTING ONLY
        """
        self.check_whitelist()
        keys = list(self.errors.keys())
        for key in keys:
            self.add_to_whitelist(key)
            return
        """

        os.remove(detexed_file)

    def get_lang(self):
        return self.lang
