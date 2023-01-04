import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {BrightConfigurationsViewComponent} from './bright-configurations-view.component';
import {RouterModule} from '@angular/router';
import {BrightConfigurationsRoutes} from './bright-configurations.routes';
import {FormsModule, ReactiveFormsModule} from "@angular/forms";
import {ButtonsModule} from "ngx-bootstrap/buttons";
import {SpinnerModule} from 'sms-ui-suite/sms-spinner/spinner.module';
@NgModule({
  declarations: [
    BrightConfigurationsViewComponent
  ],
  exports: [
    BrightConfigurationsViewComponent
  ],
  imports: [
    CommonModule,
    RouterModule.forChild(BrightConfigurationsRoutes),
    SpinnerModule,
    ReactiveFormsModule,
    FormsModule,
    ButtonsModule
  ]
})
export class BrightConfigurationsViewModule {
}
