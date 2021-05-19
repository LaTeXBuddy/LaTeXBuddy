from typing import Dict

from jinja2 import Environment, PackageLoader

from latexbuddy.problem import Problem


env = Environment(loader=PackageLoader("latexbuddy"))


def error_key(err: Problem) -> int:
    """Returns a number for each error to be able to sort them.

    This puts YaLaFi's errors on top, followed by errors without location.

    :param err: error object
    :return: error's "rating" for sorting
    """
    if err.checker.lower() == "yalafi":
        return -3
    if not err.position:
        return -2
    if not isinstance(err.position, tuple):
        return -1

    return err.position[0]


def render_html(file_name: str, file_text: str, errors: Dict[str, Problem]) -> str:
    """Renders an HTML page based on file contents and discovered errors.

    :param file_name: file name
    :param file_text: contents of the file
    :param errors: dictionary of errors returned from latexbuddy
    :return: generated HTML
    """
    err_values = sorted(errors.values(), key=error_key)
    template = env.get_template("result.html")
    return template.render(file_name=file_name, file_text=file_text, errors=err_values)
