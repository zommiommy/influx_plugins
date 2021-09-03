from .logger import logger
from influxdb import InfluxDBClient

class DBAdapter:
    def __init__(self, db_settings, db_schema):
        self.settings = db_settings
        self.db_schema = db_schema
        logger.info("Conneting to the DB on [{host}:{port}] for the database [{database}]".format(**self.settings))
        self.client = InfluxDBClient(**self.settings)


    def get(self, query_settings):
        if self.db_schema == "icinga" and query_settings.get("max_column") is not None:
            return self.client.query(
"""
SELECT time, {target_column} as value, {max_column} as max
FROM "{measurement}"
WHERE (
    time > (now() - {window})
    AND
    {host_column} = '{host}'
    AND 
    {service_column} = '{service}'
)
""".format(**query_settings)
            )
        elif self.db_schema == "icinga" and query_settings.get("max_column") is None:
            return self.client.query(
"""
SELECT time, {target_column} as value
FROM "{measurement}"
WHERE (
    time > (now() - {window})
    AND
    {host_column} = '{host}'
    AND 
    {service_column} = '{service}'
)
""".format(**query_settings)
            )
        elif self.db_schema == "telegraf" and query_settings.get("max_column") is None:
            return self.client.query(
"""
SELECT time, {value_column} as value
FROM "{measurement}"
WHERE (
    time > (now() - {window})
    AND
    {host_column} = '{host}'
    AND 
    {service_column} = '{service}'
    AND
    {kpi_column} = '{target_kpi}'
)
""".format(**query_settings)
            )
        elif self.db_schema == "telegraf" and query_settings.get("max_column") is not None:
            return self.client.query(
"""
SELECT time, {value_column} as value, {max_column} as max
FROM "{measurement}"
WHERE (
    time > (now() - {window})
    AND
    {host_column} = '{host}'
    AND 
    {service_column} = '{service}'
    AND 
    {kpi_column} = '{target_kpi}'
)
""".format(**query_settings)
            )
        else:
            raise ValueError("Cannot handle query for schema %s with settings: %s"%(self.db_schema, query_settings))


    def __del__(self):
        """On exit / delation close the client connetion"""
        if "client" in dir(self):
            self.client.close()
