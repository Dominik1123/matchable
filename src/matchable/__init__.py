try:
    from importlib.metadata import version  # type: ignore
except ImportError:
    from importlib_metadata import version  # type: ignore

__version__ = version(__name__)


from .exceptions import NoMatchError
from .match import Match as match
from .spec import Spec
