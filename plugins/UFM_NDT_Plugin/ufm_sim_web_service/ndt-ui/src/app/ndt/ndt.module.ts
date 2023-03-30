import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';

import {NdtRoutingModule} from './ndt-routing.module';
import {NdtComponent} from './ndt.component';
import {SubnetMergerViewModule} from "./views/subnet-merger-view/subnet-merger-view.module";
import {SmsAppNavbarModule} from "../../../sms-ui-suite/sms-app-navbar/sms-app-navbar.module";
import {NdtViewService} from "./services/ndt-view.service";


@NgModule({
  declarations: [
    NdtComponent
  ],
  imports: [
    CommonModule,
    NdtRoutingModule,
    SubnetMergerViewModule,
    SmsAppNavbarModule
  ]
})
export class NdtModule {
  public get NdtViewService() {
    return NdtViewService;
  }
}
