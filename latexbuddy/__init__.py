from logging import getLogger
from pkgutil import extend_path

import colorama

from latexbuddy.texfile import TexFile


# package metadata
__app_name__ = "LaTeXBuddy"  # proper name
__name__ = "latexbuddy"  # "unixified" name
__path__ = extend_path(__path__, __name__)
__version__ = "0.3.0"

__logger = getLogger(__name__)

colorama.init()
