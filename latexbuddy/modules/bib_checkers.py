import bibtexparser
import requests
import json
import time
import re

from bibtexparser.bibdatabase import UndefinedString
from pathlib import Path
from typing import List
from difflib import SequenceMatcher

from multiprocessing.dummy import Pool as ThreadPool

from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules import Module
from latexbuddy.problem import Problem, ProblemSeverity
from latexbuddy.texfile import TexFile

# TODO: logger


def get_bibfile(file: TexFile) -> Path:
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

    if m is None:
        print(f"Error: No bibliography found in the .tex at {path}")
        return None  # No bibtex file found

    path = str(path)[: -len(path.parts[-1])]  # remove filename
    return Path(path + m.group(1) + ".bib")  # assuming theres only one bibtex file


def parse_bibfile(bibfile: Path) -> (str, str, str):
    """Parses the given BibTeX file to extract the publications

    :param bibfile: Path object of the BibTeX file to be parsed
    :return: the title, year, and BibTeX Id of each publication as 3-Tuple
    """
    with bibfile.open() as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
        entries = bib_database.entries

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

    def check_for_new(self, publication: (str, str), s) -> (str, str, str, (str, str)):
        # send requests
        # ex: https://dblp.org/search/publ/api?format=json&q=In%20Search%20of%20an%20Understandable%20Consensus%20Algorithm

        c_returns = 4  # number of max returns from the request
        x = s.get(f'https://dblp.org/search/publ/api?format=json&h={c_returns}&q={publication[0]}')
        ret = json.loads(x.text)["result"]

        # time keeping
        self.time += float(ret["time"]["text"])
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
                sim = SequenceMatcher(None, title.upper(),
                                      publication[0].upper()).ratio()
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
            raise ValueError("No valid path in the \\bibliography{} command")

        if not bib_file.exists():
            raise FileNotFoundError(f"No bibliography found at {bib_file}")

        # catch error that is raised if the bibtex file is not correctly formatted
        try:
            used_pubs = parse_bibfile(bib_file)
        except UndefinedString as e:
            print(f'Error in the .bib; prob no "" or parenthesis used here: {str(e)}')
            return []

        a = time.time()

        s = requests.session()
        for pub in used_pubs:
            self.check_for_new(pub, s)

        """
        with ThreadPool(4) as p:
            p.map(self.check_for_new, used_pubs)
        """

        print(f"\n\ndblp requests took {round(time.time() - a, 3)} seconds")
        print(self.time)
        print(f"{len(used_pubs)} entries found in \"{bib_file}\"\n")

        problems = []
        for pub in self.found_pubs:
            bibtex_id = pub[3][2]
            problem_text = f"BibTeX: "
            # TODO: maybe only do this if output format is html
            suggestion = f"Potential newer version \"<i>{pub[0]}</i>\" from {pub[1]} at <a href=\"{pub[2]}\"target=\"_blank\">{pub[2]}</a>"
            problems.append(
                Problem(
                    position=(0, 0),
                    text=bibtex_id,
                    checker=self.tool_name,
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
        pass

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:
        # check similar entries example
        # for pub in results:
        # print(SequenceMatcher(None, str(pub), str(results[0])).ratio())  # why slower with str???

        # duplicates https://stackoverflow.com/questions/9427163/remove-duplicate-dict-in-list-in-python
        pass
