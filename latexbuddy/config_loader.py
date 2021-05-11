import importlib.util as importutil
import sys
import traceback

from typing import Any


class ConfigLoader:
    def __init__(self, config_file_path: str):

        if not config_file_path:
            raise AttributeError("Path of the config file must be specified!")

        self.config_file_path = config_file_path
        self.configurations = {}

        self.load_configurations()

    def load_configurations(self) -> None:

        try:
            spec = importutil.spec_from_file_location("config", self.config_file_path)
            config = importutil.module_from_spec(spec)
            spec.loader.exec_module(config)

            self.configurations = config.modules

        except FileNotFoundError:
            print(
                f"Could not find a config file at '{self.config_file_path}'. ",
                f"Using default configurations...",
                file=sys.stderr,
            )

        except Exception as e:

            print(
                f"An error occurred while loading config file at "
                f"'{self.config_file_path}':\n",
                f"{e.__class__.__name__}: {getattr(e, 'message', e)}",
                file=sys.stderr,
            )
            traceback.print_exc(file=sys.stderr)

    def get_config_option(self, tool_name: str, key: str) -> Any:
        raise NotImplementedError()

    def get_config_option_or_default(
        self, tool_name: str, key: str, default_value: Any
    ) -> Any:

        raise NotImplementedError()
