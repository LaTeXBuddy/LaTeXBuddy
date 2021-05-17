"""This module describes the LaTeXBuddy config loader and its properties."""
import importlib.util as importutil
import sys
import traceback

from argparse import Namespace
from pathlib import Path
from typing import Any, Dict


class ConfigOptionNotFoundError(Exception):
    """Describes a ConfigOptionNotFoundError.

    This error is raised when a requested config entry doesn't exist.
    """

    pass


class ConfigLoader:
    """Describes a ConfigLoader object.

    The ConfigLoader processes LaTeXBuddy's cli arguments and loads the specified
    config file or the default config file, if none is specified.
    ConfigLoader also offers methods for accessing config entries with the option
    to specify a default value on Failure.
    """

    def __init__(self, cli_arguments: Namespace):
        """Creates a ConfigLoader module.

        :param cli_arguments: The commandline arguments specified in the LaTeXBuddy call
        """

        self.flags = ConfigLoader.__parse_flags(cli_arguments)
        self.configurations = {}

        if not cli_arguments.config:
            print("No configuration file specified. Using default values...")
            return

        if cli_arguments.config.exists():
            self.load_configurations(cli_arguments.config)
        else:
            print(
                "Specified config file does not exist. Using default values...",
                file=sys.stderr,
            )

    @staticmethod
    def __parse_flags(args: Namespace) -> Dict[str, Dict[str, Any]]:
        """This private helper-function parses commandline arguments into a dictionary.

        :param args: commandline arguments specified at the start of LaTeXBuddy
        :return: a formatted dictionary containing all cli flags as config entries with
            the label "latexbuddy"
        """
        # filter out none-parameters
        parsed = {"latexbuddy": {}}

        args_dict = vars(args)

        for key in args_dict:
            if args_dict[key]:
                parsed["latexbuddy"][key] = args_dict[key]

        return parsed

    def load_configurations(self, config_file_path: Path) -> None:
        """This helper-function loads the contents of a specified config .py-file.

        :param config_file_path: config file to be loaded (.py)
        :return: None
        """

        try:
            spec = importutil.spec_from_file_location("config", config_file_path)
            config = importutil.module_from_spec(spec)
            spec.loader.exec_module(config)

            self.configurations = config.modules

        except Exception as e:

            print(
                f"An error occurred while loading config file at "
                f"'{config_file_path}':\n",
                f"{e.__class__.__name__}: {getattr(e, 'message', e)}",
                file=sys.stderr,
            )
            traceback.print_exc(file=sys.stderr)

    def __get_option(
        self, config_dict: Dict, tool_name: str, key: str, error_indicator="config"
    ) -> Any:
        """This private helper-function searches for a config entry in the specified
        dictionary (config or flags). It raises an error, if the requested config
        option is not specified in the specified dictionary.

        :param config_dict: dictionary to be searched
        :param tool_name: name of the tool owning the config option
        :param key: key of the config option
        :param error_indicator: custom string displayed in the error message on failure
        :return: the value of the requested config option, if it exists
        :raises: ConfigOptionNotFoundError, if the requested config option doesn't exist
        """

        if tool_name not in config_dict or key not in config_dict[tool_name]:
            raise ConfigOptionNotFoundError(
                f"Tool: {tool_name}, key: {key} ({error_indicator})"
            )

        return config_dict[tool_name][key]

    def get_config_option(self, tool_name: str, key: str) -> Any:
        """This method fetches the value of the config entry with the specified key for
        the specified tool or raises a ConfigOptionNotFoundError, if such an entry
        doesn't exist.

        :param tool_name: name of the tool owning the config option
        :param key: key of the config option
        :return: the value of the requested config option, if it exists
        :raises: ConfigOptionNotFoundError, if the requested config option doesn't exist
        """

        try:
            return self.__get_option(self.flags, tool_name, key, "flag")
        except ConfigOptionNotFoundError:
            pass

        return self.__get_option(self.configurations, tool_name, key)

    def get_config_option_or_default(
        self, tool_name: str, key: str, default_value: Any
    ) -> Any:
        """This method fetches the value of the config entry with the specified key for
        the specified tool or returns the specified default value, if such an entry
        doesn't exist.

        :param tool_name: name of the tool owning the config option
        :param key: key of the config option
        :param default_value: default value in case the requested option doesn't exist
        :return: the value of the requested config option or default_value, if the
            config option doesn't exist
        """

        try:
            return self.get_config_option(tool_name, key)
        except ConfigOptionNotFoundError:
            return default_value
