# Environment setup

## OS

You can code on any system you want! However, since the project is in the first place targeted at the user of Unix-like systems, we highly recommend you install on. Here are some user-friendly distributions for you to try out:

- [Ubuntu] — probably, the most popular distro. Software Center, `snap` and `apt` will get you assessed with all the tools you need.
- [Fedora] — another very popular distro. A repo for PyCharm is shipped with the OS!

Ubuntu and Fedora offer different desktop environments. If you want a macOS-like experience with little clutter and sleek designs, choose GNOME-based variants (the default ones). If you are more familiar with Windows and/or want the highest degree of customizability, choose KDE- or XFCE-based versions (Kubuntu, Fedora KDE). If you only care about performance, choose Xfce-based versions (Xubuntu, Fedora Xfce).

Users of macOS should be fine on their own. It is however recommended they install [Homebrew] for easier package management.

Windows users can also try [WSL] and use Linux together with Windows with a good editor support (e.g. remote execution and debugging).

## Code Editor

LaTeXBuddy is a (relatively big) Python-based project, so editing it with just a Notepad would be silly. We recommend you install a "smart" code editor, like [Visual Studio Code], or an IDE, like [PyCharm]. Or, if you know what you're doing, you can use Vim.

### PyCharm

PyCharm offers the best toolchain for a developer, but can be a bit too heavy on CPU and RAM. Community edition will work fine, but for a better support for Web Frameworks (which partly power LaTeXBuddy) it is recommended you use the Professional version. [It can be obtained for free if you're a student or a teacher][jetbrains education].

## Git

Make sure you've got [Git] installed.

If you're on macOS or Linux, you either already have it installed or can easily install it from a package manager. For macOS use [Homebrew], for other Linux repos it can be different; consult Google for "{DISTRO} package manager".

If you use Windows (without WSL), install Git from the [official website][git]. Choose "Git Bash" as your shell as it offers a Linux-like experience.

Most of Git's initial settings are okay, however it still needs to be configured. First and foremost, your name and email; execute the following commands:

```sh
git config --global user.name "Max Mustermann"  # replace with your name
git config --global user.email "m.mustermann@example.de"  # replace with your email
```

You can also set this up on a per-project basis. Navigate to the repository and replace `--global` with `--local` in the commands above. This will update your email and name for the repository you're in.

When a Git conflict comes our way, we want to rebase our changes rather than merge them — this makes the git tree look cleaner. Execute

```sh
git config --global pull.rebase true
```

### Client

For easier work you may want to use a Git GUI client. Luckily, there is a plethora of choices for you! VSCode and PyCharm offer very robust built-in Git editors. Other good choices include, but are not limited to: [Fork], [GitHub Desktop], [GitKraken], [Sourcetree], etc.

## Python

Obviously, a version of [Python] is required for you to develop LaTeXBuddy.

It is recommended, that the development is done using the latest Python 3 version (as this is written, it's 3.11.1). However, since the app aims to support Python versions down to 3.7, it is also recommended, that you have this version installed as well.

> **Note:** on Ubuntu and other Debian-based distros it takes a long time until the newest Python version arrives to the package manager repositories. It can be, that 3.8 is the newest version you can install. It's okay; however, if you want to have the newest version, use a Python version manager or build the needed version from sources.

To be able to "juggle" around Python versions easily, a Python version manager is recommended. [pyenv] is pretty much the standard.

Windows users can also install both Python 3.7 and Python 3.11 from .exe installers and set up their editors to use separate versions for separate occasions.

## Tox

[Tox] is the environment manager and runner that we use. It is crucial that you install it. You can install it via `pip`; consult [the official installation instructions](https://tox.wiki/en/latest/installation.html).

## pre-commit

Last but not least, we use [pre-commit] for Git hook management. It will run all the linting and formatting tools every time you commit, so you won't forget it.

Install [pre-commit] as described on the website, and install the hooks:

```sh
pre-commit install
```

[fedora]: https://getfedora.org/
[fork]: https://fork.dev/
[git]: https://git-scm.com/
[github desktop]: https://desktop.github.com/
[gitkraken]: https://www.gitkraken.com/
[homebrew]: https://brew.sh/
[jetbrains education]: https://www.jetbrains.com/community/education/
[pre-commit]: https://pre-commit.com/
[pycharm]: https://www.jetbrains.com/pycharm/
[pyenv]: https://github.com/pyenv/pyenv
[python]: https://www.python.org/
[sourcetree]: https://www.sourcetreeapp.com/
[tox]: https://tox.wiki/
[ubuntu]: https://ubuntu.com/
[visual studio code]: https://code.visualstudio.com/
[wsl]: https://docs.microsoft.com/windows/wsl/
