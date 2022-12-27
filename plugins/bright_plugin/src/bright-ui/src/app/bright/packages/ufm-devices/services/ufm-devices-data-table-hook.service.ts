/**
 * @COMPONENTS
 */
import {Injectable} from '@angular/core';
import {Observable} from "rxjs";

/**
 * @SERVICES
 */
import {BrightBackendService} from "../../bright/services/bright-backend.service";
import {UfmDevicesConstants} from "../constants/ufm-devices.constants";

@Injectable({
  providedIn: 'root'
})
export class UfmDevicesDataTableHookService {

  constructor(private brightBackendService: BrightBackendService) {
  }

  public appendBrightData(ufmDevices: Array<any>): Observable<any> {
    return new Observable<any>((observable) => {
      this.brightBackendService.getBrightNodes().subscribe({
        next: (nodes: Array<string>) => {
          ufmDevices = ufmDevices.map((ufmDevice: any) => {
            const name = ufmDevice[UfmDevicesConstants.DEVICE_SERVER_KEYS.system_name];
            ufmDevice['plugin.is_bright'] = nodes.includes(name);
            if (ufmDevice['plugin.is_bright']) {
              if (!ufmDevice['plugin.templates']) {
                ufmDevice['plugin.templates'] = [];
              }
              ufmDevice['plugin.templates'].push(
                '<ng-template><i title="Bright node" class="fas fa-cogs" style="margin-right: 4px;"></i>Bright Node</ng-template>'
              );
            }
            return ufmDevice;
          });
          observable.next(ufmDevices);
          observable.complete();
        },
        error: (err: any) => {
          console.error(err)
          observable.next(ufmDevices);
          observable.complete()
        }
      });
    });
  }
}
