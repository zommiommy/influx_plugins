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

import argparse
class MyParser(argparse.ArgumentParser):
    """Custom parser to ensure that the exit code on error is 1
        and that the error messages are printed on the stderr 
        so that the stdout is only for sucessfull data analysis"""

    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help(file=sys.stderr)
        sys.exit(1)