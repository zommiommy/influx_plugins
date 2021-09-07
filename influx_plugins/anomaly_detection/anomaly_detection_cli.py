import os
import sys
import logging
import argparse

from .anomaly_detection_main import anomaly_detection
from ..utils import (
    copyrights, Colors, logger, epoch_to_time, 
    time_to_epoch, MyParser 
)

description = """

"""


def anomaly_detection_cli():
    """The Cli adapter for the check_time utility."""
    parser = MyParser(
        description=description, 
        formatter_class=argparse.RawTextHelpFormatter
    )
    default_fmt = " {}(default: %(default)s){}".format(Colors.YELLOW, Colors.RESET)

    parser.add_argument(
        "--verbosity", 
        help="set the logging verbosity.%s"%default_fmt, 
        type=str, 
        choices=["debug", "info", "warn", "critical"], 
        default="info",
    )
    parser.add_argument(
        "--debug-plot", 
        help="Plot the data and the prediciton and save it to the given path. E.g. `--debug-plot=test.png`", 
        type=str, 
        default=None,
    )

    read_settings = parser.add_argument_group('{cyan}Read settings{reset}'.format(cyan=Colors.CYAN, reset=Colors.RESET))
    read_settings.add_argument(
        "--field",
        help="Which column contain the data to be analyzed",
        type=str, 
        required=True,
    ) 
    read_settings.add_argument(
        "--selectors",
        help=
"""The columns, separated by commas (no spaces), that will be used to group by the data.
Example:
--selectors="host,service,disk"
""",
        type=str, 
        required=True,
    ) 
    read_settings.add_argument(
        "--filter",
        help=
"""
Extra filter to add to the WHERE clauses, this can be used to include or exclude
data.
Example:
--filter="disk = 'sda' OR (host != 'notwantedhost' AND service != 'notwantedservice")
""",
        type=str, 
        default="",
    ) 
    
    
    analysis_settings = parser.add_argument_group('{cyan}Analysis settings{reset}'.format(cyan=Colors.CYAN, reset=Colors.RESET))
    analysis_settings.add_argument(
        "--window",
        help=
"""How much time to analyze. e.g. `1d1h1s` will analyze, starting from now, 
the last 24-hours + 1 hour + 1 second.%s"""%default_fmt,
        type=str, 
        default="1h",
    )  
    analysis_settings.add_argument(
        "--training-timeframe",
        help="Set the timeframe relative to now of the training.%s"%default_fmt,
        type=str, 
        default="4w"
    )  
    analysis_settings.add_argument(
        "--warning",
        help=
"""The model infers how probable is each point, this is the probability treshold 
that classifies possible anomalies.
For example 0.05 means that the values with probability less than 5%% 
will be classified as possible anomalies.
{}
""".format(default_fmt),
        type=float,
        default=0.05,
    ) 
    analysis_settings.add_argument(
        "--anomaly",
        help=
"""The model infers how probable is each point, this is the probability treshold 
that classifies anomalies.
For example 0.02 means that the values with probability less than 2%% 
will be classified as anomalies.
{}
""".format(default_fmt),
        type=float,
        default=0.02,
    ) 

    analysis_settings.add_argument(
        "--group-by-time",
        help=
"""In several applications, there are cyclical behaviours, such as more traffic
on the week-end or less requests during lunch break.
So, using a cycle of a week, data will be grouped using this value, so that the 
comparison is more fair.
Example: if this argument is `1h`, if I have to classify a point with date:
`monday 12:10`, it will compared against all the training data between 
`monday 12:00` and `monday 13:00` of the previous weeks.
If otherwise the argument is `1d`, all the data from `friday` will be compared
against the `fridies` of the previous weeks (in the training data).
{}
""".format(default_fmt),
        type=str, 
        default="1h"
    )  
    analysis_settings.add_argument(
        "--ignore-lower-values",
        help=
"""Usually the analysis will report both values that are too-big or too-small. 
This flags only keeps the higher values. This changes the warning and anomaly 
quantiles from two-tailed ones to single-tailed ones, which means that you might
want to use smaller values for the `--anomaly` and `--warning` arguments, because
this changes the distribution of the values.
""",
        action="store_true",
        default=False,
    ) 
    
    write_settings = parser.add_argument_group('{cyan}Write settings{reset}'.format(cyan=Colors.CYAN, reset=Colors.RESET))
    write_settings.add_argument(
        "--dry-run",
        help="If this flag is setted the script will not write the results on the output DB. It's mostly for testing.",
        action="store_true",
        default=False,
    ) 
    write_settings.add_argument(
        "--write-to-file",
        help=
"""If this flag is setted,the script will not write the results on the db but 
on a file with format `{output_database}.{output_measurement}.{selectors}.json`""",
        action="store_true",
        default=False,
    ) 

    db_settings = parser.add_argument_group('{cyan}Database settings (optional){reset}'.format(cyan=Colors.CYAN, reset=Colors.RESET))
    db_settings.add_argument(
        "--input-database",
        help="The databse from where the data shall be read from.%s"%default_fmt,
        type=str, 
        default="icinga2",
    )
    db_settings.add_argument(
        "--input-measurement",
        help="The measuremnt from where the data shall be read from",
        type=str, 
        required=True,
    ) 
    db_settings.add_argument(
        "--output-database",
        help="The databse from where the data shall be written to.%s"%default_fmt,
        type=str, 
        default="icinga2_ml",
    )
    db_settings.add_argument(
        "--output-measurement",
        help="The measuremnt from where the data shall be written to",
        type=str, 
        required=True,
    ) 
    db_settings.add_argument(
        "--host",
        help="The hostname / ip of the Influx DBMS.%s"%default_fmt,
        type=str, 
        default="localhost",
    )
    db_settings.add_argument(
        "--port",
        help="The port of the Influx DBMS.%s"%default_fmt,
        type=int, 
        default=8086,
    )
    db_settings.add_argument(
        "--username",
        help="The username to use to login into the Influx DBMS.%s"%default_fmt,
        type=str, 
        default="root",
    )
    db_settings.add_argument(
        "--password",
        help="The password to use to login into the Influx DBMS.%s"%default_fmt,
        type=str, 
        default="root",
    )
    db_settings.add_argument(
        "--ssl",
        help="Enable ssl",
        action="store_true",
        default=False,
    )
    db_settings.add_argument(
        "--verify-ssl",
        help="Enable verification of ssl certificates",
        action="store_true",
        default=False,
    )

    args = vars(parser.parse_args())

    anomaly_detection(args)