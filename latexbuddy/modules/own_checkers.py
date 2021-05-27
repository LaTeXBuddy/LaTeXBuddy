from latexbuddy.buddy import LatexBuddy
from latexbuddy.modules import Module
from latexbuddy.problem import Problem, ProblemSeverity
from latexbuddy.texfile import TexFile
import latexbuddy.tools as tools
import re


class UnreferencedFiguresModule(Module):
    def __init__(self):
        self.tool_name = 'refcheck'
        self.cid = '0'
        self.severity = ProblemSeverity.INFO
        self.category = 'latex'

    def run_checks(self, buddy: LatexBuddy, file: TexFile) -> list[Problem]:
        tex = file.tex
        problems = []
        # key = self.tool_name + '_' + fig_num
        pattern = r'\\begin{figure}[\w\W]*?\\end{figure}'
        figures = re.findall(pattern, tex)
        len_label = len('label{')
        labels = {}
        for figure in figures:
            match = re.search(re.escape(figure), tex)
            absolute_position = match.span()[0]
            length = match.span()[1] - match.span()[0]
            split = figure.split('\\')
            for word in split:
                if re.search(re.escape('label{') + '.*' + re.escape('}'),
                             word) is not None:
                    label = word[len_label:len(word) - 2]
                    labels[label] = (absolute_position, length)
        for label in labels.keys():
            pos_len = labels[label]
            position = pos_len[0]
            length = pos_len[1]
            line, col, offset = tools.absolute_to_linecol(file.tex, position)
            if re.search(re.escape('\\ref{') + label + re.escape('}'), tex) is None:
                problems.append(
                    Problem(
                        position=(line, col),
                        text=label,
                        checker=self.tool_name,
                        category=self.category,
                        cid=self.cid,
                        file=file.tex_file,
                        severity=self.severity,
                        description=f'Figure {label} not referenced.',
                        key=self.tool_name + '_' + label,
                        length=length,
                        context=('\\label{', '}')
                    )
                )

        return problems
