class Board:
    def __getattr__(self, name):
        return name

import sys
sys.modules[__name__] = Board()
