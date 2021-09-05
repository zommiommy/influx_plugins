import json
from influxdb import InfluxDBClient

from influx_plugins import anomaly_detection
from .test_utils import *

DATA_METHODS = [
    create_telegraf_schema_anomaly_data,
    create_icinga_schema_anomaly_data,
]

def test_check_time_icinga():
    # Create the test client to write the data to the db
    with open("./tests/test_db_settings.json", "r") as f:
        test_settings = json.load(f)
    test_db = test_settings["database"]
    test_client = InfluxDBClient(**test_settings)

    # Create the test_db
    test_client.create_database(test_db)
    test_client.switch_database(test_db)

    for data_method in DATA_METHODS:
        # write the test data
        settings = data_method(test_client)
        # Ensure that the db settings are the same used to write the data
        settings = {**test_settings, **settings}
        # run the prediction
        anomaly_detection(settings)