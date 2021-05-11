from typing import Any


class ConfigLoader:
    def __init__(self, config_file_path: str):

        self.config_file_path = config_file_path
        self.configurations = {}

    def load_configurations(self) -> None:
        raise NotImplementedError()

    def get_config_option(self, tool_name: str, key: str) -> Any:
        raise NotImplementedError()

    def get_config_option_or_default(
        self, tool_name: str, key: str, default_value: Any
    ) -> Any:

        raise NotImplementedError()
