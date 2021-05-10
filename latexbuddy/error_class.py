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
        self.dict = {
            "path": path,
            "src": src,
            "error_type": error_type,
            "error_id": error_id,
            "text": text,
            "start": start,
            "length": length,
            "suggestions": suggestions,
            "warning": warning,
            "uid": self.uid(),
        }
        buddy.add_error(self)

    """
    creates uid
    """

    def uid(self):
        return "{}\0{}\0{}\0{}\0{}\0{}".format(
            self.dict["path"],
            self.dict["src"],
            self.dict["error_type"],
            self.dict["error_id"],
            self.dict["start"],
            self.dict["length"],
        )

    """
    gets uid
    """

    def get_uid(self):
        return self.dict["uid"]

    # TODO: maybe different hashes for different error types
    def get_hash(self, language):
        string_for_hash = self.dict["error_type"] + self.dict["text"] + language
        return hashlib.md5(string_for_hash).hexdigest()

    def __eq__(self, other):
        return (
            self.dict["error_type"]
            == other.dict["error_type"] & self.dict["text"]
            == other.dict["text"]
        )  # &\
        # .error_id == other.error_id & self.src == other.src
