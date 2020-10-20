import pytest


@pytest.fixture
def type_a():
    class A:
        a: int = 0
    return A


@pytest.fixture
def type_b(type_a):
    class B(type_a):
        b: int = 0
    return B


@pytest.fixture
def type_c(type_b):
    class C(type_b):
        c: int = 0
    return C


@pytest.fixture(params=['type_a', 'type_b', 'type_c'])
def any_type(request):
    return request.getfixturevalue(request.param)
