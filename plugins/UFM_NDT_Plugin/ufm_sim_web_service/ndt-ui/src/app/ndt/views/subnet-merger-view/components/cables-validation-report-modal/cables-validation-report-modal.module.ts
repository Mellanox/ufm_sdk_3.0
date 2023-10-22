import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {CablesValidationReportModalComponent} from './cables-validation-report-modal.component';
import {CableValidationModule} from "../../../../packages/cable-validation/cable-validation.module";
import {TooltipModule} from "ngx-bootstrap/tooltip";


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
    TooltipModule
  ]
})
export class CablesValidationReportModalModule {
}
