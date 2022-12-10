from __future__ import annotations

from logging import getLogger
from pkgutil import extend_path

import colorama


# package metadata
__app_name__ = "LaTeXBuddy"  # proper name
__name__ = "latexbuddy"  # "unixified" name
__path__ = extend_path(__path__, __name__)
__version__ = "0.4.1"

__logger = getLogger(__name__)

colorama.init()
