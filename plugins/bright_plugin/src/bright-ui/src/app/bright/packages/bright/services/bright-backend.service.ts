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
import {HttpClientService} from "../../../../../../sms-ui-suite/sms-http-client/http-client.service";
import {map, Observable} from "rxjs";
import * as jstz from 'jstz';

@Injectable({
  providedIn: 'root'
})
export class BrightBackendService {
  constructor(private httpService: HttpClientService,
              private brightConstants: BrightConstants) {
  }

  getBrightConf(): Observable<any> {
    const url = this.brightConstants.brightAPIsUrls.conf;
    return this.httpService.get(url);
  }

  updateBrightConf(payload): Observable<any> {
    const url = this.brightConstants.brightAPIsUrls.conf;
    return this.httpService.put(url, payload);
  }


  getBrightNodes(): Observable<any> {
    const url = this.brightConstants.brightAPIsUrls.nodes;
    return this.httpService.get(url);
  }

  getDeviceJobs(nodes?: Array<string>, from?: number, to?: number): Observable<any> {
    let filters:Array<string> = [];
    if (nodes) {
      filters.push(`nodes=${nodes.join(',')}`);
    }
    if (from) {
      filters.push(`from=${from}`);
    }
    if (to) {
      filters.push(`to=${to}`);
    }
    if(from || to) {
      filters.push(`tz=${this.getLocalTimezone()}`);
    }
    const url = filters.length ? this.brightConstants.brightAPIsUrls.jobs.concat(`?${filters.join('&')}`) : this.brightConstants.brightAPIsUrls.jobs;
    return this.httpService.get(url);
  }

  getLocalTimezone() {
    return jstz.determine().name();
  }
}
