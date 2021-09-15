import numpy as np
from ..utils import parse_time_to_epoch

def normalize_data(data, value_type, max_value):
    """This methods expects data in the format:
    [{'time':'2021-09-03T09:54:38.890352Z', 'value': 1.9, 'max': 2}]

    where time could be either an iso date, a timestamp (both int or str),
    and max is optional.

    It returns two np arrays, the first one is the time in seconds while the 
    second is the value normalized between 0 and 1.
    """

    time = []
    values = []

    # Dispatch how the value should be normalized
    normalizer = {
        "usage":            lambda v, max: v / float(max),
        "usage_percentile": lambda v, max: v / 100,
        "usage_quantile":   lambda v, max: v,
        "free":             lambda v, max: 1 - (v / float(max)),
        "free_percentile":  lambda v, max: 1 - (v / 100),
        "free_quantile":    lambda v, max: 1 - v,
    }[value_type]


    # Dispatch the points into arrays once they are normalized
    for point in data:
        time.append(parse_time_to_epoch(point["time"]))
        values.append(normalizer(float(point["value"]), point.get("max") or max_value))

    # Conver the values to np arrays, this conversion is needed because appending
    # To a np array is not efficient nor easy
    time = np.array(time)
    values = np.array(values)

    # normalize data by removing the minimum to get better numerical stability
    # this doesn't change the predicted values
    time -= time.min()

    return (time, values)

