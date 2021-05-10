import hashlib


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
        self.dict = {"path": path, "src": src, "error_type": error_type,
                      "error_id": error_id,
                      "text": text, "start": start, "length": length,
                      "suggestions": suggestions, "warning": warning, "uid": self.uid()}
        buddy.add_error(self)

    """
    creates uid
    """

    def uid(self):
        return "{}\0{}\0{}\0{}\0{}\0{}".format(
            self.error['path'], self.['src'], self.['error_type'], self.['error_id'],
            self.['start'], self.['length']
        )

    """
    gets uid
    """

    def get_uid(self):
        return self.uid

    # TODO: maybe different hashes for different error types
    def get_hash(self, language):
        string_for_hash = self.error_type + self.text + language
        return hashlib.md5(string_for_hash).hexdigest()

    def __eq__(self, other):
        return self.error_type == other.error_type & self.text == other.text  # &\
        # .error_id == other.error_id & self.src == other.src
