import json
import logging
import pandas as pd
from influxdb import InfluxDBClient
from ..utils import logger, setLevel, DBAdapter
from ..utils import parse_time_to_epoch



def classify_point(point, training_data):
    ts = pd.Timestamp(point["time"])
    key = (ts.day_name(), ts.hour)
    warn_threshold = training_data[key]["warning"]
    anom_threshold = training_data[key]["anomaly"]
    if point["value"] > anom_threshold:
        return {
            "warning":0,
            "anomaly":1,
            "value":point["value"],
            "warn_threshould":warn_threshold,
            "anom_threshold":anom_threshold,
        }
    elif point["value"] > warn_threshold:
        return {
            "warning":1,
            "anomaly":0,
            "value":point["value"],
            "warn_threshould":warn_threshold,
            "anom_threshold":anom_threshold,
        }
    else:
        return {
            "warning":0,
            "anomaly":0,
            "value":point["value"],
            "warn_threshould":warn_threshold,
            "anom_threshold":anom_threshold,
        }

def anomaly_detection(settings):
    # Set the logger level
    setLevel({
        "debug":logging.DEBUG,
        "info":logging.INFO,
        "warn":logging.WARN,
        "critical":logging.CRITICAL,
    }[settings["verbosity"]])

    input_db_settings = {
        key:settings[key]
        for key in [
            "host",
            "port",
            "username",
            "password",
            "ssl",
            "verify_ssl",
            "cert",
        ]
        if key in settings
    }
    input_db_settings["database"] = settings["input_database"]
    output_db_settings = input_db_settings.copy()
    output_db_settings["database"] = settings["output_database"]

    in_db = DBAdapter(input_db_settings, None)

    selectors_groups = in_db.get_selectors_combinations(settings)

    logger.info("There are %s unique combinations of selectors.", len(selectors_groups))

    for selector_values in selectors_groups:
        logger.info("Analyzing the selector group: %s", selector_values)
        training_data = in_db.get_training_data(selector_values, settings)
        logger.info("Computed training data:\n%s", training_data)
        data_generator = in_db.get_anomaly_data(selector_values, settings)
        
        logger.info("Classifying the data")
        classifications = [
            {
                "measurement": settings["output_measurement"],
                "time":point["time"],
                "fields":classify_point(point, training_data),
                "tags":selector_values,
            }
            for point in data_generator
        ]
        
        
        if len(classifications) == 0:
            logger.info("There is no data to classify for the current selectors values and the current filter")
            continue

        logger.info("An example of the classified data is:\n%s", classifications[0])

        if settings["dry_run"]:
            logger.info("Dry-run enabled, gonna skip to the next task and not write any data.")
            continue

        if settings["write_to_file"]:
            file_path = "debug/{output_database}.{output_measurement}.{selectors_str}.json".format(
                selectors_str="_".join("{}_{}".format(k,v) for k,v in selector_values.items()),
                **settings,
            )
            logger.info("the flag `write_to_file` is setted, dumping the data to '%s'", file_path)
            with open(file_path, "w") as f:
                json.dump(classifications, f)

            continue

        logger.info("Writing the classified data to the db `%s`", output_db_settings["database"])
        # Write to db
        client = InfluxDBClient(**output_db_settings)
        # ensure that the database exists
        client.create_database(output_db_settings["database"])
        client.switch_database(output_db_settings["database"])
        # Write the data
        client.write_points(classifications)
        logger.info("Success, wrote the data to the db `%s`", output_db_settings["database"])