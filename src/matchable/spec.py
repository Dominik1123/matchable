"""Provide the class for creating matching specifications.

Attributes:
    WRAPPER_TYPES (:class:`Spec`): Can be used for registering custom wrappers for that will be applied
        to values associated with conditions in a :class:`Spec`. These wrapper types serve the purpose of
        defining the :class:`Combinable` behavior required for values. Since this is a :class:`Spec` as well,
        any pattern can be used for registering new wrapper types.
        For example: ``WRAPPER_TYPES[list] = MyConcatWrapper``.
        The default is :class:`LastSeenWins` for all unregistered types.
"""

from __future__ import annotations

from collections import defaultdict
from functools import reduce
import itertools as it
import operator
import sys
from typing import Any, Dict, List, Mapping, MutableMapping, Tuple, Type, TypeVar
if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

from .exceptions import NoMatchError
from .match import Condition, IsInstance, Match, Pattern


T = TypeVar('T')


class Combinable(Protocol):
    """Protocol for combinable objects via ``lhs | rhs``."""

    def __or__(self, other):
        ...  # pragma: no cover


class Wrapper:
    """Wrapper class for values stored as options."""

    def __init__(self, obj):
        self.obj = obj


class CopyUpdate(Wrapper):
    """Combine objects by using ``copy`` on the l.h.s. followed by ``update`` with the r.h.s.."""

    def __init__(self, obj: Dict):
        super().__init__(obj)

    def __or__(self, other):
        if isinstance(other, Wrapper):
            other = other.obj
        new = self.obj.copy()
        try:
            new.update(other)
        except (ValueError, TypeError):
            return NotImplemented
        return type(self)(new)


class LastSeenWins(Wrapper):
    """Combine objects by discarding the l.h.s. and using the r.h.s. instead."""

    def __or__(self, other):
        return other

    def __ror__(self, other):
        return self


class Options(MutableMapping[Condition, Combinable]):
    """Mapping from conditions to combinable objects."""

    def __init__(self, other: Mapping[Condition, Combinable] = None):
        self._types: Dict[Type, Dict[Condition, Combinable]] = defaultdict(dict)
        if other:
            for condition, value in other.items():
                self[condition] = value

    def __getitem__(self, condition: Condition) -> Combinable:
        return self._types[condition.type][condition]

    def __setitem__(self, condition: Condition, value: Combinable):
        self._types[condition.type][condition] = value

    def __delitem__(self, condition: Condition):
        del self._types[condition.type][condition]

    def __iter__(self):
        return it.chain.from_iterable(self._types.values())

    def __len__(self):
        return sum(map(len, self._types.values()))

    def match(self, obj: Any, *, typewise: bool = False) -> Combinable:
        """Match the given object by checking against all conditions and combining the applicable values.

        Args:
            obj: The object to be matched.
            typewise (bool): By default attribute-based conditions take precedence over type-based conditions,
                no matter where they occur along the class hierarchy. This means that if two such conditions apply,
                the attribute-based condition will always update the type-based condition.
                If ``typewise=True`` then this precedence only applies within the single types of the hierarchy.
                This means that the type-based condition of a subtype will update an attribute-based condition
                of an ancestor.

        Returns:
            The combined value of all conditions that the object complied with.

        Raises:
            NoMatchError: If no condition matched the given object.
        """
        options: List[Tuple[Condition, Combinable]] = []
        for tp in reversed(type.mro(type(obj))):
            tp_options = [(cond, val) for cond, val in self._types[tp].items() if cond.match(obj)]
            if typewise:
                tp_options.sort(key=operator.itemgetter(0))
            options.extend(tp_options)
        if not typewise:
            options = sorted(options, key=operator.itemgetter(0))
        if not options:
            raise NoMatchError(f'No matching conditions found for object {obj!r}')
        return reduce(operator.or_, (val for cond, val in options))


class Spec:
    """Use this class to create matching specifications and to match objects.

    The ``Spec.from_patterns`` method can be used to create a specification from a dictionary
    of patterns; this is the recommended approach.

    Example:
        Create a specification from patterns::

            from matchable import match

            spec = Spec.from_patterns({
                int: dict(msg='number'),
                dict: dict(msg='dictionary'),
                match(dict)['key'] == 'special': dict(special=True),
            })
            spec.match(0)  # {'msg': 'number'}
            spec.match({'key': 'ordinary'})  # {'msg': 'dictionary'}
            spec.match({'key': 'special'})  # {'msg': 'dictionary', 'special': True}
    """

    def __init__(self, options: Options = None):
        self.options = options or Options()

    @classmethod
    def from_patterns(cls, patterns: Dict[Pattern, Any]):
        """Create a specification from the given patterns.

        Args:
            patterns: Dictionary mapping patterns to values which form the matching result later on.

        Returns:
            A fresh instance of this class.
        """
        obj = cls()
        for pattern, value in patterns.items():
            obj.add_pattern(pattern, value)
        return obj

    def __getitem__(self, pattern):
        return self.options[self.make_condition_from_pattern(pattern)]

    def __setitem__(self, pattern: Pattern, value: Any):
        self.add_pattern(pattern, value)

    def __delitem__(self, pattern: Pattern):
        del self.options[self.make_condition_from_pattern(pattern)]

    def add_pattern(self, pattern: Pattern, value: Any):
        """Add a new pattern to the specification or replace an existing one."""
        # The following should not raise an exception unless a user did `del WRAPPER_TYPES[object]`.
        w_type = WRAPPER_TYPES.match(value)
        self.options[self.make_condition_from_pattern(pattern)] = w_type(value)

    def get_value(self, pattern: Pattern):
        """Get the value which is associated with the pattern."""
        return self.unwrap(self[pattern])

    def match(self, obj: Any, *, typewise: bool = False):
        """Match the given object against the spec's patterns and return the combined value.

        Args:
            obj: The object to be matched.
            typewise (bool): See :meth:`Options.match`.

        Returns:
            The combination of values associated with all matching patterns.

        See Also:
            :meth:`Options.match` -- For details on how the matching is performed.
        """
        return self.unwrap(self.options.match(obj, typewise=typewise))

    @staticmethod
    def make_condition_from_pattern(pattern: Pattern) -> Condition:
        """Allow ``type`` and ``Match`` patterns by converting to :class:`IsInstance`.

        Args:
            pattern: A condition, type or :class:`Match` object.

        Returns:
            Condition: A corresponding :class:`Condition` instance.
        """
        if isinstance(pattern, type):
            return IsInstance(pattern)
        elif isinstance(pattern, Match):
            return IsInstance(pattern._type)
        else:
            return pattern

    @staticmethod
    def unwrap(value):
        """Remove any wrappers if present."""
        if isinstance(value, Wrapper):
            return value.obj
        return value


WRAPPER_TYPES = Spec(Options({  # pragma: no cover
    IsInstance(object): LastSeenWins(LastSeenWins),
    IsInstance(dict): LastSeenWins(CopyUpdate),
    IsInstance(set): LastSeenWins(CopyUpdate),
    IsInstance(Wrapper): LastSeenWins(lambda x: x),  # Do not wrap again.
}))
