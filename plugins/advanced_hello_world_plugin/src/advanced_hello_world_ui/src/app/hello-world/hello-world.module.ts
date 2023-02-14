import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { HelloWorldRoutingModule } from './hello-world-routing.module';
import {HelloWorldComponent} from "./hello-world.component";
import {GeneralRouteModuleModule} from "./general-route-module/general-route-module.module";
import {DevicesDataTableModule} from "./devices-data-table/devices-data-table.module";
import {DevicesContextMenuModule} from "./devices-context-menu/devices-context-menu.module";


@NgModule({
  declarations: [
    HelloWorldComponent
  ],
  imports: [
    CommonModule,
    GeneralRouteModuleModule,
    DevicesDataTableModule,
    HelloWorldRoutingModule,
    DevicesContextMenuModule
  ]
})
export class HelloWorldModule { }
