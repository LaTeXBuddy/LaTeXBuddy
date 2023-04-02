# LaTeXBuddy / Contributing

This file contains a short guide that will get you started with _LaTeXBuddy_
development. For more information, consult the [developer's guide] in our docs.

## Prerequisities

You'll need [Python] version 3.7 or newer. We recommend using the newest version
for development. You'll also need [pre-commit] for linting and formatting. [tox]
can used for environment management, but it's not required.

If you want to test all modules, you'll need extra dependencies, like [chktex],
[languagetool], etc.

We recommend you use a Unix-like OS for development (Linux, macOS, or BSD). We
do not guarantee support for Windows right now.

## Preparation

After cloning the repo, initialize the environment:

```sh
python3 -m virtualenv .venv  # if you don't have 'virtualenv', use 'venv'
source .venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt
```

Or, using tox:

```sh
tox devenv .venv
source .venv/bin/activate
```

On Windows, you can activate the virtualenv like so:

```ps
.venv\Scripts\activate.bat
```

> #### Tip
>
> If you use VSCode or PyCharm, every in-IDE terminal window
> will activate the environment automatically

To deactivate the shell, run `deactivate`.

## Developing

If you want to implement a feature or fix a bug, create a separate branch. The
branch name should be a very short explanation of what you want to do, written
in snake-case. Good examples: `add-languagetool` or
`fix-critical-error-in-chktex`. If the branch fixes/implements a specific issue,
prepend its number, like so: `119-fix-html-output`.

Work on the new branch and don't forget to commit your changes. Please don't put
every change into one commit (unless it's reasonable). When creating commits,
try to make them granular; this will make possible reverts easier.

Don't forget to write meaningful commit messages. The commit messages shall be
in English, imperatively phrased and possibly be shorter than 50 characters.

**Bad:** fix bug  
**Bad:** Fix the critical bug in the file mymodule.py which occured every time
one would try to run latexbuddy on Ubuntu 20.04 LTS...  
**Good:** Fix Ubuntu 20.04 related bug in mymodule.py

In commit body (aka description), mention the issue number, if applicable. This
way it'll be easier to track changes and issues.

On commit, `pre-commit` will lint your file for errors, wrong formatting, etc.

Push your branch and create a merge request to the `master` branch. Please name
your merge request in such a way, that it is clear what it does without opening
it. Provide additional description, when needed. Now, just wait for a review!

**Don't** use one branch for fixing multiple, not related features. **Don't**
ping reviewers endlessly.

## Further reading

In project's [developer's guide] there is a lot more information about how to
use our GitLab repo, create issues and merge requests, use CI/CD, and many other
topics. If you don't find something you're looking for, create an issue, and
we'll look into it!

Good luck!

[chktex]: https://www.nongnu.org/chktex/
[languagetool]: https://github.com/languagetool-org/languagetool
[python]: https://www.python.org/
[pre-commit]: https://pre-commit.com/
[tox]: https://tox.wiki/
[developer's guide]: https://latexbuddy.readthedocs.io/en/stable/#developer-s-guide
