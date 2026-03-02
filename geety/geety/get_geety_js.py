import os
import sys
import inspect


GEETY_JS = ''

with open(os.path.dirname(inspect.getfile(sys.modules[__name__])) + '/geety.js', 'r') as f:
    lines = []
    for line in f.readlines():
        if line := line.strip():
            lines.append(line)
    GEETY_JS = '\n'.join(lines)
