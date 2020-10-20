import operator

import pytest

from matchable.match import Comparison, CompareAttr, CompareItem, Condition, IsInstance, Match, MatchAttr, MatchItem


@pytest.fixture
def comparison(type_c):
    return CompareAttr(type_c, 'c', operator.eq, 0)


def test_condition():
    cond = Condition(object)
    with pytest.raises(NotImplementedError):
        cond < cond
    with pytest.raises(NotImplementedError):
        cond == cond
    with pytest.raises(NotImplementedError):
        hash(cond)
    with pytest.raises(NotImplementedError):
        cond.match(0)


def test_comparison_base():
    with pytest.raises(NotImplementedError):
        Comparison(list, 0, operator.eq, 0).retrieve([0])


@pytest.mark.parametrize('attr_name', ['a', 'b', 'c'])
@pytest.mark.parametrize('op_name', ['lt', 'le', 'eq', 'ne', 'ge', 'gt'])
def test_compare_attr(type_c, attr_name, op_name):
    op = getattr(operator, op_name)
    ref = getattr(type_c, attr_name)
    cond = CompareAttr(type_c, attr_name, op, ref)
    obj = type_c()
    assert cond.match(obj) == op(ref, ref)


@pytest.mark.parametrize('obj', [{0: 0, 1: 1}, [0, 1], (0, 1)])
@pytest.mark.parametrize('identifier', [0, 1])
@pytest.mark.parametrize('op_name', ['lt', 'le', 'eq', 'ne', 'ge', 'gt'])
def test_compare_item(obj, identifier, op_name):
    op = getattr(operator, op_name)
    ref = obj[identifier]
    cond = CompareItem(type(obj), identifier, op, ref)
    assert cond.match(obj) == op(ref, ref)


def test_comparison_lt_eq(comparison, type_c):
    assert comparison == comparison
    assert not (comparison < comparison)
    assert Comparison(type_c, 'c', operator.eq, 0) != Comparison(type_c, 'c', operator.eq, 1)
    with pytest.raises(TypeError):
        comparison < 0


def test_comparison_missing_attribute(comparison):
    assert not comparison.match(0)


def test_isinstance(any_type):
    cond = IsInstance(any_type)
    assert cond.match(any_type())
    assert not cond.match(object())


def test_isinstance_lt_eq(type_a, type_b, type_c, comparison):
    cond_a = IsInstance(type_a)
    cond_b = IsInstance(type_b)
    cond_c = IsInstance(type_c)
    assert cond_a < cond_b
    assert cond_a < cond_c
    assert cond_b < cond_c
    assert cond_a < comparison
    assert cond_b < comparison
    assert cond_c < comparison
    assert cond_a == cond_a
    assert cond_a != cond_b


def test_conditions_sorting(type_a, type_b, type_c):
    ca = Comparison(type_a, 'a', operator.eq, 0)
    cb = Comparison(type_b, 'a', operator.eq, 0)
    cc = Comparison(type_c, 'a', operator.eq, 0)
    ia = IsInstance(type_a)
    ib = IsInstance(type_b)
    ic = IsInstance(type_c)
    assert sorted([cc, ca, ib, cb, ic, ia]) == [ia, ib, ic, cc, ca, cb]


def test_match(type_c):
    assert isinstance(Match(type_c).a, MatchAttr)
    assert isinstance(Match(type_c)['a'], MatchItem)


@pytest.mark.parametrize('match_cls,comp_cls', [(MatchAttr, CompareAttr), (MatchItem, CompareItem)])
@pytest.mark.parametrize('op_name', ['lt', 'le', 'eq', 'ne', 'ge', 'gt'])
def test_match_attr_item(type_c, match_cls, comp_cls, op_name):
    op = getattr(operator, op_name)
    cond = op(match_cls(type_c, 'a'), 0)
    assert isinstance(cond, comp_cls)
    assert cond == comp_cls(type_c, 'a', op, 0)
