import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {UfmDevicesDataTableHookService} from "./services/ufm-devices-data-table-hook.service";
import {BrightModule} from "../bright/bright.module";


@NgModule({
  declarations: [],
  providers: [
    UfmDevicesDataTableHookService
  ],
  imports: [
    CommonModule,
    BrightModule
  ]
})
export class UfmDevicesModule {

  public get UfmDevicesDataTableHookService() {
    return UfmDevicesDataTableHookService;
  }

}
