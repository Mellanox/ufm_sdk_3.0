import {Component, OnInit} from '@angular/core';
import {FormControl, FormGroup} from "@angular/forms";
import {BrightConstants} from "../../packages/bright/constants/bright.constants";
import {BrightConfigurationsViewService} from "./services/bright-configurations-view.service";
import {BrightBackendService} from "../../packages/bright/services/bright-backend.service";

@Component({
  selector: 'app-bright-configurations-view',
  templateUrl: './bright-configurations-view.component.html',
  styleUrls: ['./bright-configurations-view.component.scss']
})
export class BrightConfigurationsViewComponent implements OnInit {

  /**
   * @VARIABLES
   */
  public dataIsLoading = false;
  public updateInProgress = false;
  public BRIGHT_CONF_SERVER_KEYS = BrightConstants.brightConfKeys;
  public configurationsData;
  public configurationsForm: FormGroup;
  public enabled: FormControl;
  public status: FormControl;
  public host: FormControl;
  public port: FormControl;
  public certificate: FormControl;
  public certificateKey: FormControl;
  public dataRetentionPeriod: FormControl;

  constructor(private bcViewService: BrightConfigurationsViewService,
              private brightBackendService: BrightBackendService) {
  }

  ngOnInit(): void {
    this.dataIsLoading = true;
    this.brightBackendService.getBrightConf().subscribe({
      next: (data) => {
        data = data[this.BRIGHT_CONF_SERVER_KEYS.brightConfig]
        this.configurationsData = data;
        this.initFormFields(data)
        this.dataIsLoading = false;
      }
    })
  }

  private initFormFields(data): void {
    this.enabled = this.bcViewService.initEnabledFormControl(data[this.BRIGHT_CONF_SERVER_KEYS.enabled].toString());
    this.status = this.bcViewService.initConnectionStatusFormControl(data[this.BRIGHT_CONF_SERVER_KEYS.status]);
    this.host = this.bcViewService.initHostFormControl(data[this.BRIGHT_CONF_SERVER_KEYS.host]);
    this.port = this.bcViewService.initPortFormControl(data[this.BRIGHT_CONF_SERVER_KEYS.port]);
    this.certificate = this.bcViewService.initCertFormControl(data[this.BRIGHT_CONF_SERVER_KEYS.certificate]);
    this.certificateKey = this.bcViewService.initCertKeyFormControl(data[this.BRIGHT_CONF_SERVER_KEYS.certificateKey]);
    this.dataRetentionPeriod = this.bcViewService.initDataRetentionPeriodFormControl(data[this.BRIGHT_CONF_SERVER_KEYS.dataRetentionPeriod]);
    this.configurationsForm = new FormGroup({
      [this.BRIGHT_CONF_SERVER_KEYS.enabled]: this.enabled,
      [this.BRIGHT_CONF_SERVER_KEYS.status]: this.status,
      [this.BRIGHT_CONF_SERVER_KEYS.host]: this.host,
      [this.BRIGHT_CONF_SERVER_KEYS.port]: this.port,
      [this.BRIGHT_CONF_SERVER_KEYS.certificate]: this.certificate,
      [this.BRIGHT_CONF_SERVER_KEYS.certificateKey]: this.certificateKey,
      [this.BRIGHT_CONF_SERVER_KEYS.dataRetentionPeriod]: this.dataRetentionPeriod
    })
  }

  /**
   * @desc this function used to disable/enable form input depending on active value, it will be called when active value changed
   */
  public onStatusChange(): void {
    const value = this.enabled.value === 'true';
    if (!value) {
      this.configurationsForm.disable();
      this.enabled.enable();
    } else {
      this.configurationsForm.enable();
    }
  }

  private getConfPayload() {
    const payload = {
      [this.BRIGHT_CONF_SERVER_KEYS.brightConfig]: {
        [this.BRIGHT_CONF_SERVER_KEYS.enabled]: this.configurationsForm.value[this.BRIGHT_CONF_SERVER_KEYS.enabled] === 'true'
      }
    }
    if (payload[this.BRIGHT_CONF_SERVER_KEYS.brightConfig][this.BRIGHT_CONF_SERVER_KEYS.enabled]) {
      Object.assign(
        payload[this.BRIGHT_CONF_SERVER_KEYS.brightConfig],
        {
          [this.BRIGHT_CONF_SERVER_KEYS.host]: this.configurationsForm.value[this.BRIGHT_CONF_SERVER_KEYS.host],
          [this.BRIGHT_CONF_SERVER_KEYS.port]: this.configurationsForm.value[this.BRIGHT_CONF_SERVER_KEYS.port],
          [this.BRIGHT_CONF_SERVER_KEYS.certificate]: this.configurationsForm.value[this.BRIGHT_CONF_SERVER_KEYS.certificate],
          [this.BRIGHT_CONF_SERVER_KEYS.certificateKey]: this.configurationsForm.value[this.BRIGHT_CONF_SERVER_KEYS.certificateKey],
          [this.BRIGHT_CONF_SERVER_KEYS.dataRetentionPeriod]: `${this.configurationsForm.value[this.BRIGHT_CONF_SERVER_KEYS.dataRetentionPeriod]}d`
        }
      )
    }
    return payload;
  }

  public updateConfigurations(): void {
    this.updateInProgress = true;
    const payload = this.getConfPayload();
    this.brightBackendService.updateBrightConf(payload).subscribe({
      next: (data) => {
        this.initFormFields(data[this.BRIGHT_CONF_SERVER_KEYS.brightConfig]);
        this.updateInProgress = false;
      },
      error: () => {
        this.updateInProgress = false;
      }
    })
  }

}
