import {Injectable} from '@angular/core';
import {Constants} from "../../../../constants/constants";


@Injectable()
export class DevicesConstants {

    constructor(private globalConstants:Constants){}

    public readonly devicesAPIURLs = {
        "devices": this.globalConstants.baseResourcesApiURL.concat("/systems"),
    }

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
        has_smartnic_device:"has_smartnic_device" as "has_smartnic_device",
        in_bright: "in_bright" as "in_bright"
    };

    public readonly deviceServerKeys = DevicesConstants.DEVICE_SERVER_KEYS;

    public static DEVICE_TYPES = {
        'host': 'host',
        'gateway': 'gateway',
        'switch': 'switch',
        'router': 'router'

    }

    public static MODEL_IMAGES = {
        nvidia: "assets/img/logo-nvidia-17X17.png",
        blueField: "assets/img/bluefield_logo_21x15.png"
    }
    public static DEVICE_IMAGES = {
        sm_server_base: "./assets/img/sm_server_base.png",
        ha_active_server_base: "./assets/img/ha_active_server_base.png",
        sb_server_base: "./assets/img/sb_server_base.png",
        server_base: "./assets/img/server_base.png",

        sm_server_warning: "./assets/img/sm_server_warning.png",
        ha_active_server_warning: "./assets/img/ha_active_server_warning.png",
        sb_server_warning: "./assets/img/sb_server_warning.png",
        server_warning: "./assets/img/server_warning.png",

        sm_server_critical: "./assets/img/sm_server_critical.png",
        ha_active_server_critical: "./assets/img/ha_active_server_critical.png",
        sb_server_critical: "./assets/img/sb_server_critical.png",
        server_critical: "./assets/img/server_critical.png",

        sm_server_minor: "./assets/img/sm_server_minor.png",
        ha_active_server_minor: "./assets/img/ha_active_server_minor.png",
        sb_server_minor: "./assets/img/sb_server_minor.png",
        server_minor: "./assets/img/server_minor.png",

        general: "./assets/img/general.png",
        general_warning: "./assets/img/general_warning.png",
        general_critical: "./assets/img/general_critical.png",
        general_minor: "./assets/img/general_minor.png",

        router: "./assets/img/router.png",
        router_warning: "./assets/img/router_warning.png",
        router_critical: "./assets/img/router_critical.png",
        router_minor: "./assets/img/router_minor.png",

        gateway: "./assets/img/gateway.png",
        gateway_warning: "./assets/img/gateway_warning.png",
        gateway_critical: "./assets/img/gateway_critical.png",
        gateway_minor: "./assets/img/gateway_minor.png",
        layers: "./assets/img/layers.png",
        cloud: "./assets/img/cloud.png",

        general_gray: "./assets/img/general_gray.png",
        general_blue: "./assets/img/general_blue.png",

    }

}
