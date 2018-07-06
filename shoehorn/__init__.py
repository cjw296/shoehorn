from .targets.serialize import Human, STDERR
from .stdlib import StandardLibraryTarget
from .logger import Logger
from .targets.compose import Stack
from .targets.enrich import add_traceback

#: The :class:`~shoehorn.targets.Stack` to handle errors.
errors = Stack(
    add_traceback,
    Human(STDERR)
)

#: The :class:`~shoehorn.targets.Stack` to handle logging.
logging = Stack(error_target=errors)

#: The root :class:`~shoehorn.logger.Logger`
logger = Logger(logging)


def get_logger(name=None, **context):
    if name is not None:
        context['logger'] = name
    return logger.bind(**context)


__all__ = ['errors', 'logging', 'logger', 'get_logger']
