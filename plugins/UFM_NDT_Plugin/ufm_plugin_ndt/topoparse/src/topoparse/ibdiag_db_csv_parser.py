'''
Created on Jun 12, 2021

@author: samerd
'''
import os
import logging
import json
from topoparse.topo_objects import SystemObj, PortObj, LinkObj, PKeyObj


class IbdiagDbCsvParser:
    SECTIONS = {"NODES", "PORTS", "SWITCHES", "LINKS", "PKEY", "CABLE_INFO", "EXTENDED_PORT_INFO", "NODES_INFO"}
    SECTION_KEYS = {
        "NODES": "NodeGUID",
        "NODES_INFO": "NodeGUID",
        "SWITCHES": "NodeGUID",
        "PORTS": ("NodeGuid", "PortNum"),
        "EXTENDED_PORT_INFO": ("NodeGuid", "PortNum"),
    }

    def __init__(self, db_file):
        """
        Constructor
        """
        self.db_file = db_file
        self.db_data = dict()
        self.logger = logging.getLogger("")
        self._systems = list()
        self._ports = list()
        self._links = list()
        self._pkeys = dict()

    def _get_line(self, fp):
        line = next(fp)
        return line.strip()

    def _parse_section(self, fp, section):
        print("parsing section", section)
        end_msg = "END_" + section
        key = self.SECTION_KEYS.get(section)
        if key:
            section_data = dict()
        else:
            section_data = list()
        print(key)
        self.db_data[section] = section_data
        headers = self._get_line(fp)
        headers = headers.split(',')
        line = self._get_line(fp)
        line = line.strip()
        line_key = None
        while line != end_msg:
            data = line.split(',')
            data_obj = dict(zip(headers, data))
            if key:
                if isinstance(key, tuple):
                    line_key = tuple([data_obj[attr] for attr in key])
                else:
                    line_key = data_obj[key]
                section_data[line_key] = data_obj
            else:
                section_data.append(data_obj)
            line = self._get_line(fp)
        print("Found %s entries" % len(section_data))
        print("Each entry contains %s attributes" % len(headers))
        print(section_data[line_key or 0])
        print("*" * 50)

    def parse(self):
        with open(self.db_file, "r") as fp:
            has_data = True
            while has_data:
                try:
                    line = self._get_line(fp)
                    if line.startswith("START_"):
                        section = line.replace("START_", "")
                        if section in self.SECTIONS:
                            self._parse_section(fp, section)

                except StopIteration:
                    has_data = False
        self._create_topology()

    def _create_topology(self):
        for node_guid, node_data in self.db_data["NODES"].items():
            node_info = self.db_data["NODES_INFO"].get(node_guid)
            switch_data = self.db_data["SWITCHES"].get(node_guid)
            sys_obj = SystemObj(node_guid, node_data, node_info, switch_data)
            self._systems.append(sys_obj)

        for link_data in self.db_data["LINKS"]:
            link_obj = LinkObj(link_data)
            self._links.append(link_obj)

        for (node_guid, port_num), port_data in self.db_data["PORTS"].items():
            system_name = [system.system_name for system in self._systems if system.name in node_guid][0]
            link_objs = [link for link in self._links if link.source_guid in node_guid and link.source_port == port_num]
            peer = "N/A"
            if link_objs:
                link = link_objs[0]
                peer = "%s_%s" % (link.source_guid, link.source_port)
                peer = peer.replace("0x","")
            port_ex_data = self.db_data["EXTENDED_PORT_INFO"].get((node_guid, port_num))
            port_obj = PortObj(node_guid, port_num, port_data, port_ex_data, system_name, peer)
            self._ports.append(port_obj)

        for pkey_entry in self.db_data["PKEY"]:
            pkey = pkey_entry['PKey']
            if pkey not in self._pkeys:
                self._pkeys[pkey] = PKeyObj()
            self._pkeys[pkey].add_port_guid(pkey_entry)

    def _generate_json(self, obj_list, out_dir, fname, as_dict=False):
        systems_path = os.path.join(out_dir, fname)
        with open(systems_path, "w") as fp:
            if as_dict:
                json.dump({obj_key: obj.get_data() for obj_key, obj in obj_list.items()}, fp, indent=4, sort_keys=True)
            else:
                json.dump([obj.get_data() for obj in obj_list], fp, indent=4, sort_keys=True)

    def generate_json_files(self, out_dir):
        self._generate_json(self._systems, out_dir, "systems.json")
        self._generate_json(self._ports, out_dir, "ports.json")
        self._generate_json(self._links, out_dir, "links.json")
        self._generate_json(self._links, out_dir, "links.json")
        self._generate_json(self._pkeys, out_dir, "pkeys.json", as_dict=True)


if __name__ == "__main__":
    curr_dir = os.path.dirname(__file__)
    data_dir = os.path.normpath(os.path.join(curr_dir, os.pardir, os.pardir, "data"))
    db_file = os.path.join(data_dir, "ibdiagnet2.db_csv")
    parser = IbdiagDbCsvParser(db_file)
    parser.parse()
    parser.generate_json_files(data_dir)
