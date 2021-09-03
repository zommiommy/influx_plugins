from .logger import logger, setLevel
from .db_adapter import DBAdapter
from .time_parsing import *

copyrights = """influx_plugins is a free software developed by Tommaso Fontana for Wurth Phoenix S.r.l. under GPL-2 License."""

class Colors:
    BLACK="\033[30m"
    RED="\033[31m"
    GREEN="\033[32m"
    YELLOW="\033[33m"
    BLUE="\033[34m"
    MAGENTA="\033[35m"
    CYAN="\033[36m"
    WHITE="\033[37m"
    RESET="\033[0;37;40m"