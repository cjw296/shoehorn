import sys

PY36 = False
if sys.version_info[0] == 2:
    PY2 = True
    text_types = (str, unicode)
else:
    PY2 = False
    text_types = str
    if sys.version_info[1] >= 6:
        PY36 = True
