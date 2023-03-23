# LaTeXBuddy / Contributing

This file contains a short guide that will get you started with _LaTeXBuddy_
development. For more information please consult the [wiki].

## Prerequisities

_LaTeXBuddy_ is a Python-based application.

-   **Required** for development
    -   [Python] version 3.7 or newer. It is recommended, that the newest version is
        used for development. At the time of writing it is 3.11
    -   [Hatch] is used for dependency management and building. You can install it
        using any method you like. Use the latest version
-   **Needed for modules to work**
    -   [chktex]
    -   [languagetool]

It is recommended that you use a \*nix-based OS for development (like GNU/Linux
or macOS). We do not guarantee complete tech support for developers running
Windows.

## Preparation

Hatch will handle creating and maintaining virtualenvs for you, so you don't
have to worry about it. To enter the virtual environment for development, run

```sh
hatch shell
```

This will make all installedcpackages available in your terminal. Note that
you'll need to do this every time you open a new terminal window.

> #### Helpful!
>
> If you use VSCode or PyCharm, every in-IDE terminal window
> will activate the environment automatically

To deactivate the shell, press <kbd>Ctrl</kbd>+<kbd>D</kbd>

## Building

To build the package, run

```sh
hatch build
```

This will create the `dist/` directory and generate the .tar.gz and .whl files,
which can be used to install the package

## Developing

If you want to implement a feature or fix a bug, create a separate branch. The
branch name should be a very short explanation of what you want to do, written
in snake-case (e.g., `add-languagetool` or `fix-critical-error-in-chktex`).

Work on the new branch and don't forget to commit your changes. Please don't put
everything into one commit (unless it's reasonable). When creating commits, try
to make them granular; imagine people wanting to revert or rearrange the commits
and try to make their job easier.

Don't forget to write meaningful commit messages. The commit messages shall be
in English, imperatively phrased and possibly be shorter than 50 characters.

**Bad:** fix bug  
**Bad:** Fix the critical bug in the file mymodule.py which occured every time
one would try to run latexbuddy on Ubuntu 20.04 LTS...  
**Good:** Fix Ubuntu 20.04 related bug in mymodule.py

In commit body aka description, mention the issue number, if applicable. This
way it'll be easier to track changes and issues.

On commit, a tool called pre-commit will lint your file for errors, wrong
formatting, etc.

Push your branch and create a merge request to the `master` branch. Please name
your merge request in such a way, that it is clear what it does without opening
it. Provide additional description, when needed. Now, just wait for a review!

**Don't** use one branch for fixing multiple, not related features. **Don't**
ping reviewers endlessly. **Don't** push directly to master.

## Installing from wheel

If you want to poke around your app, and you have the environment activated, you
can simply run `latexbuddy` in your terminal. If, however, you want to test the
installation on your or another computer, you can install the package from the
generated .whl file.

To do this, open a clean terminal and run the following command:

```sh
pip install path/to/latexbuddy-VERSION-py3-none-any.whl
```

This will install the package in global packages on another computer, as if it
was downloaded from PyPI. You can play around with it (or use it, even). To
uninstall it, run

```sh
pip uninstall latexbuddy
```

## Further reading

In project's [wiki] there is a lot more information about using our GitLab repo,
creating issues and merge requests, CI and CD as well as many other topics, well
organized and structured. If you don't find something you're looking for, create
an issue, and we'll look into it!

[chktex]: https://www.nongnu.org/chktex/
[hatch]: https://hatch.pypa.io/
[languagetool]: https://github.com/languagetool-org/languagetool
[python]: https://www.python.org/
[wiki]: https://gitlab.com/LaTeXBuddy/LaTeXBuddy/-/wikis/Development%20Guide
