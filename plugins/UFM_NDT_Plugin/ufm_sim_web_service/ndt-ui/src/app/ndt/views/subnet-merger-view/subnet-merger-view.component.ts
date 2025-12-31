import {ChangeDetectorRef, Component, OnDestroy, OnInit, ViewChild} from '@angular/core';
import {INDTFile, NDTFileStatus} from "./components/ndt-files-view/ndt-files-view.component";
import {SubnetMergerBackendService} from "../../packages/subnet-merger/services/subnet-merger-backend.service";
import {
  IValidationReport
} from "./components/validation-reports/validation-reports.component";
import {NavigationEnd, Router} from "@angular/router";
import {finalize, Subscription} from "rxjs";
import {SubnetMergerViewService} from "./services/subnet-merger-view.service";

@Component({
  selector: 'app-subnet-merger-view',
  templateUrl: './subnet-merger-view.component.html',
  styleUrls: ['./subnet-merger-view.component.scss']
})
export class SubnetMergerViewComponent implements OnInit {

  public selectedReport: IValidationReport;
  public loading = true;

  constructor(private subnetMergerBackend: SubnetMergerBackendService,
              private subnetMergerViewService: SubnetMergerViewService,
              private router: Router,
              private cdr: ChangeDetectorRef) {
    this.router.events.subscribe((event) => {
      if (event instanceof NavigationEnd) {
        this.cdr.detectChanges();
      }
    });
  }

  ngOnInit() {
  }

  public onReportSelectionChange($event: IValidationReport) {
    this.selectedReport = $event;
    this.cdr.detectChanges();
  }


}
