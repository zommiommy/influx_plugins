import numpy as np
from time import time
from datetime import datetime, timedelta

def create_telegraf_schema_check_time_data(client):
    """Write test data following the telegraf schema:
    
    time       host        service kpi           value
    ----       ----        ------- ---           -----
    1567005362 my.host.com service disk_util      0.9
    1567005362 my.host.com service disk_util_max  2


    it returns the number of seconds that the check time will have
    to predict for each kpi and the settings needed to correctly read the data
    """
    now = datetime.now()
    client.drop_measurement("check_time_measurement_telegraf")
    
    check_time_test = [
        {
            "measurement": "check_time_measurement_telegraf",
            "tags": {
                "host": "host01",
                "service": "service01",
                "kpi": "disk_util"
            },
            "time": (now - timedelta(seconds=i)).isoformat(),
            "fields": {
                "value":v + ((100 - i) % 100) / 50 - 1,
                "max":10,
            }
        }
        for i, v in enumerate(reversed(np.linspace(0, 8, 800)))
    ]

    client.write_points(check_time_test)
    
    settings = {
        "db_type":"telegraf",
        "measurement":"check_time_measurement_telegraf",
        
        "filter":"host = 'host01' AND service = 'service01'",

        "kpi_column":"kpi",
        "target_kpi":"disk_util",

        "value_column":"value",
        "value_type":"usage",

        "max_column":"max",

        "verbosity":"info",
        "window":"1000s",
        "debug_plot":"debug/debug_telegraf.png",
        "warning_threshold":"300s",
        "critical_threshold":"400s",
    }

    return 200, 0.9, settings

def create_telegraf_schema_check_time_data_no_max(client):
    """Write test data following the telegraf schema:
    
    time       host        service kpi          value
    ----       ----        ------- ---          -----
    1567005362 my.host.com service cpu_util     0.9


    it returns the number of seconds that the check time will have
    to predict for each kpi and the settings needed to correctly read the data
    """
    now = datetime.now()
    client.drop_measurement("check_time_measurement_telegraf")
    
    check_time_test = [
        {
            "measurement": "check_time_measurement_telegraf",
            "tags": {
                "host": "host01",
                "service": "service01",
                "kpi": "cpu_util"
            },
            "time": (now - timedelta(seconds=i)).isoformat(),
            "fields": {
                "value":v,
            }
        }
        for i, v in enumerate(reversed(np.linspace(0, 0.6, 600)))
    ]
    client.write_points(check_time_test)
    
    settings = {
        "db_type":"telegraf",
        "measurement":"check_time_measurement_telegraf",

        "filter":"host = 'host01' AND service = 'service01'",

        "kpi_column":"kpi",
        "target_kpi":"cpu_util",

        "value_column":"value",
        "value_type":"usage_quantile",
        
        "verbosity":"info",
        "window":"1000s",
        "debug_plot":"debug/debug_telegraf_no_max.png",
        "warning_threshold":"500s",
        "critical_threshold":"600s",
    }

    return 400, 0.98, settings

def create_icinga_schema_check_time_data(client):
    """Write test data using the icinga schema:
    
    time       host        service disk_utilization disk_utilization_max
    ----       ----        ------- ---------------- ---------------
    1567005362 my.host.com service 0.3              2
    
    it returns the number of seconds that the check time will have
    to predict for each kpi and the settings needed to correctly read the data
    """
    now = datetime.now()
    
    check_time_test = [
        {
            "measurement": "check_time_measurement_icinga",
            "tags": {
                "host": "host01",
                "service": "service01",
            },
            "time": (now - timedelta(seconds=i)).isoformat(),
            "fields": {
                "disk_utilizzation":v,
                "disk_utilizzation_max":2,
            }
        }
        for i, v in enumerate(reversed(np.linspace(0, 1.2, 1200) + 0.3 * np.random.random(size=1200)))
    ]
    # Drop the previous data
    client.drop_measurement("check_time_measurement_icinga")
    client.write_points(check_time_test)
    
    settings = {
        "db_type":"icinga",
        "measurement":"check_time_measurement_icinga",
        "filter":"host = 'host01' AND service = 'service01'",
        "target_column":"disk_utilizzation",
        "value_type":"usage",
        "max_column":"disk_utilizzation_max",
        "verbosity":"info",
        "window":"10000s",
        "debug_plot":"debug/debug_icinga.png",
        "warning_threshold":"900s",
        "critical_threshold":"1000s",
    }

    return 800, 0.9, settings

def create_icinga_schema_check_time_data_free(client):
    """Write test data using the icinga schema:
    
    time       host        service space_left_percent
    ----       ----        ------- ------------------
    1567005362 my.host.com service 0.3               
    
    it returns the number of seconds that the check time will have
    to predict for each kpi and the settings needed to correctly read the data
    """
    now = datetime.now()
    
    check_time_test = [
        {
            "measurement": "check_time_measurement_icinga",
            "tags": {
                "host": "host01",
                "service": "service01",
            },
            "time": (now - timedelta(seconds=i)).isoformat(),
            "fields": {
                "space_left_percent":v,
            }
        }
        for i, v in enumerate(np.linspace(0.4, 0.8, 1200) + 0.1 * np.sin(np.linspace(0, 10 * np.pi, 1200)))
    ]
    # Drop the previous data
    client.drop_measurement("check_time_measurement_icinga")
    client.write_points(check_time_test)
    
    settings = {
        "db_type":"icinga",
        "measurement":"check_time_measurement_icinga",
        "filter":"host = 'host01' AND service = 'service01'",
        "target_column":"space_left_percent",
        "value_type":"free_quantile",
        "verbosity":"info",
        "window":"10000s",
        "debug_plot":"debug/debug_icinga_free.png",
        "warning_threshold":"1500s",
        "critical_threshold":"2000s",
    }

    return 1400, 0.65, settings