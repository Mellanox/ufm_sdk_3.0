import logging
import urllib
import pandas as pd
from constants import PDRConstants as Constants

class TelemetryCollector:
    """
    Represent Telemetry collector which send DataFrame once telemetry is called.
    """
    def __init__(self,test_mode) -> None:
        self.test_mode=test_mode

    def get_telemetry(self):
        """
        get the telemetry from secondary telemetry, if it in test mode it get from the simulation
        return DataFrame of the telemetry
        """
        if self.test_mode:
            url = "http://127.0.0.1:9090/csv/xcset/simulated_telemetry"
        else:
            url = f"http://127.0.0.1:{Constants.SECONDARY_TELEMETRY_PORT}/csv/xcset/{Constants.SECONDARY_INSTANCE}"
        try:
            telemetry_data = pd.read_csv(url)
        except (pd.errors.ParserError, pd.errors.EmptyDataError, urllib.error.URLError) as exception_error:
            logging.error("Failed to get telemetry data from UFM, fetched url= %s. Error: %s",url,exception_error)
            telemetry_data = None
        return telemetry_data
