/**
 * @MODULES
 */
import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {ButtonsModule} from 'ngx-bootstrap/buttons';
import {BsDatepickerModule} from "ngx-bootstrap/datepicker";
import {BsDropdownModule} from "ngx-bootstrap/dropdown";
import {SmsRadioButtonModule} from "../../../../../sms-ui-suite/sms-radio-button/sms-radio-button.module";

/**
 * @COMPONENTS
 */
import {TimePickerModalComponent} from "./time-picker-modal.component";


@NgModule({
  declarations: [
    TimePickerModalComponent
  ],
  exports: [
    TimePickerModalComponent
  ],
  imports: [
    CommonModule,
    FormsModule,
    ButtonsModule,
    SmsRadioButtonModule,
    BsDatepickerModule.forRoot(),
    BsDropdownModule.forRoot()
  ]
})
export class TimePickerModalModule {
}
