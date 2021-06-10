"""This module defines standard exceptions that are to be raised when certain
application-specific errors occur."""


class ConfigOptionError(Exception):
    """Base Exception for errors related to loading configurations"""

    pass


class ConfigOptionNotFoundError(ConfigOptionError):
    """Describes a ConfigOptionNotFoundError.

    This error is raised when a requested config entry doesn't exist.
    """

    pass


class ConfigOptionVerificationError(ConfigOptionError):
    """Describes a ConfigOptionVerificationError

    This error is raised when a requested config entry does not meet the
    specified criteria.
    """

    pass
