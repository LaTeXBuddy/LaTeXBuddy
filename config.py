"""
This is an example configuration for LaTeXBuddy and the tools that are supported
out-of-the-box. You may move this file and specify its path using the --config flag.
"""

modules = {
    "buddy": {
        "language": "en",
        "whitelist": "whitelist.wlist",
        "output": "./",
        "format": "HTML",
        "enable-modules-by-default": True,
    },
    "LanguageTool": {
        # "enabled": True,
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
    "AspellModule": {
        # "enabled": True,
    },
    "ChktexModule": {
        # "enabled": True,
    },
    "ProseLintModule": {
        "enabled": True
    },
    "TestModule": {
        "enabled": False,
    }
}
