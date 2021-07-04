"""This module describes the LaTeXBuddy config loader and its properties."""
import importlib.util as importutil
import re

from argparse import Namespace
from pathlib import Path
from typing import Any, AnyStr, Dict, List, Optional, Set, Tuple, Type, Union

from pydantic import BaseModel, ValidationError

import latexbuddy.tools as tools

from latexbuddy.exceptions import (
    ConfigOptionNotFoundError,
    ConfigOptionVerificationError,
)
from latexbuddy.log import Loggable


class ConfigLoader(Loggable):
    """Describes a ConfigLoader object.

    The ConfigLoader processes LaTeXBuddy's cli arguments and loads the specified
    config file or the default config file, if none is specified.
    ConfigLoader also offers methods for accessing config entries with the option
    to specify a default value on Failure.
    """

    _REGEX_LANGUAGE_FLAG = re.compile(r"([a-zA-Z]{2,3})(?:[-_\s]([a-zA-Z]{2,3}))?")

    def __init__(self, cli_arguments: Optional[Namespace] = None):
        """Creates a ConfigLoader module.

        :param cli_arguments: The commandline arguments specified in the LaTeXBuddy call
        """

        self.main_configurations: Dict[str, Any] = {}
        self.module_configurations: Dict[str, Dict[str, Any]] = {}

        self.main_flags: Dict[str, Any] = {}
        self.module_flags: Dict[str, Dict[str, Any]] = {}

        if cli_arguments is None:
            self.logger.debug(
                "No CLI arguments specified. Default values will be used."
            )
            return

        if not cli_arguments.config:
            self.logger.warning(
                "No configuration file specified. Default values will be used."
            )
            return

        if cli_arguments.config.exists():
            self.load_configurations(cli_arguments.config)
        else:
            self.logger.warning(
                f"File not found: {cli_arguments.config}. "
                f"Default configuration values will be used."
            )

        self.main_flags, self.module_flags = self.__parse_flags(cli_arguments)

    def __parse_flags(
        self, args: Namespace
    ) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """
        This private helper-function parses commandline arguments into two dictionaries:
        one for main-instance configurations and one for module configurations.

        :param args: commandline arguments specified at the start of LaTeXBuddy
        :return: a tuple of dictionaries, the first of which contains configuration
                 options for the main LatexBuddy instance and the second of which
                 contains all remaining options for other modules
        """

        args_dict = {
            key: value for key, value in vars(args).items() if value is not None
        }

        parsed_main, parsed_modules = self.__parse_args_dict(args_dict)

        self.logger.debug(
            f"Parsed CLI config options (main):\n{str(parsed_main)}\n\n"
            f"Parsed CLI config options (modules):\n{str(parsed_modules)}"
        )

        return parsed_main, parsed_modules

    def __parse_args_dict(
        self, args_dict: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:

        parsed_main = {}
        parsed_modules = {}

        # mutual exclusion of enable_modules and disable_modules
        # is guaranteed by argparse library
        flag_function_map = {
            "enable_modules": self.__parse_flag_enable_modules,
            "disable_modules": self.__parse_flag_disable_modules,
            "language": self.__parse_flag_language,
        }

        for key in args_dict:

            if key in flag_function_map:

                parsed_main, parsed_modules = flag_function_map[key](
                    args_dict[key], parsed_main, parsed_modules
                )

            else:
                parsed_main[key] = args_dict[key]

        return parsed_main, parsed_modules

    def __parse_flag_enable_modules(
        self,
        flag_value: Any,
        parsed_main: Dict[str, Any],
        parsed_modules: Dict[str, Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:

        parsed_main["enable-modules-by-default"] = False

        for module_name in self.module_configurations.keys():
            if module_name not in parsed_modules:
                parsed_modules[module_name] = {}

            parsed_modules[module_name]["enabled"] = False

        for module_name in flag_value.split(","):
            if module_name not in parsed_modules:
                parsed_modules[module_name] = {}

            parsed_modules[module_name]["enabled"] = True

        return parsed_main, parsed_modules

    def __parse_flag_disable_modules(
        self,
        flag_value: Any,
        parsed_main: Dict[str, Any],
        parsed_modules: Dict[str, Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:

        parsed_main["enable-modules-by-default"] = True

        for module_name in self.module_configurations.keys():
            if module_name not in parsed_modules:
                parsed_modules[module_name] = {}

            parsed_modules[module_name]["enabled"] = True

        for module_name in flag_value.split(","):
            if module_name not in parsed_modules:
                parsed_modules[module_name] = {}

            parsed_modules[module_name]["enabled"] = False

        return parsed_main, parsed_modules

    def __parse_flag_language(
        self,
        flag_value: Any,
        parsed_main: Dict[str, Any],
        parsed_modules: Dict[str, Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:

        language_match = self._REGEX_LANGUAGE_FLAG.fullmatch(flag_value)

        if language_match is not None:

            parsed_main["language"] = language_match.group(1)

            if language_match.group(2) is not None:
                parsed_main["language_country"] = language_match.group(2)

        else:

            self.logger.warning(
                f"Specified language '{flag_value}' is not a valid "
                f"language key. Please use a key in the following syntax: "
                f"<language>[-<country>] (e.g.: en-GB, en_US, de-DE)"
            )

        return parsed_main, parsed_modules

    def load_configurations(self, config_file_path: Path) -> None:
        """This helper-function loads the contents of a specified config .py-file.

        :param config_file_path: config file to be loaded (.py)
        :return: None
        """

        def lambda_function() -> None:
            spec = importutil.spec_from_file_location("config", config_file_path)
            config = importutil.module_from_spec(spec)
            spec.loader.exec_module(config)

            self.main_configurations = config.main
            self.module_configurations = config.modules

        tools.execute_no_exceptions(
            lambda_function,
            f"An error occurred while loading config file at '{str(config_file_path)}'",
        )

    @staticmethod
    def __get_option(
        config_dict: Dict,
        module,  # : Optional[Union[Type[NamedModule], NamedModule]],
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
        :param module: type or an instance of the module owning the config option; if
                       unspecified, this method will treat the config_dict as a
                       dictionary for main instance configuration entries
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

        # importing this here to avoid circular import error
        from latexbuddy.buddy import LatexBuddy

        if (
            module is None
            or isinstance(module, LatexBuddy)
            or (isinstance(module, type) and module == LatexBuddy)
        ):

            module_name = "LatexBuddy (main instance)"

            if key not in config_dict:
                raise ConfigOptionNotFoundError(
                    f"Module: {module_name}, key: {key} " f"({error_indicator})"
                )

            entry = config_dict[key]

        else:

            module_name = module.display_name

            if module_name not in config_dict or key not in config_dict[module_name]:
                raise ConfigOptionNotFoundError(
                    f"Module: {module_name}, key: {key} ({error_indicator})"
                )

            entry = config_dict[module_name][key]

        # assert that entry type is a string, if regex check is applied
        if verify_regex is not None:
            verify_type = AnyStr

        ConfigLoader.__verify_type(entry, verify_type, key, module_name)
        ConfigLoader.__verify_regex(entry, verify_regex, key, module_name)
        ConfigLoader.__verify_choices(entry, verify_choices, key, module_name)

        return entry

    @staticmethod
    def __verify_type(entry: Any, verify_type: Type, key: str, module_name: str):
        # TODO: Documentation

        if verify_type is Any:
            return

        class TypeVerifier(BaseModel):
            cfg_entry: verify_type

        try:
            TypeVerifier(cfg_entry=entry)
        except ValidationError:

            raise ConfigOptionVerificationError(
                f"config entry '{key}' for module '{module_name}' is of "
                f"type '{str(type(entry))}' (expected '{str(verify_type)}')"
            )

    @staticmethod
    def __verify_regex(
        entry: Any, verify_regex: Optional[str], key: str, module_name: str
    ):
        # TODO: Documentation

        if verify_regex is None:
            return

        pattern = re.compile(verify_regex)

        if pattern.fullmatch(entry) is None:
            raise ConfigOptionVerificationError(
                f"config entry '{key}' for module '{module_name}' does not match "
                f"the provided regular expression: entry: '{entry}', "
                f"regex: '{verify_regex}'"
            )

    @staticmethod
    def __verify_choices(
        entry: Any,
        verify_choices: Optional[Union[List[Any], Tuple[Any], Set[Any]]],
        key: str,
        module_name: str,
    ):
        # TODO: Documentation

        if verify_choices is None:
            return

        if entry not in verify_choices:
            raise ConfigOptionVerificationError(
                f"value '{str(entry)}' of config entry '{key}' for "
                f"module '{module_name}' is not contained in the specified list of "
                f"valid values: {str(verify_choices)}"
            )

    # TODO: resolve circular import error between config_loader.py and
    #  modules.__init__.py when importing NamedModule
    def get_config_option(
        self,
        module,  # : Optional[Union[Type[NamedModule], NamedModule]],
        key: str,
        verify_type: Type = Any,
        verify_regex: Optional[str] = None,
        verify_choices: Optional[Union[List[Any], Tuple[Any], Set[Any]]] = None,
    ) -> Any:
        """This method fetches the value of the config entry with the specified key for
        the specified tool or raises a ConfigOptionNotFoundError, if such an entry
        doesn't exist or the retrieved entry does not match a specified verification
        criterion.

        :param module: type or an instance of the module owning the config option; if
                       unspecified, this method will look for a configuration option
                       in the main instance's dictionary
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

        # importing this here to avoid circular import error
        from latexbuddy.buddy import LatexBuddy

        if (
            module is None
            or isinstance(module, LatexBuddy)
            or (isinstance(module, type) and module == LatexBuddy)
        ):

            try:
                return ConfigLoader.__get_option(
                    self.main_flags,
                    None,
                    key,
                    error_indicator="main flag",
                    verify_type=verify_type,
                    verify_regex=verify_regex,
                    verify_choices=verify_choices,
                )
            except ConfigOptionNotFoundError:
                pass

            return ConfigLoader.__get_option(
                self.main_configurations,
                None,
                key,
                error_indicator="main config",
                verify_type=verify_type,
                verify_regex=verify_regex,
                verify_choices=verify_choices,
            )

        else:

            try:
                return ConfigLoader.__get_option(
                    self.module_flags,
                    module,
                    key,
                    error_indicator="module flag",
                    verify_type=verify_type,
                    verify_regex=verify_regex,
                    verify_choices=verify_choices,
                )
            except ConfigOptionNotFoundError:
                pass

            return ConfigLoader.__get_option(
                self.module_configurations,
                module,
                key,
                error_indicator="module config",
                verify_type=verify_type,
                verify_regex=verify_regex,
                verify_choices=verify_choices,
            )

    # TODO: resolve circular import error between config_loader.py and
    #  modules.__init__.py when importing NamedModule
    def get_config_option_or_default(
        self,
        module,  # : Optional[Union[Type[NamedModule], NamedModule]],
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

        :param module: type or an instance of the module owning the config option; if
                       unspecified, this method will look for a configuration option
                       in the main instance's dictionary
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
            self.logger.info(
                f"Config entry '{key}' for module '{module.display_name}' not found. "
                f"Using default value '{str(default_value)}' instead..."
            )

            return default_value

        except ConfigOptionVerificationError as e:
            self.logger.warning(
                f"Config entry invalid. Using default value '{str(default_value)}' "
                f"instead. Details: {str(e)}"
            )

            return default_value
