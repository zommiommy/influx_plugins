import os
import json
import logging
from ..utils import logger, setLevel, DBAdapter, time_to_epoch, read_json_with_comments
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

    settings["window"] = time_to_epoch(settings["window"])
    settings["warning_threshold"] = time_to_epoch(settings["warning_threshold"])
    settings["critical_threshold"] = time_to_epoch(settings["critical_threshold"])

    if not os.path.exists(settings["db_settings"]):
        logger.error("The given db-settings path do not exist: '%s'", settings["db_settings"])

    # Read the json skipping comment lines
    db_settings = read_json_with_comments(settings["db_settings"])
    
    db_settings = db_settings.get("check_time", {})

    db = DBAdapter(db_settings, settings["db_type"])

    logger.info("Retrieving the data from the db")
    data = db.get_check_time_data(settings).get_points()
    logger.debug(settings)
    x, y = normalize_data(data, settings["value_type"], settings.get("max_value"))   

    logger.info("Got %s points", x.size)

    if x.size == 0:
        logger.error("Got no point!")

    return predict_time_left(x, y, settings.get("debug_plot"))
    