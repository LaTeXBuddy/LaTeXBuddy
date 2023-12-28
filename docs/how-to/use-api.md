# Using the API

```{admonition} New to LaTeXBuddy?
   :class: hint
 Please consider reading the [Beginners' Guide to Module development](module-development) first.
```

As you proceed developing your own module, you might want to simplify repeating processes and add some configuration options. Concerning that, LaTeXBuddy is offering its simple-to-use `ConfigLoader` and `tools` features.

## Using the `ConfigLoader`

The `ConfigLoader` offers a simple way to configure LaTeXBuddy to your needs by providing support for a config file and integrating CLI flags.

### Adding config options

LaTeXBuddy offers a default `config.py`, that can be tailored to your needs. To add your module and options to the `config.py`, follow these steps:

#### Add your module to `config.py`

To include your module into config, just add a new top-level entry into the `modules` dictionary consisting of your module class name as the `key` and an empty dictionary for the config options as the `value`.

_Example:_

```py
main = {...}

modules = {
    "YourModuleClassName": {},
}
```

#### Add options for your module

As you want to add some config options for your module, that's the next step to complete. Just add your desired options to the empty dictionary created beforehand.

_Example:_

```py
main = {...}

modules = {
    "YourModuleClassName": {
        "sample_option": "sample_value",
        "meaning_of_life": 42,
    },
}
```

```{note}
As you may want to use LaTeXBuddy's enable/disable function, an `"enabled":True/False` entry needs to be added to your configuration.
```

### Getting config options

Accessing configuration options generally requires two components: The first one is an instance or the type of a checker `Module`, or `None` for the configuration options of the main LaTeXBuddy instance.
The second one is `key` which is essentially a string of your choosing that identifies a specific configuration option.

Config values can also be verified by providing a type, regex (for strings) or a list of possible values, which is handled via the parameters `verify_type`, `verify_regex` and `verify_choices`.
If more than one verify parameter is specified, all specified requirements are checked. If a regex is provided, the `verify_type` parameter will always be set to `AnyStr` (even if another type was specified).

All configuration parameters are read from the config file that is specified in the Command Line call, but since CLI flags are translated to configuration options in `ConfigLoader` as well, they override any configuration option for the main LaTeXBuddy instance with the same key that might exist in the config file (e.g. "language", "output", "enable-modules-by-default" etc.).

`ConfigLoader` provides two functions for fetching configuration options:

#### `get_config_option(module, key, verify_type, verify_regex, verify_choices) -> Any`

This method fetches the value of the config entry with the specified key for the specified tool or raises a ConfigOptionNotFoundError, if such an entry doesn't exist.

Parameters:

- `module: Optional[Union[Type[NamedModule], NamedModule]]`: type or instance of the Module owning the config option
- `key: str`: key of the config option
- `verify_type: Type`: type that the config entry is required to be an instance of
- `verify_regex: Optional[str]`: regular expression that the config entry is required to match fully
- `verify_choices: Optional[Union[List[Any], Tuple[Any], Set[Any]]]`: a list/tuple/set of valid values in which the config entry is required to be contained

#### `get_config_option(module, key, default_value, verify_type, verify_regex, verify_choices) -> Any`

This method fetches the value of the config entry with the specified key for the specified tool or returns the specified default value, if such an entry doesn't exist.

Parameters:

- `module: Optional[Union[Type[NamedModule], NamedModule]]`: type or instance of the Module owning the config option
- `key: str`: key of the config option
- `default_value: Any`: default value in case the requested option doesn't exist
- `verify_type: Type`: type that the config entry is required to be an instance of
- `verify_regex: Optional[str]`: regular expression that the config entry is required to match fully
- `verify_choices: Optional[Union[List[Any], Tuple[Any], Set[Any]]]`: a list/tuple/set of valid values in which the config entry is required to be contained

## Using the included utilities

LaTeXBuddy offers a variety of utility methods in `tools.py` which mainly include functions for finding and executing shell commands or python functions and converting character positions between absolute indexing and line, column tuples. The concrete functions are:

### `kill_background_process(process: subprocess.Popen) -> None`

Kills a previously started background process by sending a `SIGTERM` signal.

**Parameters:**

- `process`: Popen object representing a running process. Accepts return values of `execute_background`.

### `execute_no_errors(*cmd: str, encoding: str = "ISO8859-1") -> str`

Executes a shell command via python's `subprocess` library and returns the contents of stdout as a string. Any output to stderr is ignored.

**Parameters:**

- `*cmd`: Tuple of strings representing the shell command and its flags and arguments
- _optional:_ `encoding`: string name of the encoding python uses to decode the contents in stdout

### `find_executable(name: str, to_install: Optional[str] = None, logger: Optional[Logger] = None, log_errors: bool = True) -> str`

Finds the path to a given executable with a call to `which`. Consequently, any executable that should be found must at least be in the user's `$PATH`.
Raises a `FileNotFoundError`, if the executable could not be located.

**Parameters:**

- `name`: name of the executable to be found
- _optional:_ `to_install`: correct name of the program or project which the requested executable belongs to (used in log messages, defaults to the value of `name`, if unspecified)
- _optional:_ `logger`: logger instance of the calling module, defaults to the standard logger for tools.py
- _optional:_ `log_errors`: specifies whether error messages should be logges as error (`True`) or debug (`False`) messages

### `absolute_to_linecol(text: str, position: int) -> Tuple[int, int, List[int]]`

Calculates the line and column of a given character from the absolute position of that character in a specific text.

**Parameters:**

- `text`: text containing the character
- `position`: absolute position of the character (0-based)

### `get_line_offsets(text: str) -> List[int]`

Calculates absolute character offsets for each line in the specified text and returns them as a list.

Indices correspond to the line numbers, but are 0-based. For example, if the first 4 lines contain 100 characters (including line breaks), `result[4]` will be 100. `result[0]` is always 0.

**Parameters:**

- `text`: the text to be processed

### `is_binary(file_bytes: bytes) -> bool`

Detects whether the bytes of a file contain binary code or not.
For correct detection, it is recommended, that at least 1024 bytes were read.

**Parameters:**

- `bytes`: bytes of a file

### `execute_no_exceptions(function_call: Callable[[], None], error_message: str, traceback_log_level: Optional[str] = None) -> None`

Calls a function and catches any Exception that is raised during this.
If an Exception is caught, the function is aborted and the error is logged, but as the Exception is caught, the program won't crash.

**Parameters:**

- `function_call`: python function to be executed
- _optional:_ `error_message`: custom error message passed to the logger, defaults to `"An error occurred while executing lambda function"`
- _optional:_ `traceback_log_level`: sets the log_level that is used to log the error traceback. If it is None, no traceback will be logged. Valid values are: "DEBUG", "INFO", "WARNING", "ERROR"
