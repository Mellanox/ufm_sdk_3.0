import {Component, EventEmitter, Input, OnInit, Output, ViewChild} from '@angular/core';
import {NewMergerWizardService} from "./services/new-merger-wizard.service";
import {XWizardComponent} from "../../../../../../../sms-ui-suite/x-wizard";

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

  constructor(public newMergerWizardService: NewMergerWizardService) {
  }

  ngOnInit(): void {
  }

  public onWizardFinish(): void {
    // deploy the new file with disabled ports boundaries
    //merger_update_topoconfig with
    /*{
    "ndt_file_name": "ndt_9",
    "boundary_port_state": "Disabled"
    }*/
    this.onMergeFinish.emit(true);
  }

  public onWizardNext($event): void {

  }

  public openWizard() {
    this.newMergerWizardService.initWizardTabs();
    this.wizardRef.openModal()
  }

  public onConnectClick(): void {
    //deploy the current active file with no-discover
    //merger_update_topoconfig with
    /*{
    "ndt_file_name": "ndt_9",
    "boundary_port_state": "No-discover"
    }*/
    this.deploying = true;
    setTimeout(() => {
      this.deploying = false;
      this.newMergerWizardService.tabs[1].isDisabled = false;
      this.newMergerWizardService.tabs[0].isNextDisabled = false;
    }, 1000)
  }

  public onFileValidated($event) {
    this.newMergerWizardService.tabs[1].isNextDisabled = false;
  }

}
