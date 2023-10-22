import {ChangeDetectorRef, Component, EventEmitter, OnDestroy, OnInit, Output, ViewChild} from '@angular/core';
import {SubnetMergerConstants} from "../../../../packages/subnet-merger/constants/subnet-merger.constants";
import {
  XCoreAgGridConstants
} from "../../../../../../../sms-ui-suite/x-core-ag-grid/constants/x-core-ag-grid.constants";
import {
  XCoreAgGridOptions
} from "../../../../../../../sms-ui-suite/x-core-ag-grid/x-core-ag-grid-options/x-core-ag-grid-options";
import {SubnetMergerBackendService} from "../../../../packages/subnet-merger/services/subnet-merger-backend.service";
import {SubnetMergerViewService} from "../../services/subnet-merger-view.service";
import {Subscription} from "rxjs";

export interface IValidationReport {
  [SubnetMergerConstants.reportAPIKeys.reportID]: number;
  [SubnetMergerConstants.reportAPIKeys.timestamp]: string;
  [SubnetMergerConstants.reportAPIKeys.reportScope]: string;
}

@Component({
  selector: 'app-validation-reports',
  templateUrl: './validation-reports.component.html',
  styleUrls: ['./validation-reports.component.scss']
})
export class ValidationReportsComponent implements OnInit, OnDestroy {

  /**
   * @CHILDREN
   */

  @ViewChild('rightControlTemplate', {static: true}) rightControlTemplate;


  /**
   * @OUTPUTS
   */

  @Output() onReportSelectionChange: EventEmitter<IValidationReport> = new EventEmitter<IValidationReport>();


  /**
   * @VARIABLES
   */

  public tableOptions: XCoreAgGridOptions = new XCoreAgGridOptions();
  public reports: Array<IValidationReport> = [];
  public loading = false;
  public refreshSub: Subscription;
  public selectedReport: IValidationReport;

  constructor(private subnetMergerBackend: SubnetMergerBackendService,
              private subnetMergerViewService: SubnetMergerViewService,
              private cdr: ChangeDetectorRef) {
  }

  ngOnInit(): void {
    this._setTableOptions();
    this.loadData();
    this.refreshSub = this.subnetMergerViewService.refreshReportsTable.subscribe(() => {
      this.loadData();
    })
  }

  private _setTableOptions() {
    Object.assign(this.tableOptions.gridOptions,
      {
        [XCoreAgGridConstants.columnDefs]: [
          {
            [XCoreAgGridConstants.field]: SubnetMergerConstants.reportAPIKeys.reportID,
            [XCoreAgGridConstants.headerName]: "ID",
            [XCoreAgGridConstants.cellClass]: "center-aligned"
          },
          {
            [XCoreAgGridConstants.field]: SubnetMergerConstants.NDTFileKeys.timestamp,
            [XCoreAgGridConstants.headerName]: "Timestamp",
            [XCoreAgGridConstants.cellClass]: "center-aligned",
            [XCoreAgGridConstants.sort]: "desc",
          }
        ]
      });

    Object.assign(this.tableOptions.extraOptions, {
      [XCoreAgGridConstants.suppressColumnsFiltering]: true,
      [XCoreAgGridConstants.rightAdditionalControlsTemplate]: this.rightControlTemplate
    })
    ;

  }

  public loadData() {
    this.loading = true;
    this.selectedReport = undefined;
    this.subnetMergerBackend.getValidationReports().subscribe({
      next: (data: Array<IValidationReport>) => {
        this.reports = data;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }

  public onRowSelectionChange($event): void {
    if ($event && $event.length) {
      this.selectedReport = $event[0];
    } else {
      this.selectedReport = undefined;
    }
    this.onReportSelectionChange.emit(this.selectedReport);
    this.cdr.detectChanges();
  }

  ngOnDestroy(): void {
    if (this.refreshSub) {
      this.refreshSub.unsubscribe();
    }
  }

}
