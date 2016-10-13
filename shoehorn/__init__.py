from shoehorn.stdlib import StandardLibraryTarget
from .logger import Logger

logger = Logger(StandardLibraryTarget())


def get_logger(name=None):
    context = {}
    if name is not None:
        context['logger'] = name
    return logger.bind(**context)
