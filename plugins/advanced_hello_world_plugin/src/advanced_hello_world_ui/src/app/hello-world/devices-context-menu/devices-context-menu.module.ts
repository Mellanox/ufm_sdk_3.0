import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';

import {DevicesContextMenuComponent} from './devices-context-menu.component';
import {ModalModule} from "ngx-bootstrap/modal";

@NgModule({
  declarations: [
    DevicesContextMenuComponent
  ],
  exports: [
    DevicesContextMenuComponent
  ],
  imports: [
    CommonModule,
    ModalModule.forRoot()
  ]
})
export class DevicesContextMenuModule {
  get DevicesContextMenuComponent() {
    return DevicesContextMenuComponent;
  }
}
