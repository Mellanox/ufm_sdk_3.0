import {
  ChangeDetectorRef,
  Component,
  EventEmitter,
  OnChanges,
  OnInit,
  Output,
  SimpleChanges,
  ViewChild
} from '@angular/core';
import {SubnetMergerConstants} from "../../../../packages/subnet-merger/constants/subnet-merger.constants";
import {
  XCoreAgGridOptions
} from "../../../../../../../sms-ui-suite/x-core-ag-grid/x-core-ag-grid-options/x-core-ag-grid-options";
import {
  XCoreAgGridConstants
} from "../../../../../../../sms-ui-suite/x-core-ag-grid/constants/x-core-ag-grid.constants";
import {SubnetMergerBackendService} from "../../../../packages/subnet-merger/services/subnet-merger-backend.service";
import {SubnetMergerViewService} from "../../services/subnet-merger-view.service";
import {finalize, Subscription} from "rxjs";

export enum NDTFileStatus {
  new = "new",
  verified = "verified",
  deployed_no_discover = "deployed_no_discover",
  deployed_completed = "deployed_completed",
  deployed_disabled = "deployed_disabled",
  deployed = "deployed"
}

export enum NDTFileCapabilities {
  Verify = "Verify",
  Deploy = "Deploy",
  Update = "Update",
  Remove = "Remove"
}

export interface INDTFile {
  [SubnetMergerConstants.NDTFileKeys.file]: string,
  [SubnetMergerConstants.NDTFileKeys.file_type]: string,
  [SubnetMergerConstants.NDTFileKeys.file_status]: NDTFileStatus,
  [SubnetMergerConstants.NDTFileKeys.timestamp]: string,
  [SubnetMergerConstants.NDTFileKeys.sha_1]: string,
  [SubnetMergerConstants.NDTFileKeys.file_capabilities]: any,
}

@Component({
  selector: 'app-ndt-files-view',
  templateUrl: './ndt-files-view.component.html',
  styleUrls: ['./ndt-files-view.component.scss']
})
export class NdtFilesViewComponent implements OnInit, OnChanges {

  /**
   * @OUTPUT
   */

  @Output() onNewMerger: EventEmitter<any> = new EventEmitter<any>();

  /**
   * CHILDREN
   */
  @ViewChild('fileNameTmp', {static: true}) fileNameTmp;
  @ViewChild('actionsTmp', {static: true}) actionsTmp;
  @ViewChild('rightControlTemplates', {static: true}) rightControlTemplates;

  /**
   * @VARIABLES
   */
  public ndtFiles: Array<INDTFile>;
  public tableOptions: XCoreAgGridOptions = new XCoreAgGridOptions();
  public activeNDTFile: string;
  public loading = false;
  public refreshSub: Subscription;

  constructor(private cdr: ChangeDetectorRef,
              private subnetMergerBackend: SubnetMergerBackendService,
              public subnetMergerViewService: SubnetMergerViewService) {
  }

  ngOnChanges(changes: SimpleChanges): void {

  }

  ngOnInit(): void {
    this._setTableOptions();
    this.loadNDTFiles();
    this.refreshSub = this.subnetMergerViewService.refreshNDtsTable.subscribe(() => {
      this.loadNDTFiles();
    })
  }

  ngOnDestroy(): void {
    if (this.refreshSub) {
      this.refreshSub.unsubscribe();
    }
  }

  public onInitialDeployFinish($event) {
    this.loadNDTFiles();
  }

  public loadNDTFiles() {
    this.loading = true;
    this.cdr.detectChanges();
    this.subnetMergerBackend.getNDTsList().pipe(finalize(() => {
      this.loading = false;
      this.cdr.detectChanges();
    })).subscribe({
      next: (data) => {
        this.subnetMergerBackend.getActiveDeployedFile().subscribe({
          next: (activeDeployedFile) => {
            if (activeDeployedFile && activeDeployedFile[SubnetMergerConstants.NDTFileKeys.last_deployed_file]) {
              this.activeNDTFile = activeDeployedFile[SubnetMergerConstants.NDTFileKeys.last_deployed_file]
            }

            this.ndtFiles = data.map((file) => {
              const fileCapabilities = {};
              file.file_capabilities.split(",").forEach((cap) => {
                if (cap && cap.length) {
                  fileCapabilities[cap] = cap;
                }
              });
              if (file.file != this.activeNDTFile) {
                fileCapabilities[NDTFileCapabilities.Remove] = NDTFileCapabilities.Remove;
              }
              file.file_capabilities = fileCapabilities;
              return file;
            }).slice();
            this.cdr.detectChanges();
          }
        })
      }
    })
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
            [XCoreAgGridConstants.cellClass]: "center-aligned",
            [XCoreAgGridConstants.maxWidth]: 100
          },
        ]
      });

    Object.assign(this.tableOptions.extraOptions, {
      [XCoreAgGridConstants.rightAdditionalControlsTemplate]: this.rightControlTemplates,
      [XCoreAgGridConstants.suppressColumnsFiltering]: true
    })
  }

  public get NDTFileCapabilities() {
    return NDTFileCapabilities
  }

  public onValidateClicked(row: INDTFile) {
    this.subnetMergerBackend.validateNDTFile(row.file).subscribe({
      next: (data) => {
        this.subnetMergerViewService.refreshReportsTable.emit();
      }
    })
  }

  public onDeployClicked(row: INDTFile) {
    this.subnetMergerBackend.deployNDTFile(row.file).subscribe({
      next: (data) => {
        this.subnetMergerViewService.refreshNDtsTable.emit();
      }
    })
  }

  public onRemoveClicked(row: INDTFile) {
    this.subnetMergerBackend.deleteNDTFile(row.file).subscribe({
      next: (data) => {
        this.subnetMergerViewService.refreshNDtsTable.emit();
      }
    })
  }

}
