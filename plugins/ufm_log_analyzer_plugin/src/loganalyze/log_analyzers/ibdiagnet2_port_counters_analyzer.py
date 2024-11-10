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

from typing import List

import pandas as pd
from loganalyze.log_analyzers.base_analyzer import BaseAnalyzer
import loganalyze.logger as log

class Ibdiagnet2PortCountersAnalyzer(BaseAnalyzer):
    def __init__(self, logs_csvs: List[str], hours: int, dest_image_path: str, sort_timestamp=False):
        super().__init__(logs_csvs, hours, dest_image_path, sort_timestamp)

        # This will make all the extra colum are int
        # Convert the 'extra' columns to integers if possible
        extra_columns = ['extra1', 'extra2', 'extra3', 'extra4', 'extra5']

        for col in extra_columns:
            self._log_data_sorted[col] = pd.to_numeric(
            self._log_data_sorted[col],
            errors='coerce'
            ).astype('Int64') 

        # self._log_data_sorted['extra'] = (
        # self._log_data_sorted['extra']
        # .fillna(0)  # Replace NaN with 0
        # .astype(int)  # Convert to integer
        # )

    def get_collectx_versions(self):
            unique_collectx_versions = self._log_data_sorted[self._log_data_sorted['type'] == 'collectx_version']['data'].unique()
            return unique_collectx_versions


    def get_number_of_switches_and_ports(self):
        """
        Generate summary statistics for 'total_devices_ports' data.
        This function calculates the average, maximum, minimum, and non-zero counts
        for switches, CAs, routers, and ports.
        """
        # Step 1: Filter data for 'total_devices_ports'
        filtered_data = self._log_data_sorted[self._log_data_sorted['type'] == 'total_devices_ports']

        # Step 2: Create a combined column for 'extra1', 'extra3', and 'extra5'
        combined_columns = ['extra1', 'extra3', 'extra5']
        filtered_data['extra135'] = pd.to_numeric(
            filtered_data[combined_columns].stack(), errors='coerce'
        ).groupby(level=0).sum(min_count=1)

        # Define columns of interest and their mapping to meaningful names
        columns_of_interest = ['data', 'extra2', 'extra4', 'extra135']
        column_mapping = {
            'data': 'Number of Switches',
            'extra2': 'CAs',
            'extra4': 'Routers',
            'extra135': 'Ports'
        }

        # Step 3: Initialize a list to store the summary statistics
        summary_stats = []

        # Step 4: Calculate statistics for each column
        for col in columns_of_interest:
            numeric_col = pd.to_numeric(filtered_data[col], errors='coerce')
            non_zero_col = numeric_col[numeric_col != 0]

            # Determine stats, defaulting to 0 if the column has no non-zero values
            avg = int(round(non_zero_col.mean())) if not non_zero_col.empty else 0
            max_val = int(non_zero_col.max()) if not non_zero_col.empty else 0
            min_val = int(non_zero_col.min()) if not non_zero_col.empty else 0
            count = int(non_zero_col.count())

            summary_stats.append({
                'Category': column_mapping.get(col, col),
                'Average': avg,
                'Maximum': max_val,
                'Minimum': min_val,
                'Total Rows (Non-Zero)': count
            })

        # Step 5: Convert the summary stats list into a DataFrame
        summary_df = pd.DataFrame(summary_stats)
        
        return summary_df
