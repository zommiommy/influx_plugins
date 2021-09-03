from ..utils import logger
import numpy as np
from sklearn.linear_model import BayesianRidge

def predict_time_left(x: np.array, y: np.array, debug_plot) -> (float, float):
    """Given the timestamps (in seconds) as a numpy array `x`
    and the values as numpy array `y` (normalied between 0 and 1), 
    do a linear regression and return in how much time (in seconds)
    the values will reach the 1 and the score on how sure the model is.
    This score is based on the R^2 coefficient and takes values
    between 0 and 1. 

    `debug_plot` is by default None, if passed it should be the path for
    the debug image to plot the data. E.g. `debug.png`.
    """
    # The regressor accepts only 2D arrays
    x = x.reshape(-1, 1)
    # Create the regressor
    reg = BayesianRidge()
    # Fit the regressor on the data
    reg.fit(x, y)

    # Extract the coefficients of the linear regression
    m, q = reg.coef_[0], reg.intercept_
    # Compute how sure the regressor is that the data
    # fits the infered model, this is the R^2 coefficient
    # So it has max 1.0, a constant predictor will have
    # R^2 coefficient equal to 0.0 and the model can get
    # arbitrarly worse, for this reason we only keep
    # positive scores.
    score = max(reg.score(x, y), 0)

    logger.info(
        ("The coefficents predicted are m:'{m}' q:'{q}'"
        " with score:'{score}'")
        .format(**locals())
    )

    if m <= 0:
        logger.info(
            "The predicted line is not growing so it will "
            "never reach the max"
        )
        # Save a debug image that can be used for debugging propouses
        if debug_plot is not None:
            # The import is here so that if this feature is not needed, you don't
            # have to install matplotlib
            import matplotlib.pyplot as plt

            plt.figure(figsize=(10, 5), dpi=150)
            ax = plt.subplot(111)

            ax.plot(x, y, label="data")
            ax.plot(x, reg.predict(x), label="fitting")

            ax.set_ylim(-0.1, 1.1)
            ax.set_xlabel("Seconds (from first point of the query)")
            ax.set_ylabel("Values normalized between 0 and 1")

            ax.legend(bbox_to_anchor=(0.5, 1), loc='lower center',
                ncol=3, fancybox=True, shadow=True
            )
            plt.savefig(debug_plot)
        return float("inf"), score

    # Given the current fitted line, compute the interception
    # with the max
    # \delta T = (max - q) / m 
    time_predicted = (1 - q)/m

    # Compute the delta from the predicted value
    # and the last measurement
    time_left = time_predicted - x[-1, 0]

    logger.info("The predicted time left is %s seconds with a score of %s%%", time_left, score * 100)


    # Save a debug image that can be used for debugging propouses
    if debug_plot is not None:
        # The import is here so that if this feature is not needed, you don't
        # have to install matplotlib
        import matplotlib.pyplot as plt

        plt.figure(figsize=(10, 5), dpi=150)
        ax = plt.subplot(111)
        ax.plot(
            [time_predicted, time_predicted],
            [-1, 1],
            "--",
            color="black",
            alpha=0.5,
        )
        ax.plot(
            [-1, time_predicted],
            [1, 1],
            "--",
            color="black",
            alpha=0.5,
        )

        ax.plot(x, y, label="data")
        ax.plot(x, reg.predict(x), label="fitting")

        ax.plot(
            [x[-1], time_predicted],
            [
                reg.predict(np.array(x[-1]).reshape(-1, 1)), 
                reg.predict(np.array(time_predicted).reshape(-1, 1))
            ],
            "--", 
            label="prediction"
        )

        ax.set_ylim(-0.1, 1.1)
        ax.set_xlabel("Seconds (from first point of the query) the predicted time is %s"%time_predicted)
        ax.set_ylabel("Values normalized between 0 and 1")

        ax.legend(bbox_to_anchor=(0.5, 1), loc='lower center',
            ncol=3, fancybox=True, shadow=True
        )
        plt.savefig(debug_plot)

    return time_left, score