import {Component, EventEmitter, Input, OnInit, Output, ViewChild} from '@angular/core';
import {NewMergerWizardService} from "./services/new-merger-wizard.service";
import {XWizardComponent} from "../../../../../../../sms-ui-suite/x-wizard";
import {SubnetMergerBackendService} from "../../../../packages/subnet-merger/services/subnet-merger-backend.service";
import {SubnetMergerViewService} from "../../services/subnet-merger-view.service";
import {IonValidationCompletedEvent, NDTStatusTypes} from "../validation-result/validation-result.component";

@Component({
  selector: 'app-new-merger-wizard',
  templateUrl: './new-merger-wizard.component.html',
  styleUrls: ['./new-merger-wizard.component.scss']
})
export class NewMergerWizardComponent implements OnInit {

  /**
   * @INPUT
   */

  @Input() activeDeployedFile: string;

  /**
   * @OUTPUT
   */
  @Output() onMergeFinish: EventEmitter<any> = new EventEmitter<any>();

  /**
   * @CHILDREN
   */
  @ViewChild('wizard', {static: true}) wizardRef: XWizardComponent;

  /**
   * @VARIABLES
   */

  public deploying = false;
  public connected = false;
  public newUploadedFile: string;

  constructor(public newMergerWizardService: NewMergerWizardService,
              private subnetMergerViewService: SubnetMergerViewService,
              private subnetMergerBackend: SubnetMergerBackendService) {
  }

  ngOnInit(): void {
  }

  public onWizardFinish(): void {
    this.subnetMergerBackend.deployNDTFile(this.newUploadedFile).subscribe({
      next: (data) => {
        this.subnetMergerViewService.refreshReportsTable.emit();
        this.subnetMergerViewService.refreshNDtsTable.emit();
        this.onMergeFinish.emit(true);
      }
    })
  }

  public onWizardNext($event): void {

  }

  public openWizard() {
    this.deploying = false;
    this.connected = false;
    this.newMergerWizardService.initWizardTabs();
    this.wizardRef.openModal()
  }

  public onConnectClick(): void {
    this.deploying = true;
    this.subnetMergerBackend.updatePortsBoundaries(this.activeDeployedFile).subscribe({
      next: (data) => {
        this.subnetMergerBackend.deployNDTFile(this.activeDeployedFile).subscribe({
          next: (data) => {
            this.deploying = false;
            this.connected = true;
            this.newMergerWizardService.tabs[1].isDisabled = false;
            this.newMergerWizardService.tabs[0].isNextDisabled = false;
            this.subnetMergerViewService.refreshNDtsTable.emit();
          },
          error: () => {
            this.deploying = false;
          }
        })
      },
      error: () => {
        this.deploying = false;
      }
    })
  }

  public onFileValidated($event) {
    this.newUploadedFile = $event;
  }

  public onReportCompleted($event:IonValidationCompletedEvent) {
    if($event.isReportCompleted && $event.report.status != NDTStatusTypes.completedWithCriticalErrors) {
      this.newMergerWizardService.tabs[1].isNextDisabled = false;
    }
  }

}
