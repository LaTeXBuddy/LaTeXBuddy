import importlib.util as importutil
import sys
import traceback

from argparse import Namespace
from pathlib import Path
from typing import Any, Dict


class ConfigOptionNotFoundError(Exception):
    pass


class ConfigLoader:
    def __init__(self, cli_arguments: Namespace):

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
        # filter out none-parameters
        parsed = {"latexbuddy": {}}

        args_dict = vars(args)

        for key in args_dict:
            if args_dict[key]:
                parsed["latexbuddy"][key] = args_dict[key]

        return parsed

    def load_configurations(self, config_file_path: Path) -> None:

        try:
            spec = importutil.spec_from_file_location("config", config_file_path)
            config = importutil.module_from_spec(spec)
            spec.loader.exec_module(config)

            self.configurations = config.modules

        except Exception as e:

            print(
                f"An error occurred while loading config file at "
                f"'{self.config_file_path}':\n",
                f"{e.__class__.__name__}: {getattr(e, 'message', e)}",
                file=sys.stderr,
            )
            traceback.print_exc(file=sys.stderr)

    def __get_option(
        self, config_dict: Dict, tool_name: str, key: str, error_indicator="config"
    ) -> Any:

        if tool_name not in config_dict or key not in config_dict[tool_name]:
            raise ConfigOptionNotFoundError(
                f"Tool: {tool_name}, key: {key} ({error_indicator})"
            )

        return config_dict[tool_name][key]

    def get_config_option(self, tool_name: str, key: str) -> Any:

        try:
            return self.__get_option(self.flags, tool_name, key, "flag")
        except ConfigOptionNotFoundError:
            pass

        return self.__get_option(self.configurations, tool_name, key)

    def get_config_option_or_default(
        self, tool_name: str, key: str, default_value: Any
    ) -> Any:

        try:
            return self.get_config_option(tool_name, key)
        except ConfigOptionNotFoundError:
            return default_value
