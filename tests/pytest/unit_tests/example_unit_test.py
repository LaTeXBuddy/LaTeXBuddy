import math

import pytest as pytest


"""
IMPORTANT NOTE: every test case method and .py-file must either begin or end in 'test'
                eg. 'test_my_cool_feature()' or 'divisibility_test()'
"""


def test_sqrt():
    num = 25
    assert math.sqrt(num) == 5


def test_square():
    assert 7*7 == 49


def test_equality():
    assert 10 == 5*2


@pytest.mark.skip
def test_to_be_skipped():
    assert False


@pytest.mark.parametrize("input_param_0, input_param_1", [(0, 1), (2, 4), (42, 9001)])
def parametrized_test(input_param_0, input_param_1):
    assert input_param_0 < input_param_1


@pytest.fixture
def input_value():
    return 42


# input value(s) are supplied to every method that uses them
def test_divisible_by_2(input_value):
    assert input_value % 2 == 0


def test_divisible_by_21(input_value):
    assert input_value % 21 == 0
