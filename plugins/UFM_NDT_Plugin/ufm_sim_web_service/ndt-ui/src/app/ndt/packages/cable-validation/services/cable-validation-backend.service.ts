import {Injectable} from '@angular/core';
import {HttpClientService} from "../../../../../../sms-ui-suite/sms-http-client/http-client.service";
import {CableValidationConstants} from "../constants/cable-validation.constants";
import {Observable} from "rxjs";
import {ICablesValidationSettings} from "../interfaces/cables-validation-status.interface";

@Injectable({
  providedIn: 'root'
})
export class CableValidationBackendService {

  constructor(private httpService: HttpClientService) {
  }

  public getCableValidationConfigurations(): Observable<any> {
    const url = CableValidationConstants.API_URLs.cableValidationSettings;
    return this.httpService.get(url);
  }

  public updateCableValidationConfigurations(payload: ICablesValidationSettings): Observable<any> {
    const url = CableValidationConstants.API_URLs.cableValidationSettings;
    return this.httpService.post(url, payload);
  }

  public getCableValidation(): Observable<any> {
    const url = CableValidationConstants.API_URLs.cableValidationReport;
    return this.httpService.get(url);
  }
}
