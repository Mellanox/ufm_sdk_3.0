import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { SettingsViewComponent } from './settings-view.component';
import {FormsModule, ReactiveFormsModule} from "@angular/forms";
import {ButtonsModule} from "ngx-bootstrap/buttons";


@NgModule({
  declarations: [
    SettingsViewComponent
  ],
  imports: [
    CommonModule,
    ButtonsModule,
    FormsModule,
    ReactiveFormsModule,
  ]
})
export class SettingsViewModule { }
