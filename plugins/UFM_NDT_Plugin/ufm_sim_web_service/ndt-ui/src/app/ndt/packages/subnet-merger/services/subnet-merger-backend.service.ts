import {Injectable} from '@angular/core';
import {HttpClientService} from "../../../../../../sms-ui-suite/sms-http-client/http-client.service";
import {Observable} from "rxjs";
import {SubnetMergerConstants} from "../constants/subnet-merger.constants";

@Injectable({
  providedIn: 'root'
})
export class SubnetMergerBackendService {

  constructor(private httpService: HttpClientService) {
  }

  public getNDTsList(): Observable<any> {
    const url = SubnetMergerConstants.mergerAPIs.NDTsList;
    return this.httpService.get(url);
  }

  public validateNDTFile(fileName: string): Observable<any> {
    const url = SubnetMergerConstants.mergerAPIs.validateNDT;
    const payload = {
      [SubnetMergerConstants.validateAPIKeys.NDTFileName]: fileName
    };
    return this.httpService.post(url, payload);
  }

  public getValidationReports(reportID?: string): Observable<any> {
    let url = `${SubnetMergerConstants.mergerAPIs.validationReports}`
    if (reportID) {
      url = `${SubnetMergerConstants.mergerAPIs.validationReports}/${reportID}`
    }
    return this.httpService.get(url);
  }

  public deployNDTFile(fileName: string): Observable<any> {
    const url = `${SubnetMergerConstants.mergerAPIs.deployNDTFile}`
    const payload = {
      [SubnetMergerConstants.validateAPIKeys.NDTFileName]: fileName
    };
    return this.httpService.post(url, payload);
  }

  public updatePortsBoundaries(fileName: string, state = SubnetMergerConstants.boundariesStates.noDiscover): Observable<any> {
    const url = `${SubnetMergerConstants.mergerAPIs.updateBoundaryPortsState}`
    const payload = {
      [SubnetMergerConstants.validateAPIKeys.NDTFileName]: fileName,
      [SubnetMergerConstants.boundariesStates.boundaryPortState]: state
    };
    return this.httpService.post(url, payload);
  }

  public getActiveDeployedFile(): Observable<any> {
    const url = SubnetMergerConstants.mergerAPIs.lastDeployedNDT;
    return this.httpService.get(url);
  }
}
