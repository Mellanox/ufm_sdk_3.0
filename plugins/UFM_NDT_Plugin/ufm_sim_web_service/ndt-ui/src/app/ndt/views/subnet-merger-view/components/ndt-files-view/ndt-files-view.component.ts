import {Component, Input, OnChanges, OnInit, SimpleChanges, ViewChild} from '@angular/core';
import {SubnetMergerConstants} from "../../../../packages/subnet-merger/constants/subnet-merger.constants";
import {
  XCoreAgGridOptions
} from "../../../../../../../sms-ui-suite/x-core-ag-grid/x-core-ag-grid-options/x-core-ag-grid-options";
import {
  XCoreAgGridConstants
} from "../../../../../../../sms-ui-suite/x-core-ag-grid/constants/x-core-ag-grid.constants";

export enum NDTFileStatus {
  new = "new",
  verified = "verified",
  deployed_no_discover = "deployed_no_discover",
  deployed = "deployed"
}

export interface INDTFile {
  [SubnetMergerConstants.NDTFileKeys.file]: string,
  [SubnetMergerConstants.NDTFileKeys.file_type]: string,
  [SubnetMergerConstants.NDTFileKeys.file_status]: NDTFileStatus,
  [SubnetMergerConstants.NDTFileKeys.timestamp]: string,
  [SubnetMergerConstants.NDTFileKeys.sha_1]: string
}

@Component({
  selector: 'app-ndt-files-view',
  templateUrl: './ndt-files-view.component.html',
  styleUrls: ['./ndt-files-view.component.scss']
})
export class NdtFilesViewComponent implements OnInit, OnChanges {

  /**
   * @INPUTS
   */
  @Input() ndtFiles: Array<INDTFile>;

  /**
   * CHILDREN
   */
  @ViewChild('fileNameTmp', {static: true}) fileNameTmp;
  @ViewChild('actionsTmp', {static: true}) actionsTmp;

  /**
   * @VARIABLES
   */
  public tableOptions: XCoreAgGridOptions = new XCoreAgGridOptions();
  public activeNDTFile: string;

  constructor() {
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['ndtFiles'] && this.ndtFiles?.length) {
      // merger_deployed_ndt request
      const resp = {
        "last_deployed_file": "ndt_3"
      }
      this.activeNDTFile = resp.last_deployed_file
    }
  }

  ngOnInit(): void {
    this._setTableOptions();
  }


  private _setTableOptions() {
    Object.assign(this.tableOptions.gridOptions,
      {
        [XCoreAgGridConstants.columnDefs]: [
          {
            [XCoreAgGridConstants.field]: SubnetMergerConstants.NDTFileKeys.timestamp,
            [XCoreAgGridConstants.headerName]: "Timestamp",
            [XCoreAgGridConstants.cellClass]: "center-aligned",
            [XCoreAgGridConstants.sort]: "desc",
          },
          {
            [XCoreAgGridConstants.field]: SubnetMergerConstants.NDTFileKeys.file,
            [XCoreAgGridConstants.headerName]: "File",
            [XCoreAgGridConstants.cellRendererParams]: {
              [XCoreAgGridConstants.ngTemplate]: this.fileNameTmp
            },
          },
          {
            [XCoreAgGridConstants.field]: SubnetMergerConstants.NDTFileKeys.file_status,
            [XCoreAgGridConstants.headerName]: "Status",
            [XCoreAgGridConstants.valueGetter]: (params) => {
              const _field = params.colDef.field;
              return params.data[_field].split("_").join(" ");
            },
            [XCoreAgGridConstants.cellClass]: "capitalize"
          },
          {
            [XCoreAgGridConstants.field]: "actions",
            [XCoreAgGridConstants.headerName]: "Actions",
            [XCoreAgGridConstants.cellRendererParams]: {
              [XCoreAgGridConstants.ngTemplate]: this.actionsTmp
            },
            [XCoreAgGridConstants.cellClass]: "center-aligned"
          },
        ]
      })
  }

  public get NDTFileStatus() {
    return NDTFileStatus
  }

  public onValidateClicked() {

  }

  public onDeployClicked() {

  }

}
