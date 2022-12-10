"""This module defines standard exceptions that are to be raised when certain
application-specific errors occur."""
from __future__ import annotations


class ExecutableNotFoundError(Exception):
    """This error is raised when LaTeXBuddy can not locate a third-party
    executable dependency on the system it is running on."""


class LanguageNotSupportedError(Exception):
    """This error is raised when LaTeXBuddy or a submodule does not support the
    configured language."""


class ConfigOptionError(Exception):
    """Base Exception for errors related to loading configurations."""


class ConfigOptionNotFoundError(ConfigOptionError):
    """Describes a ConfigOptionNotFoundError.

    This error is raised when a requested config entry doesn't exist.
    """


class ConfigOptionVerificationError(ConfigOptionError):
    """Describes a ConfigOptionVerificationError.

    This error is raised when a requested config entry does not meet the
    specified criteria.
    """
