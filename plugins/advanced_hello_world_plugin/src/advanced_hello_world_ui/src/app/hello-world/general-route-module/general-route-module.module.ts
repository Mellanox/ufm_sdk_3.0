import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {GeneralRouteModuleComponent} from './general-route-module.component';
import {GeneralRouteModuleRoutingModule} from "./general-route-module-routing.module";
import {DynamicMenuItemsService} from "./services/dynamic-menu-items.service";
import {InventoryGeneralTableComponent} from "../inventory-general-table/inventory-general-table.component";
import {GenericHistogramComponent} from "../generic-histogram/generic-histogram.component";
import {DevicesContextMenuModule} from "../devices-context-menu/devices-context-menu.module";
import {XCoreAgGridModule} from "../../../../sms-ui-suite/x-core-ag-grid/x-core-ag-grid.module";
import {SpinnerModule} from "../../../../sms-ui-suite/sms-spinner/spinner.module";
import {AgChartsAngularModule} from "ag-charts-angular";
import {SmsCardModule} from "../../../../sms-ui-suite/sms-card/sms-card.module";
import {FormsModule} from "@angular/forms";
import {SmsDropdownSelectModule} from "../../../../sms-ui-suite/sms-dropdown-select/sms-dropdown-select.module";


@NgModule({
  declarations: [
    GeneralRouteModuleComponent,
    InventoryGeneralTableComponent,
    GenericHistogramComponent
  ],
  imports: [
    CommonModule,
    GeneralRouteModuleRoutingModule,
    DevicesContextMenuModule,
    XCoreAgGridModule,
    SpinnerModule,
    AgChartsAngularModule,
    SmsCardModule,
    FormsModule,
    SmsDropdownSelectModule
  ]
})
export class GeneralRouteModuleModule {

  constructor() {
  }

  get DynamicMenuItemsService() {
    return DynamicMenuItemsService
  }
}
