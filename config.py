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
    "pdf": True,
}

modules = {
    "Aspell": {
        "enabled": True,
    },
    "Chktex": {
        "enabled": True,
    },
    "Diction": {
        "enabled": True,
    },
    "EmptySections": {
        "enabled": True,
    },
    "LanguageTool": {
        "enabled": False,
        "mode": "COMMANDLINE",
        "remote_url_check": "https://api.languagetoolplus.com/v2/check",
        "remote_url_languages": "https://api.languagetoolplus.com/v2/languages",
        "disabled-rules": [
            "WHITESPACE_RULE",
            # "TYPOGRAFISCHE_ANFUEHRUNGSZEICHEN",
        ],
        "disabled-categories": [
            # "TYPOS",
        ],
    },
    "LogFilter": {
        "enabled": True,
    },
    "ProseLint": {
        "enabled": True
    },
    "SiUnitx": {
        "enabled": True,
    },
    "URLCheck": {
        "enabled": True,
    },
    "UnreferencedFigures": {
        "enabled": True,
    },
    "NativeUseOfRef": {
        "enabled": True,
    },
    "CheckFigureResolution": {
        "enabled": True,
    },
    "YaLafi": {
        "enabled": True
    },
    "NewerPublications": {
        "enabled": True
    },
    "BibtexDuplicates": {
        "enabled": True
    },
}
