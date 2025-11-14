from typing import Final

BLACK: Final[str] = '\033[30m'
RED: Final[str] = '\033[31m'
GREEN: Final[str] = '\033[32m'
YELLOW: Final[str] = '\033[33m'
BLUE: Final[str] = '\033[34m'
MAGENTA: Final[str] = '\033[35m'
CYAN: Final[str] = '\033[36m'
WHITE: Final[str] = '\033[37m'
LIGHT_BLACK: Final[str] = '\033[90m'
LIGHT_RED: Final[str] = '\033[91m'
LIGHT_GREEN: Final[str] = '\033[92m'
LIGHT_YELLOW: Final[str] = '\033[93m'
LIGHT_BLUE: Final[str] = '\033[94m'
LIGHT_MAGENTA: Final[str] = '\033[95m'
LIGHT_CYAN: Final[str] = '\033[96m'
LIGHT_WHITE: Final[str] = '\033[97m'

BOLD: Final[str] = '\033[1m'
UNDERLINE: Final[str] = '\033[4m'
ITALIC: Final[str] = '\033[3m'
REVERSE: Final[str] = '\033[7m'
STRIKETHROUGH: Final[str] = '\033[9m'

CLEAR_ALL: Final[str] = '\033[0m'
CLEAR_COLOR: Final[str] = '\033[39m'
CLEAR_BOLD: Final[str] = '\033[22m'
CLEAR_UNDERLINE: Final[str] = '\033[24m'
CLEAR_ITALIC: Final[str] = '\033[23m'
CLEAR_REVERSE: Final[str] = '\033[27m'
CLEAR_STRIKETHROUGH: Final[str] = '\033[29m'

def printdanger(*values: object, sep: str = ' ', end: str = '\n', file=None, flush=False) -> None:
    print(BOLD + RED, *values, sep=sep, end=end + CLEAR_ALL, file=file, flush=flush)
