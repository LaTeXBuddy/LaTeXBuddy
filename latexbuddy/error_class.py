class Error:
    """
    creates an error object
    """

    def __init__(
        self,
        buddy,
        path,
        src,
        error_type,
        error_id,
        text,
        start,
        length,
        suggestions,
        warning,
    ):
        self.path = path  # the path to the file
        self.src = src  # the src tool of the error <chktex/aspell/...>
        self.error_type = error_type  # <grammar/spelling/latex>
        self.error_id = error_id  # tool intern error id as integer
        self.text = text  # the error as text if possible
        self.start = start  # the starting character
        self.length = length  # the length
        self.suggestions = suggestions  # suggestions to solve the error
        self.warning = (
            warning  # boolean. true if the error is a warning, only in tex checks
        )
        self.uid = self.uid()
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


"""
    def __eq__(self, other):
        return self.src == other.src & self.error_type == other.error_typ & \
               self.error_id == other.error_id & self.text == other.text
"""
