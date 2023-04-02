# Developing a module

Having worked with LaTeXBuddy for some time, you may want to add a checking tool that is not part of the project yet. Fortunately, this is fairly easy thanks to LaTeXBuddy's focus on modularity.

## Create a Python file for your module

Create a new .py file in `latexbuddy/modules/`. Within your file, add these import lines:

```py
from typing import List

from latexbuddy.config_loader import ConfigLoader
from latexbuddy.texfile import TexFile
from latexbuddy.modules import Module
from latexbuddy.problem import Problem
```

You are now able to create a class inheriting from the abstract `Module` class which provides an API function for you to implement. Here is an _example_ of how this could look like:

```py
class MyNewModule(Module):

    def __init__(self):
        pass

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:
        return []
```

```{note}
You are free to create as many other classes as needed, but remember that any class not inheriting from `Module` is ignored by LaTeXBuddy's module loader.
```

## Working with `TexFile`

The `TexFile` class encapsulates all information about the LaTeX file that is supposed to be checked. It offers these attributes:

- `tex`: contains the contents of the `.tex` file as a String (`str`)
- `plain`: contains the contents of the deTeXed version (plain text) of the `.tex` file as a String (`str`)
- `tex_file`: contains the `.tex` file's path as a `pathlib.Path` object
- `plain_file`: contains the deTeXed version (plain text) of the `.tex` file as a `pathlib.Path` object
- `is_faulty`: contains a boolean that is `True`, if the `.tex` file is invalid or contains syntax errors and `False` otherwise

`TexFile` also offers two methods to convert positions in the deTeXed text to the corresponding positions in the original LaTeX code:

- `get_position_in_tex(char_pos: int) -> Optional[Tuple[int, int]]`: Takes in the absolute position of a character in the deTeXed text and returns the line and column of the same character in the original LaTeX code. If the specified position is invalid, None is returned.
- `get_position_in_tex_from_linecol(line: int, col: int) -> Optional[Tuple[int, int]]`: Takes in the line and column of a character in the deTeXed text and returns the line and column of the same character in the original LaTeX code. If the specified position is invalid, None is returned.

## Working with `Problem`

The `Problem` class is a representation of a note/warning/error concerning a specific part of the text and is used as an interface between LaTeXBuddy and your module.  
A `Problem` can be constructed with the following parameters:

### `position: Tuple[int, int]` (optional)

A tuple specifying the problem's position in the checked `.tex` file and consists of two components: `(line_number, column_number)`. These numbers are referring to the position in the `.tex` file, NOT the deTeXed version.
If no position is specified, the Problem is considered _general_ and will appear in a different section than problems with a specific position.

```{note}
If you are checking the TeX version of the file and only have the absolute position of a problem, you can convert it using the first two return values of the [`absolute_to_linecol`](./use-api.md#using-the-included-utilities) method in `latexbuddy.tools`.
```

```{note}
If you are checking the deTeXed version of the file, you need to convert the position of the problematic text in the deTeXed text into the position of the same text in the original LaTeX code using either the [`get_position_in_tex`](#working-with-texfile) or the [`get_position_in_tex_from_linecol`](#working-with-texfile) method provided by `TexFile`, depending on whether you are working with absolute positions or line, column tuples.
```

### `text: str` (required)

A string containing the problematic part of the scanned text.

### `checker: Union[Type[NamedModule], NamedModule]` (required)

A `Module` instance or the type of a checker inheriting from `Module` (this is used to ensure that module names stay consistent throughout LaTeXBuddy outputs).

### `file: pathlib.Path` (required)

```{attention}
This is deprecated.
```

The path of the LaTeX file this problem refers to, given as a pathlib path.

### `p_type: Optional[str]`

_optional:_ A string containing an internal ID of the problem's category (e.g. 'double_whitespace' or 'missing_semicolon').

### `severity: ProblemSeverity = ProblemSeverity.WARNING`

_optional:_ an `Enum` specifying the level of severity for this problem. Valid values are:

- `NONE`: Problems are not being highlighted, but are still being output.

- `INFO`: Problems are highlighted with light blue color. These are suggestions; problems, that aren't criticizing the text.
  Example: suggestion to use "lots" instead of "a lot"

- `WARNING`: Problems are highlighted with orange color. These are warnings about problematic areas in documents. The files compile and work as expected, but some behavior may be unacceptable.
  Example: warning about using "$$" in LaTeX

- `ERROR`: Problems are highlighted with red color. These are errors, that prevent the documents to compile correctly.
  Example: not closed environment, or wrong LaTeX syntax

_defaults to:_ `ProblemSeverity.WARNING`

### `category: Optional[str]`

_optional:_ a string containing the name of this problem's broader category, for example "grammar", "spelling" or "latex".

_defaults to:_ `None`

### `description: Optional[str]`

_optional:_ a string containing a description of this problem or the reasoning behind it.

_defaults to:_ `None`

### `context: Optional[Tuple[str, str]]`

_optional:_ the context of the problematic part of the text, given as a tuple containing the text before and after the problematic part. Although the size of the context is not restricted, it is recommended not to give considerably more context than the sentence that contains the problem.

_defaults to:_ `None`

### `suggestions: List[str]`

_optional:_ suggestions to improve the problematic part of the text, given as a `List` of strings.

_defaults to:_ `None`

### `key: Optional[str]`

_optional:_ a semi-unique string used to compare two problems (possibly from different checking tools). This is used primarily for whitelisting, so be as precise as needed, without being overly specific. It is recommended to start the key with the name of your new tool to ensure uniqueness among all checking tools.\
If it's a pure **spelling tool** we recommend to put

```py
key = "spelling" + "_" + errortext
```

as it allows for a more universal whitelist. If not you can also try to isolate the spelling errors and then set the key like above.

If not set you will **not** be able to whitelist your Problems!

_defaults to:_ `None`

## Further Information

For advanced information to improve the capabilities of your module and to make your life easier, feel free to read the manual on [Advanced API](./use-api.md).
This page includes documentation for LaTeXBuddy's config and included utilities.
