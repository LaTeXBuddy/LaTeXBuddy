# build the LaTeXBuddy itself
FROM python:alpine AS build-latexbuddy

# install Poetry
ENV POETRY_HOME /etc/poetry
RUN wget 'https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py' \
	&& python get-poetry.py --no-modify-path \
	&& rm -rf get-poetry.py
ENV PATH /etc/poetry/bin:$PATH

# copy files
WORKDIR /latexbuddy
COPY pyproject.toml poetry.lock README.md CHANGELOG.md NOTICE ./
COPY ./latexbuddy ./latexbuddy

# install GCC and other libs for building
RUN apk add build-base

# build LaTeXBuddy
RUN poetry install && poetry build



# the end image itself
FROM python:alpine

WORKDIR /latexbuddy

# copy LaTeXBuddy installation wheel
COPY --from=build-latexbuddy /latexbuddy/dist/latexbuddy*.whl .

# install LaTeXBuddy
RUN pip install latexbuddy*.whl \
    && rm -rf latexbuddy*.whl

# install aspell
# TODO: manually supply other dictionaries
RUN apk add aspell aspell-de aspell-en aspell-fr aspell-ru aspell-uk

ENTRYPOINT [ "latexbuddy" ]
