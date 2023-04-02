import {Component, EventEmitter, OnInit, Output, ViewChild} from '@angular/core';
import {XWizardComponent} from "../../../../../../../sms-ui-suite/x-wizard";
import {InitialWizardService} from "./services/initial-wizard.service";

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

  constructor(public initialWizardService: InitialWizardService) {
  }

  ngOnInit(): void {
  }

  public onWizardFinish(): void {
    //merger_update_topoconfig with
    /*{
    "ndt_file_name": "ndt_9",
    "boundary_port_state": "Disabled"
    }*/
    this.onDeployFinish.emit(true);
  }

  public onWizardNext($event): void {

  }

  public openWizard() {
    this.initialWizardService.initWizardTabs();
    this.wizardRef.openModal()
  }

  public onFileValidated($event) {
    this.initialWizardService.tabs[1].isDisabled = false;
    this.initialWizardService.tabs[1].isNextDisabled = false;
    this.initialWizardService.tabs[0].isNextDisabled = false;
  }

}
