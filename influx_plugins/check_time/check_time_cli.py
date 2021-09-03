import os
import sys
import logging
import argparse


from .check_time_main import check_time
from ..utils import copyrights, Colors, logger, epoch_to_time, time_to_epoch

description = """
{copyrights}
{yellow}Description:{reset}
The goal of this utility is to predict the saturation time of influx data.
This for example can be used to predict the time left before a disk will
reach 100% usage.

We currently support two schemas, `telegraf` and `icinga`.

In the `telegraf` schema has two columns, `kpi` and `value` where all the values 
are, for example:
{blue}
time       host        service    kpi              value
----       ----        -------     ---              -----
1567005362 my.host.com my.service disk_utilization 0.9
1567005362 my.host.com my.service cpu_utilization  0.3
{reset}
while in the `icinga` schema all the values are in different columns:
{blue}
time       host        service    disk_utilization cpu_utilization
----       ----        -------    ---------------- ---------------
1567005362 my.host.com my.service 0.3              0.9
{reset}
Optionally, both can have a max kpi / column. 

For the `telegraf` these should be selected using the `--max-kpi` argument and 
the schema should look like this:
{blue}
time       host        service    kpi                   value
----       ----        -------     ---                  -----
1567005362 my.host.com my.service disk_utilization      90
1567005362 my.host.com my.service disk_utilization_max  100
{reset}
while for the `icinga` schema you should use the `--max-column` argument and
the schema should look like this:
{blue}
time       host        service    disk_utilization disk_utilization_max
----       ----        -------    ---------------- --------------------
1567005362 my.host.com my.service 90               100
{reset}

{yellow}Arguments:{reset}
""".format(
    copyrights=copyrights,
    blue=Colors.BLUE, 
    yellow=Colors.YELLOW, 
    reset=Colors.RESET,
)

class MyParser(argparse.ArgumentParser):
    """Custom parser to ensure that the exit code on error is 1
        and that the error messages are printed on the stderr 
        so that the stdout is only for sucessfull data analysis"""

    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help(file=sys.stderr)
        sys.exit(1)

def check_time_cli():
    """The Cli adapter for the check_time utility."""
    parser = MyParser(
        description=description, 
        formatter_class=argparse.RawTextHelpFormatter
    )
    default_fmt = " {}(default: %(default)s){}".format(Colors.YELLOW, Colors.RESET)

    parser.add_argument(
        "--db-settings", 
        help="DB setting json, an example of this file can be found in \n./tests/test_db_settings.json.%s"%default_fmt, 
        type=str, 
        default="./db_settings.json",
    )
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

    thresholds_settings = parser.add_argument_group('{cyan}thresholds settings (required){reset}'.format(cyan=Colors.CYAN, reset=Colors.RESET))
    thresholds_settings.add_argument(
        "-n", 
        "--window",
         help="the range of time to consider in the analysis.",
         type=str, 
         required=True,
    )
    thresholds_settings.add_argument(
        "-w", 
        "--warning-threshold", 
        help="the time that if the predicted time is lower the script will exit(1).", 
        type=str, 
        required=True,
    )
    thresholds_settings.add_argument(
        "-c", 
        "--critical-threshold", 
        help="the time that if the predicted time is lower the script will exit(2).",
        type=str, 
        required=True,
    )

    query_settings = parser.add_argument_group('{cyan}query settings (required){reset}'.format(cyan=Colors.CYAN, reset=Colors.RESET))
    query_settings.add_argument(
        "--db-type", 
        help="Which kind of schema the measurement has.", 
        type=str, 
        choices=["icinga", "telegraf"], 
        required=True
    )
    query_settings.add_argument(
        "--measurement", 
        help="measurement where the data will be queried.", 
        type=str, 
        required=True
    )
    query_settings.add_argument(
        "--host", 
        help="host which disks will be checked.", 
        type=str, 
        required=True
    )
    query_settings.add_argument(
        "--host-column", 
        help="The name of the host column.%s"%default_fmt,         
        type=str, 
        default="host",
    )
    query_settings.add_argument(
        "--service", 
        help="service to be checked.",         
        type=str, 
        required=True
    )
    query_settings.add_argument(
        "--service-column", 
        help="The name of the service column.%s"%default_fmt,         
        type=str, 
        default="service",
    )

    query_settings.add_argument(
        "--value-type", 
        help=
"""How the value should be interpreted:
- `usage`: value / max
- `usage_percentile`: value / 100
- `usage_quantile`: value
- `free`: 1 - (value / max)
- `free_percentile`: 1 - (value / 100)
- `free_quantile`: 1 - value
Note that for `usage` and `free` you must also specify the `--max-column` argument
with which column / kpi to use to retrieve the max.%s
"""%default_fmt,       
        type=str, 
        choices=[
            "usage", "usage_percentile", "usage_quantile", 
            "free", "free_percentile", "free_quantile"
        ],
        default="usage",
    )

    query_settings.add_argument(
        "--max-column", 
        help=
"""The column that contains the max (saturation level). 
This is used only if value-type is set to `usage` or `free`,
""",         
        type=str, 
        required=True,
    )

    icinga_settings = parser.add_argument_group('{blue}icinga db settings (required if --db-type=icinga){reset}'.format(blue=Colors.BLUE, reset=Colors.RESET))
    icinga_settings.add_argument(
        "--target-column", 
        help="Which column will be used for the analysis.",         
        type=str, 
        default=None,
    )

    telegraf_settings = parser.add_argument_group('{blue}telegraf db settings (required if --db-type=telegraf){reset}'.format(blue=Colors.BLUE, reset=Colors.RESET))
    telegraf_settings.add_argument(
        "--target-kpi", 
        help="Which kpi will be used for the analysis",         
        type=str, 
        default=None,
    )
    telegraf_settings.add_argument(
        "--kpi-column", 
        help="Which column contains the kpis",         
        type=str, 
        default="kpi",
    )
    telegraf_settings.add_argument(
        "--value-column", 
        help="Which column contains the values associated to the kpis",         
        type=str, 
        default="value",
    )

    args = vars(parser.parse_args())

    # Parse the time fields
    args["window"] = time_to_epoch(args["window"])
    args["warning_threshold"] = time_to_epoch(args["warning_threshold"])
    args["critical_threshold"] = time_to_epoch(args["critical_threshold"])

    # Run the prediction
    time_predicted, score = check_time(args)
    
    logger.info("Warning threshold %s", args["warning_threshold"])
    logger.info("Critical threshold %s", args["critical_threshold"])

    # Critical case
    if time_predicted < args["critical_threshold"]:
        logger.critical("Critical theshold failed!")
        exit_code = 2
        status = "CRITICAL"
    # Warning case
    elif time_predicted < args["warning_threshold"]:
        logger.warning("Warning theshold failed!")
        exit_code = 1
        status = "WARNING"
    # Ok case
    else:
        logger.info("Sucessfull exit")
        exit_code = 0
        status = "OK"

    # Print the data in a format that is neteye compatible
    # This should be the only thing in stdout
    print("{}: {} {} ({:.2f})".format(status, time_predicted, epoch_to_time(time_predicted), score))
    sys.exit(exit_code)