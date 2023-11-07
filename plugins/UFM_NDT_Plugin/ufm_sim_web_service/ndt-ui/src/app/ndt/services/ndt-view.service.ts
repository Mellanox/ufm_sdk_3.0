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
      },
      {
        label: 'Subnet Merger Settings',
        key: `${routePrefix}/settings`,
        route: `${routePrefix}/settings`,
        icon: 'fa fa-cog'
      }
    ]
  }

  public getSideMenuItemsForUFM(routerPrefix): Observable<any> {
    routerPrefix = `${routerPrefix}/ndt`;
    return new Observable<any>((obs) => {
      const subItems = this.getSideBarMenuItems(routerPrefix).map((_item) => {
        _item['parentKey'] = 'subnet-merger';
        return _item;
      });
      const items = [
        {
          label: 'Subnet Merger',
          key: 'subnet-merger',
          route: subItems[0].route,
          icon: 'fa fa-bezier-curve',
          subMenu: subItems
        }
      ];
      obs.next(items);
      obs.complete();
    })
  }
}
