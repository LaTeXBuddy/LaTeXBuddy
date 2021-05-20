"""
This is an example configuration for LaTeXBuddy and the tools that are supported
out-of-the-box. You may move this file and specify its path using the --config flag.
"""

modules = {
    "buddy": {
        "language": "en",
        "whitelist": "whitelist.wlist",
        "output": "errors.json",
        "enable-modules-by-default": True,
    },
    "LanguageTool": {
        "enabled": True,
        "mode": "COMMANDLINE",
        # "remote_url": "https://example.com/check/v2/"
    },
    "TestModule": {
        "enabled": False,
    }
}
