import {Component, OnInit} from '@angular/core';
import {FormControl, FormGroup} from "@angular/forms";
import {ICablesValidationSettings} from "../../packages/cable-validation/interfaces/cables-validation-status.interface";
import {SettingsViewService} from "./services/settings-view.service";
import {CableValidationConstants} from "../../packages/cable-validation/constants/cable-validation.constants";
import {CableValidationBackendService} from "../../packages/cable-validation/services/cable-validation-backend.service";
import {CV_MODE_ENUM} from "./enums/cv_mode.enum";


@Component({
  selector: 'app-settings-view',
  templateUrl: './settings-view.component.html',
  styleUrls: ['./settings-view.component.scss']
})
export class SettingsViewComponent implements OnInit {

  public cvSettingsForm: FormGroup;
  public mode: FormControl;
  public address: FormControl;
  public port: FormControl;
  public username: FormControl;
  public password: FormControl;
  public isLoading = true;

  public savedSettings: ICablesValidationSettings;

  constructor(public settingsViewService: SettingsViewService,
              private cvBackendService: CableValidationBackendService) {
  }

  public get CVConstants() {
    return CableValidationConstants;
  }

  public get CVModeEnum() {
    return CV_MODE_ENUM;
  }

  ngOnInit(): void {
    this._getCurrentConfigurations();
  }

  private _getCurrentConfigurations(): void {
    this.cvBackendService.getCableValidationConfigurations().subscribe({
      next: (data: ICablesValidationSettings) => {
        this.savedSettings = data;
        this._initFormFields(data);
        this.isLoading = false;
      },
      error: (err) => {
        this.savedSettings = undefined;
        this.isLoading = false;
      }
    })
  }

  private _initFormFields(data: ICablesValidationSettings): void {
    this.mode = this.settingsViewService.initModeFormControl(data.mode || CV_MODE_ENUM.LOCAL);
    this.address = this.settingsViewService.initAddressFormControl(data.address, this.mode.value);
    this.port = this.settingsViewService.initPortFormControl(data.port || 443, data.mode);
    this.username = this.settingsViewService.initUsernameFormControl(data.username, this.mode.value);
    this.password = this.settingsViewService.initPasswordFormControl('', this.mode.value);
    this.cvSettingsForm = new FormGroup({
      [CableValidationConstants.API_SERVER_KEYS.mode]: this.mode,
      [CableValidationConstants.API_SERVER_KEYS.address]: this.address,
      [CableValidationConstants.API_SERVER_KEYS.port]: this.port,
      [CableValidationConstants.API_SERVER_KEYS.username]: this.username,
      [CableValidationConstants.API_SERVER_KEYS.password]: this.password,
    })
    this.onModeChange()
  }


  public onModeChange(): void {
    if (this.settingsViewService.isCVLocal(this.mode.value)) {
      this.address.setValue('localhost');
      this.address.disable()
      this.port.disable()
      this.username.disable()
      this.password.disable()
    } else {
      this.address.setValue(this.savedSettings.address);
      this.address.enable()
      this.port.enable()
      this.username.enable()
      this.password.enable()
    }
  }

  public onSubmit(): void {
    this.isLoading = true;
    const payload: ICablesValidationSettings = Object.assign(
      {}, this.cvSettingsForm.value)
    if (payload.mode == CV_MODE_ENUM.LOCAL) {
      payload.address = 'localhost';
    }
    delete payload.mode;
    this.cvBackendService.updateCableValidationConfigurations(payload).subscribe({
      next: (data) => {
        this._getCurrentConfigurations();
      },
      error: () => {
        this.isLoading = false;
      }
    })
  }

}
