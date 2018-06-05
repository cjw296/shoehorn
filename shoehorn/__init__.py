from shoehorn.stdlib import StandardLibraryTarget
from .logger import Logger
from .targets import Stack

#: The :class:`~shoehorn.targets.Stack` to handle errors.
errors = Stack()

#: The :class:`~shoehorn.targets.Stack` to handle logging.
logging = Stack(error_target=errors)

#: The root :class:`~shoehorn.logger.Logger`
logger = Logger(logging)


def get_logger(name=None):
    context = {}
    if name is not None:
        context['logger'] = name
    return logger.bind(**context)
