"""
This is an example configuration for LaTeXBuddy and the tools that are supported
out-of-the-box. You may move this file and specify its path using the --config flag.
"""

modules = {
    "buddy": {
        "language": "en",
        "whitelist": "whitelist",
        "output": "./",
        "format": "HTML",
        "enable-modules-by-default": False,
    },
    "AspellModule": {
        "enabled": False,
    },
    "ChktexModule": {
        "enabled": False,
    },
    "DictionModule": {
        "enabled": False,
    },
    "EmptySectionsModule": {
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
    "ProseLintModule": {
        "enabled": False
    },
    "SiUnitxModule": {
        "enabled": False,
    },
    "URLModule": {
        "enabled": False,
    },
    "UnreferencedFiguresModule": {
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
}
