import hashlib


class Error:

    """
    creates an error object
    """

    def __init__(
        self,
        buddy,  # latexbuddy instance where the error is to be added
        path,  # the path to the file
        src,  # the src tool of the error <chktex/aspell/...>
        error_type,  # <grammar/spelling/latex>
        error_id,  # tool intern error id as integer
        text,  # the error as text if possible
        start,  # the starting character
        length,  # the length
        suggestions,  # suggestions to solve the error
        warning,  # boolean. true if the error is a warning, only in tex checks
        compare_id  # ID to compare two errors that are semantically equal, to be
        # implemented by each module TODO: make sure all modules do this
    ):
        self.path = path
        self.src = src
        self.error_type = error_type
        self.error_id = error_id
        self.text = text
        self.start = start
        self.length = length
        self.suggestions = suggestions
        self.warning = warning
        self.compare_id = buddy.get_lang() + "_" + compare_id

        self.uid = self.uid()

        # TODO: remove this; constructors shouldn't produce side effects
        buddy.add_error(self)

    """
    creates uid
    """

    def uid(self):
        return "{}\0{}\0{}\0{}\0{}\0{}".format(
            self.path, self.src, self.error_type, self.error_id, self.start, self.length
        )

    """
    gets uid
    """

    def get_uid(self):
        return self.uid

    def get_comp_id(self):
        return self.compare_id

    # Ignore for now
    """
    def get_hash(self, language):
        string_for_hash = self.dict["error_type"] + self.dict["text"] + language
        return hashlib.md5(string_for_hash).hexdigest()
    """

    def compare_with_other_comp_id(self, other_comp_id):
        return self.compare_id == other_comp_id
