from latexbuddy.buddy import LatexBuddy
from latexbuddy.modules import Module
from latexbuddy.problem import Problem, ProblemSeverity
from latexbuddy.texfile import TexFile
import re


class UnreferencedFiguresModule(Module):
    def __init__(self):
        self.tool_name = 'refcheck'
        self.cid = '0'
        self.severity = ProblemSeverity.INFO

    def run_checks(self, buddy: LatexBuddy, file: TexFile) -> list[Problem]:
        tex = file.tex
        problems = []
        # key = self.tool_name + '_' + fig_num
        pattern = r'\\begin{figure}[\w\W]*?\\end{figure}'
        figures = re.findall(pattern, tex)
        len_label = len('label{')
        labels = []
        for figure in figures:
            split = figure.split('\\')
            for word in split:
                if re.search(re.escape('label{') + '.*' + re.escape('}'),
                             word) is not None:
                    label = word[len_label:len(word) - 2]
                    labels.append(label)
        for label in labels:
            if re.search(re.escape('\\ref{') + label + re.escape('}'), tex) is None:
                problems.append(
                    Problem(
                        position=(0, 0),
                        text=label,
                        checker=self.tool_name,
                        cid=self.cid,
                        file=file.tex_file,
                        severity=self.severity,
                        description=f'Figure {label} not referenced.',
                        key=self.tool_name + '_' + label,
                    )
                )

        return problems
