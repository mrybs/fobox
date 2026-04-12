from datetime import datetime
from string import ascii_uppercase
import platform


__PD, __PI = datetime(2026, 4, 1), 2

VERSION = {
    'name': 'Fobox',
    'version': (
        __PD.strftime('%y.%#m-') if platform.system() == "Windows" else __PD.strftime('%y.%-m-')
        ) + ascii_uppercase[__PI - 1],
    'meta': {}
}

version = f'{VERSION['name']} {VERSION['version']}'
