"""
This is an example configuration for LaTeXBuddy and the tools that are supported
out-of-the-box. You may move this file and specify its path using the --config flag.
"""

main = {
    "language": "en",
    "language_country": "GB",
    "whitelist": "whitelist",
    "output": "./latexbuddy_html/",
    "format": "HTML",
    "enable-modules-by-default": True,
    "pdf": False,
}

modules = {
    "Aspell": {
        "enabled": False,
    },
    "Chktex": {
        "enabled": False,
    },
    "Diction": {
        "enabled": False,
    },
    "EmptySections": {
        "enabled": False,
    },
    "LanguageTool": {
        "enabled": False,
        "mode": "COMMANDLINE",
        # "remote_url": "https://api.languagetoolplus.com/v2/check",
        "disabled-rules": [
            "WHITESPACE_RULE",
            # "TYPOGRAFISCHE_ANFUEHRUNGSZEICHEN",
        ],
        "disabled-categories": [
            # "TYPOS",
        ],
    },
    "LogFilter": {
        "enabled": False,
    },
    "ProseLint": {
        "enabled": False
    },
    "SiUnitx": {
        "enabled": False,
    },
    "URLCheck": {
        "enabled": False,
    },
    "UnreferencedFigures": {
        "enabled": False,
    },
    "NativeUseOfRef": {
        "enabled": False,
    },
    "CheckFigureResolution": {
        "enabled": False,
    },
    "YaLafi": {
        "enabled": False
    },
    "NewerPublications": {
        "enabled": True
    },
    "BibtexDuplicates": {
        "enabled": True
    },
}
