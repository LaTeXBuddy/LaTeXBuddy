"""This is an example configuration for LaTeXBuddy and the tools that are
supported out-of-the-box.

You may move this file and specify its path using the --config flag.
"""
from __future__ import annotations

main = {
    "language": "en",
    "language_country": "GB",
    "output": "./latexbuddy_html/",
    "format": "HTML",
    "enable-modules-by-default": False,
    "pdf": True,
}

modules = {
    "LogFilter": {
        "enabled": True,
    },
}
