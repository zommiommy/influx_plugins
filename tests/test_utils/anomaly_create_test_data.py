import numpy as np
from time import time
from datetime import datetime, timedelta

def create_telegraf_schema_anomaly_data(client):
    """Write test data following the telegraf schema:
    
    time       host        service kpi           value
    ----       ----        ------- ---           -----
    1567005362 my.host.com service disk_util      0.9


    it returns the number of seconds that the check time will have
    to predict for each kpi and the settings needed to correctly read the data
    """
    now = datetime.now()
    # client.drop_measurement("anomaly_measurement_telegraf")
    
    check_time_test = [
        {
            "measurement": "anomaly_measurement_telegraf",
            "tags": {
                "host": "host01",
                "service": "service01",
                "kpi": "disk_util"
            },
            "time": (now - timedelta(seconds=i)).isoformat(),
            "fields": {
                "value":v/20 * (((100 - i) % 100) / 50 - 1),
            }
        }
        for i, v in enumerate(reversed(np.linspace(0, 8, 800)))
    ]

    client.write_points(check_time_test)
    
    settings = {
        "input_database":"test_db",
        "output_database":"test_db",
        "input_measurement":"anomaly_measurement_icinga",
        "output_measurement":"anomaly_measurement_icinga_ml",
        
        "selectors":"host,service,kpi",
        "filter":"",#"host = 'host01' AND service = 'service01'",
        "field":"value",

        "training_timeframe":"4w",
        "window":"100s",

        "warning":0.90,
        "anomaly":0.95,

        "write_to_file":False,
        "dry_run":False,

        "verbosity":"info",
    }
    return settings

def create_icinga_schema_anomaly_data(client):
    """Write test data using the icinga schema:
    
    time       host        service disk_utilization
    ----       ----        ------- ----------------
    1567005362 my.host.com service 0.3              
    
    it returns the number of seconds that the check time will have
    to predict for each kpi and the settings needed to correctly read the data
    """
    now = datetime.now()
    
    check_time_test = [
        {
            "measurement": "anomaly_measurement_icinga",
            "tags": {
                "host": "host01",
                "service": "service01",
            },
            "time": (now - timedelta(seconds=i)).isoformat(),
            "fields": {
                "disk_utilizzation":v,
            }
        }
        for i, v in enumerate(reversed(np.linspace(0, 1.2, 1200) + 0.3 * np.random.random(size=1200)))
    ]
    # Drop the previous data
    # client.drop_measurement("anomaly_measurement_icinga")
    client.write_points(check_time_test)
    
    settings = {
        "input_database":"test_db",
        "output_database":"test_db",
        "input_measurement":"anomaly_measurement_icinga",
        "output_measurement":"anomaly_measurement_icinga_ml",
        
        "selectors":"host,service",
        "filter":"",#"host = 'host01' AND service = 'service01'",
        "field":"disk_utilizzation",

        "training_timeframe":"4w",
        "window":"100s",

        "warning":0.90,
        "anomaly":0.95,

        "write_to_file":True,
        "dry_run":False,

        "verbosity":"info",
    }

    return settings
