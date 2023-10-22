import {Injectable} from '@angular/core';
import {HttpClientService} from "../../../../../../sms-ui-suite/sms-http-client/http-client.service";
import {CableValidationConstants} from "../constants/cable-validation.constants";
import {Observable} from "rxjs";

@Injectable({
  providedIn: 'root'
})
export class CableValidationBackendService {

  constructor(private httpService: HttpClientService) {
  }

  public checkIfCableValidationAvailable(): Observable<any> {
    const url = CableValidationConstants.API_URLs.isCVEnabled;
    return this.httpService.get(url);
  }

  public getCableValidation(): Observable<any> {
    const url = CableValidationConstants.API_URLs.cableValidationReport;
    return this.httpService.get(url);
  }
}
