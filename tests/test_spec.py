import pytest

from matchable.exceptions import NoMatchError
from matchable.match import IsInstance
from matchable.match import Match as match
from matchable.spec import Options, Spec, CopyUpdate, LastSeenWins, Wrapper, WRAPPER_TYPES


@pytest.fixture
def patterns(type_a, type_b, type_c):
    return {
        type_a: dict(name='a'),
        match(type_a).a > 0: dict(name='a+'),
        match(type_a).a < 0: dict(name='a-'),
        type_b: dict(name='b'),
        match(type_b).b > 0: dict(name='b+'),
        match(type_b).b < 0: dict(name='b-'),
        match(type_c): dict(name='c'),  # similar to just using type_c
        match(type_c).a > 0: dict(name='ca+'),
        match(type_c).a < 0: dict(name='ca-'),

        match(dict): dict(msg='just a dict'),
        match(dict)['key'] == 'value': dict(msg='dict with value'),
        match(list)[0] == 'first': dict(msg='first things first'),
    }


@pytest.fixture
def spec(patterns):
    return Spec.from_patterns(patterns)


@pytest.fixture
def options(spec):
    return spec.options


@pytest.fixture
def condition(type_c):
    return match(type_c).a > 0


def test_options(options, type_a, type_b, type_c):
    assert type_a in options._types
    assert type_b in options._types
    assert type_c in options._types
    assert len(options) == 12


def test_options_contains(options, condition):
    assert condition in options


def test_options_iter(options):
    assert sum(1 for __ in options) == len(options)


def test_options_getitem(options, condition):
    assert options[condition].obj == dict(name='ca+')


def test_options_setitem(options, condition):
    options[condition] |= dict(foo='bar')
    assert options[condition].obj == dict(name='ca+', foo='bar')
    options[condition] = {}
    assert options[condition] == {}


def test_options_delitem(options, condition):
    del options[condition]
    with pytest.raises(KeyError):
        options[condition]


def test_spec_getitem(spec, type_c):
    assert spec[match(type_c).a > 0].obj == dict(name='ca+')


def test_spec_setitem(spec, type_c):
    spec[match(type_c).c == 0] = dict(zero=True)
    assert spec.match(type_c()) == dict(name='c', zero=True)


def test_spec_delitem(spec, type_b, type_c):
    del spec[match(type_c)]
    del spec[type_b]
    assert spec.match(type_c()) == dict(name='a')


def test_spec_get_value(spec, type_c):
    assert spec.get_value(match(type_c).a > 0) == dict(name='ca+')


def test_spec_match_attr(spec, type_a, type_b, type_c):
    a = type_a()
    assert spec.match(a) == dict(name='a')
    a.a = -1
    assert spec.match(a) == dict(name='a-')
    a.a = 1
    assert spec.match(a) == dict(name='a+')

    b = type_b()
    assert spec.match(b) == dict(name='b')
    b.b = -1
    assert spec.match(b) == dict(name='b-')
    b.b = 1
    assert spec.match(b) == dict(name='b+')

    c = type_c()
    assert spec.match(c) == dict(name='c')
    c.a = -1
    assert spec.match(c) == dict(name='ca-')
    c.a = 1
    assert spec.match(c) == dict(name='ca+')


def test_spec_match_attr_typewise(spec, type_b):
    b = type_b()
    b.a = 1
    assert spec.match(b) == dict(name='a+')
    assert spec.match(b, typewise=True) == dict(name='b')


def test_spec_match_item(spec):
    assert spec.match({}) == dict(msg='just a dict')
    assert spec.match({'key': 'value'}) == dict(msg='dict with value')
    with pytest.raises(NoMatchError):
        spec.match([])
    assert spec.match(['first']) == dict(msg='first things first')


def test_last_seen_wins_on_impossible_update():
    spec = Spec.from_patterns({
        object: dict(),
        int: 'not a mapping',
    })
    assert spec.match(0) == 'not a mapping'


def test_last_seen_always_wins():
    spec = Spec.from_patterns({
        match(dict)['x'] > 0: {'first'},
        match(dict)['x'] > 1: LastSeenWins({'second'}),
    })
    assert spec.match({'x': 1}) == {'first'}
    assert spec.match({'x': 2}) == {'second'}


def test_copy_update_or_not_implemented():
    wrapper = CopyUpdate(dict(x=1))
    assert wrapper.__or__(0) is NotImplemented


def test_last_seen_wins_ror():
    wrapper = LastSeenWins(0)
    assert ('test' | wrapper) is wrapper


def test_raises_if_no_options(spec):
    with pytest.raises(NoMatchError):
        spec.match(0)


def test_unwrap_on_bare_value():
    obj = object()
    assert Spec.unwrap(obj) is obj


def test_custom_wrapper_type():
    patterns = {
        object: [0, 1],
        int: [2, 3],
    }
    spec = Spec.from_patterns(patterns)
    assert spec.match(0) == [2, 3]

    class Concat(Wrapper):
        def __or__(self, other):
            return type(self)(self.obj + other.obj)

    WRAPPER_TYPES[list] = Concat
    spec = Spec.from_patterns(patterns)
    assert spec.match(0) == [0, 1, 2, 3]
    del WRAPPER_TYPES[list]
