import {Injectable} from '@angular/core';
import {HttpClientService} from "../../../../../../sms-ui-suite/sms-http-client/http-client.service";
import {Observable} from "rxjs";
import {UfmDevicesConstants} from "../constants/ufm-devices.constants";

@Injectable({
  providedIn: 'root'
})
export class UfmDevicesBackendService {

  constructor(private httpService: HttpClientService,
              private ufmDevicesConstants: UfmDevicesConstants) {

  }

  public getDeviceInfo(guid: string): Observable<any> {
    const url = this.ufmDevicesConstants.devicesAPIsUrls.devices.concat(`/${guid}`)
    return this.httpService.get(url);
  }
}
