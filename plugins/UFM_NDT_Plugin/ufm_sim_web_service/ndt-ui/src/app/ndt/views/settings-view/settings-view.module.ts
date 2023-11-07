import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { SettingsViewComponent } from './settings-view.component';
import {FormsModule, ReactiveFormsModule} from "@angular/forms";
import {ButtonsModule} from "ngx-bootstrap/buttons";
import {
  SmsPluginBaseComponentModule
} from "../../../../../sms-ui-suite/sms-plugin-base-component/sms-plugin-base-component.module";


@NgModule({
  declarations: [
    SettingsViewComponent
  ],
  imports: [
    CommonModule,
    ButtonsModule,
    FormsModule,
    ReactiveFormsModule,
    SmsPluginBaseComponentModule
  ]
})
export class SettingsViewModule { }
