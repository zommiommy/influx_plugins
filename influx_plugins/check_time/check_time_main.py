import os
import json
import logging
from ..utils import logger, setLevel, DBAdapter
from .predict_time_left import predict_time_left
from .normalize_data import normalize_data

def check_time(settings):
    # Set the logger level
    setLevel({
        "debug":logging.DEBUG,
        "info":logging.INFO,
        "warn":logging.WARN,
        "critical":logging.CRITICAL,
    }[settings["verbosity"]])

    logger.info("Starting with settings %s", settings)

    # Check that the arguments are coherent
    if settings["db_type"] == "icinga":
        if settings.get("target_column") is None:
            logger.error("--db-type=icinga but --target-column was not passed")
        if settings.get("target_kpi") is not None:
            logger.error(
                "--db-type=icinga but --target-kpi was passed which is "
                "for --db-type=telegraf"
            )
        if settings.get("max_kpi") is not None:
            logger.error(
                "--db-type=icinga but --max-kpi was passed which is "
                "for --db-type=telegraf"
            )
    else:
        if settings.get("target_kpi") is None:
            logger.error("--db-type=telegraf but --target-kpi was not passed")
        if settings.get("target_column") is not None:
            logger.error(
                "--db-type=telegraf but --target-column was passed which is "
                "for --db-type=icinga"
            )

    if not os.path.exists(settings["db_settings"]):
        logger.error("The given db-settings path do not exist: '%s'", settings["db_settings"])

    with open(settings["db_settings"], "r") as f:
        db_settings = json.load(f)

    db = DBAdapter(db_settings, settings["db_type"])

    logger.info("Retrieving the data from the db")
    data = db.get_check_time_data(settings).get_points()

    x, y = normalize_data(data, settings["value_type"])   

    logger.info("Got %s points", x.size)

    return predict_time_left(x, y, settings.get("debug_plot"))
    