import urllib
import pandas as pd
from data_store import DataStore

class TelemetryCollector:
    """
    Represent Telemetry collector which send DataFrame once telemetry is called.
    Calls data store class for save the abs or delta data.
    """
    BASED_COLUMNS = ["Node_GUID", "port_guid", "Port_Number"]
    KEY = BASED_COLUMNS + ["timestamp","tag"]
    SECONDARY_TELEMETRY_PORT = 9002
    SECONDARY_INSTANCE = "low_freq_debug"

    def __init__(self,test_mode:bool,logger,data_store:DataStore) -> None:
        self.test_mode = test_mode
        self.logger = logger
        self.previous_telemetry_data = None
        self.data_store = data_store

    def get_telemetry(self):
        """
        get the telemetry from secondary telemetry, if it in test mode it get from the simulation
        return DataFrame of the telemetry
        """
        # get telemetry data
        if self.test_mode:
            url = "http://127.0.0.1:9090/csv/xcset/simulated_telemetry"
        else:
            url = f"http://127.0.0.1:{self.SECONDARY_TELEMETRY_PORT}/csv/xcset/{self.SECONDARY_INSTANCE}"
        try:
            self.logger.info(f"Collecting telemetry from {url}.")
            telemetry_data = pd.read_csv(url)
        except (pd.errors.ParserError, pd.errors.EmptyDataError, urllib.error.URLError) as connection_error:
            self.logger.error("Failed to get telemetry data from UFM, fetched url=%s. Error: %s",url,connection_error)
            telemetry_data = None

        # store telemetry data
        self.store_telemetry_data(telemetry_data)

        # return retrieved data
        return telemetry_data

    def store_telemetry_data(self, telemetry_data):
        """
        Store telemetry data into the file
        """
        try:
            if self.previous_telemetry_data is not None and telemetry_data is not None:
                delta = self._get_delta(self.previous_telemetry_data,telemetry_data)
                # when we want to keep only delta
                if len(delta) > 0:
                    self.data_store.save(delta,self.data_store.get_filename_delta())
            elif telemetry_data is not None:
                # when we want to keep the abs
                self.data_store.save(telemetry_data,self.data_store.get_filename_abs())
        except Exception as exception_error: # pylint: disable=broad-exception-caught
            self.logger.error(f"Failed to store telemetry data with error {exception_error}")

        # keep telemetry data for next delta calculation
        if telemetry_data is not None:
            self.previous_telemetry_data = telemetry_data

    def _get_delta(self, first_df: pd.DataFrame, second_df:pd.DataFrame):
        merged_df = pd.merge(second_df, first_df, on=self.BASED_COLUMNS, how='inner', suffixes=('', '_x'))
        delta_dataframe = pd.DataFrame()
        for _,col in enumerate(second_df.columns):
            col_x = col + "_x"
            if col not in self.KEY \
                    and merged_df[col].dtype != 'object' \
                    and merged_df[col_x].dtype != 'object':
                try:
                    delta_dataframe[col] = merged_df[col] - merged_df[col_x]
                except TypeError:
                    delta_dataframe[col] = second_df[col]
            else:
                delta_dataframe[col] = second_df[col]
        return delta_dataframe
