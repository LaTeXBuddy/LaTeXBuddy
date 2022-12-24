from __future__ import annotations

from logging import getLogger
from pkgutil import extend_path


# package metadata
__app_name__ = "LaTeXBuddy"  # proper name
__name__ = "latexbuddy"  # "unixified" name
__path__ = extend_path(__path__, __name__)
__version__ = "0.4.1"

__logger = getLogger(__name__)

try:
    from colorama import just_fix_windows_console

    just_fix_windows_console()
except ModuleNotFoundError:
    LOG.debug("colorama not found, we are not on Windows")
except ImportError:
    LOG.debug("Old colorama version installed, using legacy init")
    import colorama
    colorama.init()
