<h1>
<img src="docs/_static/logotype-light@2x.png" width="240" alt="LaTeXBuddy">
</h1>

> The only LaTeX checking tool you'll ever need.

LaTeXBuddy is the checking tool for LaTeX, which combines the power of various
other tools in one easy-to-use command-line tool with clear HTML output.

Aspell, ChkTeX, LanguageTool: you name it! LaTeXBuddy is modular and
Python-based, so that implementing new functionality becomes a breeze!

## Project status

LaTeXBuddy is a work in progress. We are working on fixing bugs and cleaning up.
Using LaTeXBuddy in its current state may come with a lot of inconveniences.

Upon reaching the Beta status, we will open-source this project. For now, it
remains copyrighted, yet you're free to fork it and provide your edits and
improvements to the code base.

## Install and Use

The following guide is an exeprimental Docker build of LaTeXBuddy. Proceed with
caution.

### Use with Docker

**Prerequisites:** [Docker](https://www.docker.com/products/docker-desktop)

The image is sadly not being distributed yet, so you have to build it yourself.
It isn't complicated, but it takes around 7 minutes on a MacBook Pro and takes
about 8 GB of extra space (the built container is around 1,15 GB). Once built,
the image can be reused.

1. Build the image and tag it:

    ```sh
    docker build -t latexbuddy/latexbuddy .
    ```

2. To run the image once, run the following command:

    ```sh
    docker run --rm -v $(pwd):/latexbuddy latexbuddy/latexbuddy file_to_check.tex
    ```

    This will create a container, run the command on the file `file_to_check.tex`
    in your current directory. If you wish to set another directory as root,
    change `$(pwd)` to the desired path.

3. If you often check one file, you may want to create a container and run it
   without discarding it.

    1. First, create a container:

        ```sh
        docker create --name lb -v $(pwd):/latexbuddy latexbuddy/latexbuddy file_to_check.tex
        ```

        The container will have the name `lb` — you are free to choose
        a different one.

    2. Every time you want to run checks, run:

        ```sh
        docker start -a lb
        ```

        The `-a` option redirects the output in your terminal, so you can see the
        output.

    3. After finishing, remove the container:

        ```sh
        docker rm lb
        ```

## Authors

LaTeXBuddy was created as part of SEP (Software Development Internship) at the
TU Braunchweig. You can find the complete author list in the [AUTHORS](AUTHORS)
file.

## Licence

Generally speaking, LaTeXBuddy is licensed under the
[GNU General Public License v3.0 or later][gpl-3.0-or-later] with docs licensed
under the [GNU Free Documentation License v1.3 or later][gfdl-1.3-or-later].

For information on which file is licensed under which licence, take a look at
the [DEP-5 (`debian/copyright`)](./.reuse/dep5) file.

### Source code

LaTeXBuddy\
Copyright © 2021-2022 [LaTeXBuddy authors](./AUTHORS)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

### Documentation

LaTeXBuddy documentation\
Copyright © 2021-2022 [LaTeXBuddy authors](./AUTHORS)

Permission is granted to copy, distribute and/or modify this document
under the terms of the GNU Free Documentation License, Version 1.3
or any later version published by the Free Software Foundation;
with no Invariant Sections, no Front-Cover Texts, and no Back-Cover Texts.

### Complementary files

Smaller files are licensed either under the [Apache License 2.0][apache-2.0] or
are in public domain as per [Creative Commons Zero v1.0 Universal][cc0-1.0].

---

This project is hosted on GitLab:
<https://gitlab.com/LaTeXBuddy/LaTeXBuddy.git>

[apache-2.0]: https://spdx.org/licenses/Apache-2.0.html
[cc0-1.0]: https://spdx.org/licenses/CC0-1.0.html
[gfdl-1.3-or-later]: https://spdx.org/licenses/GFDL-1.3-or-later.html
[gpl-3.0-or-later]: https://spdx.org/licenses/GPL-3.0-or-later.html
