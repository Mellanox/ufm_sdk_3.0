from os.path import join,exists
from os import remove,makedirs
from pathlib import Path
from datetime import datetime
import pandas as pd

class DataStore:
    """
    arrange the data store of the telemetries that we save, abs or delta. remove old data when want.
    """
    OUTPUT_FILE_FORMAT = "%Y_%m_%d_%H_%M_%S.csv"
    AMOUNT_FILES_TO_KEEP = 10
    BASE_PATH = "/opt/ufm/ufm_plugin_pdr_deterministic/datastore"
    ABS_PATH = "abs"
    DELTA_PATH = "delta"
    TAR_SUFFIX = "*.csv"

    def __init__(self,logger) -> None:
        self.logger = logger
        if not exists(self.BASE_PATH):
            makedirs(self._folder_abs())
            makedirs(self._folder_delta())

    def _folder_abs(self) -> str:
        return join(self.BASE_PATH,self.ABS_PATH)

    def _folder_delta(self) -> str:
        return join(self.BASE_PATH,self.DELTA_PATH)

    def _get_filename(self) -> str:
        return datetime.now().strftime(self.OUTPUT_FILE_FORMAT)

    def get_filename_abs(self) -> str:
        """
        return a filename for abs data
        """
        return join(self._folder_abs(),self._get_filename())

    def get_filename_delta(self) -> str:
        """
        return a filename for delta data
        """
        return join(self._folder_delta(),self._get_filename())

    def _get_files_to_remove(self, data_path:str, suffix:str, to_keep:int) -> list:
        """
        find the file names of the oldest which is after the amount of to_keep
        search for in the data_path with the suffix.
        """
        files_to_remove = []
        input_path_dir = Path(data_path)
        files = list(input_path_dir.glob(suffix))
        files.sort(key=lambda p: p.name)
        files = [str(p) for p in files]
        if len(files) > to_keep:
            files_to_remove = files[:len(files)- to_keep]
        return files_to_remove

    def clean_old_files(self) -> None:
        """
        search for the both locations to clean the old files.
        """
        for data_path in [self._folder_abs(),self._folder_delta()]:
            files = self._get_files_to_remove(data_path,self.TAR_SUFFIX,self.AMOUNT_FILES_TO_KEEP)
            if len(files) > 0:
                self._remove_files(files)

    def _remove_files(self, files: list) -> None:
        """
        Delete a list of files
        :param files: (List) List of files to be removed
        :return: None
        """
        self.logger.info(f"Removing {len(files)} old files")
        for file in files:
            try:
                if exists(file):
                    remove(file)
            except FileNotFoundError:
                pass
            except OSError as exc:
                self.logger.error("Failed to remove file %s [%s]", file, exc)

    def save(self, dataframe:pd.DataFrame, file_name:str) -> None:
        """
        save dataframe to the file name
        """
        self.logger.info(f"Saving data to {file_name}")
        dataframe.to_csv(file_name)
