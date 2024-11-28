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
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-module-docstring


from plugins.ufm_log_analyzer_plugin.src.loganalyze.log_analyzers.ibdiagnet_log_analyzer\
    import IBDIAGNETLogAnalyzer


class UFMTopAnalyzer:
    def __init__(self):
        self._analyzers = []

    def add_analyzer(self, analyzer):
        self._analyzers.append(analyzer)

    def full_analysis_all_analyzers(self):
        """
        Returns a list of all the graphs created and their title
        """
        graphs_and_titles = []
        dataframes = []
        lists_to_add = []
        for analyzer in self._analyzers:
            tmp_images_list, tmp_dataframes, tmp_lists = analyzer.full_analysis()
            graphs_and_titles.extend(tmp_images_list)
            dataframes.extend(tmp_dataframes)
            lists_to_add.extend(tmp_lists)

        has_ibdiagnet_analyzer = any(isinstance(instance, IBDIAGNETLogAnalyzer) \
                                     for instance in self._analyzers)
        if not has_ibdiagnet_analyzer:
            dataframes.append(("Fabric info", ("No Fabric Info found")))

        return graphs_and_titles, dataframes, lists_to_add
