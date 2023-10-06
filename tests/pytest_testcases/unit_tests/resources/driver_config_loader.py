class ConfigLoader:
    def __init__(self):
        pass

    def get_config_option_or_default(
        self,
        module,
        key: str,
        default_value=None,
        verify_type=None,
        verify_regex=None,
        verify_choices=None,
    ):
        if key == "language":
            return "en"
        if key == "language_country":
            return None
        if key == "mode":
            return "COMMANDLINE"
        if key == "disabled-rules":
            return ""
        if key == "disabled-categories":
            return ""
        if key == "format":
            return "not html"

    def get_config_option(
        self,
        module,
        key: str,
    ):
        if key == "format":
            return "json"
