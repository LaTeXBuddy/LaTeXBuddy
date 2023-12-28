# LaTeXBuddy - a LaTeX checking tool
# Copyright (C) 2021-2022  LaTeXBuddy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""This module describes the LaTeXBuddy config loader and its properties."""
import importlib.util
import logging
import re
from argparse import Namespace
from pathlib import Path
from typing import Any
from typing import AnyStr
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Type
from typing import TYPE_CHECKING
from typing import Union

from pydantic import BaseModel
from pydantic import ValidationError

import latexbuddy.tools
from latexbuddy.exceptions import ConfigOptionNotFoundError
from latexbuddy.exceptions import ConfigOptionVerificationError

if TYPE_CHECKING:
    from latexbuddy.modules import NamedModule

LOG = logging.getLogger(__name__)


class ConfigLoader:
    """Describes a ConfigLoader object.

    The ConfigLoader processes LaTeXBuddy's cli arguments and loads the
    specified config file or the default config file, if none is
    specified. ConfigLoader also offers methods for accessing config
    entries with the option to specify a default value on Failure.
    """

    _REGEX_LANGUAGE_FLAG = re.compile(
        r"([a-zA-Z]{2,3})(?:[-_\s]([a-zA-Z]{2,3}))?",
    )

    def __init__(self, cli_arguments: Optional[Namespace] = None):
        """Creates a ConfigLoader module.

        :param cli_arguments: The command-line arguments specified in
            the LaTeXBuddy call
        """

        self.main_configurations: Dict[str, Any] = {}
        self.module_configurations: Dict[str, Dict[str, Any]] = {}

        self.main_flags: Dict[str, Any] = {}
        self.module_flags: Dict[str, Dict[str, Any]] = {}

        if cli_arguments is None:
            LOG.debug(
                "No CLI arguments specified. Default values will be used.",
            )
            return

        if not cli_arguments.config:
            LOG.warning(
                "No configuration file specified. "
                "Default values will be used.",
            )
            return

        if cli_arguments.config.exists():
            self.load_configurations(cli_arguments.config)
        else:
            LOG.warning(
                f"File not found: {cli_arguments.config}. "
                f"Default configuration values will be used.",
            )

        self.main_flags, self.module_flags = self.__parse_flags(cli_arguments)

    def __parse_flags(
        self,
        args: Namespace,
    ) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """Parses and sorts command-line arguments into two dicts.

        The first :py:class:`dict` stores main-instance configuration,
        the second one stores the module-specific options.

        :param args: commandline arguments specified at the start of
                     LaTeXBuddy
        :return: a tuple of dictionaries, the first of which contains
                 configuration options for the main LatexBuddy instance
                 and the second of which contains all remaining options
                 for other modules
        """

        args_dict = {
            key: value for key, value in vars(args).items() if
            value is not None
        }

        parsed_main, parsed_modules = self.__parse_args_dict(args_dict)

        LOG.debug(
            f"Parsed CLI config options (main):\n{str(parsed_main)}\n\n"
            f"Parsed CLI config options (modules):\n{str(parsed_modules)}",
        )

        return parsed_main, parsed_modules

    def __parse_args_dict(
        self,
        args_dict: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """This private helper function parses the preprocessed args_dict
        (without None-elements).

        :param args_dict: preprocessed dictionary to be parsed
        """
        parsed_main: dict[str, Any] = {}
        parsed_modules: dict[str, dict[str, Any]] = {}

        # mutual exclusion of enable_modules and disable_modules
        # is guaranteed by argparse library
        flag_function_map: Dict[
            str,
            Callable[
                [Any, Dict[str, Any], Dict[str, Dict[str, Any]]],
                Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]],
            ],
        ] = {
            "enable_modules": self.__parse_flag_enable_modules,
            "disable_modules": self.__parse_flag_disable_modules,
            "language": self.__parse_flag_language,
        }

        for key in args_dict:

            if key in flag_function_map:

                parsed_main, parsed_modules = flag_function_map[key](
                    args_dict[key],
                    parsed_main,
                    parsed_modules,
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
        """This private helper-function parses the CLI flag '--
        enable_modules'."""

        parsed_main["enable-modules-by-default"] = False

        for module_name in self.module_configurations:
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
        """This private helper-function parses the CLI flag '--
        disable_modules'."""
        parsed_main["enable-modules-by-default"] = True

        for module_name in self.module_configurations:
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
        """This private helper-function parses the CLI flag '-- language'."""
        language_match = self._REGEX_LANGUAGE_FLAG.fullmatch(flag_value)

        if language_match is not None:

            parsed_main["language"] = language_match.group(1)

            if language_match.group(2) is not None:
                parsed_main["language_country"] = language_match.group(2)

        else:

            LOG.warning(
                f"Specified language '{flag_value}' is not a valid "
                f"language key. Please use a key in the following syntax: "
                f"<language>[-<country>] (e.g.: en-GB, en_US, de-DE)",
            )

        return parsed_main, parsed_modules

    def load_configurations(self, config_file_path: Path) -> None:
        """This helper-function loads the contents of a specified config.

        .py- file.

        :param config_file_path: config file to be loaded (.py)
        :return: None
        """

        def lambda_function() -> None:
            spec = importlib.util.spec_from_file_location(
                "config",
                config_file_path,
            )
            if spec is None or spec.loader is None:
                _msg = (
                    f"{str(config_file_path)}: "
                    "Import error: Couldn't find a suitable file loader"
                )
                raise ValueError(_msg)
            config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config)

            self.main_configurations = config.main
            self.module_configurations = config.modules

        latexbuddy.tools.execute_no_exceptions(
            lambda_function,
            f"An error occurred while loading config file at "
            f"'{str(config_file_path)}'",
        )

    @staticmethod
    def __get_option(
        config_dict: Dict[str, Any],
        module: "Optional[Union[Type[NamedModule], NamedModule]]",
        key: str,
        verify_type: Type = Any,  # type: ignore
        verify_regex: Optional[str] = None,
        verify_choices: Optional[
            Union[List[Any], Tuple[Any], Set[Any]]
        ] = None,
        error_indicator: str = "config",
    ) -> Any:
        """Searches for a config entry in the specified dictionary (config or
        flags).

        It raises an error, if the requested config option is not found
        in the dictionary or if the retrieved entry does not match
        specified criteria.

        :param config_dict: dictionary to be searched
        :param module: type or an instance of the module owning the
                       config option;
                       if unspecified, this method will treat the
                       ``config_dict`` as a dictionary for main
                       instance configuration entries
        :param key: key of the config option
        :param verify_type: typing type that the config entry is
                            required to be an instance of (otherwise
                            ``ConfigOptionVerificationError`` is
                            raised)
        :param verify_regex: regular expression that the config entry
                             is required to match fully (otherwise
                             ``ConfigOptionVerificationError`` is
                             raised)
                             Note: this overrides ``verify_type`` with
                             py:obj:`typing.AnyStr`
        :param verify_choices: a list/tuple/set of valid values in
                               which the config entry needs to be
                               contained in order to be valid
        :param error_indicator: custom string displayed in the error
                                message on failure
        :return: the value of the requested config option, if it exists
        :raises: ConfigOptionNotFoundError, if the requested config
                 option doesn't exist
        :raises: ConfigOptionVerificationError, if the requested config
                 option does not meet the specified criteria
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
                _msg = f"Module: {module_name}, key: {key} ({error_indicator})"
                raise ConfigOptionNotFoundError(_msg)

            entry = config_dict[key]

        else:
            module_name = module.display_name

            if module_name not in config_dict or key not in config_dict[
                    module_name
            ]:
                _msg = f"Module: {module_name}, key: {key} ({error_indicator})"
                raise ConfigOptionNotFoundError(_msg)

            entry = config_dict[module_name][key]

        # assert that entry type is a string, if regex check is applied
        if verify_regex is not None:
            verify_type = AnyStr  # type: ignore

        ConfigLoader.__verify_type(entry, verify_type, key, module_name)
        ConfigLoader.__verify_regex(entry, verify_regex, key, module_name)
        ConfigLoader.__verify_choices(entry, verify_choices, key, module_name)

        return entry

    @staticmethod
    def __verify_type(
        entry: Any,
        verify_type: Type,  # type: ignore
        key: str,
        module_name: str,
    ) -> None:
        # TODO: Documentation

        if verify_type is Any:
            return

        class TypeVerifier(BaseModel):
            cfg_entry: verify_type  # type: ignore

        try:
            TypeVerifier(cfg_entry=entry)
        except ValidationError as err:
            _msg = (
                f"config entry '{key}' for module '{module_name}' is of "
                f"type '{str(type(entry))}' (expected '{str(verify_type)}')"
            )
            raise ConfigOptionVerificationError(_msg) from err

    @staticmethod
    def __verify_regex(
        entry: Any,
        verify_regex: Optional[str],
        key: str,
        module_name: str,
    ) -> None:
        # TODO: Documentation

        if verify_regex is None:
            return

        pattern = re.compile(verify_regex)

        if pattern.fullmatch(entry) is None:
            _msg = (
                f"config entry '{key}' for module '{module_name}' "
                f"does not match the provided regular expression: "
                f"entry: '{entry}', "
                f"regex: '{verify_regex}'",
            )
            raise ConfigOptionVerificationError(_msg)

    @staticmethod
    def __verify_choices(
        entry: Any,
        verify_choices: Optional[Union[List[Any], Tuple[Any], Set[Any]]],
        key: str,
        module_name: str,
    ) -> None:
        # TODO: Documentation

        if verify_choices is None:
            return

        if entry not in verify_choices:
            _msg = (
                f"value '{str(entry)}' of config entry '{key}' for "
                f"module '{module_name}' is not contained in the specified "
                f"list of valid values: {str(verify_choices)}",
            )
            raise ConfigOptionVerificationError(_msg)

    # TODO: resolve circular import error between config_loader.py and
    #  modules.__init__.py when importing NamedModule
    def get_config_option(
        self,
        module: "Optional[Union[Type[NamedModule], NamedModule]]",
        key: str,
        verify_type: Type = Any,  # type: ignore
        verify_regex: Optional[str] = None,
        verify_choices: Optional[
            Union[List[Any], Tuple[Any], Set[Any]]
        ] = None,
    ) -> Any:
        """This method fetches the value of the config entry with the specified
        key for the specified tool or raises a ConfigOptionNotFoundError, if
        such an entry doesn't exist or the retrieved entry does not match a
        specified verification criterion.

        :param module: type or an instance of the module owning the
                       config option; if unspecified, this method will
                       look for a configuration option in the main
                       instance's dictionary
        :param key: key of the config option
        :param verify_type: typing type that the config entry is
                            required to be an instance of (otherwise
                            ``ConfigOptionVerificationError`` is raised)
        :param verify_regex: regular expression that the config entry
                             is required to match fully (otherwise
                             ``ConfigOptionVerificationError`` is
                             raised)

                             Note: this overrides verify_type with 'AnyStr'
        :param verify_choices: a list/tuple/set of valid values in
                               which the config entry needs to be
                               contained in order to be valid
        :return: the value of the requested config option, if it exists
        :raises: ConfigOptionNotFoundError, if the requested config
                 option doesn't exist
        :raises: ConfigOptionVerificationError, if the requested config
                 option does not meet the specified criteria
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
        module: "Optional[Union[Type[NamedModule], NamedModule]]",
        key: str,
        default_value: Any,
        verify_type: Type = Any,  # type: ignore
        verify_regex: Optional[str] = None,
        verify_choices: Optional[
            Union[List[Any], Tuple[Any], Set[Any]]
        ] = None,
    ) -> Any:
        """This method fetches the value of the config entry with the specified
        key for the specified tool or returns the specified default value, if
        such an entry doesn't exist or the retrieved entry does not match a
        specified verification criterion.

        :param module: type or an instance of the module owning the
                       config option; if unspecified, this method will
                       look for a configuration option in the main
                       instance's dictionary
        :param key: key of the config option
        :param default_value: default value in case the requested
                              option doesn't exist
        :param verify_type: typing type that the config entry is
                            required to be an instance of (otherwise
                            ``ConfigOptionVerificationError`` is raised)
        :param verify_regex: regular expression that the config entry
                             is required to match fully (otherwise
                             ``ConfigOptionVerificationError`` is raised).

                             Note: this overrides ``verify_type`` with
                             :py:obj:`typing.AnyStr`
        :param verify_choices: a list/tuple/set of valid values in
                               which the config entry needs to be
                               contained in order to be valid
        :return: the value of the requested config option or
                 ``default_value``, if the config option doesn't exist
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
            LOG.info(
                f"Config entry '{key}' "  # type: ignore
                f"for module '{module.display_name}' not found. "
                f"Using default value '{str(default_value)}' instead...",
            )

            return default_value

        except ConfigOptionVerificationError as e:
            LOG.warning(
                f"Config entry invalid. "
                f"Using default value '{str(default_value)}' "
                f"instead. Details: {str(e)}",
            )

            return default_value
