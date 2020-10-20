"""Provide classes for attribute-based patterns which are then used for matching."""

from __future__ import annotations

import functools
import operator
from typing import Any, Callable, Generic, Hashable, Type, TypeVar, Union


T = TypeVar('T')


class Condition(Generic[T]):
    """Base class for type-bound conditions used for matching objects.

    Attributes:
        type: The type to which the condition is bound.
    """

    def __init__(self, tp: Type[T]):
        self.type = tp

    def __lt__(self, other: Condition):
        raise NotImplementedError

    def __eq__(self, other):
        raise NotImplementedError

    def __hash__(self):
        raise NotImplementedError

    def match(self, obj: Any) -> bool:
        """Check whether the given object matches the condition."""
        raise NotImplementedError


@functools.total_ordering
class Comparison(Condition):
    """Compare a characteristic of an object to a reference value.

    Args:
        tp: Type to which this condition is bound.
        identifier: Identifies the characteristic.
        op: Function which performs the comparison (e.g. :func:`operator.eq`).
        ref: Reference value used in the comparison.
    """
    def __init__(self, tp: Type[T], identifier: Hashable, op: Callable[[Any, Any], bool], ref):
        super().__init__(tp)
        self.identifier = identifier
        self.op = op
        self.ref = ref

    def __lt__(self, other):
        if isinstance(self, Comparison) and isinstance(other, Comparison):
            return False
        return NotImplemented

    def __eq__(self, other):
        attributes = operator.attrgetter('type', 'identifier', 'op', 'ref')
        return type(self) == type(other) and attributes(self) == attributes(other)

    def __hash__(self):
        return hash((self.type, self.identifier, self.op))

    def retrieve(self, obj):
        """Retrieve the characteristic from the given object."""
        raise NotImplementedError

    def match(self, obj: T) -> bool:
        """Check whether the given object has the required attribute and if it passes the comparison."""
        try:
            return self.op(self.retrieve(obj), self.ref)
        except (AttributeError, LookupError):
            return False


class CompareAttr(Comparison):
    """Compare an attribute of an object to a reference value."""

    def retrieve(self, obj):
        """Retrieve the identified attribute from the given object."""
        return getattr(obj, self.identifier)


class CompareItem(Comparison):
    """Compare an item of an object to a reference value."""

    def retrieve(self, obj):
        """Retrieve the identified item from the given object."""
        return obj[self.identifier]


@functools.total_ordering
class IsInstance(Condition):
    """Condition the type of objects."""

    def __lt__(self, other):
        if type(self) == type(other):
            return self.type in other.type.mro()
        return True

    def __eq__(self, other):
        return type(self) == type(other) and self.type == other.type

    def __hash__(self):
        return hash(self.type)

    def match(self, obj) -> bool:
        """Check whether the given object is an instance of the reference type."""
        return isinstance(obj, self.type)


class Match(Generic[T]):
    """Use this class in order to create patterns on types.

    Args:
        tp: The type to which the resulting pattern refers.

    Example:
        ``match(MyType).x > 0`` creates a comparison for attribute ``x`` with reference value ``0``.
        ``match(MyType)['x'] > 0`` creates a comparison for item ``'x'`` with reference value ``0``.
    """

    def __init__(self, tp: Type[T]):
        self._type = tp

    def __getattr__(self, name: str) -> MatchAttr[T]:
        return MatchAttr(self._type, name)

    def __getitem__(self, id_: Hashable) -> MatchItem[T]:
        return MatchItem(self._type, id_)


class MatchCharacteristic(Match[T]):
    """Represents a characteristic of a type.

    This class can create comparisons for the respective characteristic.
    """

    Comparison = Comparison

    def __init__(self, tp: Type[T], attr: Hashable):
        super().__init__(tp)
        self._attr = attr

    def _make_op_func(name: str):  # type: ignore
        op = getattr(operator, name)

        def _op_func(self, ref) -> Condition[T]:
            return self.Comparison(self._type, self._attr, op, ref)
        return _op_func

    __lt__ = _make_op_func('__lt__')
    __le__ = _make_op_func('__le__')
    __eq__ = _make_op_func('__eq__')
    __ne__ = _make_op_func('__ne__')
    __ge__ = _make_op_func('__ge__')
    __gt__ = _make_op_func('__gt__')

    del _make_op_func


class MatchAttr(MatchCharacteristic[T]):
    """Represents a generic attribute of a type.

    This class can create comparisons for the respective attribute.
    """

    Comparison = CompareAttr


class MatchItem(MatchCharacteristic[T]):
    """Represents a generic item of a type.

    This class can create comparisons for the respective item.
    """

    Comparison = CompareItem


Pattern = Union[type, Condition, Match]
