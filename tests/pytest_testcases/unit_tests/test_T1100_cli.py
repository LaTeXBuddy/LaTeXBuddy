import os
from pathlib import Path
from typing import Optional, List, Tuple

import pytest

from tests.pytest_testcases.tools import execute_and_collect


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def generate_cli_command(
    script_dir,
    language: Optional[str],
    whitelist: Optional[str],
    output: Optional[str],
    format: Optional[str],
    en_modules: Optional[List[str]],
    dis_modules: Optional[List[str]],
) -> List[str]:

    cmd = ["latexbuddy"]

    if language:
        cmd.append("--language")
        cmd.append(language)

    if whitelist:
        cmd.append("--whitelist")
        cmd.append(whitelist)

    if output:
        cmd.append("--output")
        cmd.append(output)

    if format:
        cmd.append("--format")
        cmd.append(format)

    if en_modules:
        cmd.append("--enable-modules")
        cmd.append(",".join(en_modules))

    if dis_modules:
        cmd.append("--disable-modules")
        cmd.append(",".join(dis_modules))

    cmd.append(script_dir + "/resources/T1100_test_document.tex")

    return cmd


def assert_flag_config_options(
    language: Tuple[Optional[str], Optional[str]],
    whitelist: Optional[str],
    output: Optional[str],
    format: Optional[str],
    en_modules: Optional[List[str]],
    dis_modules: Optional[List[str]]
):
    pass


@pytest.mark.parametrize(
    "language, whitelist, output, format, en_modules, dis_modules",
    [
        (
            (None, (None, None)),
            (None, None),
            (None, None),
            (None, None),
            (None, None),
            (None, None),
        ),
    ],
)
def test_unit_cli_check_flag_parsing(
    language: Tuple[Optional[str], Tuple[Optional[str], Optional[str]]],
    whitelist: Tuple[Optional[str], Optional[str]],
    output: Tuple[Optional[str], Optional[str]],
    format: Tuple[Optional[str], Optional[str]],
    en_modules: Tuple[Optional[List[str]], Optional[List[str]]],
    dis_modules: Tuple[Optional[List[str]], Optional[List[str]]]
):

    cmd = generate_cli_command(
        language=language[0],
        whitelist=whitelist[0],
        output=output[0],
        format=format[0],
        en_modules=en_modules[0],
        dis_modules=dis_modules[0]
    )
    execute_and_collect(*cmd)
