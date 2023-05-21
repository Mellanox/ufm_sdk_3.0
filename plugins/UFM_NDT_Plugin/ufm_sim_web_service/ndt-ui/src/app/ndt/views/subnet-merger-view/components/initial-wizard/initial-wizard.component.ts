import {Component, EventEmitter, OnInit, Output, ViewChild} from '@angular/core';
import {XWizardComponent} from "../../../../../../../sms-ui-suite/x-wizard";
import {InitialWizardService} from "./services/initial-wizard.service";
import {SubnetMergerBackendService} from "../../../../packages/subnet-merger/services/subnet-merger-backend.service";
import {SubnetMergerViewService} from "../../services/subnet-merger-view.service";
import {IonValidationCompletedEvent, NDTStatusTypes} from "../validation-result/validation-result.component";

@Component({
  selector: 'app-initial-wizard',
  templateUrl: './initial-wizard.component.html',
  styleUrls: ['./initial-wizard.component.scss']
})
export class InitialWizardComponent implements OnInit {

  /**
   * @OUTPUT
   */
  @Output() onDeployFinish: EventEmitter<any> = new EventEmitter<any>();

  /**
   * @CHILDREN
   */
  @ViewChild('wizard', {static: true}) wizardRef: XWizardComponent;

  /**
   * @VARIABLES
   */

  public selectedFileName: string;

  constructor(public initialWizardService: InitialWizardService,
              private subnetMergerViewService: SubnetMergerViewService,
              private subnetMergerBackendService: SubnetMergerBackendService) {
  }

  ngOnInit(): void {
  }

  public onWizardFinish(): void {
    this.subnetMergerBackendService.deployNDTFile(this.selectedFileName).subscribe({
      next: (data) => {
        this.subnetMergerViewService.refreshReportsTable.emit();
        this.subnetMergerViewService.refreshNDtsTable.emit();
        this.onDeployFinish.emit(true);
      }
    })
  }

  public onWizardNext($event): void {

  }

  public openWizard() {
    this.initialWizardService.initWizardTabs();
    this.wizardRef.openModal()
  }

  public onFileValidated($event) {
    this.selectedFileName = $event;
  }

  public onReportCompleted($event: IonValidationCompletedEvent) {
    this.initialWizardService.tabs[1].isDisabled = this.initialWizardService.tabs[1].isNextDisabled = this.initialWizardService.tabs[0].isNextDisabled = !$event.isFileDeployable;
  }

  public onFileUploaded($event) {
    this.initialWizardService.tabs[1].isDisabled = this.initialWizardService.tabs[1].isNextDisabled = this.initialWizardService.tabs[0].isNextDisabled = true;
  }

}
