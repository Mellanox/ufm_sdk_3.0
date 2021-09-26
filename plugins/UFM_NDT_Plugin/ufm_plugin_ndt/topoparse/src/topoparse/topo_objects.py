'''
Created on Jun 12, 2021

@author: samerd
'''
from topoparse.parse_utils import get_vendor, get_device_type, get_speed_val, \
    get_width_val, get_mtu, get_logical_state, get_physical_state


class TopoObj:
    def get_data(self):
        return self.__dict__


class SystemObj(TopoObj):
    def __init__(self, node_guid, node_data, node_info, switch_data):
        node_guid = node_guid.replace("0x", "")
        #         self.capabilities = []
        #         self.cpu_speed = 0
        #         self.cpu_type = "any"
        #         self.cpus_number = 0
        dev_id = int(node_data["DeviceID"])
        vendor_id = int(node_data["VendorID"])
        if switch_data:
            self.description = node_info["FWInfo_PSID"]
            self.model = node_info["FWInfo_PSID"]
            self.technology = get_device_type(dev_id)
            self.type = "switch"
        else:
            self.description = "server"
            self.model = "Computer"
            self.technology = "Computer"
            self.type = "host"
        self.fw_version = "N/A"
        #         self.groups = [
        #             "Servers"
        #         ],
        self.guid = node_guid
        #         self.has_smartnic_device = false
        #         self.has_ufm_agent = false
        #         self.ip = "0.0.0.0"
        #         self.is_managed = true
        #         self.is_manual_ip = false
        #         self.mirroring_template = false
        #         self.modules = [
        #             "0c42a10300280000_0_00",
        #             "0c42a103001b80ce_0_00"
        #         ],
        self.name = node_guid
        self.ports = []
        # self.psid = "N/A"
        # self.ram = 0
        # TODO
        self.role = "endpoint"
        # self.script = "N/A"
        # self.server_operation_mode = "Not_UFM_Server"
        self.severity = "Info"
        # self.sm_mode = "noSM"
        # self.state = "active"
        self.sw_version = "N/A"
        self.system_guid = node_data["SystemImageGUID"].replace("0x", "")
        self.system_name = node_data["NodeDesc"].replace('"', '')
        #         self.temperature = "N/A"
        #         self.total_alarms = 0

        # self.url = ""
        self.vendor = get_vendor(vendor_id)


class PortObj(TopoObj):
    def __init__(self, node_guid, port_num, port_data, port_ex_data, system_name, peer):
        node_guid = node_guid.replace("0x", "")
        self.active_speed = get_speed_val(int(port_data["LinkSpeedActv"]))[0]
        self.active_width = get_width_val(int(port_data["LinkWidthActv"]))[0]
        self.capabilities = []  # todo
        self.description = "Switch IB Port"
        self.dname = port_num
        self.enabled_speed = get_speed_val(int(port_data["LinkSpeedEn"]))
        self.enabled_width = get_width_val(int(port_data["LinkWidthEn"]))
        self.external_number = 1  # todo
        self.guid = port_data['PortGuid'].replace("0x", "")
        # self.high_ber_severity =  "N/A"
        self.lid = int(port_data['LID'])
        self.logical_state = get_logical_state(int(port_data["PortState"]))
        # self.mirror =  "disable"
        # self.module =  "N/A"
        self.mtu = get_mtu(int(port_data['NMTU']))
        self.name = "%s_%s" % (node_guid, port_num)
        self.number = int(port_num)
        self.node_description = "%s:%s" % (system_name, self.number)
        # self.path =  "default / Switch: SLG01-02 / NA / 1"
        self.peer = peer
        #         self.peer_guid =  "0c42a103001b8256"
        #         self.peer_ip =  "0.0.0.0"
        #         self.peer_lid =  254
        #         self.peer_node_description =  "luna-0001 mlx5_10"
        #         self.peer_node_guid =  "0c42a103001b8256"
        #         self.peer_node_name =  "luna-0001"
        #         self.peer_port_dname =  "HCA-2/1"
        self.physical_state = get_physical_state(int(port_data["PortPhyState"]))
        self.severity = "Info"
        self.supported_speed = get_speed_val(int(port_data["LinkSpeedSup"]))
        self.supported_width = get_width_val(int(port_data["LinkWidthSup"]))
        self.systemID = self.guid
        #         self.system_capabilities =  []
        #         self.system_ip =  "0.0.0.0"
        #         self.system_mirroring_template =  False
        self.system_name = system_name
        self.tier = 4


class LinkObj(TopoObj):
    def __init__(self, link_data):
        # {'NodeGuid1': '0x506b4b03009eeb88', 'PortNum1': '1', 'NodeGuid2': '0x506b4b03009eeb82', 'PortNum2': '37'}
        src_guid = link_data['NodeGuid1']
        dst_guid = link_data['NodeGuid2']

        src_port = link_data['PortNum1']
        dst_port = link_data['PortNum2']
        if dst_guid < src_guid:
            src_guid, dst_guid = dst_guid, src_guid
            src_port, dst_port = dst_port, src_port
        self.cable_info = {},  # todo
        self.capabilities = [],  # todo
        self.destination_guid = dst_guid
        self.destination_port = dst_port
        self.destination_port_dname = dst_port
        # self.destination_port_node_description = "SLG03-13:39",
        self.name = "%s_%s:%s_%s" % (src_guid, src_port, dst_guid, dst_port)
        self.severity = "Info"  # todo
        self.source_guid = src_guid
        self.source_port = src_port
        self.source_port_dname = src_port
        # self.source_port_node_description = "SSPINE3-15:13",
        self.width = "4x"  # todo


class PKeyObj(TopoObj):
    def __init__(self):
        self.guids = list()
        self.ip_over_ib = True  # todo
        self.partition = "management"  # todo

    def add_port_guid(self, pkey_guid_entry):
        guid_obj = {
            "guid": pkey_guid_entry["PortGUID"].replace("0x", ""),
            "membership": "limited",
            "index0": False
        }
        if guid_obj not in self.guids:
            self.guids.append(guid_obj)

    def get_data(self):
        data = dict(self.__dict__)
        data['guids'] = list(data['guids'])
        return data
