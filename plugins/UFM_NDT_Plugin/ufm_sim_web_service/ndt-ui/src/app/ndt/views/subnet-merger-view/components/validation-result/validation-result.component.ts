import {
  ChangeDetectorRef,
  Component,
  EventEmitter,
  Input,
  OnChanges, OnDestroy,
  OnInit,
  Output,
  SimpleChanges,
  ViewChild
} from '@angular/core';
import {
  XCoreAgGridOptions
} from "../../../../../../../sms-ui-suite/x-core-ag-grid/x-core-ag-grid-options/x-core-ag-grid-options";
import {
  XCoreAgGridConstants
} from "../../../../../../../sms-ui-suite/x-core-ag-grid/constants/x-core-ag-grid.constants";
import {SubnetMergerConstants} from "../../../../packages/subnet-merger/constants/subnet-merger.constants";
import {SubnetMergerBackendService} from "../../../../packages/subnet-merger/services/subnet-merger-backend.service";

export enum NDTStatusTypes {
  running = "Running",
  completed = "Completed",
  completedSuccessfully = "Completed successfully",
  completedWithCriticalErrors = "Completed with critical errors",
  completedWithErrors = "Completed with errors"
}

export interface INDTValidationReport {
  status: NDTStatusTypes;
  timestamp: string;
  NDT_file: string;
  report: any;
  error?: any;
}

export interface IonValidationCompletedEvent {
  isReportCompleted: boolean,
  report: INDTValidationReport
}

@Component({
  selector: 'app-validation-result',
  templateUrl: './validation-result.component.html',
  styleUrls: ['./validation-result.component.scss']
})
export class ValidationResultComponent implements OnInit, OnChanges, OnDestroy {

  /**
   * @INPUTS
   */

  @Input() validationReportID: string | number;

  /**
   * @OUTPUT
   */
  @Output() onValidationCompleted = new EventEmitter<IonValidationCompletedEvent>();

  /**
   * @CHILDREN
   */

  @ViewChild('leftControlTemplate', {static: true}) leftControlTemplate;

  /**
   * @VARIABLES
   */

  report: INDTValidationReport;
  reportTableOptions: XCoreAgGridOptions = new XCoreAgGridOptions();
  pollingTimer;

  constructor(private subnetMergerBackendService: SubnetMergerBackendService,
              private cdr: ChangeDetectorRef) {
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (this.validationReportID) {
      this.onValidationCompletedFn();
      this._pollReport();
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

  private _pollReport(): void {
    this.report = undefined;
    this.cdr.detectChanges();
    this.subnetMergerBackendService.getValidationReports(this.validationReportID + '').subscribe({
      next: (data: INDTValidationReport) => {
        this.report = data;
        if (this.pollingTimer !== -1 && !this.isReportCompleted) {
          setTimeout(() => {
            this._pollReport();
          }, 5000);
        } else {
          clearTimeout(this.pollingTimer);
          this.pollingTimer = undefined;
          this.cdr.detectChanges();
          this.onValidationCompletedFn();
        }
      }
    })
  }

  public get reportOutputType() {
    return this.report && typeof this.report.report;
  }

  public get reportStatusClass() {
    let classes = ""
    switch (this.report.status) {
      case NDTStatusTypes.completedSuccessfully:
        classes = "success";
        break;
      case NDTStatusTypes.completedWithErrors:
        classes = "danger";
        break;
    }
    return classes;
  }

  public get isReportCompleted(): boolean {
    return this.report && this.report.status.toLowerCase().includes(NDTStatusTypes.completed.toLowerCase());
  }

  public onValidationCompletedFn() {
    this.onValidationCompleted.emit({
      isReportCompleted: this.isReportCompleted,
      report: this.report
    });
  }

  ngOnDestroy(): void {
    if (this.pollingTimer) {
      clearTimeout(this.pollingTimer);
    }
    this.pollingTimer = -1;
  }

}
