import {Component, EventEmitter, OnInit, Output} from '@angular/core';
import {IFileUploaderOptions} from "../../../../packages/file-uploader/interfaces/file-uploader-options.interface";
import {SubnetMergerConstants} from "../../../../packages/subnet-merger/constants/subnet-merger.constants";
import {SubnetMergerBackendService} from "../../../../packages/subnet-merger/services/subnet-merger-backend.service";
import {SubnetMergerViewService} from "../../services/subnet-merger-view.service";
import {IonValidationCompletedEvent} from "../validation-result/validation-result.component";

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
  @Output() onReportCompleted: EventEmitter<IonValidationCompletedEvent> = new EventEmitter();
  @Output() onFileUploaded: EventEmitter<string> = new EventEmitter();

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

  public onFileUploadedFN($event): void {
    this.uploadedFileName = $event[SubnetMergerConstants.validateAPIKeys.NDTFileName];
    this.fileIsUploaded = true;
    this.subnetMergerViewService.refreshNDtsTable.emit();
    this.onFileUploaded.emit(this.uploadedFileName);
  }

  public onValidateClick(): void {
    this.validationIsRunning = true;
    this.subnetMergerBackend.validateNDTFile(this.uploadedFileName).subscribe({
      next: (data) => {
        this.activeValidationReportID = data[SubnetMergerConstants.reportAPIKeys.reportID];
        this.subnetMergerViewService.refreshNDtsTable.emit();
        this.subnetMergerViewService.refreshReportsTable.emit();
      }
    })
  }

  public onValidationCompleted($event:IonValidationCompletedEvent) {
    this.validationIsRunning = !$event.isReportCompleted;
    if ($event.isReportCompleted) {
      this.onFileValidated.emit(this.uploadedFileName);
      this.onReportCompleted.emit($event);
    }
  }

}
