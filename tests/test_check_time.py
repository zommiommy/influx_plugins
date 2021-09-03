import json
from influxdb import InfluxDBClient

from influx_plugins import check_time
from .test_utils import *

DATA_METHODS = [
    create_icinga_schema_check_time_data,
    create_icinga_schema_check_time_data_free,
    create_telegraf_schema_check_time_data_no_max,
    create_telegraf_schema_check_time_data,
]

def test_check_time_icinga():
    # Create the test client to write the data to the db
    with open("./tests/test_db_settings.json", "r") as f:
        test_settings = json.load(f)
    test_db = test_settings.pop("database")
    test_client = InfluxDBClient(**test_settings)
    # Create the test_db
    test_client.create_database(test_db)
    test_client.switch_database(test_db)

    for data_method in DATA_METHODS:
        # write the test data
        to_predict, min_score, settings = data_method(test_client)
        # Ensure that the db settings are the same used to write the data
        settings["db_settings"] = "./tests/test_db_settings.json"
        # run the prediction
        time_predicted, score = check_time(settings)
        # Check that it's reasonable (max 25% error)
        assert (abs(time_predicted - to_predict) / to_predict) < 0.25, "Did not correctly predicted the time"
        # Check that the score is over the lowerbound tought for this task
        assert score >= min_score, "Prediction with lower score than expected on perfectly clean data"