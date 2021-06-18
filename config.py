"""
This is an example configuration for LaTeXBuddy and the tools that are supported
out-of-the-box. You may move this file and specify its path using the --config flag.
"""

modules = {
    "LatexBuddy": {
        "language": "en",
        "whitelist": "whitelist",
        "output": "./",
        "format": "HTML",
        "enable-modules-by-default": True,
    },
    "AspellModule": {
        "enabled": True,
    },
    "ChktexModule": {
        "enabled": True,
    },
    "DictionModule": {
        "enabled": True,
    },
    "EmptySectionsModule": {
        "enabled": True,
    },
    "LanguageTool": {
        "enabled": True,
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
        "enabled": True
    },
    "SiUnitxModule": {
        "enabled": True,
    },
    "URLModule": {
        "enabled": True,
    },
    "UnreferencedFiguresModule": {
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
}
