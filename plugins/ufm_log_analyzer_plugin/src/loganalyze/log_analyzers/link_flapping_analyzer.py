#
# Copyright © 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#
from datetime import datetime
import gzip
from itertools import islice
import os
import re
import shutil
from typing import List
from loganalyze.log_analyzers.base_analyzer import BaseImageCreator
import loganalyze.logger as log
from utils.netfix.link_flapping import get_link_flapping
FILE_NAME_PATTERN=r"^secondary_(5m|1h|1d|1w)_(\d{14})\.gz$"
TIME_PATTERN="%Y%m%d%H%M%S"

class LinkFlappingAnalyzer(BaseImageCreator):
    def __init__(self, telemetry_samples_csv:List[str], dest_image_path:str):
        super().__init__(dest_image_path)
        self._telemetry_samples_csv = telemetry_samples_csv
        self._mapped_samples = {"5m":{}, "1h":{}, "1d":{}, "1w":{}}
        self.map_files_by_sampling_rate_and_date()

    def map_files_by_sampling_rate_and_date(self):
        for sample_file in self._telemetry_samples_csv:
            try:
                file_name = os.path.basename(sample_file)
                match = re.match(FILE_NAME_PATTERN, file_name)
                if match:
                    interval_time = match.group(1)
                    date_time_str = match.group(2)
    
                    # Convert the date_time string to a datetime object
                    date_time = datetime.strptime(date_time_str, TIME_PATTERN)
                    self._mapped_samples[interval_time][date_time] = sample_file
                else:
                    log.LOGGER.debug(f"File {file_name} cannot be used for links flapping")
            except Exception as e:
                log.LOGGER.debug(f"Error while working file {file_name} for links flapping")
        #Sorting the inner dict so the first item would be the last timestamp
        sorted_data = {key: sorted(value.items(), key=lambda x: x[0], reverse=True) for key, value in self._mapped_samples.items()}
        self._mapped_samples = {key: dict(value) for key, value in sorted_data.items()}

    def ungz_to_csv(self, file_path):
        # Ensure the input file has a .gz extension
        if not file_path.endswith('.gz'):
            print(f"Error: {file_path} is not a .gz file.")
            return ""

        # Create the output file path by replacing .gz with .csv
        output_file_path = file_path[:-3] + '.csv'

        # Open the .gz file and write its content to a new .csv file
        with gzip.open(file_path, 'rb') as f_in:
            with open(output_file_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        return output_file_path

    def get_link_flapping_per_interval(self, interval='1d'):
        telemetry_sample_files = self._mapped_samples.get(interval)
        if len(telemetry_sample_files) < 2:
            log.LOGGER.warn(f"Can't run link flapping logic for {interval}, not enoght samples")
            return
        print(f"ALLLLL {telemetry_sample_files}")
        first_two_items = list(islice(telemetry_sample_files.items(), 2))
        t1, latest_sample_gz = first_two_items[0]
        t2, older_sample_gz = first_two_items[1]
        print(f"BOAZ TIME {t1} vs {t2}")
        # Now that we know which files to use, un gz them
        link_flapping = get_link_flapping(self.ungz_to_csv(older_sample_gz), self.ungz_to_csv(latest_sample_gz))
        columns_to_keep =['link_hash_id', 'estimated_time']
        link_flapping = link_flapping.loc[:, columns_to_keep]
        # Drop duplicate columns
        link_flapping = link_flapping.loc[:, ~link_flapping.columns.duplicated()]
        # Reset the index and drop the old index column
        link_flapping = link_flapping.reset_index(drop=True)

        print(link_flapping)
    def full_analysis(self):
        self.get_link_flapping_per_interval()
        return super().full_analysis()
