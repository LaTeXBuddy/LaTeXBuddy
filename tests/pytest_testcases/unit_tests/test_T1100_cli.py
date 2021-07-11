import os
from pathlib import Path

import pytest


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_unit_cli_check_flag_parsing():
    pass
