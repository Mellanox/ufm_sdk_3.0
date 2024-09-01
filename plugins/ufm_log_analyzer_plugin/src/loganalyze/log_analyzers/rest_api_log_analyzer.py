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
from urllib.parse import urlparse
import pandas as pd
import numpy as np
from loganalyze.log_analyzers.base_analyzer import BaseAnalyzer

class RestApiAnalyzer(BaseAnalyzer):

    def __init__(self, logs_csvs: List[str], hours: int, dest_image_path: str, sort_timestamp=True):
        super().__init__(logs_csvs, hours, dest_image_path, sort_timestamp)
        #Removing all the request coming from the ufm itself
        self._log_data_sorted = self._log_data_sorted.loc\
            [self._log_data_sorted['user'] != 'ufmsystem']
        #Splitting the URL for better analysis
        self._log_data_sorted[['uri', 'query_params']] = self._log_data_sorted['url']\
            .apply(self.split_url_to_uri_and_query_params).apply(pd.Series)
        self._have_duration = self._have_data_in_column('duration')
        self._have_user = self._have_data_in_column('user')
        self._funcs_for_analysis = {self.analyze_endpoints_freq}

    @staticmethod
    def split_url_to_uri_and_query_params(url):
        """
        Parse the URL into its components
        """
        if url:
            parsed_url = urlparse(url)
            base_uri = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path
            query_params = parsed_url.query if parsed_url.query else np.nan
            return base_uri, query_params
        return np.nan, np.nan

    def _have_data_in_column(self, column):
        """
        Returns True/False if the column has any data.
        This needed since old versions of UFM do not have this data
        and will result in less analysis.
        """
        return self._log_data_sorted[column].notna().all()

    def analyze_endpoints_freq(self, endpoints_count_to_show=10):
        by_uri_per_time = self._log_data_sorted.groupby(['uri',
                                                         'aggregated_by_time']).size().reset_index(
                                                             name='amount_per_uri')
        total_amount_per_uri = by_uri_per_time.groupby('uri')['amount_per_uri'].sum()
        top_x_uris = total_amount_per_uri.nlargest(endpoints_count_to_show).index
        data_to_show = by_uri_per_time.pivot(index='aggregated_by_time',
                                             columns='uri',
                                             values='amount_per_uri').fillna(0)
        data_to_show = data_to_show[top_x_uris]

        self._plot_and_save_pivot_data_in_bars(data_to_show,
                                                      "time",
                                                      "requests count",
                                                      f"Top {endpoints_count_to_show} "\
                                                        "requests count over time",
                                                      "legend")
