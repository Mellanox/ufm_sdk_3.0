/**
 @copyright:
 Copyright (C) Nvidia Technologies Ltd. 2014-2022. ALL RIGHTS RESERVED.

 This software product is a proprietary product of Mellanox Technologies
 Ltd. (the "Company") and all right, title, and interest in and to the
 software product, including all associated intellectual property rights,
 are and shall remain exclusively with the Company.

 This software product is governed by the End User License Agreement
 provided with the software product.

 @author: Nasr Ajaj
 @date:    11th,May,22
 **/

import {Injectable} from '@angular/core';
import {Constants} from "../../../../constants/constants";


@Injectable({
  providedIn: 'root'
})
export class BrightConstants {

    constructor(private globalConstants:Constants){}

    public readonly brightAPIsUrls ={
        jobs: Constants.baseBrightPluginApiURL.concat("/data/jobs"),
        nodes: Constants.baseBrightPluginApiURL.concat("/data/nodes"),
        conf: Constants.baseBrightPluginApiURL.concat("/conf")
    };

    public static brightConfKeys = {
      brightConfig: "bright-config" as "bright-config",
      status: "status" as "status",
      timezone: "timezone" as "timezone",
      statusErrMessage: "err_message" as "err_message",
      enabled: "enabled" as "enabled",
      host: "host" as "host",
      port: "port" as "port",
      dataRetentionPeriod: "data_retention_period" as "data_retention_period",
      certificate: "certificate" as "certificate",
      certificateKey: "certificate_key" as "certificate_key"
    };

    public static brightStatusValues = {
      healthy: "Healthy",
      unhealthy: "Unhealthy",
      disabled: "Disabled"
    }

}
