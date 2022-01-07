import json
from influxdb import InfluxDBClient

from influx_plugins import anomaly_detection
from influx_plugins.utils import logger, read_json_with_comments
from subprocess import run, PIPE
from .test_utils import *


DATA_METHODS = [
    create_telegraf_schema_anomaly_data,
    create_icinga_schema_anomaly_data,
]

def test_check_time_icinga():
    # Create the test client to write the data to the db
    test_settings =  read_json_with_comments("./tests/test_db_settings.json")["anomaly_detection"]
    test_db = test_settings["input_database"]
    db_settings = {
        "database":test_db,
        "username":test_settings["username"],
        "password":test_settings["password"],
    }
    test_client = InfluxDBClient(**db_settings)

    # Create the test_db
    test_client.create_database(test_db)
    test_client.switch_database(test_db)

    for data_method in DATA_METHODS:
        # write the test data
        settings = data_method(test_client)

        cli_args = " ".join(
            "" if v == False
            else 
                "--{}".format(k.replace("_", "-"))
                if v == True
                else
                "--{}=\"{}\"".format(k.replace("_", "-"), v)
            for k, v in settings.items()
        )
        # Ensure that the db settings are the same used to write the data
        settings = {**test_settings, **settings}
        # run the prediction
        anomaly_detection(settings)

        logger.warn("Calling subprocess with '%s'", "./bin/anomaly_detection " + cli_args)
        result = run("./bin/anomaly_detection " + cli_args, shell=True, check=False, stdout=PIPE)
        print(result.stdout)