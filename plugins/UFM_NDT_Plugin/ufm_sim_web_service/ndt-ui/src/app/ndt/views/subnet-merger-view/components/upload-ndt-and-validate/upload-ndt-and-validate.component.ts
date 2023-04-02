import {Component, EventEmitter, OnInit, Output} from '@angular/core';
import {IFileUploaderOptions} from "../../../../packages/file-uploader/interfaces/file-uploader-options.interface";

@Component({
  selector: 'app-upload-ndt-and-validate',
  templateUrl: './upload-ndt-and-validate.component.html',
  styleUrls: ['./upload-ndt-and-validate.component.scss']
})
export class UploadNdtAndValidateComponent implements OnInit {

  /**
   * @OUTPUTS
   */

  @Output() onFileValidated: EventEmitter<boolean> = new EventEmitter();

  /**
   * @VARIABLES
   */

  public fileUploaderConfig: IFileUploaderOptions = {
    url: '/ufmRestV2/Topology_Compare/networkdiff', // merger_upload_ndt
    filesTypes: []
  }

  public fileIsUploaded: boolean = false;
  public validationIsRunning = false;
  public activeValidationReportID = undefined;

  constructor() {
  }

  ngOnInit(): void {
  }

  public get validateAvailable() {
    return this.fileIsUploaded && !this.validationIsRunning;
  }

  public onFileUploaded($event): void {
    this.fileIsUploaded = true;
  }

  public onValidateClick(): void {
    // request to merger_verify_ndt
    this.validationIsRunning = true;
    setTimeout(() => {
      this.activeValidationReportID = "111";
    }, 2000)
  }

  public onValidationCompleted($event) {
    this.validationIsRunning = !$event;
    if ($event) {
      this.onFileValidated.emit(true);
    }
  }

}
