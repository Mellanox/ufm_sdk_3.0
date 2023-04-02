import {Component, OnInit} from '@angular/core';
import {
  SmsPluginBaseComponentComponent
} from "../../../../../sms-ui-suite/sms-plugin-base-component/sms-plugin-base-component.component";

@Component({
  selector: 'app-subnet-merger-view',
  templateUrl: './subnet-merger-view.component.html',
  styleUrls: ['./subnet-merger-view.component.scss']
})
export class SubnetMergerViewComponent extends SmsPluginBaseComponentComponent implements OnInit {

  public ndtFiles: Array<any> = [];


  constructor() {
    super();
  }

}
