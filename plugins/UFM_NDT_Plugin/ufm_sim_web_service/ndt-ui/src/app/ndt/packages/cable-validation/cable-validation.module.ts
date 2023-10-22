import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {CableValidationTableComponent} from './components/cable-validation-table/cable-validation-table.component';
import {XCoreAgGridModule} from "../../../../../sms-ui-suite/x-core-ag-grid/x-core-ag-grid.module";


@NgModule({
  declarations: [
    CableValidationTableComponent
  ],
  exports: [
    CableValidationTableComponent
  ],
  imports: [
    CommonModule,
    XCoreAgGridModule
  ]
})
export class CableValidationModule {
}
