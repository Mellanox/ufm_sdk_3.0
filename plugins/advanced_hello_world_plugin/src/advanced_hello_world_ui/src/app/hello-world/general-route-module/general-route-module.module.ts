import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { GeneralRouteModuleComponent } from './general-route-module.component';
import {GeneralRouteModuleRoutingModule} from "./general-route-module-routing.module";
import {DynamicMenuItemsService} from "./services/dynamic-menu-items.service";



@NgModule({
  declarations: [
    GeneralRouteModuleComponent
  ],
  imports: [
    CommonModule,
    GeneralRouteModuleRoutingModule
  ]
})
export class GeneralRouteModuleModule {

  constructor() {
  }

  get DynamicMenuItemsService() {
    return DynamicMenuItemsService
  }
}
