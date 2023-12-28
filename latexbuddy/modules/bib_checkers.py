# LaTeXBuddy BibTeX-related checkers
# Copyright (C) 2021-2022  LaTeXBuddy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations

import json
import logging
import re
import time
from difflib import SequenceMatcher
from pathlib import Path

import bibtexparser
import requests
from bibtexparser.bibdatabase import UndefinedString

from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules import Module
from latexbuddy.problem import Problem
from latexbuddy.problem import ProblemSeverity
from latexbuddy.texfile import TexFile


LOG = logging.getLogger(__name__)


def get_bibfile(file: TexFile) -> Path | None:
    """Checks the given file text for a \bibliography{} command and returns the
    full path of the input BibTeX file. For now only works with a single BibTeX
    file.

    :param file: TexFile object of the LaTeX file to check
    :return:
    """
    tex = file.tex
    path = file.tex_file
    # TODO: improve the pattern
    pattern = r"\\bibliography\{([A-Za-z0-9_/-]+)\}"
    # in particular space
    m = re.search(pattern, tex)

    if m is None:  # TODO: maybe log this
        return None

    bib_path = path.parent / f"{m.group(1)}.bib"
    if not bib_path.exists():
        _msg = f"No bibliography found at {bib_path}"
        raise FileNotFoundError(_msg)

    return bib_path  # assuming theres only one bibtex file


def parse_bibfile(bibfile: Path) -> list[tuple[str, str, str]]:
    """Parses the given BibTeX file to extract the publications.

    :param bibfile: Path object of the BibTeX file to be parsed
    :return: the title, year, and BibTeX Id of each publication as
        3-Tuple
    """
    with bibfile.open() as bibtex_file:
        try:
            bib_database = bibtexparser.load(bibtex_file)
            entries: list[dict[str, str]] = bib_database.entries
        # catch error that is raised if the bibtex file is not correctly
        # formatted
        except UndefinedString as exc:
            _msg = (
                f"{str(bibfile)}:"
                f"Could not parse BibTeX file: "
                f"Invalid format: {str(exc)}",
            )
            raise ValueError(_msg) from exc

    results = []
    for entry in entries:
        try:
            """If (entry["ENTRYTYPE"] == "inproceedings"):"""
            title: str = entry["title"]
            # remove parenthesis from start/end of title for better comparison
            # later on
            while title[0] == "{" or title[0] == "(":
                title = title[1:]
            while title[-1] == "}" or title[-1] == ")":
                title = title[:-1]
            results.append((title, entry["year"], entry["ID"]))
        except KeyError:
            pass

    return results


class NewerPublications(Module):
    SIMILARITY_THRESHOLD = 0.85

    def __init__(self) -> None:
        self.severity = ProblemSeverity.INFO
        self.category = "latex"
        self.found_pubs: list[tuple[str, str, str, tuple[str, str, str]]] = []
        self.debug = False

    def check_for_new(
        self,
        publication: tuple[str, str, str],
        session: requests.Session,
    ) -> None:
        # send requests
        # Example:
        # https://dblp.org/search/publ/api?format=json&q=In%20Search%20of%20an%20Understandable%20Consensus%20Algorithm

        c_returns = 4  # number of max returns from the request
        x = session.get(
            f"https://dblp.org/search/publ/api"
            f"?format=json"
            f"&h={c_returns}"
            f"&q={publication[0]}",
        )
        ret = json.loads(x.text)["result"]

        try:
            # TODO: handle multiple newer publications found
            for hit in ret["hits"]["hit"]:
                # found publication is not newer
                if int(hit["info"]["year"]) <= int(publication[1]):
                    continue

                title = hit["info"]["title"]
                # remove period at the end, dblp adds it sometimes
                if title[-1] == ".":
                    title = title[:-1]

                # Check if the title is somewhat similar to the one from BibTeX
                sim = SequenceMatcher(
                    None,
                    title.upper(),
                    publication[0].upper(),
                ).ratio()
                if sim < self.SIMILARITY_THRESHOLD:
                    continue

                year = hit["info"]["year"]

                # use electronic edition if exists else dblp url
                try:
                    url = hit["info"]["ee"]
                except KeyError:
                    url = hit["info"]["url"]

                self.found_pubs.append((title, year, url, publication))

        except KeyError:
            pass  # if no hit found or incomplete

    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:
        bib_file = get_bibfile(file)

        if bib_file is None:
            # No bib_file found
            return []

        used_pubs = parse_bibfile(bib_file)

        start = time.perf_counter()

        s = requests.session()
        for pub in used_pubs:
            self.check_for_new(pub, s)

        LOG.debug(
            f"dblp requests took "
            f"{round(time.perf_counter() - start, 3)} seconds",
        )
        LOG.debug(f'{len(used_pubs)} entries found in "{bib_file}"\n')

        output_format = config.get_config_option(LatexBuddy, "format")
        html_formats = {"html", "HTML"}
        problem_text = "BibTeX outdated: "
        problems = []

        for found_pub in self.found_pubs:
            bibtex_id = found_pub[2]
            # HTML tags if output to HTML page
            if output_format in html_formats:
                suggestion = (
                    f'Potential newer version "<i>{found_pub[0]}</i>" from '
                    f'<b>{found_pub[1]}</b> at <a href="{found_pub[2]}"'
                    f'target="_blank">{found_pub[2]}</a>'
                )
            else:
                suggestion = (
                    f'Potential newer version "{found_pub[0]}" '
                    f"from {found_pub[1]} at {found_pub[2]}"
                )
            problems.append(
                Problem(
                    position=None,
                    text=bibtex_id,
                    checker=NewerPublications,
                    category=self.category,
                    file=file.tex_file,
                    severity=self.severity,
                    description=suggestion,
                    context=(problem_text, ""),
                    key=self.display_name + "_" + bibtex_id,
                ),
            )
        return problems


class BibtexDuplicates(Module):
    SIMILARITY_THRESHOLD = 0.85

    def __init__(self) -> None:
        self.severity = ProblemSeverity.INFO
        self.category = "latex"
        self.found_duplicates: list[tuple[str, str]] = []
        self.debug = False

    def clean_str(self, to_clean: str) -> str:
        try:
            while to_clean[0] == "{":
                to_clean = to_clean[1:]
            while to_clean[-1] == "}":
                to_clean = to_clean[:-1]
        except IndexError:
            # empty word or only parentheses
            return ""
        return to_clean.upper()

    def compare_entries(
        self,
        entry_1: dict[str, str],
        entry_2: dict[str, str],
    ) -> None:
        ids = (entry_1["ID"], entry_2["ID"])
        same_keys = set(entry_1.keys()).intersection(set(entry_2.keys()))
        same_keys.remove("ID")
        total_ratio: float = 0
        for key in same_keys:
            total_ratio += SequenceMatcher(
                None,
                self.clean_str(entry_1[key]),
                self.clean_str(entry_2[key]),
            ).ratio()
        ratio = total_ratio / len(same_keys)
        if ratio > self.SIMILARITY_THRESHOLD:
            LOG.debug(
                f"{entry_1} is probably a duplicate of {entry_2}. "
                f"Similarity ratio: {ratio}",
            )
            self.found_duplicates.append(ids)

    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:
        bib_file = get_bibfile(file)

        if bib_file is None:
            # No bib_file found
            return []

        with bib_file.open() as bibtex_file:
            try:
                bib_database = bibtexparser.load(bibtex_file)
                entries: list[dict[str, str]] = bib_database.entries
            # catch error that is raised if the bibtex file is not correctly
            # formatted
            except UndefinedString as exc:
                _msg = (
                    f"{str(bib_file)}: "
                    f"Could not parse BibTeX file: Invalid format: {str(exc)}"
                )
                raise ValueError(_msg) from exc

        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                self.compare_entries(entries[i], entries[j])

        context = "BibTeX duplicate: "
        description = (
            "Possible duplicate entries in the BibTeX file. These entries "
            "are really similar and might be redundant. It's recommended "
            "to compare them manually."
        )
        problems = []
        for dup_ids in self.found_duplicates:
            problem_text = f"{dup_ids[0]} <=> {dup_ids[1]}"
            problems.append(
                Problem(
                    position=None,
                    text=problem_text,
                    checker=BibtexDuplicates,
                    category=self.category,
                    file=file.tex_file,
                    severity=self.severity,
                    description=description,
                    context=(context, ""),
                    key=f"{self.display_name}_{dup_ids[0]}_{dup_ids[1]}",
                ),
            )

        return problems
