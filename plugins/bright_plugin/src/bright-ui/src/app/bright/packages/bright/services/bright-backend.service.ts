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
import {BrightConstants} from "../constants/bright.constants";
import {HttpClient} from "@angular/common/http";
import {map, Observable} from "rxjs";


@Injectable()
export class BrightBackendService {
    constructor(private httpService: HttpClient,
                private brightConstants: BrightConstants) {
    }

    getDeviceJobs(devices: string): Observable<any> {
        let url = this.brightConstants.brightAPIsUrls.getDeviceJobs.concat("?device="+ devices)
        return this.httpService.get(url)
            .pipe(map(response => {
              console.log(response);
              return <any>response;
            }
            ));
    }
}
