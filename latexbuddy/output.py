from typing import Dict

from jinja2 import Environment, PackageLoader

from latexbuddy.problem import Problem, ProblemSeverity


env = Environment(loader=PackageLoader("latexbuddy"))


def problem_key(problem: Problem) -> int:
    """Returns a number for each problem to be able to sort them.

    This puts YaLaFi's problems on top, followed by errors without location.

    :param problem: problem object
    :return: error's "rating" for sorting
    """
    if problem.checker.lower() == "yalafi":
        return -3
    if not problem.position:
        return -2
    if not isinstance(problem.position, tuple):
        return -1

    return problem.position[0]


def render_html(file_name: str, file_text: str, problems: Dict[str, Problem]) -> str:
    """Renders an HTML page based on file contents and discovered problems.

    :param file_name: file name
    :param file_text: contents of the file
    :param problems: dictionary of errors returned from latexbuddy
    :return: generated HTML
    """
    problem_values = sorted(problems.values(), key=problem_key)
    template = env.get_template("result.html")
    return template.render(
        file_name=file_name, file_text=file_text, problems=problem_values
    )
