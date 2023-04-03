import {Component, EventEmitter, OnInit, Output} from '@angular/core';
import {IFileUploaderOptions} from "../../../../packages/file-uploader/interfaces/file-uploader-options.interface";
import {SubnetMergerConstants} from "../../../../packages/subnet-merger/constants/subnet-merger.constants";
import {SubnetMergerBackendService} from "../../../../packages/subnet-merger/services/subnet-merger-backend.service";
import {SubnetMergerViewService} from "../../services/subnet-merger-view.service";

@Component({
  selector: 'app-upload-ndt-and-validate',
  templateUrl: './upload-ndt-and-validate.component.html',
  styleUrls: ['./upload-ndt-and-validate.component.scss']
})
export class UploadNdtAndValidateComponent implements OnInit {

  /**
   * @OUTPUTS
   */

  @Output() onFileValidated: EventEmitter<string> = new EventEmitter();

  /**
   * @VARIABLES
   */

  public fileUploaderConfig: IFileUploaderOptions = {
    url: SubnetMergerConstants.mergerAPIs.uploadNDT, // merger_upload_ndt
    filesTypes: ['.csv', '.txt']
  }

  public fileIsUploaded: boolean = false;
  public uploadedFileName: string;
  public validationIsRunning = false;
  public activeValidationReportID = undefined;

  constructor(private subnetMergerBackend: SubnetMergerBackendService,
              private subnetMergerViewService: SubnetMergerViewService) {
  }

  ngOnInit(): void {
  }

  public get validateAvailable() {
    return this.fileIsUploaded && !this.validationIsRunning;
  }

  public onFileUploaded($event): void {
    this.uploadedFileName = $event[SubnetMergerConstants.validateAPIKeys.NDTFileName];
    this.fileIsUploaded = true;
    this.subnetMergerViewService.refreshNDtsTable.emit();
  }

  public onValidateClick(): void {
    this.validationIsRunning = true;
    this.subnetMergerBackend.validateNDTFile(this.uploadedFileName).subscribe({
      next: (data) => {
        this.activeValidationReportID = data[SubnetMergerConstants.reportAPIKeys.reportID];
        this.subnetMergerViewService.refreshReportsTable.emit();
      }
    })
  }

  public onValidationCompleted($event) {
    this.validationIsRunning = !$event;
    if ($event) {
      this.onFileValidated.emit(this.uploadedFileName);
    }
  }

}
