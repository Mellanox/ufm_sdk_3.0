import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';

import {SubnetMergerViewComponent} from './subnet-merger-view.component';
import {InitialWizardComponent} from './components/initial-wizard/initial-wizard.component';
import {XWizardModule} from "../../../../../sms-ui-suite/x-wizard";
import {FileUploaderModule} from "../../packages/file-uploader";
import {
  SmsPluginBaseComponentModule
} from "../../../../../sms-ui-suite/sms-plugin-base-component/sms-plugin-base-component.module";
import {UploadNdtAndValidateComponent} from './components/upload-ndt-and-validate/upload-ndt-and-validate.component';
import {ValidationResultComponent} from './components/validation-result/validation-result.component';
import {XCoreAgGridModule} from "../../../../../sms-ui-suite/x-core-ag-grid/x-core-ag-grid.module";
import {NdtFilesViewComponent} from './components/ndt-files-view/ndt-files-view.component';
import {TooltipModule} from "ngx-bootstrap/tooltip";


@NgModule({
  declarations: [
    SubnetMergerViewComponent,
    InitialWizardComponent,
    UploadNdtAndValidateComponent,
    ValidationResultComponent,
    NdtFilesViewComponent
  ],
  imports: [
    CommonModule,
    XWizardModule,
    FileUploaderModule,
    SmsPluginBaseComponentModule,
    XCoreAgGridModule,
    TooltipModule
  ]
})
export class SubnetMergerViewModule {
}
