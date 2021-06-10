"""This module defines standard messages that are to be printed to the command line
as well as builders for those.
"""


def not_found(executable: str, to_install: str) -> str:

    # importing this here to avoid circular import error
    from latexbuddy import __app_name__

    return (
        f"'{executable}' not found! "
        f"Make sure you've installed {to_install} correctly. "
        f"Refer to the {__app_name__} manual for help."
    )
