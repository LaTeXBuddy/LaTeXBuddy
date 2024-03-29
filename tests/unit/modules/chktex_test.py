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

import shutil
from pathlib import Path

import pytest

from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules.chktex import Chktex
from latexbuddy.texfile import TexFile

pytestmark = pytest.mark.skipif(
    shutil.which("chktex") is None,
    reason="ChkTeX is not installed",
)

_DOCUMENT_CONTENTS = R"""Note: This file was written with only two purposes in mind:
    o To test the program upon it
    o To show off some of the features

Most of the file does thus consist of lots of pseudo-commands, which
are nonsense in a TeXnical manner.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


% Warning 1

\foo This is a error.
So is this is \foo
\smallskip This is a not. $\foo Neither$ is this.
Tesst
Errror
Sammmple

\startsection[title={Testing ConTeXt}]
These should be now a errror.
\stoptext

% Warning 2

This a faulty reference is to \ref{foo}
This is not a faulty reference to~\ref{foo}

% Warning 3

$[(ab)^{-1}]^{-2}$  is not beautiful
${{[{(ab)}^{-1}]}}^{-2}$ is beautiful

% Warning 4-6, 28

Testing {\it italic} in \/ this {\em sentence\/}, as {\em you \/ see\/}.
Testing {\it italic\/} in this {\em sentecne,} as {\em you see}.

% LaTeX2e

Testing \textem{italic} in \/ this \textit{sentence\/}, as \textem{you \/ see\/}.
Testing \textem{italic\/} in this \textit{sentence}, as \textem{you see}.

% Warning 7

This \'is a test of $\hat{j}$ acents.
This \'{\i}s a test of $\hat{\jmath}$ accents.

% Warning 8

It wasn't anything - just a 2---3 star--shots.
It wasn't anything --- just a 2--3 star-shots.
It's just a startt-shot.
is also used to send cross-calls (xc) and cross-traps (xt) to other
% From Knuths TeXbook Chapter 14
% "How TeX Breaks Paragraphs into Lines", fourth paragraph:
in plain TeX---are the key
This is a random word: ajskld

% Using DashExcpt
The Birch--Swinnerton-Dyer conjecture is correct.
The Birch--Swinnerton--Dyer conjecture is not correct.
The Birch-Swinnerton-Dyer conjecture is not correct (but not not caught).

% Warning 9-10

% Brackets:

)}{[])} }}}]]])))
{[]} ((([[[{{{}}}]]])))

% Envs:

\begin{quux} \begin{baz} \end{quux} \end{baz} \end{asoi} \begin{dobedo}

\begin{foo} \begin{bar} \end{bar}\end{foo}

% Warning 11

Foo...bar. $1,...,3$. $1+...+3$. $1,\cdots,3$. $1\cdot\ldots\cdot3$.
Foo\dots bar. $1,\ldots,3$. $1+\cdots+3$. $1,\ldots,3$. $1\cdot\cdots\cdot3$.

% Warning 12

1st. Foo Inc. Ab.cd. foo ab.cd. Foo. bar baz., billy.; bob.: joe.! frank.? james.. george
1st.\ foo Inc.\ ab.cd.\ foo ab.cd.\ Foo.\ bar baz., billy.; bob.:\ joe.!\ frank.?\ james..\ george

% Warning 13

Look at THIS! It's an error.
Look at THIS\@! It's an error. D. E. Knuth.

% Warning 14

\hat
\hat{a}

% Warning 18,19

Is this an "example", or is it an �example�.
Is this an `example', or is it an `example'.

% Warning 20

That bug is \unknown\ to me.
% That bug is \unknown\ to me.

% Warning 21

\LaTeX\ is an extension of \TeX\. Right?
\LaTeX\ is an extension of \TeX. Right?

% Warning 23

```Hello', I heard him said'', she remembered.
``\,`Hello', I heard him said'', she remembered.

% Warning 24

Indexing text \index{text} is fun!
Indexing text\index{text} is fun!
Indexing text%
     \index{text} is fun!
Indexing text
     \index{text} is fun!

% Warning 25

$5\cdot10^10$
$5\cdot10^{10}$

% Warning 26

Do you understand ?
Do you understand?

% Warning 27

\input input.tex
\input input

% Warning 29
The program opens a screen sized 640x200 pixels
The program opens a screen sized $640\times200$ pixels

% Warning 30

White           is a beautiful colour.
White is a beautiful colour.

% Warning 31
\begin{verbatim}
\this is
\end{verbatim} foo bar

% Warning 32-34

This is either an 'example`, an ''example`` or an `"`example'`'.
This is either an `example', an ``example'' or an ``example''.

% Warning 35

$sin^2 + cos^2 = 1$
$\sin^2 + \cos^2 = 1$

% Warning 36-37

This( an example( Nuff said )), illustrates( ``my'' )point.
This (an example (Nuff said)), illustrates (``my'') point.

% Warning 38
``An example,'' he said, ``would be great.''
``An example'', he said, ``would be great''.

% Warning 39

For output codes, see table ~\ref{tab:fmtout}.
For output codes, see table~\ref{tab:fmtout}.

% Warning 40
$\this,$ and $$this$$.
$\this$, and $$this.$$

% Warning 41
foo \above qux
\frac{foo}{qux}

% Warning 42
This is a footnote \footnote{foo}.
This is a footnote\footnote{foo}.

% Warning 43
Here is a mistake $\left{x\right}$.
This one triggers warning 22 $\left\{x\right\}$.
Here \chktex\ doesn't complain $\left\lbrace x\right\rbrace$.

% Warning 44 -- user regex -- default message
You should always write a good intro.
You should always write a good introduction.

% Warning 44 -- user regex -- user message
For every $p\not|n$ you have an ugly prime which doesn't divide $n$.
For every $p\nmid n$ you have a cute prime which doesn't divide $n$.

% Math mode check
\ensuremath{sin x\text{is not the same as sin x, but is the same as $sin x$}}
Also, $x(3)\text{ is not x(3) but it is $x(3)$}$

This is\\% a comment. Nothing here should be checked(right)?
a broken line.
But this is not a \% comment, so we should find this error(right)?

Here(on this line only)is a warning $sin(x)$ suppressed. % chktex 36 chktex 35
Here(on this line only)is a warning $sin(x)$ suppressed. % CHKTEX 35 36

In section~\ref{sec:3} we have a warning.
In section~\ref{sec:4} it is suppressed. % chktex -1
% In section~\ref{sec:5} we don't have a warning.

\begin{tabular*}{1.0\linewidth}[h]{|c|cc|}
  a & b \\
  \hline
  c & d
\end{tabular*}

% Verb check

\verb@\this is )() lots of errors, etc. Or what?@
\verb#

\begin{verbatim}
\this is
\end{verbatim} FOO

% Warning 16,15

$$(

% Local Variables:
% require-final-newline: nil
% End:
% There should be no newline at the end of this file to test bug #46539
"""


@pytest.fixture
def tex_file(tmp_path: Path) -> TexFile:
    document = tmp_path / "document.tex"
    document.write_text(_DOCUMENT_CONTENTS)
    return TexFile(document, compile_tex=False)


@pytest.mark.xfail(reason="Invalid TeX document", strict=True)
def test_run_checks(tex_file: TexFile, driver_config_loader) -> None:
    output_problems = Chktex().run_checks(driver_config_loader, tex_file)

    # added tolerance because of versional differences in ChkTeX
    assert 112 <= len(output_problems) <= 117
