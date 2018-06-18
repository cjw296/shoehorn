import sys

PY36 = False
if sys.version_info[0] == 2:
    PY2 = True
    PY3 = False
    text_types = (str, unicode)
    Unicode = unicode
else:
    PY2 = False
    PY3 = True
    text_types = str
    Unicode = str
    if sys.version_info[1] >= 6:
        PY36 = True
