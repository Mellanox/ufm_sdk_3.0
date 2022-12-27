import {Injectable} from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs";
import {UfmDevicesConstants} from "../constants/ufm-devices.constants";

@Injectable({
  providedIn: 'root'
})
export class UfmDevicesBackendService {

  constructor(private httpService: HttpClient,
              private ufmDevicesConstants: UfmDevicesConstants) {

  }

  public getDeviceInfo(guid: string): Observable<any> {
    const url = this.ufmDevicesConstants.devicesAPIsUrls.devices.concat(`/${guid}`)
    return this.httpService.get(url);
  }
}
