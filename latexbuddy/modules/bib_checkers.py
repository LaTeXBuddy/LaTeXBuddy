import json
import re
import time

from difflib import SequenceMatcher
from multiprocessing.dummy import Pool as ThreadPool
from pathlib import Path
from typing import List, Optional

import bibtexparser
import requests

from bibtexparser.bibdatabase import UndefinedString

from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules import Module
from latexbuddy.problem import Problem, ProblemSeverity
from latexbuddy.texfile import TexFile


# TODO: logger


def get_bibfile(file: TexFile) -> Optional[Path]:
    """Checks the given file text for a \bibliography{} command and returns the full
    path of the input BibTeX file. For now only works with a single BibTeX file.

    :param file: TexFile object of the LaTeX file to check
    :return:
    """
    tex = file.tex
    path = file.tex_file
    pattern = r"\\bibliography\{([A-Za-z0-9_/-]+)\}"  # TODO: improve the pattern
    # in particular space
    m = re.search(pattern, tex)

    if m is None:  # TODO: maybe log this
        # raise ValueError("No valid bibliography found in the .tex at {path}")
        return None

    path = str(path)[: -len(path.parts[-1])]  # remove filename
    bib_path = Path(path + m.group(1) + ".bib")

    if not bib_path.exists():
        raise FileNotFoundError(f"No bibliography found at {bib_path}")

    return bib_path  # assuming theres only one bibtex file


def parse_bibfile(bibfile: Path) -> (str, str, str):
    """Parses the given BibTeX file to extract the publications

    :param bibfile: Path object of the BibTeX file to be parsed
    :return: the title, year, and BibTeX Id of each publication as 3-Tuple
    """
    with bibfile.open() as bibtex_file:
        try:
            bib_database = bibtexparser.load(bibtex_file)
            entries = bib_database.entries
        # catch error that is raised if the bibtex file is not correctly formatted
        except UndefinedString as e:
            raise ValueError(
                f'Error in the .bib; prob no "" or parenthesis used here: {str(e)}'
            )

    results = []
    for entry in entries:
        try:
            """if (entry["ENTRYTYPE"] == "inproceedings"):"""
            t = entry["title"]
            # remove parenthesis from start/end of title for better comparison later on
            while t[0] == "{" or t[0] == "(":
                t = t[1:]
            while t[-1] == "}" or t[-1] == ")":
                t = t[:-1]
            results.append((t, entry["year"], entry["ID"]))
        except KeyError:
            pass

    return results


class NewerPublications(Module):
    def __init__(self):
        self.tool_name = "newer_publication"
        self.severity = ProblemSeverity.INFO
        self.category = "latex"
        self.time = 0
        self.found_pubs = []
        self.debug = False

    def check_for_new(self, publication: (str, str), s) -> (str, str, str, (str, str)):
        # send requests
        # ex: https://dblp.org/search/publ/api?format=json&q=In%20Search%20of%20an%20Understandable%20Consensus%20Algorithm

        c_returns = 4  # number of max returns from the request
        x = s.get(
            f"https://dblp.org/search/publ/api?format=json&h={c_returns}&q={publication[0]}"
        )
        ret = json.loads(x.text)["result"]

        # time keeping
        self.time += float(ret["time"]["text"])
        if self.debug:
            print(ret["time"]["text"])

        try:
            # TODO: handle multiple newer publications found
            for hit in ret["hits"]["hit"]:
                # found publication is not newer
                if int(hit["info"]["year"]) <= int(publication[1]):
                    continue

                title = hit["info"]["title"]
                if title[-1] == ".":  # remove . at the end, dblp adds it sometimes
                    title = title[:-1]

                # Check if the title is somewhat similar to the one from BibTeX
                sim = SequenceMatcher(
                    None, title.upper(), publication[0].upper()
                ).ratio()
                if sim < 0.85:
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

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:
        bib_file = get_bibfile(file)

        if bib_file is None:
            # No bib_file found
            return []

        used_pubs = parse_bibfile(bib_file)

        a = time.time()

        s = requests.session()
        for pub in used_pubs:
            self.check_for_new(pub, s)

        """
        with ThreadPool(4) as p:
            p.map(self.check_for_new, used_pubs)
        """

        if self.debug:
            print(f"\n\ndblp requests took {round(time.time() - a, 3)} seconds")
            print(self.time)
            print(f'{len(used_pubs)} entries found in "{bib_file}"\n')

        output_format = config.get_config_option(LatexBuddy, "format")
        html_formats = {"html", "HTML"}
        problem_text = "BibTeX outdated: "
        problems = []

        for pub in self.found_pubs:
            bibtex_id = pub[3][2]
            if output_format in html_formats:  # HTML tags if output to HTML page
                suggestion = (
                    f'Potential newer version "<i>{pub[0]}</i>" from '
                    f'<b>{pub[1]}</b> at <a href="{pub[2]}"'
                    f'target="_blank">{pub[2]}</a>'
                )
            else:
                suggestion = (
                    f'Potential newer version "{pub[0]}" from {pub[1]} at {pub[2]}'
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
                    key=self.tool_name + "_" + bibtex_id,
                )
            )
        return problems


class BibtexDuplicates(Module):
    def __init__(self):
        self.tool_name = "bibtex_duplicate"
        self.severity = ProblemSeverity.INFO
        self.category = "latex"
        self.found_duplicates = []
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

    def compare_entries(self, entry_1, entry_2) -> None:
        ids = (entry_1["ID"], entry_2["ID"])
        same_keys = set(entry_1.keys()).intersection(set(entry_2.keys()))
        same_keys.remove("ID")
        total_ratio = 0
        for key in same_keys:
            total_ratio += SequenceMatcher(
                None, self.clean_str(entry_1[key]), self.clean_str(entry_2[key])
            ).ratio()
        ratio = total_ratio / len(same_keys)
        if ratio > 0.85:
            if self.debug:
                print(
                    f"------------------\n{ratio}\n{entry_1}\n{entry_2}\n------------------"
                )
            self.found_duplicates.append(ids)

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:

        bib_file = get_bibfile(file)

        if bib_file is None:
            # No bib_file found
            return []

        with bib_file.open() as bibtex_file:
            try:
                bib_database = bibtexparser.load(bibtex_file)
                entries = bib_database.entries
            # catch error that is raised if the bibtex file is not correctly formatted
            except UndefinedString as e:
                raise ValueError(
                    f'Error in the .bib; prob no "" or parenthesis used here: {str(e)}'
                )

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
                    key=f"{self.tool_name}_{dup_ids[0]}_{dup_ids[1]}",
                )
            )

        return problems
