import {Injectable} from '@angular/core';
import {Observable} from "rxjs";

@Injectable({
  providedIn: 'root'
})
export class NdtViewService {

  /**
   * @VARIABLES
   */
  public static isRunningFromUFM = window["is_ufm"];
  public static ufmRESTBase = window['ufm_rest_base'];

  constructor() {
  }

  public getSideBarMenuItems(routePrefix = 'ndt') {
    return [
      {
        label: 'Subnet Merger',
        key: `${routePrefix}/subnet-merger`,
        route: `${routePrefix}/subnet-merger`,
        icon: 'fa fa-object-ungroup'
      }
    ]
  }

  public getSideMenuItemsForUFM(routerPrefix): Observable<any> {
    routerPrefix = `${routerPrefix}/ndt`;
    return new Observable<any>((obs) => {
      obs.next(this.getSideBarMenuItems(routerPrefix));
      obs.complete();
    })
  }
}
