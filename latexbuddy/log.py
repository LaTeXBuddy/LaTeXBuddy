from __future__ import annotations

import logging
import typing
from abc import ABC

if typing.TYPE_CHECKING:
    from logging import Logger


class Loggable(ABC):
    """This class provides logging functionality to any class that inherits
    from it.

    .. deprecated::    Just use ``logging.getLogger(__name__)`` instead.
    """

    __logger = logging.getLogger("latexbuddy")

    @property
    def logger(self):
        """Returns a logger that includes the full module path and the
        classname in its name."""
        return self.__logger.getChild(
            ".".join(self.__module__.split(".")[1:]),
        ).getChild(self.__class__.__name__)

    @logger.setter
    def logger(self, value: Logger) -> None:
        """Ignores any overwrite operations for property 'logger'."""
