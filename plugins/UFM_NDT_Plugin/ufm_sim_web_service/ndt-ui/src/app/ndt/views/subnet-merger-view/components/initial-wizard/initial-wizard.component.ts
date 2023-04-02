import {Component, OnInit, ViewChild} from '@angular/core';
import {XWizardComponent} from "../../../../../../../sms-ui-suite/x-wizard";
import {InitialWizardService} from "./services/initial-wizard.service";

@Component({
  selector: 'app-initial-wizard',
  templateUrl: './initial-wizard.component.html',
  styleUrls: ['./initial-wizard.component.scss']
})
export class InitialWizardComponent implements OnInit {

  /**
   * @CHILDREN
   */
  @ViewChild('wizard', {static: true}) wizardRef: XWizardComponent;

  constructor(public initialWizardService: InitialWizardService) {
  }

  ngOnInit(): void {
  }

  public onWizardFinish(): void {

  }

  public onWizardNext($event): void {

  }

  public openWizard() {
    this.initialWizardService.initWizardTabs();
    this.wizardRef.openModal()
  }

  public onFileValidated($event) {
    this.initialWizardService.tabs[1].isDisabled = false;
    this.initialWizardService.tabs[0].isNextDisabled = false;
  }

}
