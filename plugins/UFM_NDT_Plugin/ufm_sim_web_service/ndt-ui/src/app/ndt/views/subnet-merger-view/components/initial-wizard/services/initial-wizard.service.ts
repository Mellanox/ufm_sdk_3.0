import {Injectable} from '@angular/core';
import {XWizardTab} from "../../../../../../../../sms-ui-suite/x-wizard";

@Injectable({
  providedIn: 'root'
})
export class InitialWizardService {
  public wizardConfig = {
    title: 'Bring Up Merger',
    action: 'Deploy'
  };

  public tabs: Array<XWizardTab>;

  constructor() {
  }

  public initWizardTabs() {
    const tabs = [new XWizardTab, new XWizardTab];
    tabs[0].name = 'Initiate';
    tabs[1].name = 'Deploy';
    tabs[0].isDisabled = false;
    tabs[1].isDisabled = true;
    tabs[0].isFirstTab = true;
    tabs[1].isLastTab = true;
    this.tabs = tabs;
  }

}
