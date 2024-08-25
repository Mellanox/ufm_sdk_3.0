import pandas as pd
import urllib.error
import logging
from constants import PDRConstants

class TelemetryCollector:
    """
    collecting data for the algorithm
    """
    def __init__(self,test_mode:bool) -> None:
        self.test_mode = test_mode

    def get_telemetry(self):
        """
        get the telemetry from secondary telemetry, if it in test mode it get from the simulation
        return DataFrame of the telemetry
        """
        if self.test_mode:
            url = f"http://127.0.0.1:9090/csv/xcset/simulated_telemetry"
        else:
            url = f"http://127.0.0.1:{PDRConstants.SECONDARY_TELEMETRY_PORT}/csv/xcset/{PDRConstants.SECONDARY_INSTANCE}"
        try:
            telemetry_data = pd.read_csv(url)
        except (pd.errors.ParserError, pd.errors.EmptyDataError, urllib.error.URLError) as e:
            logging.error(f"Failed to get telemetry data from UFM, fetched url={url}. Error: {e}")
            telemetry_data = None
        return telemetry_data
