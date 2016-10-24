import sys

if sys.version_info[0] == 2:
    PY2 = True
    text_types = (str, unicode)
else:
    PY2 = False
    text_types = str
