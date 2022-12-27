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
 @date:    May 15th, 2022
 **/

import {Injectable}    from '@angular/core';

@Injectable()
export class DeviceJobsConstants {

    constructor() {
    }

    public static JOBS_SERVER_FIELDS = {
        jobID: "jobID" as "jobID",
        childType: "childType" as "childType",
        status: "status" as "status",
        starttime: "starttime" as "starttime",
        endtime: "endtime" as "endtime",
        inqueue: "inqueue" as "inqueue",
        username: "username" as "username",
        uniqueKey: "uniqueKey" as "uniqueKey"
    };

    public static JOB_TYPE_MAP = {
        SlurmJob: "Slurm"
    }

    public static JOB_STATUS_MAP = {
        SUCCESS: 'far fa-check-circle',
        RUNNING: 'far fa-check-circle',
        FAILED: 'far fa-check-circle',
    }
}
