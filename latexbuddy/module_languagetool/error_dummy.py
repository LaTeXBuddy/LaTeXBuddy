class Error:
    def __init__(
        self,
        path: str,
        src: str,
        error_type: str,
        error_id: str,
        text: str,
        character_start: int,
        length: int,
        suggestions: [str],
        is_warning: bool,
    ):
        self.path = path
        self.src = src
        self.error_type = error_type
        self.error_id = error_id
        self.text = text
        self.character_start = character_start
        self.length = length
        self.suggestions = suggestions
        self.is_warning = is_warning

        self.uid = self.createUID()

    def createUID(self):
        return "not yet implemented..."

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return (
            f"{self.error_type}:{self.error_id};  {self.character_start}:{self.length},  "
            f"\u001b[31m{self.text}\u001b[0m, suggestions: {self.suggestions}"
        )
