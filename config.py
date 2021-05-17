"""
This is an example configuration for LaTeXBuddy and the tools that are supported
out-of-the-box. You may move this file and specify its path using the --config flag.
"""

modules = {
    "latexbuddy": {
        "language": "en",
        "whitelist": "whitelist.wlist",
        "output": "errors.json"
    },
    "languagetool": {
        "mode": "LOCAL_SERVER"
    },
}
