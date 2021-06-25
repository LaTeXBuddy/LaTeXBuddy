"""This module describes the LaTeXBuddy config loader and its properties."""
import importlib.util as importutil
import re

from argparse import Namespace
from pathlib import Path
from typing import Any, AnyStr, Dict, List, Optional, Set, Tuple, Type, Union

from pydantic import BaseModel, ValidationError

import latexbuddy.tools as tools

from latexbuddy import __logger as root_logger
from latexbuddy.exceptions import (
    ConfigOptionNotFoundError,
    ConfigOptionVerificationError,
)


class ConfigLoader:
    """Describes a ConfigLoader object.

    The ConfigLoader processes LaTeXBuddy's cli arguments and loads the specified
    config file or the default config file, if none is specified.
    ConfigLoader also offers methods for accessing config entries with the option
    to specify a default value on Failure.
    """

    __logger = root_logger.getChild("config_loader")

    _REGEX_LANGUAGE_FLAG = re.compile(r"([a-zA-Z]{2,3})(?:[-_\s]([a-zA-Z]{2,3}))?")

    def __init__(self, cli_arguments: Namespace):
        """Creates a ConfigLoader module.

        :param cli_arguments: The commandline arguments specified in the LaTeXBuddy call
        """

        self.configurations = {}

        if not cli_arguments.config:
            self.__logger.warning(
                "No configuration file specified. Default values will be used."
            )
            return

        if cli_arguments.config.exists():
            self.load_configurations(cli_arguments.config)
        else:
            self.__logger.warning(
                f"File not found: {cli_arguments.config}. "
                f"Default configuration values will be used."
            )

        self.flags = self.__parse_flags(cli_arguments)

    def __parse_flags(self, args: Namespace) -> Dict[str, Dict[str, Any]]:
        """This private helper-function parses commandline arguments into a dictionary.

        :param args: commandline arguments specified at the start of LaTeXBuddy
        :return: a formatted dictionary containing all cli flags as config entries with
            the label corresponding to the display name of the main LaTeXBuddy instance
        """

        from latexbuddy.buddy import LatexBuddy

        module_key = LatexBuddy.display_name
        parsed = {module_key: {}}

        args_dict = {
            key: value for key, value in vars(args).items() if value is not None
        }

        for key in args_dict:
            # mutual exclusion of enable_modules and disable_modules
            # is guaranteed by argparse library
            if key == "enable_modules":

                parsed[module_key]["enable-modules-by-default"] = False

                for module_name in self.configurations.keys():
                    if module_name not in parsed:
                        parsed[module_name] = {}

                    parsed[module_name]["enabled"] = False

                for module_name in args_dict[key].split(","):
                    if module_name not in parsed:
                        parsed[module_name] = {}

                    parsed[module_name]["enabled"] = True

            elif key == "disable_modules":

                parsed[module_key]["enable-modules-by-default"] = True

                for module_name in self.configurations.keys():
                    if module_name not in parsed:
                        parsed[module_name] = {}

                    parsed[module_name]["enabled"] = True

                for module_name in args_dict[key].split(","):
                    if module_name not in parsed:
                        parsed[module_name] = {}

                    parsed[module_name]["enabled"] = False

            elif key == "language":

                language_match = self._REGEX_LANGUAGE_FLAG.fullmatch(args_dict[key])

                if language_match is not None:

                    parsed["buddy"]["language"] = language_match.group(1)

                    if language_match.group(2) is not None:
                        parsed["buddy"]["language_country"] = language_match.group(2)

                else:

                    self.__logger.warning(
                        f"Specified language '{args_dict[key]}' is not a valid "
                        f"language key. Please use a key in the following syntax: "
                        f"<language>[-<country>] (e.g.: en-GB, en_US, de-DE)"
                    )

            else:
                parsed[module_key][key] = args_dict[key]

        self.__logger.debug(f"Parsed CLI config options:\n{str(parsed)}")

        return parsed

    def load_configurations(self, config_file_path: Path) -> None:
        """This helper-function loads the contents of a specified config .py-file.

        :param config_file_path: config file to be loaded (.py)
        :return: None
        """

        def lambda_function() -> None:
            spec = importutil.spec_from_file_location("config", config_file_path)
            config = importutil.module_from_spec(spec)
            spec.loader.exec_module(config)

            self.configurations = config.modules

        tools.execute_no_exceptions(
            lambda_function,
            f"An error occurred while loading config file at '{str(config_file_path)}'",
        )

    @staticmethod
    def __get_option(
        config_dict: Dict,
        tool_name: str,
        key: str,
        verify_type: Type = Any,
        verify_regex: Optional[str] = None,
        verify_choices: Optional[Union[List[Any], Tuple[Any], Set[Any]]] = None,
        error_indicator: str = "config",
    ) -> Any:
        """This private helper-function searches for a config entry in the specified
        dictionary (config or flags). It raises an error, if the requested config
        option is not specified in the specified dictionary or the retrieved entry does
        not match a specified verification criterion.

        :param config_dict: dictionary to be searched
        :param tool_name: name of the tool owning the config option
        :param key: key of the config option
        :param verify_type: typing type that the config entry is required to be an
                            instance of (otherwise ConfigOptionVerificationError is
                            raised)
        :param verify_regex: regular expression that the config entry is required to
                             match fully (otherwise ConfigOptionVerificationError is
                             raised)
                             Note: this overrides verify_type with 'AnyStr'
        :param verify_choices: a list/tuple/set of valid values in which the config
                               entry needs to be contained in order to be valid
        :param error_indicator: custom string displayed in the error message on failure
        :return: the value of the requested config option, if it exists
        :raises: ConfigOptionNotFoundError, if the requested config option doesn't exist
        :raises: ConfigOptionVerificationError, if the requested config option does not
                 meet the specified criteria
        """

        if tool_name not in config_dict or key not in config_dict[tool_name]:
            raise ConfigOptionNotFoundError(
                f"Tool: {tool_name}, key: {key} ({error_indicator})"
            )

        entry = config_dict[tool_name][key]

        # assert that entry type is a string, if regex check is applied
        if verify_regex is not None:
            verify_type = AnyStr

        if verify_type is not Any:

            class TypeVerifier(BaseModel):
                cfg_entry: verify_type

            try:
                TypeVerifier(cfg_entry=entry)
            except ValidationError:

                raise ConfigOptionVerificationError(
                    f"config entry '{key}' for module '{tool_name}' is of "
                    f"type '{str(type(entry))}' (expected '{str(verify_type)}')"
                )

        if verify_regex is not None:

            pattern = re.compile(verify_regex)

            if pattern.fullmatch(entry) is None:
                raise ConfigOptionVerificationError(
                    f"config entry '{key}' for module '{tool_name}' does not match the "
                    f"provided regular expression: entry: '{entry}', "
                    f"regex: '{verify_regex}'"
                )

        if verify_choices is not None:

            if entry not in verify_choices:
                raise ConfigOptionVerificationError(
                    f"value '{str(entry)}' of config entry '{key}' for "
                    f"module '{tool_name}' is not contained in the specified list of "
                    f"valid values: {str(verify_choices)}"
                )

        return entry

    # TODO: resolve circular import error between config_loader.py and
    #  modules.__init__.py when importing NamedModule
    def get_config_option(
        self,
        module,  # : Union[Type[NamedModule], NamedModule],
        key: str,
        verify_type: Type = Any,
        verify_regex: Optional[str] = None,
        verify_choices: Optional[Union[List[Any], Tuple[Any], Set[Any]]] = None,
    ) -> Any:
        """This method fetches the value of the config entry with the specified key for
        the specified tool or raises a ConfigOptionNotFoundError, if such an entry
        doesn't exist or the retrieved entry does not match a specified verification
        criterion.

        :param module: type or an instance of the module owning the config option
        :param key: key of the config option
        :param verify_type: typing type that the config entry is required to be an
                            instance of (otherwise ConfigOptionVerificationError is
                            raised)
        :param verify_regex: regular expression that the config entry is required to
                             match fully (otherwise ConfigOptionVerificationError is
                             raised)
                             Note: this overrides verify_type with 'AnyStr'
        :param verify_choices: a list/tuple/set of valid values in which the config
                               entry needs to be contained in order to be valid
        :return: the value of the requested config option, if it exists
        :raises: ConfigOptionNotFoundError, if the requested config option doesn't exist
        :raises: ConfigOptionVerificationError, if the requested config option does not
                 meet the specified criteria
        """

        try:
            return ConfigLoader.__get_option(
                self.flags,
                module.display_name,
                key,
                error_indicator="flag",
                verify_type=verify_type,
                verify_regex=verify_regex,
                verify_choices=verify_choices,
            )
        except ConfigOptionNotFoundError:
            pass

        return ConfigLoader.__get_option(
            self.configurations,
            module.display_name,
            key,
            verify_type=verify_type,
            verify_regex=verify_regex,
            verify_choices=verify_choices,
        )

    # TODO: resolve circular import error between config_loader.py and
    #  modules.__init__.py when importing NamedModule
    def get_config_option_or_default(
        self,
        module,  # : Union[Type[NamedModule], NamedModule],
        key: str,
        default_value: Any,
        verify_type: Type = Any,
        verify_regex: Optional[str] = None,
        verify_choices: Optional[Union[List[Any], Tuple[Any], Set[Any]]] = None,
    ) -> Any:
        """This method fetches the value of the config entry with the specified key for
        the specified tool or returns the specified default value, if such an entry
        doesn't exist or the retrieved entry does not match a specified verification
        criterion.

        :param module: type or an instance of the module owning the config option
        :param key: key of the config option
        :param default_value: default value in case the requested option doesn't exist
        :param verify_type: typing type that the config entry is required to be an
                            instance of (otherwise ConfigOptionVerificationError is
                            raised)
        :param verify_regex: regular expression that the config entry is required to
                             match fully (otherwise ConfigOptionVerificationError is
                             raised)
                             Note: this overrides verify_type with 'AnyStr'
        :param verify_choices: a list/tuple/set of valid values in which the config
                               entry needs to be contained in order to be valid
        :return: the value of the requested config option or default_value, if the
            config option doesn't exist
        """

        try:
            return self.get_config_option(
                module,
                key,
                verify_type=verify_type,
                verify_regex=verify_regex,
                verify_choices=verify_choices,
            )

        except ConfigOptionNotFoundError:
            self.__logger.info(
                f"Config entry '{key}' for module '{module.display_name}' not found. "
                f"Using default value '{str(default_value)}' instead..."
            )

            return default_value

        except ConfigOptionVerificationError as e:
            self.__logger.warning(
                f"Config entry invalid. Using default value '{str(default_value)}' "
                f"instead. Details: {str(e)}"
            )

            return default_value
