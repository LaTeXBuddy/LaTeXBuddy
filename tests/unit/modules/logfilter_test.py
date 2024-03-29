#  LaTeXBuddy - a LaTeX checking tool
#  Copyright (c) 2023  LaTeXBuddy
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules.logfilter import LogFilter
from latexbuddy.texfile import TexFile

_DOCUMENT_CONTENTS = R"""\documentclass{article}
% \begin{document}
\chapter{Entwicklungsrichtlinien}

Dieses Kapitel beinhaltet Details zu dem Ablauf der Entwicklung der Software.


\section{Konfigurationsmanagement}

Dieser Abschnitt befasst sich mit dem Thema Konfigurationsmanagement. Hier werden unter anderem die Entwicklungsrichtlinien, -umgebung und der Release-Ablauf beschrieben.

\subsection{Source-Code-Repository}\label{angebot:entwicklungsrichtlinien:scm}

Der Source-Code des Projektes wird in einem Git-Repository auf dem Server vom GITZ\footnote{\url{https://git.rz.tu-bs.de/sw-technik-fahrzeuginformatik/sep/sep-2021/ibr_alg_0/latexbuddy}} bereitgestellt und verwaltet.

Im Git-Repository gelten für die von Nutzern erstellten Branches und Commits einige Richtlinien, die weiter beschrieben werden.

\subsubsection{Branching-Modell}

Die Entwicklung des Projektes erfolgt nach dem „Trunk Based Development“-Modell\footnote{\url{https://trunkbaseddevelopment.com/}}. Der Trunk-Branch heißt „\texttt{master}“ und beinhaltet immer eine korrekte, ausführbare Version des Projektes. Für Features und Bugfixes werden kurzlebige Branches erstellt, die durch Merge-Requests eingeführt werden.

\subsubsection{Commit-Richtlinien}

Im Repository gelten Commit-Richtlinien, die zu einer klaren Übersicht der Entwicklungsgeschichte führen. Die Commits sind „atomar“, damit sie einfach rückgängig gemacht und nicht gelöscht werden können. Jeder Commit beinhaltet eine eindeutige Commit-Nachricht und eine optionale Beschreibung.

\subsection{Versionierung}

Die Versionierung der Software erfolgt nach dem SemVer-Modell\footnote{\url{https://semver.org/lang/de/}}. Dieses Modell bietet eine klare Kategorisierung von verschiedenen Releases.

Jede Versionsnummer besteht aus drei Teilen, die jeweils die Major-, Minor- und Patch-Version definieren. Ein Patch-Release bringt kompatible Bugfixes ein, wohingegen ein Minor-Release neue Funktionalitäten einbringt und ein Major-Release zus"atzlich zu einem Minor-Release mit dem Einbringen der neuen Funktionalit"aten die Kompatibilität mit der vorherigen Produkt-Version verletzt.
% Minor und Major bringen beide neue Funktionalität ein, evtl darüber verbinden
% Vorschlag: Ein Patch-Release bringt kompatible Bugfixes und sowohl der Minor- als auch der Major-Release bringen neue Funktionalität ein, der Major-Release verletzt dabei aber im Gegensatz zum Minor-Release die Kompatibilität mit der vorherigen Produkt-Version.

\subsubsection{Changelog}

Neben dem Code wird im Repository ein Änderungsprotokoll gespeichert. Das Protokoll wird in der Datei „\texttt{CHANGELOG}“ gespeichert, das Format entspricht dem „Keep a~Changelog“\footnote{\url{https://keepachangelog.com/de/1.0.0/}}.


\section{Design- und Programmierrichtlinien}

In diesem Abschnitt werden Richtlinien, die für den Source-Code gelten, festgelegt.

\subsection{Sprache der Entwicklung}

Die Entwicklung erfolgt auf Englisch. Das heißt, die gesamten Kommentare, Dokumentation, Commit-Nachrichten, Issues und Merge-Requests werden auf Englisch geschrieben.

\subsection{Code-Stil}\label{angebot:entwicklungsrichtlinien:codestyle}

Als Python-Code-Stil wird \textit{Black}\footnote{\url{https://github.com/psf/black/blob/master/docs/the_black_code_style.md}} benutzt. Dieser Stil ist konform zu PEP~8, bis auf die maximale Zeilenlänge, welche auf 88 vergrößert ist. Dazu werden die \texttt{import}-Klauseln mithilfe \textit{isort}\footnote{\url{https://pycqa.github.io/isort/}} sortiert.

\subsection{Dokumentationsstil}

Alle Methoden, Klassen und andere Code-Elemente werden ausführlich dokumentiert. Für Python-Code gilt PEP~257\footnote{\url{https://www.python.org/dev/peps/pep-0257/}}. Die JavaScript-Dokumentation erfolgt nach JSDoc\footnote{\url{https://jsdoc.app/}}.

\section{Verwendete Software}

In diesem Abschnitt wird die verwendete Software für das Projekt erläutert: sowohl die Projekt-Abhängigkeiten, als auch die Entwickler-Tools.

\subsection{Programmiersprachen}

\begin{description}

\item [\textit{Python}] wird für den Programm-Code (den sogenannten Back-End) benutzt. Die Entwicklung erfolgt mithilfe beliebiger Python-Version mit dem Präfix „3.9“; die entwickelte Software wird jedoch mit Python 3.6 und höher abwärtskompatibel sein.

\item [\textit{JavaScript}] wird für die interaktiven Elemente der Web-basierten Vorschau benutzt. Die Ziel-Version der Sprache ist ECMAScript~2015, die von 97,32\% der Browser unterstützt wird.

\item [\textit{HTML5} und \textit{CSS3}] werden für die Aufbau der Web-Seiten und deren Design benutzt.
\end{description}

\subsection{Projekt-Abhängigkeiten}

Die Drittanbieter-Bibliotheken und -Module, die im Produkt benutzt werden, umfassen, sind aber nicht beschränkt auf:

\begin{description}
    \item [\textit{colorama}] eine Bibliothek, die eine farbige Ausgabe auf allen Betriebssysteme ermöglicht\footnote{\url{https://github.com/tartley/colorama}}.
    \item [\textit{Flask}] ein einfacher Web-Server, der benutzt wird, um den Austausch der Information zwischen der Web-Oberfläche und dem Back-End ermöglicht\footnote{\url{https://flask.palletsprojects.com/en/1.1.x/}}.
\end{description}

\subsection{Entwicklung-Tools}

Zur Bearbeitung des Source-Codes wird eine IDE benutzt. Je nach den Präferenzen der einzelnen Entwicklerin bzw. des einzelnen Entwicklers, kann das \textit{Visual~Studio~Code}\footnote{\url{https://code.visualstudio.com/}} oder \textit{PyCharm~Professional}\footnote{\url{https://www.jetbrains.com/pycharm/}} sein. Diese IDEs ermöglichen unter anderem kollaborative Entwicklung in Echtzeit.

Außerdem werden die folgenden Open-Source-Tools benutzt:

\begin{description}
    \item [\textit{Black}] der bereits in \ref{angebot:entwicklungsrichtlinien:codestyle} erwähnte Code-Formatter.
    \item [\textit{Git}] eine freie Software zur Versionsverwaltung. Die Team-Mitglieder:innen haben eine freie Wahl, was die Benutzung einer externen Git-Client-Software angeht.\footnote{\url{https://git-scm.com/}}
    \item [\textit{isort}] der bereits in \ref{angebot:entwicklungsrichtlinien:codestyle} erwähnte Code-Formatter.
    \item [\textit{Poetry}] eine Software, die eine einfachere und sicherere Verwaltung der Abhängigkeiten ermöglicht.\footnote{\url{https://python-poetry.org/}}
\end{description}

\subsection{Team-Tools}

Außerdem werden die folgenden Instrumente für die nicht mit dem Source-Code verbundenen Aktivitäten benutzt:

\begin{description}
    \item [\textit{diagrams.net}] \textit{(früher draw.io)} Visualisierungsprogramm zum Erstellen von Diagrammen und anderen graphischen Bildern\footnote{\url{https://www.diagrams.net/}}.
    \item [\textit{GitLab}] die in \ref{angebot:entwicklungsrichtlinien:scm} bereits erwähnte GitLab-Instanz vom GITZ dient auch als eine Issue-Tracking- und Code-Review-Software.
    \item [\textit{ShareLaTeX}] \textit{(heutzutage auch Overleaf)} Online-Editor für \LaTeX-Dokumente. Bereitgestellt vom GITZ, dieser ermöglicht unter anderem die gleichzeitige Arbeit von mehreren Team-Mitgliedern an einem Dokument\footnote{\url{https://sharelatex.rz.tu-bs.de/}}.
\end{description}
\end{document}
"""


@pytest.fixture
def tex_file(tmp_path: Path) -> TexFile:
    document = tmp_path / "document.tex"
    document.write_text(_DOCUMENT_CONTENTS)
    return TexFile(document, compile_tex=True)


@pytest.fixture
def tex_filter(tmp_path: Path) -> Path:
    return Path(
        __file__,
    ).parent.parent.parent.parent / "latexbuddy" / "modules" / "texfilt.awk"


_problem_re = re.compile(
    r"(?P<line_no>\d+):",
)

_space_re = re.compile(r'\s+')


@pytest.mark.xfail(reason="Document can't get compiled", strict=True)
def test_run_checks(
    tex_file: TexFile,
    tex_filter: Path,
):
    problems = LogFilter().run_checks(ConfigLoader(), tex_file)

    raw_problems = subprocess.check_output(
        ("awk", "-f", tex_filter, tex_file.log_file),
        text=True,
    )
    raw_problems_normalized = _space_re.sub(' ', raw_problems)

    for problem in problems:
        if problem.description is not None:
            assert _space_re.sub(' ', problem.description).strip() in \
                raw_problems_normalized

    # FIXME: LogFilter does not set positions
    # problem_line_nos = [problem.position[0] for problem in problems]
    # for problem in raw_problems.split(" "):
    #     match = _problem_re.match(problem)
    #     if not match:
    #         continue
    #     line_no = match.group("line_no")
    #     assert line_no in problem_line_nos
