import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {CablesValidationReportModalComponent} from './cables-validation-report-modal.component';
import {CableValidationModule} from "../../../../packages/cable-validation/cable-validation.module";
import {PopoverModule} from "ngx-bootstrap/popover";
import {RouterModule} from "@angular/router";


@NgModule({
  declarations: [
    CablesValidationReportModalComponent
  ],
  exports: [
    CablesValidationReportModalComponent
  ],
  imports: [
    CommonModule,
    CableValidationModule,
    PopoverModule,
    RouterModule
  ]
})
export class CablesValidationReportModalModule {
}
