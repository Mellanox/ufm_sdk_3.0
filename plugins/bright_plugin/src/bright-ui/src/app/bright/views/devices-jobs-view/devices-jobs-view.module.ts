import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import {DevicesJobsViewComponent} from "./devices-jobs-view.component";
import {BrightModule} from "../../packages/bright/bright.module";
import { XCoreAgGridModule } from 'sms-ui-suite/x-core-ag-grid/x-core-ag-grid.module';
import { SpinnerModule } from 'sms-ui-suite/sms-spinner/spinner.module';
import {RouterModule} from "@angular/router";
import {UfmDevicesModule} from "../../packages/ufm-devices/ufm-devices.module";



@NgModule({
  declarations: [DevicesJobsViewComponent],
  exports: [
    DevicesJobsViewComponent
  ],
  imports: [
    CommonModule,
    BrightModule,
    XCoreAgGridModule,
    RouterModule,
    SpinnerModule,
    UfmDevicesModule
  ]
})
export class DevicesJobsViewModule { }
