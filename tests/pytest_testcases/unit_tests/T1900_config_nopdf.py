"""
This is an example configuration for LaTeXBuddy and the tools that are supported
out-of-the-box. You may move this file and specify its path using the --config flag.
"""

main = {
    "language": "en",
    "language_country": "GB",
    "module_dir": "tests/pytest_testcases/integration_tests/resources/T700_driver_modules/",
    "output": "./latexbuddy_html/",
    "format": "HTML",
    "enable-modules-by-default": False,
    "pdf": False,
}

modules = {
    "LogFilter": {
        "enabled": True,
    },
}
