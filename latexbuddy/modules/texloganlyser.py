import latexbuddy.tools as tools
import os

from typing import List
from pathlib import Path
from latexbuddy.modules import Module
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.problem import Problem, ProblemSeverity
from latexbuddy.texfile import TexFile
from latexbuddy import __logger as root_logger
from latexbuddy.messages import not_found


class TexLogAnalyser(Module):

    def __init__(self):
        self.tool_name = "texloganalyser"

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:
        return []


