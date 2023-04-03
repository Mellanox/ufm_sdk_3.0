import {Component, EventEmitter, OnInit} from '@angular/core';
import {SubnetMergerConstants} from "../../../../packages/subnet-merger/constants/subnet-merger.constants";
import {
  XCoreAgGridConstants
} from "../../../../../../../sms-ui-suite/x-core-ag-grid/constants/x-core-ag-grid.constants";
import {
  XCoreAgGridOptions
} from "../../../../../../../sms-ui-suite/x-core-ag-grid/x-core-ag-grid-options/x-core-ag-grid-options";

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
export class ValidationReportsComponent implements OnInit {

  /**
   * @OUTPUTS
   */

  onReportSelectionChange: EventEmitter<IValidationReport> = new EventEmitter<IValidationReport>();


  /**
   * @VARIABLES
   */

  public tableOptions: XCoreAgGridOptions = new XCoreAgGridOptions();
  public reports: Array<IValidationReport> = [];
  public loading = false;
  public selectedReport: IValidationReport;

  constructor() {
  }

  ngOnInit(): void {
    this._setTableOptions();
    this.loadData();
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

  }

  public loadData() {
    this.loading = true;
    // TODO:: replace it with the response from merger_verify_ndt_reports
    setTimeout(() => {
      this.reports = [
        {
          "report_id": 1,
          "report_scope": "Single",
          "timestamp": "2023-03-23 13:57:21"
        },
        {
          "report_id": 2,
          "report_scope": "Single",
          "timestamp": "2023-03-23 13:57:22"
        },
        {
          "report_id": 3,
          "report_scope": "Single",
          "timestamp": "2023-03-23 14:41:29"
        },
        {
          "report_id": 4,
          "report_scope": "Single",
          "timestamp": "2023-03-23 15:00:15"
        },
        {
          "report_id": 5,
          "report_scope": "Single",
          "timestamp": "2023-03-23 16:00:13"
        },
        {
          "report_id": 6,
          "report_scope": "Single",
          "timestamp": "2023-03-23 16:03:23"
        },
        {
          "report_id": 7,
          "report_scope": "Single",
          "timestamp": "2023-03-23 16:08:53"
        },
        {
          "report_id": 8,
          "report_scope": "Single",
          "timestamp": "2023-03-23 16:11:42"
        },
        {
          "report_id": 9,
          "report_scope": "Single",
          "timestamp": "2023-03-23 16:13:40"
        },
        {
          "report_id": 10,
          "report_scope": "Single",
          "timestamp": "2023-03-23 16:17:18"
        }
      ]
      this.loading = false;
    }, 2000)
  }

  public onRowSelectionChange($event): void {
    if ($event && $event.length) {
      this.selectedReport = $event[0];
    } else {
      this.selectedReport = undefined;
    }
    this.onReportSelectionChange.emit(this.selectedReport);
  }

}
