import os
import re

from pathlib import Path
from typing import List, Optional, Tuple

import pytest

from tests.pytest_testcases.tools import execute_and_collect


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def generate_cli_command(
    script_dir: str,
    language: Optional[str],
    whitelist: Optional[str],
    output: Optional[str],
    format: Optional[str],
    en_modules: Optional[List[str]],
    dis_modules: Optional[List[str]],
) -> List[str]:
    cmd = ["latexbuddy", "-v"]

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


__REGEX_CLI_CONFIG_OPTIONS_MAIN = re.compile(
    r"Parsed CLI config options \(main\):\n({.*})"
)
__REGEX_CLI_CONFIG_OPTIONS_MODULES = re.compile(
    r"Parsed CLI config options \(modules\):\n({.*})"
)


def assert_flag_config_options(
    cmd_output: str,
    language: Tuple[Optional[str], Optional[str]],
    whitelist: Optional[str],
    output: Optional[str],
    format: Optional[str],
    en_modules: Optional[List[str]],
    dis_modules: Optional[List[str]],
):
    main_match = __REGEX_CLI_CONFIG_OPTIONS_MAIN.search(cmd_output)
    modules_match = __REGEX_CLI_CONFIG_OPTIONS_MODULES.search(cmd_output)

    assert main_match
    assert modules_match

    main_dictionary = main_match.group(1)
    # modules_dictionary = modules_match.group(1)

    if language[0]:
        assert f"'language': {language[0]}" in main_dictionary
    else:
        assert "'language': " not in main_dictionary

    if language[1]:
        assert f"'language_country': {language[1]}" in main_dictionary
    else:
        assert "'language_country': " not in main_dictionary

    if whitelist:
        assert f"'whitelist': {whitelist}" in main_dictionary
    else:
        assert "'whitelist': " not in main_dictionary

    if output:
        assert f"'output': {output}" in main_dictionary
    else:
        assert "'output': " not in main_dictionary

    if format:
        assert f"'format': {format}" in main_dictionary
    else:
        assert "'format': " not in main_dictionary

    if en_modules:
        assert f"'enable-modules-by-default': {False}" in main_dictionary
    elif not dis_modules:
        assert "'enable-modules-by-default': " not in main_dictionary

    if dis_modules:
        assert f"'enable-modules-by-default': {True}" in main_dictionary
    elif not en_modules:
        assert "enable-modules-by-default" not in main_dictionary


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
        (
            ("de-DE", ("'de'", "'DE'")),
            (None, None),
            (None, None),
            (None, None),
            (None, None),
            (None, None),
        ),
        (
            ("de_DE", ("'de'", "'DE'")),
            (None, None),
            (None, None),
            (None, None),
            (None, None),
            (None, None),
        ),
        (
            (None, (None, None)),
            (
                "resources/my_nonexistent_whitelist",
                "'resources/my_nonexistent_whitelist'",
            ),
            (None, None),
            (None, None),
            (None, None),
            (None, None),
        ),
        (
            (None, (None, None)),
            (None, None),
            ("resources/my_output_dir/", "'resources/my_output_dir/'"),
            (None, None),
            (None, None),
            (None, None),
        ),
        (
            (None, (None, None)),
            (None, None),
            (None, None),
            ("HTML", "'HTML'"),
            (None, None),
            (None, None),
        ),
        (
            (None, (None, None)),
            (None, None),
            (None, None),
            (None, None),
            (
                ["LanguageTool", "Aspell", "FantasyModule"],
                ["LanguageTool", "Aspell", "FantasyModule"],
            ),
            (None, None),
        ),
        (
            (None, (None, None)),
            (None, None),
            (None, None),
            (None, None),
            (None, None),
            (
                ["LanguageTool", "Diction", "FantasyModule2"],
                ["LanguageTool", "Diction", "FantasyModule2"],
            ),
        ),
    ],
)
def test_unit_cli_check_flag_parsing(
    script_dir,
    language: Tuple[Optional[str], Tuple[Optional[str], Optional[str]]],
    whitelist: Tuple[Optional[str], Optional[str]],
    output: Tuple[Optional[str], Optional[str]],
    format: Tuple[Optional[str], Optional[str]],
    en_modules: Tuple[Optional[List[str]], Optional[List[str]]],
    dis_modules: Tuple[Optional[List[str]], Optional[List[str]]],
):
    cmd = generate_cli_command(
        script_dir=script_dir,
        language=language[0],
        whitelist=whitelist[0],
        output=output[0],
        format=format[0],
        en_modules=en_modules[0],
        dis_modules=dis_modules[0],
    )
    result = execute_and_collect(*cmd)

    assert_flag_config_options(
        cmd_output=result,
        language=language[1],
        whitelist=whitelist[1],
        output=output[1],
        format=format[1],
        en_modules=en_modules[1],
        dis_modules=dis_modules[1],
    )
