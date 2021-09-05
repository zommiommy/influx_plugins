from .logger import logger
import itertools
import numpy as np
import pandas as pd
from influxdb import InfluxDBClient

class DBAdapter:
    def __init__(self, db_settings, db_schema):
        self.settings = db_settings
        self.db_schema = db_schema
        logger.info("Conneting to the DB on [{host}:{port}] for the database [{database}]".format(**self.settings))
        self.client = InfluxDBClient(**self.settings)

    def query(self, query, *args, **kwargs):
        logger.info("Executing query:\n%s", query)
        result = self.client.query(
            query,
            *args,
            **kwargs
        )
        logger.info("Got %s points", len(result))
        return result

    def get_selectors_combinations(self, query_settings):
        """Takes the list of selectors and """
        if query_settings["filter"] != "":
            query_settings["extra_filter"] = "AND " + query_settings["filter"]
        else:
            query_settings["extra_filter"] = ""

        return [ dict(x) for x in (itertools.product(*[
            [
                (selector, x["selector"])
                for x in self.query(
"""
SELECT DISTINCT({selector}) as selector
FROM (
    SELECT *
    FROM {input_measurement}
    WHERE (
        time > (now() - {window})
        {extra_filter}
    )
)
""".format(selector=selector, **query_settings)                
                ).get_points()
            ]
            for selector in query_settings["selectors"].split(",")
        ]))]


    def get_anomaly_data(self, selector_values, query_settings):
        """Get the data and compute the warning and anomaly quantiles
        for each hour of each day of the week."""
        selector_filters = "".join(
            "AND {} = '{}' ".format(k, v)
            for k, v in selector_values.items()
        )
        return self.query(
"""
SELECT {field} as value
FROM {input_measurement}
WHERE (
    time > (now() - {window})
    {selector_filters}
    {extra_filter}
)
""".format(selector_filters=selector_filters, **query_settings)                
            ).get_points()

    def get_training_data(self, selector_values, query_settings):
        """Get the data and compute the warning and anomaly quantiles
        for each hour of each day of the week."""
        selector_filters = "".join(
            "AND {} = '{}' ".format(k, v)
            for k, v in selector_values.items()
        )
        points = self.query(
"""
SELECT {field} as value
FROM {input_measurement}
WHERE (
    time > (now() - {training_timeframe})
    {selector_filters}
    {extra_filter}
)
""".format(selector_filters=selector_filters, **query_settings)                
                )
        if len(points) == 0:
            return {}
                
        df = pd.DataFrame([
            (x["time"], x["value"])
            for x in points.get_points()
        ], columns=["time", "value"])

        df = df.set_index("time")
        df.index = pd.DatetimeIndex(df.index)
        t = df.groupby(lambda x: (x.day_name(), x.hour)).quantile([
            query_settings["warning"], 
            query_settings["anomaly"], 
        ])
        t = t.stack().unstack(1).droplevel(1)
        t.columns = ["warning", "anomaly"]
        return {
            key: {
                "warning":warning,
                "anomaly":anomaly,
            }
            for key, warning, anomaly in t.itertuples()
        }


    def get_check_time_data(self, query_settings):
        """Take the settings ad depending on which schema the db is, retrieve
        the data with the appropriate query."""
        if query_settings["filter"] != "":
            query_settings["extra_filter"] = "AND " + query_settings["filter"]
        else:
            query_settings["extra_filter"] = ""

        if self.db_schema == "icinga" and query_settings.get("max_column") is not None:
            return self.client.query(
"""
SELECT time, {target_column} as value, {max_column} as max
FROM "{measurement}"
WHERE (
    time > (now() - {window})
    {extra_filter}
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
    {extra_filter}
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
    {kpi_column} = '{target_kpi}'
    {extra_filter}
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
    {kpi_column} = '{target_kpi}'
    {extra_filter}
)
""".format(**query_settings)
            )
        else:
            raise ValueError("Cannot handle query for schema %s with settings: %s"%(self.db_schema, query_settings))


    def __del__(self):
        """On exit / delation close the client connetion"""
        if "client" in dir(self):
            self.client.close()
