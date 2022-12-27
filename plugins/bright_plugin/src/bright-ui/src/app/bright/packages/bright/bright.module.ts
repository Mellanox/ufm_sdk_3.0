import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import {BrightConstants} from "./constants/bright.constants";
import {BrightBackendService} from "./services/bright-backend.service";

@NgModule({
  imports: [
    CommonModule
  ],
  providers: [
    BrightBackendService,
    BrightConstants
  ],
  declarations: []
})
export class BrightModule { }
