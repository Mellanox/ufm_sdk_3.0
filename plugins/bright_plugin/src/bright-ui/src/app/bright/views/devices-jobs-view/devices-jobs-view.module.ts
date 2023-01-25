import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {DevicesJobsViewComponent} from "./devices-jobs-view.component";
import {BrightModule} from "../../packages/bright/bright.module";
import {XCoreAgGridModule} from 'sms-ui-suite/x-core-ag-grid/x-core-ag-grid.module';
import {SpinnerModule} from 'sms-ui-suite/sms-spinner/spinner.module';
import {RouterModule} from "@angular/router";
import {UfmDevicesModule} from "../../packages/ufm-devices/ufm-devices.module";
import {DevicesJobsRoutes} from "./devices-jobs.routes";
import {BrowserAnimationsModule} from "@angular/platform-browser/animations";
import {TimePickerModalModule} from "../../packages/time-picker-modal/time-picker-modal.module";
import {SmsPluginBaseComponentModule} from "../../../../../sms-ui-suite/sms-plugin-base-component/sms-plugin-base-component.module";


@NgModule({
  declarations: [
    DevicesJobsViewComponent
  ],
  exports: [
    DevicesJobsViewComponent
  ],
  imports: [
    CommonModule,
    BrowserAnimationsModule,
    SmsPluginBaseComponentModule,
    BrightModule,
    XCoreAgGridModule,
    RouterModule.forChild(DevicesJobsRoutes),
    SpinnerModule,
    UfmDevicesModule,
    TimePickerModalModule
  ]
})
export class DevicesJobsViewModule {
}
