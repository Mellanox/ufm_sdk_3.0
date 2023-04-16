import {Injectable} from "@angular/core";
import {Constants} from "../../../../constants/constants";

@Injectable({
  providedIn: 'root'
})
export class UfmDevicesConstants {

  constructor() {
  }

  public readonly devicesAPIsUrls = {
    devices: Constants.baseResourcesApiUrl.concat("/systems")
  };


  public static DEVICE_SERVER_KEYS = {
    sm_mode: "sm_mode" as "sm_mode",
    temperature: "temperature" as "temperature",
    total_alarms: "total_alarms" as "total_alarms",
    cpu_type: "cpu_type" as "cpu_type",
    cpus_number: "cpus_number" as "cpus_number",
    cpu_speed: "cpu_speed" as "cpu_speed",
    ram: "ram" as "ram",
    script: "script" as "script",
    url: "url" as "url",
    description: "description" as "description",
    fw_version: "fw_version" as "fw_version",
    has_ufm_agent: "has_ufm_agent" as "has_ufm_agent",
    guid: "guid" as "guid",
    psid: "psid" as "psid",
    server_operation_mode: "server_operation_mode" as "server_operation_mode",
    state: "state" as "state",
    system_guid: "system_guid" as "system_guid",
    model: "model" as "model",
    vendor: "vendor" as "vendor",
    is_manual_ip: "is_manual_ip" as "is_manual_ip",
    is_managed: "is_managed" as "is_managed",
    severity: "severity" as "severity",
    technology: "technology" as "technology",
    mirroring_template: "mirroring_template" as "mirroring_template",
    system_name: "system_name" as "system_name",
    ip: "ip" as "ip",
    role: "role" as "role",
    name: "name" as "name",
    sw_version: "sw_version" as "sw_version",
    capabilities: "capabilities" as "capabilities",
    groups: "groups" as "groups",
    type: "type" as "type",
    modules: "modules" as "modules",
    ports: "ports" as "ports",
    level: "level" as "level",
    site_name: "site_name" as "site_name",
    has_smartnic_device: "has_smartnic_device" as "has_smartnic_device",
    in_bright: "in_bright" as "in_bright"
  };

}
