#!/usr/bin/python3

"""
@copyright:
    Copyright (C) Mellanox Technologies Ltd. 2014-2020.  ALL RIGHTS RESERVED.

    This software product is a proprietary product of Mellanox Technologies
    Ltd. (the "Company") and all right, title, and interest in and to the
    software product, including all associated intellectual property rights,
    are and shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Anan Al-Aghbar
@date:   Sep 27, 2021
"""

import os
import time
import logging
from tempfile import NamedTemporaryFile
try:
    from utils.utils import Utils
    from utils.ufm_rest_client import UfmRestClient, HTTPMethods
    from utils.args_parser import ArgsParser
    from utils.config_parser import ConfigParser
    from utils.logger import Logger, LOG_LEVELS
except ModuleNotFoundError as e:
    print("Error occurred while importing python modules, "
          "Please make sure that you exported your repository to PYTHONPATH by running: "
          f'export PYTHONPATH="${{PYTHONPATH}}:{os.path.dirname(os.getcwd())}"')


class UfmTopologyConfigParser(ConfigParser):

    config_file = "ufm_topology.cfg"

    UFM_TOPOLOGY_SECTION = "ufm-topology"
    UFM_TOPOLOGY_SECTION_STORED_DATA_PATH = "path_to_export"
    UFM_TOPOLOGY_SECTION_GEPHI_FILE_NAME = "gephi_file_name"
    UFM_TOPOLOGY_SECTION_TOPO_FILE_NAME = "topo_file_name"
    UFM_TOPOLOGY_SECTION_EXPORT_TO_GEXF = "export_to_gephi"
    UFM_TOPOLOGY_SECTION_EXPORT_AS_TOPO = "export_as_topo"

    UFM_TOPOLOGY_COMPARE_SECTION = 'ufm-topology-compare'
    UFM_TOPOLOGY_COMPARE_SECTION_COMPARE_TOPOLOGY_WITH = "compare_topology_with"
    UFM_TOPOLOGY_COMPARE_SECTION_EXPORT_COMPARE_TO_GEPHI= "export_compare_topology_to_gephi"

    def __init__(self, args):
        super().__init__(args)
        self.sdk_config.read(self.config_file)

    def get_path_to_export(self):
        return self.get_config_value(self.args.path_to_export,
                                     self.UFM_TOPOLOGY_SECTION,
                                     self.UFM_TOPOLOGY_SECTION_STORED_DATA_PATH,
                                     'api_results')

    def get_gephi_file_name(self):
        return self.get_config_value(self.args.gephi_file_name,
                                     self.UFM_TOPOLOGY_SECTION,
                                     self.UFM_TOPOLOGY_SECTION_GEPHI_FILE_NAME,
                                     f'{Utils.get_timebased_filename()}_topology.gexf')

    def get_topo_file_name(self):
        return self.get_config_value(self.args.topo_file_name,
                                     self.UFM_TOPOLOGY_SECTION,
                                     self.UFM_TOPOLOGY_SECTION_TOPO_FILE_NAME,
                                     f'{Utils.get_timebased_filename()}.topo')

    def get_export_to_gephi(self):
        return self.safe_get_bool(self.args.export_to_gephi,
                                  self.UFM_TOPOLOGY_SECTION,
                                  self.UFM_TOPOLOGY_SECTION_EXPORT_TO_GEXF,
                                  False)

    def get_export_as_topo(self):
        return self.safe_get_bool(self.args.export_as_topo,
                                  self.UFM_TOPOLOGY_SECTION,
                                  self.UFM_TOPOLOGY_SECTION_EXPORT_AS_TOPO,
                                  False)

    def get_compare_topo_with(self):
        return self.get_config_value(self.args.compare_topology_with,
                                     self.UFM_TOPOLOGY_COMPARE_SECTION,
                                     self.UFM_TOPOLOGY_COMPARE_SECTION_COMPARE_TOPOLOGY_WITH,
                                     "")

    def get_export_topology_compare_to_gephi(self):
        return self.safe_get_bool(self.args.export_compare_topology_to_gephi,
                                  self.UFM_TOPOLOGY_COMPARE_SECTION,
                                  self.UFM_TOPOLOGY_COMPARE_SECTION_EXPORT_COMPARE_TO_GEPHI,
                                  False)


class UfmTopologyConstants(object):
    NODE_GUID = "guid"
    NODE_NAME = "system_name"
    NODE_IP = "ip"
    NODE_SEVERITY = "severity"
    NODE_TYPE = "type"

    NODE_ATTR_ID = "id"
    NODE_ATTR_TITLE = "title"
    NODE_ATTR_TYPE = "type"

    NODES_ATTRIBUTES = [
        {
            NODE_ATTR_ID: NODE_NAME,
            NODE_ATTR_TITLE: "Name",
            NODE_ATTR_TYPE: "string"
        },
        {
            NODE_ATTR_ID: NODE_SEVERITY,
            NODE_ATTR_TITLE: "Severity",
            NODE_ATTR_TYPE: "string"
        },
        {
            NODE_ATTR_ID: NODE_GUID,
            NODE_ATTR_TITLE: "GUID",
            NODE_ATTR_TYPE: "string"
        },
        {
            NODE_ATTR_ID: NODE_IP,
            NODE_ATTR_TITLE: "IP",
            NODE_ATTR_TYPE: "string"
        },
        {
            NODE_ATTR_ID: NODE_TYPE,
            NODE_ATTR_TITLE: "Type",
            NODE_ATTR_TYPE: "string"
        }
    ]

    LINK_SOURCE_GUID = "source_guid"
    LINK_DEST_GUID = "destination_guid"
    LINK_NAME = "name"

    UNAFFECTED_NODE_COLOR = {
        "R": 118,
        "G": 185,
        "B": 0,
        "A": 1
    }

    ADDED_NODE_COLOR = {
        "R": 77,
        "G": 137,
        "B": 189,
        "A": 1
    }

    DELETED_NODE_COLOR = {
        "R": 150,
        "G": 150,
        "B": 150,
        "A": 1
    }

    args_list = [
        {
            "name": "--export_to_gephi",
            "help": "Option to export the topology as gexf file",
            "no_value": True
        }, {
            "name": "--export_as_topo",
            "help": "Option to export the topology as topo file",
            "no_value": True
        }, {
            "name": "--path_to_export",
            "help": "Option to specify where the exported files will be stored [Default = 'api_results']"
        }, {
            "name": "--gephi_file_name",
            "help": "Option to specify the name of the exported Gephi file [Default = 'gephi.gexf']"
        }, {
            "name": "--topo_file_name",
            "help": "Option to specify the name of the exported topo file [Default = 'topology.gexf']"
        }, {
            "name": "--compare_topology_with",
            "help": "The path of the external topo file to compare it with the current topology"
        }, {
            "name": "--export_compare_topology_to_gephi",
            "help": "Option to export the result of the topology compare as gexf file",
            "no_value": True
        }
    ]


class UfmTopologyGephiExporter(object):

    def __init__(self):
        self.fo = None

    def _write_node_attributes(self):
        self.fo.write('''
\t\t<attributes class="node" mode="static">
''')
        for attr in UfmTopologyConstants.NODES_ATTRIBUTES:
            self.fo.write('\t\t\t<attribute id="{0}" title="{1}" type="{2}"/>\n'
                          .format(attr.get(UfmTopologyConstants.NODE_ATTR_ID),
                                  attr.get(UfmTopologyConstants.NODE_ATTR_TITLE),
                                  attr.get(UfmTopologyConstants.NODE_ATTR_TYPE)))
        self.fo.write('''\t\t</attributes>''')

    def _write_node(self, node, added=False, removed=False):
        self.fo.write('\t\t\t<node id="{0}" label="{1}">\n'
                      .format(node.get(UfmTopologyConstants.NODE_GUID),
                              node.get(UfmTopologyConstants.NODE_NAME)))

        if added:
            node_color = UfmTopologyConstants.ADDED_NODE_COLOR
        elif removed:
            node_color = UfmTopologyConstants.DELETED_NODE_COLOR
        else:
            node_color = UfmTopologyConstants.UNAFFECTED_NODE_COLOR
        self.fo.write(f'\t\t\t\t<viz:color r="{node_color.get("R")}" g="{node_color.get("G")}" '
                      f'b="{node_color.get("B")}" a="{node_color.get("A")}"/>\n')

        self.fo.write('\t\t\t\t<attvalues>\n')
        for attr in UfmTopologyConstants.NODES_ATTRIBUTES:
            self.fo.write('\t\t\t\t\t<attvalue for="{0}" value="{1}"/>\n'
                          .format(attr.get(UfmTopologyConstants.NODE_ATTR_ID),
                                  node.get(attr.get(UfmTopologyConstants.NODE_ATTR_ID))))
        self.fo.write('\t\t\t\t</attvalues>\n')
        self.fo.write('\t\t\t</node>\n')

    def _write_nodes(self, nodes, added_nodes=None, removed_nodes=None):
        self.fo.write('''
\t\t<nodes>
''')
        for node in nodes:
            self._write_node(node, added= added_nodes and node.get(UfmTopologyConstants.NODE_GUID) in added_nodes)
        if removed_nodes:
            for key, node in removed_nodes.items():
                self._write_node(node, removed=True)
        self.fo.write('''\t\t</nodes>''')

    def _write_edges(self, links):
        self.fo.write('''
\t\t<edges>
''')
        for link in links:
            self.fo.write('\t\t\t<edge id="{0}" source="{1}" target="{2}"/>\n'
                          .format(link.get(UfmTopologyConstants.LINK_NAME),
                                  link.get(UfmTopologyConstants.LINK_SOURCE_GUID),
                                  link.get(UfmTopologyConstants.LINK_DEST_GUID)))
        self.fo.write('''\t\t</edges>
    ''')

    def close(self, path_to_export):
        """
        Close the temporary file and rename it to "normal"
        """
        if not self.fo is None:
            self.fo.close()
            if os.path.exists(path_to_export):
                os.remove(path_to_export)
            os.rename(self.fo.name, path_to_export)
            self.fo = None

    def get_added_nodes_dict(self, added_nodes_arr):
        added_nodes = {}
        for node in added_nodes_arr:
            added_nodes[node.get(UfmTopologyConstants.NODE_GUID)] = node
        return added_nodes

    def get_removed_nodes_dict(self, removed_nodes_arr):
        removed_nodes = {}
        for node in removed_nodes_arr:
            _node = {}
            # set the node attributes of the removed nodes because it dose not exist in the compare result
            for attr in UfmTopologyConstants.NODES_ATTRIBUTES:
                _id = attr.get(UfmTopologyConstants.NODE_ATTR_ID)
                if _id == UfmTopologyConstants.NODE_NAME:
                    _node[UfmTopologyConstants.NODE_NAME] = node
                else:
                    _node[_id] = "N/A"

            removed_nodes[node] = _node
        return removed_nodes

    def export_topology_as_gexf_file(self, nodes, links, path_to_export, compare_result=None):
        # this function will export the topology as GEXF  (Graph Exchange XML Format)
        # .GEXF file can be used later on in the visualization tools (e.g. Gephi)

        added_nodes = None
        removed_nodes = None
        if compare_result:
            # Convert the result of compare from arrays to dicts
            added_nodes = self.get_added_nodes_dict(compare_result.get("added").get("nodes"))
            removed_nodes = self.get_removed_nodes_dict(compare_result.get("removed").get("nodes"))

        self.fo = NamedTemporaryFile(delete=False, dir=os.path.dirname(path_to_export),
                                     prefix='.tmp',
                                     mode='w', encoding='ascii') # Open temporary file streaming

        Logger.log_message("Generating %s file"%path_to_export)

        self.fo.write('''<?xml version="1.0" encoding="UTF-8"?>
<gexf xmlns="http://www.gexf.net/1.1draft"
    xmlns:viz="http://www.gexf.net/1.2draft/viz"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.gexf.net/1.1draft http://www.gexf.net/1.1draft/gexf.xsd"
    version="1.1">
    <graph mode="static" defaultedgetype="undirected">''')
        self._write_node_attributes()
        self._write_nodes(nodes= nodes, added_nodes=added_nodes, removed_nodes=removed_nodes)
        self._write_edges(links= links)

        self.fo.write('''</graph>
</gexf>
''')
        self.close(path_to_export= path_to_export)
        Logger.log_message("The file %s is saved successfully"% path_to_export)


class UFMTopologyTopoExporter:

    @staticmethod
    def export_topology_as_topo_file(export_to_path):
        try:
            url = "Topology_Compare/topology_file"
            response = ufm_rest_client.send_request(url, method=HTTPMethods.POST)
            response = response.json()
            file_name = response.get('file_name')
            file_content = ufm_rest_client.send_request(url + "/" + file_name)
            with open(export_to_path, 'wb') as f:
                f.write(file_content.content)
                Logger.log_message("The file %s is saved successfully"%export_to_path)
        except Exception as e:
            Logger.log_message(f'Error to export topology: {e}', LOG_LEVELS.ERROR)


class UFMTopologyCompare:

    @staticmethod
    def compare_topology_with_custom_topo(path_custom_topo_file, path_to_export):
        try:
            with open(path_custom_topo_file, 'rb') as f:
                url = "Topology_Compare/networkdiff"
                response = ufm_rest_client.send_request(url, method=HTTPMethods.POST,files={'filename': f})
                job_id = response.json()
                job_is_completed = False
                while not job_is_completed:
                    time.sleep(5)
                    jobs_url = f'jobs/{job_id}'
                    job_response = ufm_rest_client.send_request(jobs_url)
                    if job_response.raise_for_status():
                        break
                    job_response = job_response.json()
                    job_is_completed = job_response.get("Status") == "Completed"
                if job_is_completed:
                    topo_diff_response = ufm_rest_client.send_request(url).json()
                    Utils.write_json_to_file(path_to_export,topo_diff_response)
                    return topo_diff_response

        except Exception as e:
            Logger.log_message(f'Error to compare topology: {e}',LOG_LEVELS.ERROR)

if __name__ == "__main__":

    # init app args
    args = ArgsParser.parse_args("UFM Topology Management", UfmTopologyConstants.args_list)

    # init app config parser & load config files
    config_parser = UfmTopologyConfigParser(args)

    # init logs configs
    logs_file_name = config_parser.get_logs_file_name()
    logs_level = config_parser.get_logs_level()
    Logger.init_logs_config(logs_file_name, logs_level)


    # init ufm rest client
    ufm_rest_client = UfmRestClient(host = config_parser.get_ufm_host(),
                                    client_token=config_parser.get_ufm_access_token(),username = config_parser.get_ufm_username(),
                                    password = config_parser.get_ufm_password(),ws_protocol=config_parser.get_ufm_protocol())

    if config_parser.get_export_to_gephi():
        # load systems,links
        nodes = ufm_rest_client.get_systems()
        links = ufm_rest_client.get_links()
        gephi_file_name = config_parser.get_gephi_file_name()
        path_to_export = config_parser.get_path_to_export() + '/' + gephi_file_name
        exporter = UfmTopologyGephiExporter()
        exporter.export_topology_as_gexf_file(nodes=nodes, links=links, path_to_export=path_to_export)

    if config_parser.get_export_as_topo():
        topo_file_name = config_parser.get_topo_file_name()
        path_to_export = config_parser.get_path_to_export() + '/' + topo_file_name
        UFMTopologyTopoExporter.export_topology_as_topo_file(path_to_export)

    if len(config_parser.get_compare_topo_with()) > 0:
        file_path = config_parser.get_compare_topo_with()

        result_file_name = Utils.get_timebased_filename()
        export_to_path = f'{config_parser.get_path_to_export()}/{result_file_name}_compare.json'
        compare_result = UFMTopologyCompare.compare_topology_with_custom_topo(file_path,export_to_path)

        if config_parser.get_export_topology_compare_to_gephi():
            nodes = ufm_rest_client.get_systems()
            links = ufm_rest_client.get_links()
            path_to_export = f'{config_parser.get_path_to_export()}/{result_file_name}_compare.gexf'

            exporter = UfmTopologyGephiExporter()
            exporter.export_topology_as_gexf_file(nodes=nodes, links=links,
                                                  path_to_export=path_to_export, compare_result=compare_result)

