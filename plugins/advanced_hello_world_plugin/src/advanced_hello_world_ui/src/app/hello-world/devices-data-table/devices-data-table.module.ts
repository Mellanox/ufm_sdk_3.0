import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';

import {DevicesDataTableService} from "./services/devices-data-table.service";


@NgModule({
  declarations: [],
  providers: [
    DevicesDataTableService
  ],
  imports: [
    CommonModule
  ]
})
export class DevicesDataTableModule {

  public get DevicesDataTableService() {
    return DevicesDataTableService;
  }

}
