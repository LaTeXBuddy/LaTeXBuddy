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

LaTeXBuddy is temporarily copyrighted. You can expect it to become open-source
later this year (we're thinking of GPL).

The LaTeXBuddy logo is based on the
[Origami](https://www.flaticon.com/free-icon/origami_2972006) icon,
made by [Freepik](https://www.freepik.com)
from [www.flaticon.com](https://www.flaticon.com/).
