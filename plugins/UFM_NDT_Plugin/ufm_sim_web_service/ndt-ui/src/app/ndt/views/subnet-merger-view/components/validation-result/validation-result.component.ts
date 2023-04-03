import {Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges, ViewChild} from '@angular/core';
import {
  XCoreAgGridOptions
} from "../../../../../../../sms-ui-suite/x-core-ag-grid/x-core-ag-grid-options/x-core-ag-grid-options";
import {
  XCoreAgGridConstants
} from "../../../../../../../sms-ui-suite/x-core-ag-grid/constants/x-core-ag-grid.constants";
import {SubnetMergerConstants} from "../../../../packages/subnet-merger/constants/subnet-merger.constants";

export enum NDTStatusTypes {
  running = "Running",
  completed = "Completed successfully",
  completedWithErrors = "Completed with errors"
}

export interface INDTValidationReport {
  status: NDTStatusTypes;
  timestamp: string;
  NDT_file: string;
  report: any;
}

@Component({
  selector: 'app-validation-result',
  templateUrl: './validation-result.component.html',
  styleUrls: ['./validation-result.component.scss']
})
export class ValidationResultComponent implements OnInit, OnChanges {

  /**
   * @INPUTS
   */

  @Input() validationReportID: string | number;

  /**
   * @OUTPUT
   */
  @Output() onValidationCompleted = new EventEmitter<boolean>();

  /**
   * @CHILDREN
   */

  @ViewChild('leftControlTemplate', {static: true}) leftControlTemplate;

  /**
   * @VARIABLES
   */

  report: INDTValidationReport;
  reportTableOptions: XCoreAgGridOptions = new XCoreAgGridOptions();

  constructor() {
  }

  ngOnChanges(changes: SimpleChanges): void {
    // should poll the provided validationReportID
    //merger_verify_ndt_reports/validationReportID
    if (this.validationReportID) {
      this.onValidationCompleted.emit(this.isReportCompleted);
      // TODO:: remove static data after the e2e integration
      this.report =
        {
          "status": NDTStatusTypes.running,
          "timestamp": "2023-03-14 09:27:06",
          "NDT_file": "ndt_1",
          "report": ""
        }
      setTimeout(() => {
        this.report =
          {
            "status": NDTStatusTypes.completed,
            "timestamp": "2023-03-14 09:27:06",
            "NDT_file": "ndt_1",
            // "report": "NDT and IBDIAGNET are fully match"
            "report": [
              {
                "category": "missing_in_ibdiagnet",
                "description": "SwitchX -  Mllanox Technologies/11 - SwitchIB Mellanox Technologies/6"
              },
              {
                "category": "error",
                "description": "Duplicated GUIDs detected in fabric: -E- Node GUID = 0x0002c90000000041 is duplicated at: Node = SW-0-0/U1, DR =  [0,1,5], -E- Node GUID = 0x0002c90000000041 is duplicated at: Node = SW-0-1/U1, DR =  [0,1,6]"
              }
            ]
          }
        this.onValidationCompleted.emit(this.isReportCompleted);
      }, 2000)
    }
  }

  ngOnInit(): void {
    this._setReportTableOptions();
  }

  private _setReportTableOptions() {
    Object.assign(this.reportTableOptions.gridOptions,
      {
        [XCoreAgGridConstants.columnDefs]: [
          {
            [XCoreAgGridConstants.field]: SubnetMergerConstants.reportAPIKeys.category,
            [XCoreAgGridConstants.headerName]: "Category",
            [XCoreAgGridConstants.valueGetter]: (params) => {
              const _field = params.colDef.field;
              return params.data[_field].split("_").join(" ");
            },
            [XCoreAgGridConstants.cellClass]: "capitalize",
            [XCoreAgGridConstants.filter]: XCoreAgGridConstants.checkboxFilter,
            [XCoreAgGridConstants.maxWidth]: 300
          },
          {
            [XCoreAgGridConstants.field]: SubnetMergerConstants.reportAPIKeys.description,
            [XCoreAgGridConstants.headerName]: "Description",
            [XCoreAgGridConstants.tooltipField]: SubnetMergerConstants.reportAPIKeys.description,
          }
        ]
      })

    Object.assign(this.reportTableOptions.extraOptions, {
      [XCoreAgGridConstants.leftAdditionalControlsTemplate]: this.leftControlTemplate
    })
  }

  public get reportOutputType() {
    return this.report && typeof this.report.report;
  }

  public get reportStatusClass() {
    let classes = ""
    switch (this.report.status) {
      case NDTStatusTypes.completed:
        classes = "success";
        break;
      case NDTStatusTypes.completedWithErrors:
        classes = "danger";
        break;
    }
    return classes;
  }

  public get isReportCompleted(): boolean {
    return this.report &&
      (this.report.status === NDTStatusTypes.completed || this.report.status === NDTStatusTypes.completedWithErrors)
  }

}
