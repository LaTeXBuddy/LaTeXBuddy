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
class NewerPublications(Module):
    def __init__(self):
        self.tool_name = "newer_publication"
        self.severity = ProblemSeverity.INFO
        self.category = "latex"
        self.time = 0

    def __get_bibfile(self, file: TexFile):
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

    def __parse_bibfile(self, bibfile: Path):
        with bibfile.open() as bibtex_file:
            bib_database = bibtexparser.load(bibtex_file)
            entries = bib_database.entries

        # duplicates https://stackoverflow.com/questions/9427163/remove-duplicate-dict-in-list-in-python
        results = []

        for _ in range(len(entries)):
            try:
                if (
                    True or entries[_]["ENTRYTYPE"] == "inproceedings"
                    or entries[_]["ENTRYTYPE"] == "article"
                ):
                    # TODO: what entry types?
                    a = entries[_]["title"]
                    while a[0] == "{":
                        a = a[1:]
                    while a[-1] == "}":
                        a = a[:-1]
                    results.append((a, entries[_]["year"]))
                    # TODO: Error if one is empty
                    # print(entries[_]["title"])
                    # print(entries[_]["year"])
            except KeyError:
                pass
        # check similar entries example
        # for pub in results:
            # print(SequenceMatcher(None, str(pub), str(results[0])).ratio())  # why slower with str???
        return results

    def check_for_new(self, publication: (str, str)):
        # send requests
        # ex: https://dblp.org/search/publ/api?format=json&q=In%20Search%20of%20an%20Understandable%20Consensus%20Algorithm
        c_returns = 4  # number of max returns from the request

        # session = requests.session()  # TODO: maybe add sessions for better performance
        x = requests.get(f'https://dblp.org/search/publ/api?format=json&h={c_returns}&q={publication[0]}')
        ret = json.loads(x.text)
        self.time += float(ret["result"]["time"]["text"])

        #print(ret["result"]["time"]["text"])
        try:
            n_hits = ret["result"]["hits"]["@total"]
            if int(n_hits) < 2:
                # only one result means that it's most probably the same article
                return

            # print(f"Found {l} entries:")
            for hit in ret["result"]["hits"]["hit"]:
                if int(hit["info"]["year"]) <= int(publication[1]):
                    continue
                title = hit["info"]["title"]
                if title[-1] == ".":  # remove . at the end, dblp adds it sometimes
                    title = title[:-1]
                sim = SequenceMatcher(None, title.upper(), publication[0].upper()).ratio()
                if sim < 0.85:  # Heuristic tuning parameter
                    continue
                year = hit["info"]["year"]

                #print()
                #print(year)
                #print(title)
                #print(f"Similarity: {sim}")
                #print(publication)
        except KeyError:
            pass  # if no hit found

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:
        bib_file = self.__get_bibfile(file)

        if bib_file is None:
            raise ValueError("No valid path in the \\bibliography{} command")

        if not bib_file.exists():
            raise FileNotFoundError(f"No bibliography found at {bib_file}")

        # catch error that is raised if the bibtex file is not correctly formatted
        try:
            used_pubs = self.__parse_bibfile(bib_file)
        except UndefinedString as e:
            print(f'Error in the .bib; prob no "" or parenthesis used here: {str(e)}')
            return []

        a = time.time()

        with ThreadPool(4) as p:
            p.map(self.check_for_new, used_pubs)

        print(f"\n\ndblp requests took {round(time.time() - a, 3)} seconds")
        print(self.time)
        print(f"{len(used_pubs)} entries found in \"{bib_file}\"\n")

        return []
