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



# build diction
FROM alpine:latest AS build-diction

# download diction
RUN wget 'http://www.moria.de/~michael/diction/diction-1.14.tar.gz' \
    && tar -xzf diction-1.14.tar.gz

# build diction
WORKDIR /diction-1.14
RUN apk add build-base
RUN ./configure && make



# build languagetool
FROM debian:buster AS build-languagetool

RUN apt-get update -y
RUN apt-get install -y \
    git \
    maven \
    openjdk-11-jdk-headless \
    unzip

RUN git clone --depth 1 https://github.com/languagetool-org/languagetool.git --branch v5.3

WORKDIR /languagetool
RUN mvn clean
RUN mvn package -DskipTests
RUN unzip languagetool-standalone/target/*.zip -d /dist



# build chktex
FROM alpine:latest AS build-chktex

# download chktex
RUN wget 'http://download.savannah.gnu.org/releases/chktex/chktex-1.7.6.tar.gz' \
    && tar -xzf chktex-1.7.6.tar.gz

# build chktex
WORKDIR /chktex-1.7.6
RUN apk add build-base
RUN ./configure --prefix /usr/local
RUN make
RUN chmod 644 chktexrc



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

# install diction
COPY --from=build-diction /diction-1.14/diction /usr/local/bin/diction

# install chktex
COPY --from=build-chktex /chktex-1.7.6/chktex /usr/local/bin/chktex
COPY --from=build-chktex /chktex-1.7.6/chktexrc /usr/local/etc/chktexrc

# install LanguageTool
RUN apk add libstdc++ openjdk11-jre-headless
COPY --from=build-languagetool /dist /languagetool
RUN echo "exec java -jar \"$(find /languagetool -maxdepth 2 -name languagetool-commandline.jar)\" \$@" > /usr/local/bin/languagetool \
    && chmod 755 /usr/local/bin/languagetool

ENTRYPOINT [ "latexbuddy" ]
