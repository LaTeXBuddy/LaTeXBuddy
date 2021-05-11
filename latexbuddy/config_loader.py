from typing import Any


class ConfigLoader:
    def __init__(self, config_file_path: str):

        if not config_file_path:
            raise AttributeError("Path of the config file must be specified!")

        self.config_file_path = config_file_path
        self.configurations = {}

        self.load_configurations()

    def load_configurations(self) -> None:
        raise NotImplementedError()

    def get_config_option(self, tool_name: str, key: str) -> Any:
        raise NotImplementedError()

    def get_config_option_or_default(
        self, tool_name: str, key: str, default_value: Any
    ) -> Any:

        raise NotImplementedError()
