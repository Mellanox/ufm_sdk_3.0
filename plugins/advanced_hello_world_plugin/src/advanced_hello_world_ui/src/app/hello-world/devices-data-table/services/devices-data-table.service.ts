import {Injectable} from '@angular/core';
import {observable, Observable} from "rxjs";

@Injectable({
  providedIn: 'root'
})
export class DevicesDataTableService {

  constructor() {
  }

  public appendBrightData(data: Array<any>): Observable<any> {
    return new Observable<any>((observable)=>{
      const dev = data[0];
      observable.next(data.map((device) => {
        device['plugin.is_bright2'] = device.guid == dev.guid || device.guid == dev.guid;
        if (device['plugin.is_bright2']) {
          if (!device['plugin.templates']) {
            device['plugin.templates'] = [];
          }
          if (device.guid == dev.guid) {
            device['plugin.templates'].push(
              '<ng-template><i title="Bright node" class="fas fa-cogs"></i></ng-template>'
            );
          } else {
            device['plugin.templates'].push(
              '<ng-template><i title="Bright node" class="fas fa-plus"></i></ng-template>'
            );
          }
        }
        return device;
      }));
    });
  }
}
