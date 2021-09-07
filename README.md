# Influx Plugins
For more info on the arguments just call the binary with `--help` it has a description of the script and all the arguments.


# Testing
To run the tests just run:
```bash
$ docker-compose up
$ pytest -s
```
This will start a new self-contained influx db and will popolate it with data
and test the predictions.

# Examples:
```bash
$ ./bin/check_time --db-type="telegraf" --measurement="check_time_measurement_telegraf" --filter="host = 'host01' AND service = 'service01'" --kpi-column="kpi" --target-kpi="disk_util" --value-column="value" --value-type="usage" --max-column="max" --verbosity="info" --window="1000s" --debug-plot="debug/debug_telegraf.png" --warning-threshold="300s" --critical-threshold="400s"

INFO:db_adapter.py:__init__:11:Conneting to the DB on [localhost:8086] for the database [test_db]
INFO:check_time_main.py:check_time:54:Retrieving the data from the db
INFO:db_adapter.py:query:15:Executing query:

SELECT time, value as value
FROM "check_time_measurement_telegraf"
WHERE (
    time > (now() - 1000s)
    AND
    kpi = 'cpu_util'
    AND host = 'host01' AND service = 'service01'
)

INFO:db_adapter.py:query:21:Got 1 points
INFO:check_time_main.py:check_time:59:Got 600 points
INFO:predict_time_left.py:predict_time_left:33:The coefficents predicted are m:'0.001001669449019937' q:'1.8528845124876625e-11' with score:'1.0'
INFO:predict_time_left.py:predict_time_left:75:The predicted time left is 399.33333337649526 seconds with a score of 100.0%
INFO:check_time_cli.py:check_time_cli:202:Warning threshold 500.0
INFO:check_time_cli.py:check_time_cli:203:Critical threshold 600.0
INFO:check_time_cli.py:check_time_cli:217:Sucessfull exit
OK: 399.33333337649526 6m39.33s (100.00%)
```
The result can also be checked by the exit code:
- 0 -> OK
- 1 -> Warn
- 2 -> Critical

Also, all the logging is done in `stderr` so the last line will be the only thing in `stdout`.


```bash
$ ./bin/anomaly_detection --input-database="test_db" --output-database="test_db" --input-measurement="anomaly_measurement_telegraf" --output-measurement="anomaly_measurement_telegraf_ml" --selectors="host,service,kpi" --field="value" --training-timeframe="4w" --window="100s" --warning="0.9" --anomaly="0.95" --verbosity="info"

INFO:db_adapter.py:__init__:11:Conneting to the DB on [localhost:8086] for the database [test_db]
INFO:db_adapter.py:get_selectors_combinations:26:Finding all the combinations of the selectors fields
INFO:db_adapter.py:query:15:Executing query:

SELECT DISTINCT(host) as selector
FROM (
    SELECT *
    FROM anomaly_measurement_telegraf
    WHERE (
        time > (now() - 100s)

    )
)

INFO:db_adapter.py:query:21:Got 1 points
INFO:db_adapter.py:query:15:Executing query:

SELECT DISTINCT(service) as selector
FROM (
    SELECT *
    FROM anomaly_measurement_telegraf
    WHERE (
        time > (now() - 100s)

    )
)

INFO:db_adapter.py:query:21:Got 1 points
INFO:db_adapter.py:query:15:Executing query:

SELECT DISTINCT(kpi) as selector
FROM (
    SELECT *
    FROM anomaly_measurement_telegraf
    WHERE (
        time > (now() - 100s)

    )
)

INFO:db_adapter.py:query:21:Got 1 points
INFO:anomaly_detection_main.py:anomaly_detection:68:There are 1 unique combinations of selectors.
INFO:anomaly_detection_main.py:anomaly_detection:71:Analyzing the selector group: {'host': 'host01', 'service': 'service01', 'kpi': 'disk_util'}
INFO:db_adapter.py:query:15:Executing query:

SELECT value as value
FROM anomaly_measurement_telegraf
WHERE (
    time > (now() - 4w)
    AND host = 'host01' AND service = 'service01' AND kpi = 'disk_util'

)

INFO:db_adapter.py:query:21:Got 1 points
INFO:anomaly_detection_main.py:anomaly_detection:73:Computed training data:
{('Sunday', 8): {'warning': 0.1089461827284105, 'anomaly': 0.14387984981226534}, ('Sunday', 9): {'warning': 0.16010012515644556, 'anomaly': 0.21819274092615767}, ('Sunday', 10): {'warning': 0.19846808510638297, 'anomaly': 0.26138673341677093}, ('Sunday', 11): {'warning': 0.28001802252816027, 'anomaly': 0.3178423028785982}, ('Sunday', 12): {'warning': 0.1853376720901127, 'anomaly': 0.2444545682102627}, ('Tuesday', 8): {'warning': 0.16190237797246557, 'anomaly': 0.22798498122653316}, ('Tuesday', 9): {'warning': 0.22798498122653316, 'anomaly': 0.28047058823529414}}
INFO:db_adapter.py:query:15:Executing query:

SELECT value as value
FROM anomaly_measurement_telegraf
WHERE (
    time > (now() - 100s)
    AND host = 'host01' AND service = 'service01' AND kpi = 'disk_util'

)

INFO:db_adapter.py:query:21:Got 1 points
INFO:anomaly_detection_main.py:anomaly_detection:76:Classifying the data
INFO:anomaly_detection_main.py:anomaly_detection:92:An example of the classified data is:
{'measurement': 'anomaly_measurement_telegraf_ml', 'time': '2021-09-07T08:13:42.372610Z', 'fields': {'warning': 0, 'anomaly': 0, 'value': -0.0, 'warn_threshould': 0.16190237797246557, 'anom_threshold': 0.22798498122653316}, 'tags': {'host': 'host01', 'service': 'service01', 'kpi': 'disk_util'}}
INFO:anomaly_detection_main.py:anomaly_detection:109:Writing the classified data to the db `test_db`
INFO:anomaly_detection_main.py:anomaly_detection:117:Success, wrote the data to the db `test_db`
```
This will write data in the format:
```json
{
    "measurement": "anomaly_measurement_telegraf_ml", 
    "time": "2021-09-07T08:13:42.372610Z",
    "tags": {
        "host": "host01", 
        "service": "service01", 
        "kpi": "disk_util"
    },
    "fields": {
        "warning": 0, 
        "anomaly": 0, 
        "value": -0.0, 
        "warn_threshould": 0.16190237797246557, 
        "anom_threshold": 0.22798498122653316
    }
}
```