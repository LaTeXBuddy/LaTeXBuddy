from typing import List

from latexbuddy import TexFile
from latexbuddy.problem import Problem


class Preprocessor:
    def __init__(self):
        pass

    def parse_preprocessor_comments(self, file: TexFile):
        pass

    def apply_preprocessor_filter(self, problems: List[Problem]) -> List[Problem]:
        pass
