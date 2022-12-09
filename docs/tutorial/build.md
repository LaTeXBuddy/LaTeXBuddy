# Build from source

## With Docker

```{caution}
The following is an experimental Docker build of LaTeXBuddy. It is not optimized and very unstable.
```

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
