import os
import sys
import logging
import argparse
import urllib3
urllib3.disable_warnings()

from .anomaly_detection_main import anomaly_detection
from ..utils import (
    copyrights, Colors, logger, epoch_to_time, 
    time_to_epoch, MyParser,
    read_json_with_comments,
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
For example 0.95 means that the values with probability less than 5%% 
will be classified as possible anomalies.
{}
""".format(default_fmt),
        type=float,
        default=0.95,
    ) 
    analysis_settings.add_argument(
        "--anomaly",
        help=
"""The model infers how probable is each point, this is the probability treshold 
that classifies anomalies.
For example 0.99 means that the values with probability less than 1%% 
will be classified as anomalies.
{}
""".format(default_fmt),
        type=float,
        default=0.99,
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

    db_settings = parser.add_argument_group(
"""{cyan}Database settings (optional){reset}
The settings for the DB will follow the following priorities:
- Command line argument, if specified
- Db settings json, if present and if specified
- Default (this can be found at the end of the help of each parameter)
""".format(cyan=Colors.CYAN, reset=Colors.RESET)
    )
    
    db_settings.add_argument(
        "--db-settings", 
        help="DB setting json, an example of this file can be found in \n./tests/test_db_settings.json.%s"%default_fmt, 
        type=str, 
        default="./db_settings.json",
    )
    db_settings.add_argument(
        "--input-database",
        help="The databse from where the data shall be read from. (default \"icinga2\")",
        type=str, 
        default=None,
    )
    db_settings.add_argument(
        "--input-measurement",
        help="The measuremnt from where the data shall be read from",
        type=str, 
        default=None,
    ) 
    db_settings.add_argument(
        "--output-database",
        help="The databse from where the data shall be written to. (default \"icinga2_ml\")",
        type=str, 
        default="icinga2_ml",
    )
    db_settings.add_argument(
        "--output-measurement",
        help="The measuremnt from where the data shall be written to",
        type=str, 
        default=None,
    ) 
    db_settings.add_argument(
        "--host",
        help="The hostname / ip of the Influx DBMS. (default \"localhost\")",
        type=str, 
        default=None,
    )
    db_settings.add_argument(
        "--port",
        help="The port of the Influx DBMS. (default 8086)",
        type=int, 
        default=None,
    )
    db_settings.add_argument(
        "--username",
        help="The username to use to login into the Influx DBMS. (default \"root\")",
        type=str, 
        default=None,
    )
    db_settings.add_argument(
        "--password",
        help="The password to use to login into the Influx DBMS. (default \"root\")",
        type=str, 
        default=None,
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
    db_settings.add_argument(
        "--cert",
        help=
"""Path to client certificate information to use for mutual TLS authentication. 
You can specify a local cert to use as a single file containing the private key 
and the certificate, or as a tuple of both files paths. %s"""%default_fmt,
        type=str,
        default=None,
    )

    args = vars(parser.parse_args())

    if "db-settings" in args:
        json_db_settings = read_json_with_comments(args["db-settings"]).get("anomaly_detection", {})
    else:
        json_db_settings = {}
    
    # Merge the values so that proper defaults and settings are propagated 
    # following the right priority
    # In python 3.9 and 3.5 there are better ways to merge dictionaries
    # but we need to support old python versions so we are stuck with this
    db_defaults = {
        "input_database": "icinga2",
        "input_measurement": "measurement",
        "output_database": "icinga2_ml",
        "output_measurement": "measurement",
        "host": "localhost",
        "port": 8086,
        "username": "root",
        "password": "root",
        "ssl": False,
        "verify_ssl": False,
        "timeout": 60,
        "retries": 3,
        "use_udp": False,
        "udp_port": 4444,
        "proxies": {},
        "cert": None
    }
    db_defaults.update({
        k: v
        for k, v in json_db_settings.items()
        if v is not None
    })
    db_defaults.update({
        k: v
        for k, v in args.items()
        if v is not None
    })

    anomaly_detection(db_defaults)
