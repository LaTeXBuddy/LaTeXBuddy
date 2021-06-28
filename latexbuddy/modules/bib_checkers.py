import bibtexparser
import requests
import json
import time
import re

from bibtexparser.bibdatabase import UndefinedString
from pathlib import Path

import latexbuddy.tools as tools

from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules import Module
from latexbuddy.problem import Problem, ProblemSeverity
from latexbuddy.texfile import TexFile


class NewerPublications(Module):
    def __init__(self):
        self.tool_name = "newer_publication"
        self.severity = ProblemSeverity.INFO
        self.category = "latex"

    def __get_bibfile(self, file: TexFile):
        tex = file.tex
        path = file.tex_file
        pattern = r"\\bibliography\{([A-Za-z0-9_/-]+)\}"
        m = re.search(pattern, tex)

        if m is None:
            print(f"Error: No bibliography found in the .tex at {path}")
            return None  # No bibtex file found

        path = str(path)[: -len(path.parts[-1])]  # remove filename
        return Path(path + m.group(1) + ".bib")  # assuming theres only one bibtex file

    def __get_publications(self, bibfile: Path):
        with bibfile.open() as bibtex_file:
            bib_database = bibtexparser.load(bibtex_file)
            entries = bib_database.entries
        # print(entries)
        # print(len(entries))
        # duplicates https://stackoverflow.com/questions/9427163/remove-duplicate-dict-in-list-in-python
        results = []

        for _ in range(len(entries)):
            try:
                if (
                    entries[_]["ENTRYTYPE"] == "inproceedings"
                    or entries[_]["ENTRYTYPE"] == "article"
                ):
                    # TODO: what entry types?
                    results.append((entries[_]["title"], entries[_]["year"]))
                    # TODO: Error if one is empty
                    # print(entries[_]["title"])
                    # print(entries[_]["year"])
            except KeyError:
                pass
        return results

    def check_for_new(self, publication: (str, str)):
        # send requests
        # ex: https://dblp.org/search/publ/api?format=json&q=In%20Search%20of%20an%20Understandable%20Consensus%20Algorithm
        # print(publication)
        x = requests.get(f'https://dblp.org/search/publ/api?format=json&q={publication[0]}')
        ret = json.loads(x.text)
        try:
            l = ret["result"]["hits"]["@total"]
            if int(l) < 2:
                return
            print()
            print(f"Found {l} entries:")
            for hit in ret["result"]["hits"]["hit"]:
                print(hit["info"]["year"])
                print(hit["info"]["title"])
                print(publication[0])
        except KeyError:
            # if no hit found
            pass

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:
        bib_file = self.__get_bibfile(file)

        # check if the referenced bibtex file exists
        if bib_file is None:
            return []

        if not bib_file.exists():
            print(f"Error: No bibliography found at {bib_file}")
            return []

        # catch error that is raised if the bibtex file is not correctly formatted
        try:
            used_pubs = self.__get_publications(bib_file)
        except UndefinedString as e:
            print(f'Error in the .bib; prob no "" or parenthesis used here: {str(e)}')
            return []

        a = time.time()
        for pub in used_pubs:
            self.check_for_new(pub)
            # print(f"Old entry: {pub}")

        print(f"dblp requests took {time.time() - a} seconds")
        print(f"{len(used_pubs)} entries found")

        return []
