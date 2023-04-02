import {Component, OnInit} from '@angular/core';
import {
  SmsPluginBaseComponentComponent
} from "../../../../../sms-ui-suite/sms-plugin-base-component/sms-plugin-base-component.component";
import {INDTFile, NDTFileStatus} from "./components/ndt-files-view/ndt-files-view.component";

@Component({
  selector: 'app-subnet-merger-view',
  templateUrl: './subnet-merger-view.component.html',
  styleUrls: ['./subnet-merger-view.component.scss']
})
export class SubnetMergerViewComponent extends SmsPluginBaseComponentComponent implements OnInit {

  public ndtFiles: Array<INDTFile> = [];
  public loading = true;

  constructor() {
    super();
  }

  ngOnInit() {
    super.ngOnInit();
    this.loadNDTFiles();
  }

  public onInitialDeployFinish($event) {
    this.loadNDTFiles();
  }

  public loadNDTFiles() {
    // TODO:: should be replaced with request to merger_ndts_list
    this.loading = true;
    setTimeout(() => {
      this.ndtFiles = [
        {
          "file": "ndt_1",
          "timestamp": "2023-03-09 11:30:53",
          "sha-1": "1705f730ec164d32d4b7f7d18489dd40f3d1c99c",
          "file_type": "current_topo",
          "file_status": NDTFileStatus.verified
        },
        {
          "file": "ndt_3",
          "timestamp": "2023-03-16 10:16:28",
          "sha-1": "1705f730ec164d32d4b7f7d18489dd40f3d1c99c",
          "file_type": "current_topo",
          "file_status": NDTFileStatus.deployed_no_discover
        },
        {
          "file": "ndt_4",
          "timestamp": "2023-03-16 10:53:00",
          "sha-1": "1705f730ec164d32d4b7f7d18489dd40f3d1c99c",
          "file_type": "current_topo",
          "file_status": NDTFileStatus.deployed
        },
        {
          "file": "ndt_9",
          "timestamp": "2023-03-23 10:10:22",
          "sha-1": "b23531eaa2bd884df2c0d9e0085cfff32aa7ea25",
          "file_type": "current_topo",
          "file_status": NDTFileStatus.deployed
        }
      ];
      this.loading = false;
    }, 2000)
  }

}
