import {Injectable} from '@angular/core';
import {observable, Observable} from "rxjs";

@Injectable({
  providedIn: 'root'
})
export class DynamicMenuItemsService {

  constructor() {
  }

  public getSideBarMenuItems(route_prefix:string=""): Observable<any> {
    return new Observable<any>((observable) => {
      observable.next(
        [
          {
            label: "Dynamic Menu Item",
                key: "dynamic-menu-items",
                route: `${route_prefix}/general`,
                icon: "fa fa-tasks",
                subMenu: [
                    {
                        label: "General Module",
                        key: "general-module",
                        parentKey: "dynamic-menu-items",
                        route: `${route_prefix}/general`
                    }
                ]
          }
        ]
      )
    })
  }
}
